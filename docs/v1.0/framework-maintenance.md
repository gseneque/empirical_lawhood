# Maintain the framework

SPDX-License-Identifier: CC-BY-4.0

This guide identifies work that changes shared EL machinery.
Routine investigation, method and domain contributions use their public guides instead.
Locate the owning contract and its existing tests before changing it.

## Select the affected owner

| Change | Owner and evidence |
| --- | --- |
| Scientific records or canonical identities | `science`; exact canonical bytes, decoder revisions and complete outcome census |
| Authoring or plan derivation | `design` and `execution`; authored-object correspondence and deterministic plan construction |
| Worker placement or resource admission | `execution`; local/process/remote boundaries and explicit unsupported-capability reasons |
| Artifact publication or retained verification | `storage`; mutation controls, exact-byte bindings, access and final closing checks |
| Application composition | `api`; public operation requests, concrete service binding and structured results |
| Presentation | `cli` or `workbench`; shared application result and diagnostic consistency |
| Packaging and discovery | Build hooks and owning extension declarations; generated projections and installed-artifact checks |

Do not add a domain scheduler, independent recovery store or another registration census.
Reuse the ports and owners described by the [architecture guide](architecture.md).
An application may bind providers, but an inward contract must not import application code.

## Work procedure

1. Read the current owner and affected tests.
2. State the failed contract and the behavior the change must preserve.
3. Change the authoritative declaration or implementation.
4. Regenerate its projections through the existing ordered generator.
5. Run the focused contract and process-boundary checks.
6. Run the required release profile and installed-artifact checks.
7. Retain the source, complete check census and limitations with the result.

```sh
uv run --no-sync python scripts/generate_extension_projections.py --json
uv run --no-sync python scripts/check_documentation.py
```

The [testing guide](../development/testing.md) owns profile selection.
The [integrity performance guide](../development/integrity-bookkeeping-performance.md)
explains read ownership, cache accounting, archive composition and meaningful
before/after measurements for shared bookkeeping changes.
The [release procedure](../release/release-artifacts.md) owns acceptance and retained verification packets.
Do not label a collection-only, skipped or interrupted test run as passing acceptance.

## Evidence preservation

Preserve original evidence bytes, identities, retained histories and accepted decisions.
Changed source receives a changed implementation identity.
Do not rewrite a historic scientific record to make its producing path look current.
A changed stored format requires an explicit revision and supported reader or documented migration.

Read current work plans before changing their scope.
Ignored plans remain under their existing custody and publication rules.
A code reorganization does not select a new scientific acquisition or reopen accepted work.

## Public and internal interfaces

The [public reference](public-api.md) is the contract for the three contributor jobs.
Undocumented implementation helpers are internal even when importable from Python.
The [detailed implementation map](../development/architecture.md) is for framework work.
The [programme index](../../programmes/README.md) owns scientific history and findings.
