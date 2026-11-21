# Exchange retained knowledge between local stores

SPDX-License-Identifier: CC-BY-4.0

This guide gives the bounded local store contract and an executable certificate exchange.
Original scientific records, producing receipts and evidence ceilings remain unchanged.
The store records custody and discovery. A later consumer retains its own admission procedure.

## Prerequisites and first action

Select the [locked environment](../using/environments.md) and explicit [operator profiles](../using/configuration.md).
Read the [portable assessment procedure](portable-assessments.md) first.
Select actual completed certificates, including adverse or unevaluable findings when present.
Keep their full original contribution directories available.

Select two distinct guarded artifact roots, with distinct storage-root identities, for stores A and B.
Select new store and transfer directories beneath the corresponding artifact roots.
Select a new catalogue path beneath B's guarded scratch root.
Stop if a required mount is unavailable.
Profiles and directory choices are operational selections; they change no scientific identity.

The [public example](../../scripts/examples/portable_knowledge_store.py) composes existing application storage, certificate verification, replica recovery and catalogue services:

```sh
uv run --no-sync python scripts/examples/portable_knowledge_store.py \
  --project-root /selected/checkout \
  --source-operator-profile /work/original-retained-access.json \
  --store-a-operator-profile /work/store-a-profile.json \
  --store-b-operator-profile /work/store-b-profile.json \
  --certificate-directory /original/artifacts/certificate-positive \
  --certificate-directory /original/artifacts/certificate-adverse \
  --source-transfer-directory /original/artifacts/new-transfer \
  --store-a-directory /store-a/artifacts/knowledge \
  --store-b-directory /store-b/artifacts/knowledge \
  --store-a-transfer-directory /store-a/artifacts/new-export \
  --catalog-relative-path knowledge/new-projection.sqlite3
```

Use the returned transfer identities, directories and exact locators.
The example initializes new stores, imports into A, exports from A, imports into B, rebuilds B's projection and resolves each original object.
It invokes no worker or scientific acquisition.
Its disjoint operation measurements describe local read/copy overhead only.
Do not add those measurements to overlapping parent windows or infer missing original scientific costs.

To include a notice, add `--notice-directory` and every exact referenced certificate directory.
A correction or contrary notice retains both conflicting certificates.
The notice's publisher label remains an unsigned local custodian assertion.
This example selects the exposed development-certificate route.
Deployments with restricted evidence must supply their actual current access and reveal owner.

## Workbench inspection and reviewed exchange

Select **Knowledge & exchange** in the [research workbench](../using/research-workbench.md).
Select the store's operator context, exact namespace and original directory.
The context selects the catalogue relative path. A new catalogue rebuild requires an unused path.
**Browse current imports** returns at most eight imports per query.
The displayed total covers that selected import page only.
Use **Resolve original** to verify a complete returned locator through its current owner.
Select exact objects for export with the row controls. Matching labels do not merge different identities.

For certificate inspection, select the original certificate directory and **Verify original certificate**.
The report separates the original assertion from producing custody, replay, authorship and current admission.
Partial reads preserve unavailable verification. They do not supply a verified scientific finding.
This route accepts exposed development packages. Protected evidence retains its owning access procedure.

Review the initialization, import, export or new catalogue action before **Apply reviewed action**.
For import, select the source operator profile and original transfer directory.
Select the source retained-root contract when the original study requires it.
For export, select every dependency and the new destination directory.
The review binds current profiles, root contracts, context, selections and destinations.
Import and export also bind the complete transfer identity.
Apply repeats the original owners' checks. A changed transfer or review binding refuses before copying.
For an interrupted import, select recovery of its original copy plan.
Review grants no access, execution authority, consumer admission or scientific qualification.

`preview_knowledge_transfer` and `KnowledgeStore.preview_export` reuse the original export validation without copying or creating destinations.
Their physical counts cover the complete selected object packages. Outer transfer controls are additional.
`create_knowledge_transfer` and `KnowledgeStore.export` accept an optional `expected_transfer` identity from that review.
They compare it before destination creation. Existing callers retain their original behavior.

## Original records, namespaces and types

The [store API](../../src/empirical_lawhood/api/knowledge_store.py) uses the [registered runtime contracts](../../src/empirical_lawhood/storage/contracts/knowledge_store.py).
Each object keeps its complete `ObjectIdentity`: original ID, schema, exact version and full content digest.
The store namespace, origin namespace, publisher label and physical directory are separate fields.
Neither an ID nor a human label is globally unique.
Two assertions with the same label or original ID can coexist with different complete identities.

`ScientificTypeRegistry` composes the existing `RecordCodecCatalog`.
Register a `ScientificTypeDescriptor` containing the exact record type, its identity field, original filename, dependency description and optional current verifier.
The [certificate descriptors](../../src/empirical_lawhood/api/knowledge_certificate_types.py) call the existing certificate and notice verifiers.
They create no second inference algorithm or scientific scheduler.
Adding another domain descriptor requires no scientific-kind enum edit or SQL migration.

An unknown exact revision remains an identifiable opaque body.
Its declared ID is not interpreted, and its scientific assessment and semantic dependency completeness remain unestablished.
An installed decoder alone establishes record interpretation, not a scientific finding.
A registered verifier must still establish its own original scoped assessment.
No data record can select executable code or import a decoder.

Every operation requires a code-owned `require_access(identity, action)` callback.
Its actions are `DISCOVER`, `READ`, `EXPORT` and `IMPORT`.
The callback returns `None` or raises; it cannot grant authority through a returned label.
It must consult the actual current access owner for the selected evidence.
Store metadata, imported certificates and cached verification reports cannot replace it.
The guarded filesystem and original certificate verifier remain additional independent boundaries.

## Bounded transfer and durable import

A transfer contains one canonical `control/transfer.json` publication and complete original packages under `objects/`.
Its manifest binds every selected object, root, dependency and physical member.
The outer transport publication has an operational namespace derived from its exact manifest.
Embedded scientific namespaces and bytes remain unchanged.

`create_knowledge_transfer` verifies registered original prerequisites before copying.
It then checks the copied complete closure through the same registered owners.
Missing dependencies, cycles, unassigned bytes, changed identities and unsupported interpreted records refuse.
Unknown bodies remain explicitly opaque rather than acquiring an inferred scientific verdict.

`KnowledgeStore.import_transfer` reuses `replicate_artifact_publications`.
That existing owner retains the exact copy plan, hashes every selected member, preserves complete publication batches and checks current access during copying.
It publishes its own completion receipt only after complete original/destination verification.
The store publishes `import.json` last and checks the current copied census again before returning success.
The primary import record binds the exact transfer and replica completion receipt.

| Default selected limit | Value |
| --- | ---: |
| Objects in a transfer | 16 |
| Object dependency depth | 8 |
| Physical members, including outer publication controls | 8,192 |
| Individual physical member | 16 MiB |
| Aggregate physical closure | 256 MiB |
| Individual store control record | 4 MiB |
| Physical path depth | 48 |
| Recursive contribution parent depth | 8 |
| Contribution authentications in one operation | 128 |
| Closure directory entries visited in one operation | 131,072 |
| Closure-census bytes hashed in one operation | 4 GiB |
| Imports in one store, including incomplete imports | 64 |
| Import records in one query page | 8 |

Each query page can describe up to 128 objects under the default limits.
The physical SQL query uses a row limit and the existing SQLite instruction budget.
Nested store operations share the selected closure budget; they cannot reset it.
The census hash budget does not claim to meter every internal artifact-verifier read or impose a process wall-time limit.
The replica service separately enforces complete-copy member/byte bounds and its fixed verification passes.
Use actual invocation measurements for expenditure.

Select `KnowledgeStoreLimits` and `RecursiveClosureLimits` explicitly when another supported finite envelope is needed.
Bounds refuse the whole requested closure; they never truncate its evidence census.
Legacy contribution export retains its original default contract unless this bounded context is selected.
The [contribution procedure](../using/recursive-inquiry.md#carry-a-contribution-into-another-investigation) remains unchanged.

## Recovery and original history

An interrupted import retains its directory and the replica service's exact progress plan.
It has no completed store import standing without `import.json` and its valid original closure.
Repeat `import_transfer` with the same source, expected transfer identity and explicit `resume=True`.
The replica owner reuses matching complete files and restarts only its owned unpublished partial copy.
Changed complete files, a different copy plan, unexpected members or revoked access refuse recovery.
Preserve the failed attempt and select a new destination when its original plan cannot be recovered.

A repeated complete transfer returns `DUPLICATE_VERIFIED` after current verification.
It rewrites no original import, scientific record, receipt or update notice.
Corrections, supersession, withdrawal and contrary assertions remain separate exact predecessor records.
There is no shared mutable latest-value field that can erase disagreement.
Authorship, trust and execution authority remain local decisions outside this transport.

## Catalogue, resolution and freshness

`rebuild_projection` authenticates complete primary imports into a new explicitly selected guarded catalogue.
It reports incomplete import directories separately and gives them no completed-import rows.
The existing catalogue stores physical logical-artifact and locator records for the import receipts.
It does not reclassify arbitrary domain results as an existing scientific kind.
The scientific store records remain readable through their exact locators when the disposable catalogue is absent.
Rebuilding this projection grants no authority to replace an issued catalogue.

`query` returns discovery metadata and `KnowledgeObjectLocator` records.
It does not replay scientific assessments or claim that a discovered body is available or admissible.
Use the returned cursor for another bounded import page.
A catalogue can omit later imports; its observation scope is explicit.

`resolve` checks the current namespace, exact import receipt, complete transfer closure, access guard and registered verifier.
Cached discovery cannot hide a missing member or revoked access.
With `allow_incomplete=True`, unavailable or restricted dependencies return the selected identity without a verified scientific verdict.
Invalid locator or primary-receipt identities still refuse.

Reports identify the import/update source and the observation time actually read.
They always leave unseen corrections and global status unknown.
An offline replica cannot establish that another publisher has issued no later correction or withdrawal.
Discovery, byte custody, scientific assessment, authorship and current consumer admission are separate results.

This contract selects local guarded filesystem exchange and the shipped catalogue implementation.
It introduces no network service, replication consensus or global trust authority.
Incremental or shared-closure optimization remains a separate measured decision.
