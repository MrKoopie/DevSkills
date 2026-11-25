#!/usr/bin/env python3
"""Apply a prevalidated review-thread plan through gh or glab only."""

import argparse
import json
import subprocess
import sys
from urllib.parse import quote

from fetch_feedback import github, gitlab, run


def cli(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{command[0]} timed out after a write; inspect the thread before retrying") from error
    except OSError as error:
        raise RuntimeError(f"Cannot run {command[0]}: {error}") from error

    if result.returncode:
        raise RuntimeError(f"{command[0]} failed: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{command[0]} returned invalid JSON after a write; inspect the thread before retrying") from error

    if data.get("errors"):
        raise RuntimeError(f"{command[0]} reported an API error; inspect the thread before retrying")

    return data


def groups(records, provider):
    grouped = {}

    for record in records:
        if provider == "github" and record["source"] != "inline":
            continue

        thread_id = record.get("thread_id") if provider == "github" else record.get("discussion_id")

        if thread_id:
            grouped.setdefault(thread_id, []).append(record)

    for comments in grouped.values():
        comments.sort(key=lambda item: (item.get("created_at") or "", int(item["id"])))

    return grouped


def validate_plan(plan, data, current_user):
    if plan.get("head_sha") != data["head_sha"] or not data["head_sha"]:
        raise ValueError("Target head changed or is unavailable; refresh and revalidate feedback")

    provider = plan["provider"]
    grouped = groups(data["records"], provider)
    actions = plan.get("actions")

    if not isinstance(actions, list) or not actions:
        raise ValueError("Plan requires at least one action")

    seen = set()
    prepared = []

    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("Each action must be an object")

        thread_id = action.get("thread_id")

        if not isinstance(thread_id, str) or thread_id in seen:
            raise ValueError("Each action needs a unique thread_id")

        seen.add(thread_id)
        comments = grouped.get(thread_id)

        if not comments:
            raise ValueError(f"Thread {thread_id} was not found in complete feedback")

        latest = comments[-1]

        if latest["id"] != str(action.get("last_comment_id")):
            raise ValueError(f"Thread {thread_id} has a new comment; revalidate it")

        kind = action.get("action")

        if kind not in ("reply", "resolve"):
            raise ValueError(f"Unsupported action for {thread_id}")

        if kind == "reply" and latest.get("author") == current_user:
            raise ValueError(f"The latest comment in {thread_id} is already yours")

        revalidated = action.get("revalidated") is True

        if any(comment.get("resolved") is True for comment in comments) and (kind == "resolve" or not revalidated):
            raise ValueError(f"Thread {thread_id} is already resolved")

        if provider == "github" and any(comment.get("outdated") is True for comment in comments) and not revalidated:
            raise ValueError(f"Thread {thread_id} is outdated; revalidate it")

        if kind == "reply" and (not isinstance(action.get("body"), str) or not action["body"].strip()):
            raise ValueError(f"Reply body is required for {thread_id}")

        if provider == "gitlab" and kind == "resolve" and not any(comment.get("resolvable") is True for comment in comments):
            raise ValueError(f"GitLab discussion {thread_id} is not marked resolvable")

        root = next((comment for comment in comments if not comment.get("in_reply_to_id")), comments[0])
        prepared.append((action, root))

    return prepared


def perform(plan, prepared):
    provider = plan["provider"]
    repo = plan["repo"]
    number = int(plan["number"])
    host = ["--hostname", plan["host"]] if plan.get("host") else []
    results = []

    for action, root in prepared:
        thread_id = action["thread_id"]

        if provider == "github":
            owner, name = repo.split("/", 1)

            if action["action"] == "reply":
                endpoint = f"repos/{owner}/{name}/pulls/{number}/comments/{root['id']}/replies"
                command = ["gh", "api", *host, "-X", "POST", "-f", f"body={action['body']}", endpoint]
            else:
                query = "mutation($threadId: ID!) { resolveReviewThread(input: {threadId: $threadId}) { thread { id isResolved } } }"
                command = ["gh", "api", *host, "graphql", "-f", f"query={query}", "-F", f"threadId={thread_id}"]
        else:
            project = quote(repo, safe="")
            base = f"projects/{project}/merge_requests/{number}/discussions/{quote(thread_id, safe='')}"

            if action["action"] == "reply":
                command = ["glab", "api", *host, "-X", "POST", "-f", f"body={action['body']}", f"{base}/notes"]
            else:
                command = ["glab", "api", *host, "-X", "PUT", "-F", "resolved=true", base]

        response = cli(command)

        if provider == "github" and action["action"] == "resolve":
            resolved = (((response.get("data") or {}).get("resolveReviewThread") or {}).get("thread") or {}).get("isResolved")

            if resolved is not True:
                raise RuntimeError(f"Resolution of {thread_id} is uncertain; inspect the thread before retrying")

        if provider == "gitlab" and action["action"] == "resolve":
            confirmed = run(["glab", "api", *host, base])

            if not any(note.get("resolved") is True for note in confirmed.get("notes", [])):
                raise RuntimeError(f"Resolution of {thread_id} is uncertain; inspect the thread before retrying")

        result = {
            "thread_id": thread_id,
            "action": action["action"],
            "url": response.get("html_url") or response.get("web_url") or root.get("url"),
        }
        results.append(result)
        print(f"Completed {result['action']} for {thread_id}: {result['url'] or 'no URL returned'}", file=sys.stderr, flush=True)

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Send the planned replies or resolutions")
    args = parser.parse_args()

    try:
        plan = json.load(sys.stdin)
        provider = plan["provider"]

        if provider not in ("github", "gitlab"):
            raise ValueError("provider must be github or gitlab")

        repo = plan["repo"]
        number = int(plan["number"])

        if "/" not in repo or number < 1:
            raise ValueError("Invalid repository or PR/MR number")

        target = argparse.Namespace(repo=repo, number=number, host=plan.get("host"))
        data = github(target) if provider == "github" else gitlab(target)
        host = ["--hostname", plan["host"]] if plan.get("host") else []
        user = run(["gh", "api", *host, "user"] if provider == "github" else ["glab", "api", *host, "user"])
        current_user = user.get("login") if provider == "github" else user.get("username")

        if not current_user:
            raise ValueError("Could not verify the authenticated user")

        prepared = validate_plan(plan, data, current_user)

        if args.execute:
            result = perform(plan, prepared)
        else:
            result = [{"thread_id": item["thread_id"], "action": item["action"]} for item, _ in prepared]

        print(json.dumps({"executed": args.execute, "results": result}, indent=2))
        return 0
    except (KeyError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
