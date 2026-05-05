# Phase 8 URL Lock

**Locked:** 2026-05-04
**Re-locked:** 2026-05-04 — handle corrected from `cdlee` to `opencdlee-dotcom` after `gh auth status` revealed the active account is `opencdlee-dotcom`. Original commit history references the prior URL; live source-of-truth is the values below.
**Decision-by:** user (08-01 Task 0 checkpoint, resolved upfront by /gsd-execute-phase orchestrator)
**Choice:** option-personal

RAW_INSTALL_URL: https://raw.githubusercontent.com/opencdlee-dotcom/osbuilder/main/install.sh
REPO_HTTPS_URL: https://github.com/opencdlee-dotcom/osbuilder
REPO_GIT_CLONE_URL: https://github.com/opencdlee-dotcom/osbuilder.git

## Why locked here

Pitfall 4 — install one-liner is a documentation lie until a real public repo
exists. Downstream plans (08-04 CI workflow, 08-05 CI surface, 08-06 README,
08-HUMAN-UAT.md clean-machine test) read this file to substitute the URL into
committed text.

## If `option-defer` was chosen

Not applicable — option-personal selected. URL fields above are concrete.
