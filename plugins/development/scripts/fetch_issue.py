#!/usr/bin/env python3
"""Fetch a complete issue snapshot through gh or glab, never direct HTTP."""

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
from urllib.parse import quote


def run_json(command: list[str]) -> object:
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


def require_aware_timestamp(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label} is missing its timestamp")

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"{label} has an invalid timestamp") from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{label} timestamp has no timezone")

    return value


def normalize_issue(provider: str, issue: dict, comments: list[dict]) -> dict:
    if provider not in ("github", "gitlab") or not isinstance(issue, dict) or not isinstance(comments, list):
        raise RuntimeError("Incomplete or malformed issue response")

    number_key = "number" if provider == "github" else "iid"

    for key in ("id", number_key):
        value = issue.get(key)

        if type(value) is not int or value < 1:
            raise RuntimeError(f"Issue response is missing a valid {key}")

    target_key = "html_url" if provider == "github" else "web_url"
    target = issue.get(target_key)
    title = issue.get("title")

    if not isinstance(target, str) or not target or not isinstance(title, str) or not title:
        raise RuntimeError("Issue response is missing its URL or title")

    updated_at = require_aware_timestamp(issue.get("updated_at"), "Issue updated_at")
    body = issue.get("body") if provider == "github" else issue.get("description")

    if body is None:
        body = ""

    if not isinstance(body, str):
        raise RuntimeError("Issue body has an unexpected shape")

    records = []

    for comment in comments:
        if not isinstance(comment, dict) or not isinstance(comment.get("id"), (int, str)) or isinstance(comment.get("id"), bool):
            raise RuntimeError("Issue comment is missing its ID")

        comment_body = comment.get("body")

        author = comment.get("user") if provider == "github" else comment.get("author")
        author_key = "login" if provider == "github" else "username"

        if not isinstance(comment_body, str) or not isinstance(author, dict) or not isinstance(author.get(author_key), str) or not author[author_key]:
            raise RuntimeError("Issue comment has an unexpected shape")

        comment_id = str(comment["id"])
        comment_url = comment.get(target_key)
        created_at = comment.get("created_at")

        if comment_url is not None and not isinstance(comment_url, str):
            raise RuntimeError("Issue comment has an unexpected URL")

        created_at = require_aware_timestamp(created_at, "Issue comment created_at")

        if provider == "gitlab" and not comment_url:
            comment_url = f"{target}#note_{comment_id}"

        if not isinstance(comment_url, str) or not comment_url:
            raise RuntimeError("Issue comment is missing its URL")

        records.append({
            "id": comment_id,
            "body": comment_body,
            "author": author[author_key],
            "url": comment_url,
            "created_at": created_at,
        })

    records.sort(key=lambda item: (
        datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).astimezone(timezone.utc),
        0 if item["id"].isdecimal() else 1,
        int(item["id"]) if item["id"].isdecimal() else item["id"],
    ))

    return {
        "provider": provider,
        "target": target,
        "title": title,
        "body": body,
        "updated_at": updated_at,
        "comments": records,
        "counts": {"comments": len(records)},
    }


def github_issue(repo: str, number: int, host: str | None) -> dict:
    owner, name = repo.split("/", 1)
    base = f"repos/{owner}/{name}/issues/{number}"
    host_args = ["--hostname", host] if host else []
    issue = run_json(["gh", "api", *host_args, base])
    pages = run_json(["gh", "api", *host_args, "--paginate", "--slurp", f"{base}/comments?per_page=100"])

    if not isinstance(issue, dict) or not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise RuntimeError("Incomplete or malformed GitHub issue response")

    if issue.get("number") != number:
        raise RuntimeError("GitHub issue response has an unexpected number")

    return normalize_issue("github", issue, [comment for page in pages for comment in page])


def gitlab_issue(repo: str, number: int, host: str | None) -> dict:
    project = quote(repo, safe="")
    base = f"projects/{project}/issues/{number}"
    host_args = ["--hostname", host] if host else []
    issue = run_json(["glab", "api", *host_args, base])
    notes = run_json(["glab", "api", *host_args, "--paginate", f"{base}/notes?per_page=100"])

    if not isinstance(issue, dict) or not isinstance(notes, list):
        raise RuntimeError("Incomplete or malformed GitLab issue response")

    if issue.get("iid") != number:
        raise RuntimeError("GitLab issue response has an unexpected IID")

    return normalize_issue("gitlab", issue, notes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=("github", "gitlab"))
    parser.add_argument("--repo", required=True, help="owner/repo or GitLab full project path")
    parser.add_argument("--number", required=True, type=int, help="Issue number or IID")
    parser.add_argument("--host", help="GitHub or GitLab host for self-managed instances")
    args = parser.parse_args(argv)
    parts = args.repo.split("/")

    if args.number < 1 or len(parts) < 2 or any(not part for part in parts) or (args.provider == "github" and len(parts) != 2):
        parser.error("provide a positive number and a full repository path")

    try:
        data = github_issue(args.repo, args.number, args.host) if args.provider == "github" else gitlab_issue(args.repo, args.number, args.host)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
