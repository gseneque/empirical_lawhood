# Continuing sources and finite operations

SPDX-License-Identifier: CC-BY-4.0

This guide gives the shared contract for a continuing source.
It separates source ownership, actor information, finite effects and retained evidence.
Use it to compose a source adapter with the existing custody owners.

## Prerequisites and first action

Select the [locked environment](../using/environments.md) and explicit external storage.
Read the [shared-service pattern](shared-services.md) and [native custody procedure](native-subwork.md).
Provide the actual source permission and code-owned native ports.
A lease record alone grants no source, execution or outcome authority.

Define one `ContinuingSourceSession` from `science.inquiry.continuing_source`.
Keep its source, source generation, lifecycle owner and common dependence root explicit.
Actors, scientific windows, finite requests and retained runs have separate identities.
An additional actor, window, connection or source restart creates no independent scientific unit.

Compose `api.continuing_source.open_continuing_source` in the source service.
Supply the selected `ExternalArtifactPlane`, relative custody root, clock, package bytes, effect ports and current access owner.
Keep this context outside the lifetime of a browser or application request.
The composition does not launch the source or infer scientific identities.

For the exposed software example, run the [counter recipe](../../scripts/examples/continuing_source.py):

```sh
uv run --no-sync python scripts/examples/continuing_source.py \
  --project-root /absolute/path/to/selected/source \
  --operator-profile /absolute/path/to/operator-storage.json \
  --output-directory /selected/artifact/root/continuing-counter-01
```

The new output directory must lie inside the profile's selected artifact root.
The recipe starts one bounded local counter process with two actor handles.
It retains the complete source snapshot, event custody, finite contacts and `report.json`.
It deliberately interrupts one segment publication and preserves the resulting unevaluable history.
Two counter applications are disclosed software effects, not scientific acquisitions.
The recipe limits its external source to 120 seconds, four queued effects and 32 results.
It measures source CPU, control requests, persistence and asynchronous inquiry separately.
Control elapsed time includes persistence and transport time. Do not add those overlapping measurements.

## Existing owners and added contracts

| Responsibility | Owner and boundary |
| --- | --- |
| Clocks and cutoffs | Existing `science.models.time` records retain units, frames, origins, phases and explicit transports. This profile accepts exact mappings only. |
| Session, actor and finite operation | `science.inquiry.continuing_source` binds generations, original windows, information, package, prepared commitment and scheduled envelope. |
| Mutable source ownership | `runtime.continuing_source.ContinuingSourceOwner` owns one bounded actor census and separate actor handles. |
| Current permission | The injected `LiveSourceAccess` checks actual source access. Actor reads and effect submissions repeat the current check. |
| Event and operation custody | `infrastructure.continuing_source.ExternalContinuingSourceStore` composes the existing guarded artifact plane and its immutable manifests. |
| Possible effect contact | The existing `ExternalNativeEffectContactStore` retains the original finite operation and exact input materializations. |
| Scientific controller | Existing `prepare_commitment` and `deliver_prepared_commitment` retain their finite controller contracts. |
| Cost | Existing [work cost records](work-cost-accounting.md) retain original measurements and their separate scopes. |

The session contract adds no scheduler, source installer, general control algorithm or replacement artifact writer.
The prepared controller bridge already retains commitment bytes before native delivery.
Use that bridge when its compiled study and prospective design fit the source.
For a continuing source, the source adapter must also enforce its current generation and native expiry.
Preserve the original prepared controller record as the finite operation's `prepared_commitment`.
Call the existing delivery method from the source-owned effect port after durable publication.
Do not translate an unknown delivery trace into a successful live receipt.
The adapter must derive actual receipt times from its native evidence.

## Actor information and source events

`LiveActorLease` separates connection, allocation and life generations.
A replacement must advance at least one generation without reversing another.
The replacement boundary is durable before the new handle becomes available.
The old handle refuses.
The new handle starts with empty observation memory.
Other actors keep their own handles and information.

An observation retains occurrence, sampling and availability coordinates.
It also retains its original actor lease, channel, payload identity, retention expiry and derived ancestors.
The source declares a maximum delay and retention duration for each actor.
Availability and current read cutoffs remain separate checks.
An earlier causal phase cannot conceal a future availability coordinate.

Each actor reads only its own permitted, currently retained observations.
The actor handle exposes no historical-store or evaluator-ledger reader.
Eviction also removes derived observations whose ancestors are no longer retained.
A new derived observation cannot restore an evicted or foreign ancestor.
The owner may retain original evidence for audit without making it available to an actor.

This profile accepts outcome-blind or exposed development source sessions.
An evaluator or privileged ledger cannot be relabelled as an actor source.
These are trusted Python interfaces, not an operating-system sandbox.
They bound service-managed memory and access.
They cannot erase copies that a client already received.
An untrusted client requires a separate process and an authorized transport boundary.

## Finite effect and recovery

`FiniteLiveOperation` binds the original package, prepared bytes, admitted observation identities and information cutoff.
It preserves the original scheduled application interval and actor lease.
The application request timeout uses seconds.
The scientific horizon uses its declared native clock.
The native action expiry is a separate coordinate.
Changing one quantity does not change the others.

The custody owner publishes and verifies the actual prepared bytes and complete operation before any submission.
It then retains the existing native-contact marker.
Persistence failure prevents a new effect submission.
The native adapter must call `require_live_application` immediately before application, including after a queue delay.
It must also enforce actual current native permission.
A stale generation, expired lease or expired action refuses.
The native adapter owns lease-loss fallback or loss-of-control behavior.
Storage failure cannot authorize an additional unretained fallback command.

Request deduplication, command acceptance, native application and observed result are distinct states.
A contact without a confirmed reply returns `UNKNOWN_EFFECT_DO_NOT_REPEAT`.
Repeating the same request returns its retained state without another submission.
Reusing a request ID with changed operands refuses.
An `ACCEPTED` receipt alone proves no application.
An `APPLIED` receipt alone proves no observed scientific outcome.

Use `read_continuing_operation` for retained inspection.
Use `reconcile_continuing_operation` with the native adapter's read-only observer for actual later evidence.
Reconciliation preserves known acceptance and application facts.
It cannot repeat the effect or rewrite an earlier result.

### Inspect exposed historical records in the workbench

Use the example's returned `session_directory` with the [research workbench](../using/research-workbench.md).
Select **Continuing source history** and the original session directory.
Select each event and actor-boundary window explicitly, with at most sixteen records per window.
Choose **Open result**.
The read uses the original session, segment and boundary custody readers.
Delayed coordinates, missing segments and sequence gaps keep their original values.
The retained lifecycle disposition does not certify event completeness.
Read the separate event-window status and original gaps.
An actor-boundary record describes a historical lease. It grants no current actor memory or source access.

Select **Finite source operation** and its original request ID to inspect one retained operation.
The read retains the exact package, prepared commitment, input identities, contact and effect receipt.
An absent reply remains `UNKNOWN_EFFECT_DO_NOT_REPEAT`.
This view supplies no effect-submission or reconciliation action.

The terminal application operations are `continuing.session` and `continuing.operation`.
Both require `directory` and the explicit operator profile in the selected context.
The session operation accepts `first_segment`, `segment_count`, `first_boundary` and `boundary_count`.
The operation view requires `request_id`.
The API [exposed history selector](../../src/empirical_lawhood/api/continuing_source.py)
authenticates the original `session.json` before it returns the existing custody owner.
The [application composition](../../src/empirical_lawhood/api/application_continuing.py)
uses the shared invocation, exact-value, pagination and final byte checks.
It accepts only `DEVELOPMENT_ONLY` and `DEVELOPMENT_VISIBLE` session publications.
Outcome-blind and restricted histories need their actual owning access route.
No historical read acquires live ownership, creates a new lease or starts a source process.

Package replacement requires a durable boundary before new submissions.
An in-flight operation keeps its original package, inputs, schedule and native port.
An unsubmitted operation from the replaced package refuses.
The session's native transport ownership remains fixed.
Replacing that native implementation requires a separately admitted session and source generation.

## Bounds, gaps and stops

The session selects smaller limits within these shared maxima:

| Quantity | Maximum |
| --- | ---: |
| Actors | 16 |
| Retained event segments | 1,024 |
| Events in one ingest batch or segment | 64 |
| Retained observations per actor | 128 |
| Observations in one actor read | 64 |
| Finite operations | 256 |
| Domain payload or prepared commitment | 64 KiB |
| Canonical control record | 1 MiB |
| Segments in one historical read | 16 |

The owner admits one bounded input batch without an internal waiting queue.
A busy owner returns `LiveBackpressure`.
The source adapter must bound its transport queue and preserve any dropped sequence as an event gap.
These are item and byte bounds, not a process-memory or real-time guarantee.
Select storage capacity for the complete retained census and ordinary custody metadata.
Each actor has at most one in-flight submission call.
Drain those calls before the source owner exits.
An exit with an in-flight call refuses a closed-session record and preserves the original contact for reconciliation.

Each immutable segment binds its predecessor, original global event sequence, complete event census and explicit sequence gaps.
The segment is published after its original event records and payloads.
Interrupted publication does not enter actor memory.
Historical reads verify manifests, complete members and predecessor relationships.
A selected complete read window does not establish complete session history.

An event gap makes this profile's session history `UNEVALUABLE_EVENT_HISTORY`.
New scientific effects stop even if the external process continues.
Retention capacity exhaustion or publication failure has the same scientific disposition.
The owner attempts to retain a loss boundary.
If storage also refuses that boundary, an unclosed session remains unevaluable after owner loss.
Advisory progress may coalesce for display.
Scientific event segments cannot use that UI behavior.

An owner restart cannot renew a live session from historical bytes.
Read and reconciliation remain available through their separate ports.
Reattachment requires an explicit new source generation and the original dependence root.
No software fixture, receipt or session boundary establishes scientific qualification.
