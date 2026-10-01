# PRISMA Workstream Collision Gate

Status: \`CANONICAL_COORDINATION_ADAPTER\`

This is the missing coordination layer between the existing Factory Ledger, Authority Mesh/AutoMesh and Change Assurance machinery.

## Boundaries

Factory Ledger remains capability truth.

Authority Mesh / AutoMesh remains task-scoped authority, snapshot, drift and evidence.

Code Atlas / Change Assurance remains repository understanding and impact assurance.

This adapter reads live GitHub PR state and changed paths. It does not create another capability registry, authority engine, impact engine or source of truth.

## Machine-readable declaration

Governed technical PRs declare exactly one block:

\`\`\`text
<!-- PRISMA-WORKSTREAM
id: visual-canonical-registration-g01
role: canonical
requested_action: ADVANCE
capabilities: visual.canonical_promotion_integration_v1
surfaces: prisma-html, governance, quality
scope: prisma-html/tools/visual_promotion/canonical_registration/**
owner: optional-owner
-->
\`\`\`

The declaration is coordination metadata only.

## Roles

\`canonical\` — current chosen implementation line for a workstream.

\`proposal\` — candidate line; it stops when it collides with an active canonical line.

\`continuation\` — new line after a previous workstream completes. It must use a new workstream id.

The gate never selects a winner between competing canonical claims.

## Fail-closed rules

A governed PR without a valid declaration is blocked.

A declared capability id that does not exist in the current canonical Factory Ledger is blocked.

Two active PRs with the same workstream id conflict.

Two active PRs with the same capability id and overlapping governed scope conflict.

Two active PRs touching the same exclusive path conflict.

A workstream id already used by a merged PR cannot be silently reused.

If a canonical PR has a conflicting non-canonical peer, the canonical PR may proceed and the peer is the one that must stop. If two canonical claims collide, both stop for human reconciliation.

## Deliberate non-inference

The gate never chooses ownership from PR age, author, commit count, branch name or similarity.

Atlasfin similarity, selector similarity, filename similarity and token overlap are not authority.

Impact radius is not authorization.

The coordination result does not replace the Factory Ledger or Authority Mesh decision.

## Security

The workflow runs from the canonical default branch with \`pull_request_target\` and never executes arbitrary PR source.

Permissions are read-only for repository contents and pull requests.

The adapter never pushes, merges, closes, labels or mutates runtime state.

## Required merge enforcement

To make this a true merge barrier, the repository administrators must mark:

\`PRISMA Workstream Collision Gate / Workstream collision / ownership guard\`

as a required check for \`main\`.

That repository-settings operation is deliberately outside this source-level adapter.

## Current #595 / #596 incident

The two PRs modify 37 common paths, including the canonical-registration implementation subtree. This is exactly an exclusive workstream collision. The gate treats it as coordination evidence and never attempts to decide by code similarity which implementation should survive.

## Recommended sequence

Live PR change → Workstream Collision Gate → Factory Ledger Anti-Rework Proposal → task-exact Authority Mesh → Factory Ledger Mutation gate → domain verification → merge.

No gate promotes production, runtime or customer certification.
