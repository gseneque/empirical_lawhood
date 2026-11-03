# Compatibility and support

SPDX-License-Identifier: CC-BY-4.0

This policy defines the first public interface and data-contract baseline.
It separates compatibility, tested software behavior and scientific authority.
Use it to select a supported interface and understand an honest stopping condition.

## Source and release identity

Package metadata owns the distribution version.
The [external release-status record](../release/release-status.md) owns the selected source, tested artifacts and software evidence.
A version string alone does not identify a checked Git tree or qualify a scientific result.
Publication, its date and any DOI require their separate owner selection.

The public baseline governs the names and contracts documented for the selected release.
Unpublished source-project iterations do not create a compatibility promise.
The source archive retains historical records and their original identities.
They are not a parallel public command interface.

Artifact manifests retain the exact producing validator version and source hash
as provenance. Current readers authenticate the original publication and validate
its bytes with the installed format and semantic contracts. A producing stamp
cannot select a decoder or supply an absent format. Complete atomic sibling,
media, size, record revision and current access checks still apply. Reading grants
no source eligibility or scientific qualification.

## Four supported surfaces

| Surface | Support boundary |
|---|---|
| Installed CLI | Documented commands, options, output fields and refusal exits in the [generated reference](../reference/cli.md) |
| Documented API | Documented request/result records and application operations of `EmpiricalLawhoodApi`, with [explicit composition](architecture.md#application-composition-and-module-responsibilities) |
| Versioned data/provider contracts | Strict canonical schemas, their relationships and the [registered provider protocols](extending-the-engine.md#provider-and-record-contracts) |
| Maintained checkout recipes | Documented operator scripts and typed handoffs, checked for the selected release. They do not promise arbitrary stable internal imports. |

Use the documented fields and effects for the selected version.
Treat an unknown reason code as a refusal.
Undocumented helpers, test fixtures and arbitrary retained adapter imports carry no general stability promise.
The [environment guide](../using/environments.md) owns the tested platform and selected lock/profile.
Other platforms require their own verification.

## Inspect a capability page from Python

Use the supported `EmpiricalLawhoodApi` inspection composition for a bounded
question: which five declared capabilities appear on the first page? Save the
code below as `inspect_capabilities.py` in your chosen work directory. From the
selected checkout and [locked base environment](../using/environments.md), run
`uv run --no-sync python /absolute/work/inspect_capabilities.py` with your actual
script path. A selected installed wheel can use the same interface.

```python
from empirical_lawhood.api import CapabilityListRequest, create_inspection_api

api = create_inspection_api()
result = api.list_capabilities(CapabilityListRequest(limit=5))
if not result.succeeded or result.payload is None:
    raise RuntimeError(result.to_mapping())

page = result.payload
print(result.operation, result.status.value, page.returned_count)
for registration in page.registrations:
    manifest = registration.manifest
    print(manifest.capability_key, manifest.capability_version)
```

The first line is `capability.list SUCCEEDED 5`; five key/version pairs follow.
The result is `ApiResult[CapabilityListSummary]`. Its `payload` holds static
registrations, binding/availability descriptions and pagination fields. Use
`page.next_cursor` in a new `CapabilityListRequest` to select the next bounded
page; use `result.to_mapping()` for the versioned JSON-compatible envelope.
On refusal, inspect `status`, `reason_codes` and `errors` instead of treating a
missing payload as an empty scientific result.

This example reads installed descriptors and returns objects in memory. It
opens no scientific inputs or catalog, constructs no native provider, runs no
tasks and writes no output files. `SUCCEEDED` means the lookup completed;
capabilities and maximum evidence ceilings do not establish readiness,
qualification or execution/reveal authority. Select an actual operation in
the [workflow catalogue](../reference/workflows.md) next. For existing scientific
outcomes, follow the family's receipt-bound result procedure and applicable
access requirements in [results and failures](../using/results-and-failures.md).

The request, result and facade operation use the documented API surface.
Arbitrary adapter imports have no general stability promise. Storage and
execution require their explicit application services and authority; see
[application composition](architecture.md#application-composition-and-module-responsibilities).

## Canonical data and scientific change

Schema identity, format revision and canonical bytes determine persisted identity.
Unknown fields, duplicate keys and unsupported revisions refuse at the strict decoder.
New fields or changed contracts require a declared revision and matching decoder.
A caller cannot make an old record current by renaming its namespace or changing a schema marker.

A scientific change requires its own protocol, source, configuration and validation identities.
It cannot inherit old qualification receipts or grants.
Historical input mappings must retain original bytes, source hashes and interpretation.
Applicable target custody and authority remain separate requirements.
The current OriginalF and frozen-nomination transports preserve exact fixed bytes and an explicit historical-to-current identity crosswalk.
Their current import receipts grant no historical source closure, new calibration or scientific qualification.
Other foreign banks and censuses retain their owning export requirements.
The [input guide](../../programmes/foundations/emergent-structure/reference/input-formats.md) gives the implemented input boundaries and first missing prerequisites.
Absent permitted inputs remain stopping conditions.

The [recursive workflow](../using/recursive-inquiry.md) adds explicit
operation and development-plan records around existing scientific contracts.
The original RC inputs, unit results, summaries and fixed-study provider retain
their schemas, revisions and canonical meaning. Phase products have separate
schemas; their assessed reduction projects to the original RC result contract.
Reading retained evidence authenticates its producing source and receipts,
without requiring the reader to claim that it produced those bytes. A development
plan or completion receipt supplies no prospective issue, execution or reveal
authority. Portable contributions retain their original exposure and evidence
roles when imported.

## Selected source and exposed examples

New authoring packets retain the selected committed source and its exact manifest.
The separate source observation reports the actual Git status.
An empty Git status is not a general admission requirement.
Source drift, undeclared executable inputs and foreign loaded modules remain refusal conditions.

The packet's `provenance/` directory contains these separate records and their authenticated artifact manifests:

- `selected-source-manifest.json` binds the selected executable and input members.
- `source-observation.json` discloses the source capture and actual checkout status.

Keep these companions with the authored packet.
Readers authenticate their exact joins before they accept a selected-source handoff.
Historical `CLEAN_GIT_COMMIT` records retain their original bytes and verification rules.
Companion removal cannot convert a selected-source packet into a historical clean-source packet.
The [integration guide](../using/paper-study-workflows.md#one-application-handoff-and-the-existing-lifecycle) gives the shared source and custody procedure.

These SDK authoring functions require an explicit `artifact_writer`:

| Function | Module |
| --- | --- |
| `author_fresh_rc` | `empirical_lawhood.api.rc_authoring` |
| `author_synthetic_material_response` | `empirical_lawhood.api.synthetic_material_authoring` |
| `author_uniform_electron_gas_analytic_reference` | `empirical_lawhood.api.uniform_electron_gas_authoring` |

Supply the guarded artifact plane for the selected external destination.
The corresponding public CLI commands supply that plane through their storage selection.
Other arguments retain their documented meanings.

The [integration example generator](../../scripts/generate_integration_examples.py) owns the current editable exposed projections.
Regeneration binds current source and lock without requiring a numbered predecessor chain.
Retained scientific inputs stay unchanged in their original custody.
These exposed examples add zero scientific units and grant no qualification.

Installed preparation checks establish their stated preparation scope.
Installed Matrix result and recovery claims also require actual command acceptance on the selected wheel.
A preparation check alone cannot establish that acceptance.

## Local catalog baseline and recovery

The public SQLite catalog has `application_id=0x454C4157`, schema version `1` and Alembic head `initial_catalog`.
[database.py](../../src/empirical_lawhood/infrastructure/sql/database.py) owns those constants.
The [initial migration](../../src/empirical_lawhood/infrastructure/sql/migrations/versions/initial_catalog.py) owns the public tables and indexes.
There is no source-project three-revision upgrade chain in this baseline.
Foreign database identities refuse before catalog writes.

The catalog is a rebuildable projection of authenticated records.
Canonical scientific records and external receipts remain the primary custody.
Before a permitted replacement, retain the existing database and its provenance.
Use the installed catalog preview/rebuild operation with its exact authenticated projection and authority controls.
A missing decoder, migration, projection or grant stops the operation.
Keep schema markers unchanged during manual inspection.

## Software gate and later scientific selection

The software gate reports scientific status `NOT_PERFORMED`.
Keep that immutable software-gate snapshot.
A later qualification or review selection binds its manifest hash and supplies its own exact receipts and status.
It also binds the selected source and artifact hashes.
The later selection does not overwrite an older packet or imply that the software gate performed science.
The [release status guide](../release/release-status.md) identifies the external evidence owner.

## Report a defect

Use the repository's [issue tracker](https://github.com/gseneque/empirical_lawhood/issues), subject to its access permissions.
Give the package version and exact Git commit or wheel hash.
Give the command, reason code, exit status, OS/architecture, Python version and relevant native versions.
Include a redacted minimal input and the expected/observed behavior.
State whether native contact or writes occurred.
Include the selected manifest and relevant log hashes when available.

Remove private keys, credentials, held outcomes and private storage paths.
The project gives no promised response time or support entitlement.
Access permissions and scientific authority remain the researcher's responsibility.
The [contribution guide](../../CONTRIBUTING.md) gives the change and verification procedure.

## Licenses and package notices

Installed recipients can read `empirical_lawhood/PACKAGE-NOTICES.md` through `importlib.resources`.
The notice identifies the public finite specification's license and hash, plus vendored reactor provenance.
Distribution metadata includes the full MPL license text.
The [licensing guide](../reference/licensing.md) owns the complete scope and reuse account.

## References and research

The [architecture guide](architecture.md) maps these interfaces to implemented owners.
The [scientific integrity guide](../reference/scientific-integrity.md) states the independent evidence and authority gates.
The linked catalog source and [migration checks](../../tests/infrastructure/test_catalog_migrations.py) establish the local schema boundary.
