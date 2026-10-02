from __future__ import annotations
import datetime as dt, json
from .errors import GitHubError

PR_TITLE = "PRISMA curated recovery: automated AutoGit batch"

def _policy_blocked(text: str) -> bool:
    low=(text or "").lower()
    return ("base branch policy prohibits" in low or "add the `--auto` flag" in low or "add the --auto flag" in low or "not mergeable" in low)

def _read_latest_state(ctx) -> dict:
    try:
        p=ctx.out/"autogit latest state.json"
        if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        ctx.artifact("latest_state_read_warning.txt").write_text(repr(exc), encoding="utf-8")
    return {}

def _try_reuse_open_pr(ctx, gh, head_sha: str):
    state=_read_latest_state(ctx); opened=state.get("opened_pr") or {}; url=opened.get("url") or ""
    if not url: return None
    view=gh.view(url); ctx.artifact("gh_pr_reuse_candidate.json").write_text(json.dumps(view, indent=2, ensure_ascii=False), encoding="utf-8")
    if str(view.get("state","")).upper()=="OPEN" and str(view.get("headRefOid") or "")==head_sha:
        return {"url":url,"number":opened.get("number",""),"head":opened.get("head",view.get("headRefName","")),"base":opened.get("base",view.get("baseRefName","")),"reused":True}
    return None

def _write_pr_summary(ctx, name: str, data: dict) -> None:
    ctx.artifact(name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _require_pr_head(gh, pr_url: str, expected_head: str, phase: str) -> dict:
    view=gh.view(pr_url)
    if view.get("_error") or view.get("_parse_error"): raise GitHubError(f"GitHub PR view unavailable during {phase}", phase="pr-gate", detail={"view":view})
    state=str(view.get("state") or "").upper(); actual=str(view.get("headRefOid") or "")
    if state!="OPEN": raise GitHubError(f"PR is not open during {phase}", phase="pr-gate", detail={"state":state})
    if not actual or actual!=expected_head: raise GitHubError(f"PR head changed before {phase}", phase="pr-gate", detail={"expected_head":expected_head,"actual_head":actual})
    return view

def _post_merge_proof(ctx, gh, git, remote: str, base: str, pr_url: str, pr_number: str, pr_head_sha: str, auto: bool) -> dict:
    status, post = gh.wait_merged(pr_url, 60, 2)
    if status != "merged": raise GitHubError("Merge did not reach merged state", phase="post-merge", detail={"status":status,"view":post})
    merge_obj=post.get("mergeCommit") if isinstance(post.get("mergeCommit"),dict) else {}
    merge_sha=str(merge_obj.get("oid") or "")
    merged_at=str(post.get("mergedAt") or "")
    if not merge_sha or not merged_at: raise GitHubError("Merged PR lacks merge SHA or mergedAt", phase="post-merge")
    git.fetch(remote,base); origin=f"{remote}/{base}"; canonical_head=git.rev_parse(origin)
    if not git.is_ancestor(merge_sha,canonical_head): raise GitHubError("Merged commit is not an ancestor of canonical main",phase="post-merge",detail={"merge_sha":merge_sha,"canonical_head":canonical_head})
    proof={"schemaVersion":"prisma.autogit.post-merge-proof.v1","prNumber":pr_number,"prHeadSha":pr_head_sha,"mergeSha":merge_sha,"canonicalMainHead":canonical_head,"mergedAt":merged_at,"headExactBeforeMerge":True,"mergeShaObservedByGitHub":True,"autoMergeUsed":auto}
    _write_pr_summary(ctx,"post_merge_proof.json",proof); return proof

def run_pr_gate(ctx, git, gh):
    git.assert_clean(); remote=ctx.policy.remote; base=ctx.policy.repo_expected_branch
    git.fetch(remote,base); origin=f"{remote}/{base}"
    if not git.is_ancestor(origin,"HEAD"): raise GitHubError("origin/main is not ancestor of HEAD; divergence detected",phase="pr-gate")
    ahead=git.ahead_count(origin,"HEAD")
    if ahead<=0: return {"result":"nothing_to_push","ahead":0}
    git.diff_check(f"{origin}..HEAD"); head_sha=git.rev_parse("HEAD")
    commits=ctx.shell.run(["git","log","--oneline",f"{origin}..HEAD"],check=True,name="git_log_pr_commits").stdout
    pr_body=ctx.artifact("PR_BODY.md")
    pr_body.write_text("## AutoGit curated batch\n\n```text\n"+commits.strip()+"\n```\n\n"+f"Ahead commits: {ahead}\n",encoding="utf-8")
    reused=_try_reuse_open_pr(ctx,gh,head_sha)
    if reused: pr=reused; ctx.opened_pr=pr; ctx.write_state("pr-reused",pr)
    else:
        branch=f"{ctx.policy.remote_branch_prefix}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        git.push_head(branch,remote); pr_obj=gh.create_pr(PR_TITLE,str(pr_body),base,branch); pr=pr_obj.__dict__; pr["reused"]=False; ctx.opened_pr=pr; ctx.write_state("pr-created",pr)
    ok,checks=gh.checks_watch(pr["url"], "forgeos-quality-gate"); ctx.artifact("gh_checks_watch.txt").write_text(checks,encoding="utf-8")
    if not ok: gh.capture_failed_check_logs(pr["url"],ctx.report_dir,"checks_failed"); raise GitHubError("GitHub checks failed",phase="pr-gate")
    # Server-side branch protection is the authoritative merge barrier; this local re-read closes AutoGit's own race window.
    _require_pr_head(gh,pr["url"],head_sha,"merge")
    merged,text=gh.merge(pr["url"],auto=False,delete_branch=True,expected_head=head_sha); ctx.artifact("gh_merge_attempt.txt").write_text(text,encoding="utf-8"); auto=False
    if not merged:
        if not _policy_blocked(text): gh.capture_failed_check_logs(pr["url"],ctx.report_dir,"merge_failed"); raise GitHubError("PR merge failed",phase="pr-gate",detail={"text":text})
        auto=True
        _require_pr_head(gh,pr["url"],head_sha,"enable-auto-merge")
        ok_auto,text_auto=gh.merge(pr["url"],auto=True,delete_branch=True,expected_head=head_sha); ctx.artifact("gh_auto_merge_enable.txt").write_text(text_auto,encoding="utf-8")
        if ok_auto:
            status,view=gh.wait_merged(pr["url"],ctx.policy.auto_merge_wait_seconds,30); _write_pr_summary(ctx,"gh_auto_merge_final.json",{"status":status,"view":view})
            if status=="merged": merged=True
            elif status=="pending": result={"result":"auto_merge_pending","pr":pr,"auto":True,"view":view,"ahead":ahead}; ctx.write_state("auto-merge-pending",result); return result
            else: raise GitHubError("Auto-merge reached terminal state without merge",phase="pr-gate",detail={"status":status,"view":view})
        else:
            view=gh.view(pr["url"]); policy_payload={"merge_attempt":text,"auto_merge_attempt":text_auto,"pr_view":view,"pr":pr,"ahead":ahead}
            _write_pr_summary(ctx,"branch_policy_blocked_auto_disabled.json",policy_payload)
            result={"result":"merge_blocked_auto_merge_disabled","pr":pr,"auto":False,"admin_merge_allowed":False,"view":view,"ahead":ahead,"next":"Enable repository auto-merge or manually merge the PR after required governance checks pass."}
            ctx.write_state("merge-blocked-auto-disabled",result); return result
    if not merged: raise GitHubError("Internal PR gate state error: merge path ended without merged=true",phase="pr-gate")
    proof=_post_merge_proof(ctx,gh,git,remote,base,pr["url"],str(pr.get("number") or ""),head_sha,auto)
    ctx.final_head=proof["canonicalMainHead"]
    result={"result":"merged","pr":pr,"auto_merge_enabled":auto,"admin_merge_used":False,"final_head":ctx.final_head,"merge_sha":proof["mergeSha"],"post_merge_proof":proof,"ahead":ahead}
    ctx.write_state("merged",result); return result
