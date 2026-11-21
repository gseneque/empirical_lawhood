# Share configuration through an owning composition

SPDX-License-Identifier: CC-BY-4.0

This guide gives a worked pattern for shared immutable configuration and read-only services.
It preserves separate method ownership, input permissions and scientific receipts.
Select an exact service revision before constructing its consumers.

## Prerequisites and first action

Select the [locked base environment](../using/environments.md) and its matching checkout or source distribution.
Read the [supported interfaces](extension-interfaces.md) and [record revision rules](record-revisions.md).
Use explicit external paths for any subsequent execution or retained evidence.

Run the pure composition example:

```sh
uv run --no-sync python scripts/examples/shared_mass_reference.py
```

The report identifies one shared service, two providers and separate input handles.
The example opens no scientific input and executes no task.
Its invented implementation pin and exposed mass values provide software evidence only.

## Declare one owner

The existing `CompositeCampaignRuntimeProvider` joins complete, nonoverlapping provider products.
`CampaignRuntimeProviderRegistry` selects an explicit composition by its complete capability-registry fingerprint.
`LayeredCampaignRuntimeProviderResolver` selects that composition before its ordinary factory route.
Additional construction records or ports refuse because the composition already consumed its selections.

The worked API is `api.shared_mass_composition.compose_mass_reference`.
It accepts the original mass-balance registry, compiled plan, two configurations, scope bytes, scope identity and separate input suppliers.
Its two-operation limit belongs to this example.
The generic composition contract has no corresponding two-operation limit.

| Responsibility | Worked owner and contract |
| --- | --- |
| Namespace and service revision | `MassScopeService`: `mass-balance.shared-scope@1.0.0` |
| Configuration and decoder | Exact `MassScope@1.0.0`, canonical bytes, SHA-256 identity and a 4,096-byte limit |
| Construction | API composition decodes the common scope once and supplies the same immutable service to both providers |
| Scientific producer | `shared_mass_reference.producer.MassForecastProvider` retains `mass-balance.predict@1.0.0` |
| Scientific consumer | `shared_mass_reference.consumer.MassAssessmentProvider` retains `mass-balance.assess@1.0.0` |
| Input permission | A separate `OperationInputHandle` binds each operation, exact execution plan and finite input census |
| Execution and receipts | Existing runners, scheduler, artifact plane and receipt store retain each original task |

Both providers resolve a typed `ScopeServiceSelection` containing the service namespace, service revision and exact configuration identity.
Wrong namespace, revision or bytes give distinct refusals.
The common scope retains quantity, kg units, population, source, receiver and clock.
A correctly encoded but incompatible scope refuses before any provider construction or input access.

The service contains no observations, native handle, effect authority or cost ledger.
The composition creates no duplicate configuration records or scientific identities to satisfy constructor ownership.
Existing operation configurations retain their original embedded scope and canonical bytes.
The shared service adds no new scientific meaning to those records.

## Preserve separate permissions

Each input handle exposes at most sixteen exact immutable input specifications.
A changed specification or another operation's input refuses before the supplier is called.
The underlying supplier may be shared, but its wrappers retain separate permissions.
The existing artifact and runtime owners still authenticate returned bytes, lineage and access.
Service selection alone grants no input access.

The original forecast and independent assessment retain distinct task identities and receipts.
Adverse and unevaluable outcomes remain in the complete three-unit software denominator.
Completed recovery reuses both original receipts without another source read or calculation.
Each native effect, resource allocation and cost record must retain its actual owner when an effectful extension uses this pattern.

This Python interface is a contract for trusted installed implementations.
It is not a process sandbox against malicious code that inspects private objects.
Scientific input records cannot select arbitrary imports or service implementations.

## Keep registration conflicts explicit

Do not register the common construction record independently under both owners.
Provide it once to the owning composition and inject only its permitted reference.
Global constructor-schema ownership and effect-authorizing port ownership remain exclusive.
Same-class output codec reuse does not relax either rule.
Two conflicting implementations of the same schema and revision still refuse.

Use distinct ports for independently authorized effects and resource accounting.
Do not wrap an unrestricted mutable object in this immutable service type.
The example rejects every configuration type except its exact immutable `MassScope`.

## Mutable sources require a lifecycle owner

A mutable substrate needs one service that owns its session and lifecycle.
Each actor needs a separately authorized handle bound to its session, actor, allocation and applicable generation.
Sharing a session identity must not share observations, effect rights or an evaluator's private ledger.
The owning service must check current permissions and generation before every read or effect.

Finite commitments, expiry, uncertain delivery, event retention and recovery belong to the continuing-source contract.
This immutable example does not implement that lifecycle or advertise a continuing-source capability.
Do not infer actor isolation or native-effect acceptance from its successful composition.
Retain separate continuing-source acceptance before selecting a mutable service.
