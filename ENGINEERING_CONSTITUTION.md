# Engineering Constitution

> **Authority:** This is the canonical governance constitution for repository-change control. It is enforced by [`docs/governance/ENGINEERING_GOVERNANCE_POLICY.json`](docs/governance/ENGINEERING_GOVERNANCE_POLICY.json), [`scripts/fitness/check_engineering_governance.py`](scripts/fitness/check_engineering_governance.py), required CI, CODEOWNERS, and the external branch-protection controls documented in [`.github/BRANCH_PROTECTION_GUIDE.md`](.github/BRANCH_PROTECTION_GUIDE.md).
>
> **Scope boundary:** A repository cannot make itself metaphysically immutable. A repository owner or GitHub administrator can change external settings. This constitution makes bypassing governance on the normal pull-request path detectable and rejectable; external controls remain the responsibility of the human/admin authority.

## 1. Purpose and scope

The repository is a living engineering system with history, boundaries, invariants, evidence, and consequences. This constitution governs every modification to product code, tests, CI, automation, configuration, documentation, migrations, dependencies, and governance artifacts.

It supplements, and does not replace, the existing operational and domain constitutions, especially `CLAUDE.md`, `AGENTS.md`, `docs/architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md`, and `docs/architecture/CODE_ACCEPTANCE_CONSTITUTION.md`. Where rules conflict, the higher-precedence rule below controls.

## 2. Authority and precedence

A lower item never silently overrides a higher item:

1. Safety and data integrity
2. Security, privacy, safeguarding, and least privilege
3. This constitution and constitutional amendment controls
4. Architectural invariants and explicit repository contracts
5. Required CI, verification, and fitness gates
6. Product and task requirements
7. Performance optimisation
8. Convenience
9. Speed of implementation

Convenience, urgency, confidence, a green individual test, or a user request never overrides integrity or evidence.

## 3. Definitions

- **Change:** any added, modified, renamed, or deleted repository artifact.
- **Dependency path:** the direct and transitive code, data, contract, deployment, and operational boundaries a change relies upon.
- **Foundational defect:** an unresolved defect that can invalidate correctness, safety, integrity, security, migration safety, or verification on the affected dependency path.
- **Constitutionally sensitive artifact:** a policy, gate, test of a gate, CI workflow, entry protocol, ownership rule, or branch-protection declaration listed in the machine-readable policy.
- **Independent verification:** a test, deterministic gate, CI execution, code-owner review, or platform protection not controlled solely by the author of the change.
- **Exception:** a bounded, recorded deviation from a rule. Silence is never an exception.

## 4. Mandatory pre-modification gate

Before changing a repository artifact, the author must create or update the current acceptance packet with evidence for:

1. current state and relevant runtime truth;
2. relevant architecture, contracts, and ownership boundaries;
3. existing failures and the old-problem frontier on the dependency path;
4. a root-cause statement or an explicit `UNKNOWN` with a stop condition;
5. intended change and affected invariants;
6. tests, rollback/containment, and verification strategy;
7. evidence-status labels for every major claim.

If these facts cannot be established, the change is **blocked**. The appropriate response is to report the blocker, not to invent certainty, weaken a gate, delete a test, or add a compensating patch.

The machine-checked packet is `docs/changes/CURRENT_CODE_ACCEPTANCE_PACKET.json`. It is evidence of a governed change, not self-approval.

## 5. Old-problem frontier

Every change must trace its dependency path and identify unresolved historical defects relevant to that path.

> **No new feature may be used as a reason to ignore an unresolved foundational defect on its dependency path.**

A foundational defect must be repaired or explicitly contained before feature extension. This rule does **not** demand unrelated cosmetic cleanup: debt outside the affected dependency path is recorded, not used as an arbitrary veto.

## 6. Modification, architecture, testing, security, and migration rules

- Make the smallest reversible change that preserves the existing architectural boundaries.
- No code or contract may bypass a declared boundary, forbidden import rule, ownership rule, or required invariant.
- Tests are specifications. Removing, skipping, deselecting, weakening, or muting a test to manufacture green status is prohibited.
- CI, gates, and their negative tests are production controls. A passing happy-path test does not prove a gate blocks a violation.
- New dependencies require an ADR in the same governed change; accidental manifest edits are rejected.
- Migration changes require an accompanying test and must not introduce destructive SQL in the normal path. Destructive data operations require an explicit constitutional exception and human/admin authority.
- Secrets, personal data, credentials, and unsafe privileges are never introduced to satisfy a task.

## 7. Evidence status

Every major claim is labelled using exactly one of:

`UNKNOWN` · `ASSUMED` · `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `RUNTIME VERIFIED` · `FAILURE TESTED` · `OPERATIONALLY VERIFIED`

These statuses are not interchangeable. A file existing is not runtime verification; a test passing is not operational verification; a claim with unavailable evidence remains `UNKNOWN`.

## 8. No self-certification

The author proposes a change; independent mechanisms decide whether it is mergeable. The same agent or person who produces a change must not be the sole authority declaring it safe.

Normal mergeability requires the repository checks, required CI, and the independently configured protected-branch/CODEOWNERS review path. An author cannot self-approve a constitutional amendment through a local file, a test change, or a PR description.

## 9. Constitutional amendment and sensitive-artifact control

Constitutionally sensitive artifacts are listed in the machine-readable policy. A normal feature change may not silently alter them.

A sensitive change requires all of the following:

1. a new immutable amendment record under `docs/governance/amendments/`;
2. a stated reason, scope, risk, affected invariants, mitigation, rollback, verification plan, owner, and expiration where relevant;
3. a PR declaration naming the amendment record and the required independent reviewer;
4. independent human/code-owner approval through protected-branch controls;
5. a passing governance audit and a negative test proving the control still rejects a prohibited path.

The author may create a proposal record but may not label it approved. A normal PR must not change the constitution, the enforcement mechanism, and the approval authority while self-certifying the result.

## 10. Exceptions and emergency path

Exceptions are explicit, scoped, owned, risk-assessed, and time-bounded. Each record must name:

- reason and scope;
- affected invariant and risk;
- owner and independent approver;
- mitigation and verification plan;
- expiration and follow-up repair.

An emergency allows accelerated review, never ungoverned work. Emergency changes retain traceability, minimum scope, rollback/containment, post-incident verification, retrospective, and follow-up repair. “Skip for now” is not an exception.

## 11. Audit and entry protocol

Every agent begins by loading the governing entry points, discovering the current reality, tracing relevant old debt, identifying invariants, and determining verification requirements before it writes code.

Run the governance audit from the repository root:

```bash
python scripts/fitness/check_engineering_governance.py
```

The audit checks the canonical constitution, policy shape, protected artifacts, required CI wiring, entry-point references, code ownership declarations, amendment-record format, dependency/migration/test-weakening controls, and the declared external-control limitations.

## 12. Non-circumvention and stop rule

An agent must never:

- disable, skip, or downgrade a gate to make its own change pass;
- delete or weaken a failing test to manufacture green CI;
- change a constitution to authorize its own behaviour;
- add an undocumented dependency or unsafe migration to unblock work;
- present unexecuted runtime verification as executed;
- conceal an unknown, limitation, bypass, or external-control gap.

When blocked, report the blocker and stop. Do not circumvent it.

## 13. Immutability model

```text
Human / admin authority
        ↓ constitutional amendment and platform protection
Constitution and policy
        ↓ CI, hooks, gates, CODEOWNERS, protected branch
Agent / developer workflow
        ↓ understand → repair/contain → verify → extend
```

Normal agents cannot bypass normal governance without changing protected artifacts, producing a visible amendment record, and passing independent repository and platform controls. A repository owner or administrator remains the ultimate external authority and can alter those controls; this limitation is stated rather than hidden.
