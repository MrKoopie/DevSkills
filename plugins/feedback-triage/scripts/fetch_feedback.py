#!/usr/bin/env python3
"""Fetch complete PR/MR feedback through gh or glab, never direct HTTP."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote


def run(command):
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=300)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{command[0]} timed out for {command[-1]}") from error
    except OSError as error:
        raise RuntimeError(f"Cannot run {command[0]}: {error}") from error

    if result.returncode:
        raise RuntimeError(f"{command[0]} failed for {command[-1]}: {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{command[0]} returned invalid JSON: {error}") from error


def feedback_body(item, source):
    if "body" not in item or (item["body"] is not None and not isinstance(item["body"], str)):
        raise RuntimeError(f"{source} {item.get('id')} has an invalid body")

    return item["body"] or ""


def feedback_timestamp(item, source, fallback=None):
    value = item.get("created_at") or fallback

    if not isinstance(value, str):
        raise RuntimeError(f"{source} {item.get('id')} has an invalid timestamp")

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"{source} {item.get('id')} has an invalid timestamp") from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{source} {item.get('id')} has an invalid timestamp")

    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def require_head_sha(provider, *candidates):
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    raise RuntimeError(f"Missing current {provider} head SHA")


def github(args):
    owner, repo = args.repo.split("/", 1)
    base = f"repos/{owner}/{repo}"
    host = ["--hostname", args.host] if args.host else []
    metadata = run(["gh", "api", *host, f"{base}/pulls/{args.number}"])

    if not isinstance(metadata, dict) or not isinstance(metadata.get("head"), dict):
        raise RuntimeError("Missing current GitHub head SHA")

    head_sha = require_head_sha("GitHub", metadata["head"].get("sha"))
    records = []
    endpoints = (
        ("review", f"{base}/pulls/{args.number}/reviews?per_page=100"),
        ("inline", f"{base}/pulls/{args.number}/comments?per_page=100"),
        ("conversation", f"{base}/issues/{args.number}/comments?per_page=100"),
    )

    for kind, endpoint in endpoints:
        pages = run(["gh", "api", *host, "--paginate", "--slurp", endpoint])

        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise RuntimeError(f"Unexpected paginated response for {kind}")

        for page in pages:
            for item in page:
                if kind == "review" and isinstance(item, dict) and item.get("state") == "PENDING":
                    continue

                body = feedback_body(item, kind)
                created_at = feedback_timestamp(item, kind, item.get("submitted_at") if kind == "review" else None)
                records.append({
                    "source": kind,
                    "id": str(item["id"]),
                    "body": body,
                    "author": (item.get("user") or {}).get("login"),
                    "url": item.get("html_url"),
                    "path": item.get("path"),
                    "line": item.get("line"),
                    "review_id": item.get("pull_request_review_id"),
                    "in_reply_to_id": item.get("in_reply_to_id"),
                    "state": item.get("state"),
                    "commit_id": item.get("commit_id") if kind == "review" else None,
                    "submitted_at": item.get("submitted_at") if kind == "review" else None,
                    "created_at": created_at,
                })

    query = """query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $number) {
          reviewThreads(first: 100, after: $endCursor) {
            nodes {
              id
              isResolved
              isOutdated
              comments(first: 1) { nodes { databaseId } }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }"""
    thread_pages = run([
        "gh", "api", *host, "graphql", "--paginate", "--slurp",
        "-F", f"owner={owner}", "-F", f"repo={repo}",
        "-F", f"number={args.number}", "-f", f"query={query}",
    ])

    if not isinstance(thread_pages, list):
        raise RuntimeError("Unexpected paginated GitHub review threads response")

    threads_by_root = {}

    for page in thread_pages:
        if not isinstance(page, dict):
            raise RuntimeError("Missing GitHub review thread data")

        if page.get("errors"):
            raise RuntimeError("GitHub review thread query returned errors")

        try:
            threads = page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
        except (KeyError, TypeError) as error:
            raise RuntimeError("Missing GitHub review thread data") from error

        if not isinstance(threads, list):
            raise RuntimeError("Missing GitHub review thread data")

        for thread in threads:
            if not isinstance(thread, dict) or not isinstance(thread.get("comments"), dict):
                raise RuntimeError("Missing GitHub review thread data")

            roots = thread["comments"].get("nodes")

            if not isinstance(roots, list) or not roots or not isinstance(roots[0], dict) or roots[0].get("databaseId") is None:
                raise RuntimeError("Missing GitHub review thread root comment")

            threads_by_root[str(roots[0]["databaseId"])] = thread

    for record in records:
        if record["source"] != "inline":
            continue

        root_id = str(record["in_reply_to_id"] or record["id"])
        thread = threads_by_root.get(root_id)

        if thread is None:
            raise RuntimeError(f"Missing GitHub review thread for inline comment {record['id']}")

        try:
            record["thread_id"] = thread["id"]
            record["resolved"] = thread["isResolved"]
            record["outdated"] = thread["isOutdated"]
        except KeyError as error:
            raise RuntimeError(f"Missing GitHub review thread state for inline comment {record['id']}") from error

    return {
        "provider": "github",
        "target": metadata.get("html_url"),
        "head_sha": head_sha,
        "records": records,
        "counts": {kind: sum(record["source"] == kind for record in records) for kind, _ in endpoints},
    }


def gitlab(args):
    project = quote(args.repo, safe="")
    base = f"projects/{project}/merge_requests/{args.number}"
    host = ["--hostname", args.host] if args.host else []
    metadata = run(["glab", "api", *host, base])

    if not isinstance(metadata, dict):
        raise RuntimeError("Missing current GitLab head SHA")

    diff_refs = metadata.get("diff_refs")

    if not isinstance(diff_refs, dict):
        diff_refs = {}

    head_sha = require_head_sha("GitLab", metadata.get("sha"), diff_refs.get("head_sha"))
    records = []
    seen = set()
    endpoints = (
        ("discussion", f"{base}/discussions?per_page=100"),
        ("note", f"{base}/notes?per_page=100"),
    )

    for kind, endpoint in endpoints:
        items = run(["glab", "api", *host, "--paginate", endpoint])

        if not isinstance(items, list):
            raise RuntimeError(f"Unexpected paginated response for {kind}")

        for item in items:
            if not isinstance(item, dict):
                raise RuntimeError(f"Invalid {kind} response item")

            if kind == "discussion":
                notes = item.get("notes")

                if not isinstance(notes, list) or not notes:
                    raise RuntimeError(f"GitLab discussion {item.get('id')} has missing notes")
            else:
                notes = [item]

            for note in notes:
                note_id = str(note["id"])
                body = feedback_body(note, kind)
                created_at = feedback_timestamp(note, kind)

                if note_id in seen:
                    continue

                seen.add(note_id)
                position = note.get("position") or {}
                records.append({
                    "source": kind,
                    "id": note_id,
                    "discussion_id": item.get("id") if kind == "discussion" else None,
                    "resolved": note.get("resolved"),
                    "resolvable": note.get("resolvable"),
                    "individual_note": item.get("individual_note") if kind == "discussion" else None,
                    "system": note.get("system", False),
                    "body": body,
                    "author": (note.get("author") or {}).get("username"),
                    "url": note.get("web_url") or f"{metadata['web_url']}#note_{note_id}",
                    "path": position.get("new_path") or position.get("old_path"),
                    "line": position.get("new_line") or position.get("old_line"),
                    "created_at": created_at,
                })

    return {
        "provider": "gitlab",
        "target": metadata.get("web_url"),
        "head_sha": head_sha,
        "records": records,
        "counts": {kind: sum(record["source"] == kind for record in records) for kind, _ in endpoints},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=("github", "gitlab"))
    parser.add_argument("--repo", required=True, help="owner/repo or GitLab full project path")
    parser.add_argument("--number", required=True, type=int, help="PR number or MR IID")
    parser.add_argument("--host", help="GitHub or GitLab host for self-managed instances")
    args = parser.parse_args()

    if args.number < 1 or "/" not in args.repo or args.repo.startswith("/") or args.repo.endswith("/"):
        parser.error("provide a positive number and a full repository path")

    try:
        data = github(args) if args.provider == "github" else gitlab(args)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
