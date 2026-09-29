## Summary

## Checklist
- [ ] Tests
- [ ] Docs
- [ ] Security

## PRISMA Workstream (required for governed technical changes)

For changes under PRISMA governed technical scopes, include exactly one declaration:

<!-- PRISMA-WORKSTREAM
id: <unique-workstream-id>
role: proposal
requested_action: VERIFY
capabilities: <canonical-capability-id>
surfaces: <surface>
scope: <repo/path/**>
owner: <optional-owner>
-->

Use \`canonical\` only for the already-chosen active implementation line. Use \`continuation\` only for a genuinely new line after completion, and use a new \`id\`.

Do not invent capability IDs; Factory Ledger remains the capability authority.

## ForgeOS Evidence (if touching \`forgeos/**\` or \`docs/forgeos-foundation/**\`)
- [ ] \`STATUS\` included in PR description
- [ ] \`FILES_CHANGED\` included in PR description
- [ ] \`DIFF summary\` included in PR description
- [ ] ARCH-01 host shell remains domain-agnostic
- [ ] BOUND-01 no forbidden cross-layer imports
- [ ] CON-01 cross-layer interactions are contract-driven
- [ ] LIFE-02 teardown coverage is explicit and validated
- [ ] PACK-01 package manifest, BOM, rollback plan, and release notes remain consistent
- [ ] Evidence artifact links attached from \`ForgeOS Quality Gate\` workflow
