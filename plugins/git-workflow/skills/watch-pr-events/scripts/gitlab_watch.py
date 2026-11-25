"""Read and classify GitLab MR events for the shared watcher."""

from datetime import datetime
import hashlib
import json
import re
import subprocess
from urllib.parse import quote

PIPELINE_CONCLUSIONS = {
    "success": "success",
    "failed": "failure",
    "canceled": "cancelled",
    "skipped": "skipped",
}
API_ERRORS = (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError)


def api(command, host, endpoint, pages=False, query=None):
    args = ["glab", "api", "--hostname", host]
    if query is not None:
        args.extend(["--raw-field", f"query={query}"])
    if not pages:
        return json.loads(command([*args, endpoint]))
    # glab prints one JSON array per page, which may span multiple lines.
    data = command([*args, "--paginate", endpoint]).lstrip()
    decoder = json.JSONDecoder()
    items = []
    if not data:
        raise ValueError("Empty paginated GitLab response")
    while data:
        page, end = decoder.raw_decode(data)
        if not isinstance(page, list):
            raise ValueError("Expected a GitLab page array")
        items.extend(page)
        data = data[end:].lstrip()
    return items


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def pipeline_identity(pipeline):
    pipeline = pipeline or {}
    fields = ("project_id", "id", "sha", "ref", "status", "updated_at")
    group = (pipeline.get("detailed_status") or {}).get("group")
    return tuple(pipeline.get(key) for key in fields) + (group,)


def train_pipeline_matches(get, repo, mr, pipeline_id, sha):
    # GitLab GraphQL resolves headPipeline through diff_head_pipeline, which
    # checks the pipeline's checkout or original source SHA against diffHeadSha.
    query = (
        f"{{ project(fullPath: {json.dumps(repo)}) {{ "
        f'mergeRequest(iid: "{mr["iid"]}") {{ diffHeadSha headPipeline {{ id sha }} }} '
        "} }"
    )
    try:
        response = get("graphql", query=query)
    except API_ERRORS:
        return False
    if not isinstance(response, dict) or response.get("errors"):
        return False
    try:
        evidence = response["data"]["project"]["mergeRequest"]
        head_pipeline = evidence["headPipeline"]
        return (
            evidence["diffHeadSha"] == mr["sha"]
            and head_pipeline["id"] == f"gid://gitlab/Ci::Pipeline/{pipeline_id}"
            and head_pipeline["sha"] == sha
        )
    except (KeyError, TypeError):
        return False


def read_pipeline(get, repo, mr, expected):
    pipeline = mr.get("head_pipeline")
    if not pipeline:
        return {}, {}
    project, pipeline_id, sha, ref, status, _, group = pipeline_identity(pipeline)
    if not isinstance(project, int) or not isinstance(pipeline_id, int):
        raise ValueError("Missing GitLab pipeline identity")
    if sha != mr["sha"]:
        train_ref = f'refs/merge-requests/{mr["iid"]}/train'
        if (
            ref not in (f'refs/merge-requests/{mr["iid"]}/merge', train_ref)
            or not isinstance(sha, str)
            or not re.fullmatch(r"[a-f0-9]{40}", sha)
        ):
            return {}, {}
        try:
            commit = get(f"projects/{project}/repository/commits/{sha}")
        except API_ERRORS:
            commit = {}
        if not isinstance(commit, dict):
            commit = {}
        parents = commit.get("parent_ids") or []
        source_is_parent = (
            commit.get("id") == sha
            and isinstance(parents, list)
            and len(parents) == 2
            and parents[1] == mr["sha"]
        )
        # A train may rebase or squash the source before creating its checkout.
        if not source_is_parent and (
            ref != train_ref
            or not train_pipeline_matches(get, repo, mr, pipeline_id, sha)
        ):
            return {}, {}
    jobs = get(
        f"projects/{project}/pipelines/{pipeline_id}/jobs?per_page=100", pages=True
    )
    warnings = {
        f'job:{project}:{job["id"]}': {
            "project_id": project,
            "pipeline_id": str(pipeline_id),
            "job_id": job["id"],
            "fingerprint": "allowed_failure",
        }
        for job in jobs
        if job.get("allow_failure") is True and job["status"] == "failed"
    }
    if not warnings and group == "success-with-warnings":
        warnings[f"pipeline:{project}:{pipeline_id}"] = {
            "project_id": project,
            "pipeline_id": str(pipeline_id),
            "fingerprint": group,
        }
    selected = [
        job
        for job in jobs
        if (
            job["name"] in expected if expected else not job.get("allow_failure", False)
        )
    ]
    jobs_green = set(expected) <= {job["name"] for job in selected} and all(
        job["status"] == "success" or (not expected and job["status"] == "skipped")
        for job in selected
    )
    conclusion = PIPELINE_CONCLUSIONS.get(status)
    return {
        str(pipeline_id): {
            "name": "pipeline",
            "project_id": project,
            "sha": sha,
            "pipeline_status": status,
            "status": "completed" if conclusion else "in_progress",
            "conclusion": conclusion,
            "jobs_green": jobs_green,
            "jobs": {
                str(job["id"]): {"name": job["name"], "status": job["status"]}
                for job in selected
            },
        }
    }, warnings


def current_diff_time(get, endpoint, mr):
    refs = mr.get("diff_refs") or {}
    if refs.get("head_sha") != mr["sha"]:
        return None
    try:
        versions = get(f"{endpoint}/versions?per_page=1")
    except API_ERRORS:
        return None
    if (
        not isinstance(versions, list)
        or not versions
        or not isinstance(versions[0], dict)
    ):
        return None
    version = versions[0]
    if (
        version.get("head_commit_sha"),
        version.get("base_commit_sha"),
        version.get("start_commit_sha"),
    ) != (mr["sha"], refs.get("base_sha"), refs.get("start_sha")):
        return None
    return timestamp(version.get("created_at"))


def current_approvals(get, endpoint, mr, votes):
    diff_time = current_diff_time(get, endpoint, mr)
    if not diff_time:
        return {}
    current = {
        user: value
        for user, value in votes.items()
        if (approved_at := timestamp(value)) and approved_at > diff_time
    }
    if not current or len(current) == len(votes):
        return current

    # If GitLab retained votes across a push, its overall approval gate can
    # include those votes. Check whether current votes alone satisfy each rule.
    try:
        approval_state = get(f"{endpoint}/approval_state")
    except API_ERRORS:
        return {}  # The rule endpoint may be unavailable on this tier.
    rules = approval_state.get("rules") if isinstance(approval_state, dict) else None
    if not isinstance(rules, list):
        return {}
    for rule in rules:
        required = rule.get("approvals_required") if isinstance(rule, dict) else None
        if type(required) is not int or required < 0:
            return {}
        if required == 0:
            continue
        approvals = rule.get("approved_by")
        if rule.get("approved") is not True or not isinstance(approvals, list):
            return {}
        users = {
            str(entry["id"])
            for entry in approvals
            if isinstance(entry, dict) and "id" in entry
        }
        if len(current.keys() & users) < required:
            return {}
    return current


def snapshot(command, state):
    def get(endpoint, pages=False, query=None):
        return api(command, state["host"], endpoint, pages, query)

    endpoint = (
        f'projects/{quote(state["repo"], safe="")}/merge_requests/{state["number"]}'
    )

    def mr_snapshot(mr):
        status, head = mr.get("state"), mr.get("sha")
        if mr.get("iid") != state["number"] or status not in (
            "opened",
            "merged",
            "closed",
        ):
            raise ValueError("Incomplete or transitional GitLab MR state")
        if status == "opened" and not re.fullmatch(r"[a-f0-9]{40}", head or ""):
            raise ValueError("Incomplete GitLab MR head")
        return {
            "provider": "gitlab",
            "head": head,
            "open": status == "opened",
            "merged": status == "merged",
            "merged_at": mr.get("merged_at"),
            "merge_commit_sha": mr.get("merge_commit_sha"),
            "feedback": {},
            "runs": {},
        }

    mr = get(endpoint)
    result = mr_snapshot(mr)
    if not result["open"]:
        return result

    feedback = result["feedback"]
    discussion_resolution = result["discussion_resolution"] = {}
    for discussion in get(f"{endpoint}/discussions?per_page=100", pages=True):
        resolved_notes = []
        for note in discussion["notes"]:
            author = (note.get("author") or {}).get("username", "")
            if (
                not note.get("system")
                and author.casefold() != state["actor"].casefold()
            ):
                feedback[f'note:{note["id"]}'] = fingerprint(note.get("body") or "")
            if note.get("resolvable") is True and isinstance(
                note.get("resolved"), bool
            ):
                resolved_notes.append(note["resolved"])
        if resolved_notes and discussion.get("id"):
            discussion_resolution[discussion["id"]] = all(resolved_notes)

    approvals = get(f"{endpoint}/approvals")
    reviewers = get(f"{endpoint}/reviewers?per_page=100", pages=True)
    votes = {
        str(item["user"]["id"]): item.get("approved_at")
        for item in approvals["approved_by"]
    }
    reviews = {
        str(item["user"]["id"]): item["state"]
        for item in reviewers
        if item.get("state")
        in ("reviewed", "requested_changes", "approved", "unapproved")
    }
    feedback["review:state"] = fingerprint([approvals.get("approved"), votes, reviews])
    merge_status = mr.get("detailed_merge_status")
    if (
        state.get("until_ready")
        and approvals.get("approved") is True
        and votes
        and merge_status
        not in ("approvals_syncing", "preparing", "not_approved", "requested_changes")
        and "requested_changes" not in reviews.values()
    ):
        current = current_approvals(get, endpoint, mr, votes)
        if current:
            result.update(
                review_decision="APPROVED",
                opinions={
                    user: {
                        "state": "APPROVED",
                        "commit_id": mr["sha"],
                        "approved_at": value,
                    }
                    for user, value in current.items()
                },
            )
    result["runs"], result["ci_warnings"] = read_pipeline(
        get, state["repo"], mr, state.get("jobs", [])
    )

    confirmed = get(endpoint)
    confirmed_snapshot = mr_snapshot(confirmed)
    if not confirmed_snapshot["open"]:
        return confirmed_snapshot
    fields = ("sha", "diff_refs", "detailed_merge_status", "updated_at")
    if any(mr.get(key) != confirmed.get(key) for key in fields) or pipeline_identity(
        mr.get("head_pipeline")
    ) != pipeline_identity(confirmed.get("head_pipeline")):
        raise RuntimeError("GitLab MR or pipeline changed during snapshot")
    return result
