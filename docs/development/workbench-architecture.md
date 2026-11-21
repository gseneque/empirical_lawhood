# Local workbench architecture

SPDX-License-Identifier: CC-BY-4.0

This decision selects the workbench's application and process boundaries.
The explorer supplies a registered collection, recursive inspection, retained
results and programme/discipline Knowledge views. Secondary tools preserve the
exposed RC lifecycle and other original operations. Each enabled operation needs its own accepted handler.
The [operator guide](../using/research-workbench.md) gives the selected module
commands and the current inspection scope.
Use the [compatibility policy](compatibility.md) for the existing public surfaces.

## Processes and ownership

```text
Browser -> loopback broker -> selected engine process -> API application services
                                                     -> existing scientific owners
CLI -----------------------------------------------> API application services
```

The broker is an outer application in `empirical_lawhood.workbench`.
It accepts registered requests and starts one selected engine invocation.
It neither compiles scientific tasks nor owns their scheduling or native cadence.
Application context, descriptions, requests and projections belong to the API.
Existing programme, inquiry, assessment and custody services keep their meanings.
Infrastructure owns retained invocation records and bounded process I/O.
CLI parsing and browser rendering remain separate presentation owners.

The engine entry point is a module in the selected installation.
The broker runs the explicitly selected interpreter with a fixed argument array
and a bounded JSON request on standard input. Requests cannot select Python
imports, shell commands or another interpreter. A negotiation response identifies
the actual package, interpreter and supported application contract before dispatch.
Each invocation starts in a new process. It never changes a running process's
import path to select another installation.

A browser connection, application invocation, scientific run and continuing
source session have separate identities. Closing a browser does not cancel or
repeat work. The effectful slice will persist dispatch intent before entry and
return an existing handle for an identical request key. An uncertain entry stays
uncertain until its owning records resolve it. Continuing sources keep their
backend session service independently of an individual browser or request.

## Frontend and dependencies

The frontend consists of native JavaScript modules, CSS and HTML under the
workbench package's `assets` directory. There is no production JavaScript
dependency, bundler or network asset. The wheel includes these
files as ordinary package resources. The sdist includes the same sources.
The console uses the EL blog's navy, off-white, gold, Inter typeface and selected
equal-circle recursive logo. The earlier gentle-growth logo remains in secondary
tools. Both exact masters and the font are bundled for local use.
Their [asset provenance](../../src/empirical_lawhood/workbench/assets/PROVENANCE.md)
retains the original bytes, identity and separate font licence.
The current whole-distribution source rules therefore include frontend changes.
A console edit does not have an independent scientific implementation identity.

Browser checks use the separate [frontend manifest](../../frontend/package.json)
and npm lockfile. They select Playwright Test 1.65.0, Node 24 and npm 11.7.0.
Install this toolchain into an explicitly selected external directory, with its
cache, browser scratch, screenshots and traces also external. It is not a Python
runtime dependency and does not change the scientific lock.

The initial browser is the host's stable Google Chrome through Playwright's
`chrome` channel. Record its actual version for each acceptance. The current
host is Ubuntu 20.04.6 with glibc 2.31. That host is outside Playwright's current
listed Linux platforms, so a successful selected-browser exercise establishes
only the observed host/browser combination. Do not infer other-platform coverage.
Use an existing browser; do not replace the user's browser installation.
See the primary [browser-channel documentation](https://playwright.dev/docs/browsers#google-chrome--microsoft-edge)
and [platform requirements](https://playwright.dev/docs/intro#system-requirements).

## Local transport

The first transport uses the standard-library HTTP handler on `127.0.0.1` with
an explicitly selected port. It serves only a closed asset list and versioned
application endpoints. It is a local one-operator service. It has no internet
hosting, arbitrary file server, directory listing or multiuser contract.
The Python [HTTP server documentation](https://docs.python.org/3.11/library/http.server.html)
does not offer a production security boundary; the broker must enforce the
local controls below before the first view is exposed.

Requests require the exact Host, same-origin browser context, JSON content type,
bounded content length and a fresh session secret. The secret is supplied in a
URL fragment and then a request header, never a query string or retained log.
Refuse cross-origin requests and unsupported methods. Set a restrictive content
security policy, disable framing and MIME guessing, and return `no-store` for
scientific projections. Render scientific text as text, without executable HTML.
Links use an explicit permitted protocol policy.

Use bounded polling for advisory updates. There is no persistent report cache,
event stream or automatic disk scan. One active invocation per selected context
is sufficient initially. Request and response sizes, pagination and any read
timeout are explicit application limits. They do not become scientific deadlines.
The selected RC effects and Matrix frontier read have durable lifetimes
independent of HTTP timeouts. Dispatch intent precedes exclusive worker entry.
PID, boot and start-tick observations distinguish a live worker from PID reuse;
an unavailable observation remains uncertain. Response-delivery expiry closes
the pipe without killing or repeating work. No scientific response cache exists.

The [shared attempt composition](../../src/empirical_lawhood/api/invocation_retention.py)
owns context, bounded input capture and stage records below the CLI and workbench.
The [invocation service](../../src/empirical_lawhood/api/application_invocation.py)
uses that composition with the shared [operational-progress.v2 owner](../using/progress.md).
A separate bounded progress companion carries invocation identity and sequence.
Nested owners fan observations to the CLI and share one heartbeat. Unreported task and
attempt identities stay absent; telemetry cannot set scientific or execution state.

## Compatibility and current access

Application request and projection versions are independent of canonical record
schemas and the existing `ApiResult` envelope. Unknown versions refuse before
handler entry. Exact Decimal values and large identifiers retain their original
representation. A presentation projection creates no canonical scientific object.

Only engines containing the new entry point can satisfy its negotiation contract.
The accepted foundation engine predates that entry point. Preserve it and its
documented CLI. Do not inject a bridge into a frozen scientific installation.
A later reader may inspect original evidence only through its tested public
custody and semantic owners. Otherwise display the operation as unavailable and
name the missing compatible reader. No legacy execution adapter is selected.

Context contains explicit source, interpreter, operator profile, artifact-root
contract, trust/catalog selections, worker limits and output destinations where
the operation requires them. It contains no saved access verdict. Static
discovery needs no execution storage plane. Every retained read refreshes current
access through its actual owner, and final byte checks remain mandatory.

Ordinary navigation uses execution records. A scientific assessment is a separate
explicit action. The selected Matrix programme uses its actual `read` method with
reconstruction off; it has no `read_execution` method. Full reconstruction needs
an explicitly selected durable scientific-read route. The current Matrix route
keeps reconstruction off even in its durable worker. Protected or unavailable records cannot be
made visible by a browser filter, prior successful read or cached projection.

## Extension constraints

The operational collection belongs to `api.application_collection` and the
guarded atomic store in `storage.workbench_state`. A collection is at most
one MiB and 256 entries. It stores explicit original locators, aliases and
editorial metadata; it is neither a scientific catalogue nor a response cache.
`application_exploration` and `application_companions` compose fresh original
reads, exact records and verified joins. The domain composition owns any
scientific field mapping. Immutable evidence and editable selections stay separate.

The shell separates transport, navigation, diagrams, geometry, collection,
details and activity into fixed local modules. Scientific records cannot select
code. Shared geometry uses measured labels and fixed circle ports; visible
windows stop at sixteen nodes, thirty-two edges and eight expansion levels.
Routing has a one-second budget; failure selects the complete outline.
The complete outline remains available. Positions and editorial memberships
cannot establish scientific relationships. Navigation preferences contain no
scientific bodies, paths or access decisions.

Remote observation uses `execution.operational_observation` for versioned finite
contracts, infrastructure for original supervision reads and sealed transfer,
and `api.operational_observation` for composition. The standalone collector owns
its observation lifetime. Existing native-subwork, supervision, deployment and
transfer owners retain their actions and meanings. The browser sees only a
verified local snapshot, never provider credentials or raw provider responses.
Source cadence, staleness, collector sequence, allocation and complete return
coverage remain explicit. Scientific completion, financial lifetime and original
evidence return are independently terminal. See the
[operator procedure](../using/observing-remote-work.md).

The source, allocation body and current collection pins are checked before an
observation returns. Collector replacement preserves accounting floors and
retired lifetimes. Original-return journal actions separately record byte
verification, original scientific reading and contribution inspection; none
implies destination admission. The registered Rubisco preparation-response callback
already supplies bounded prefix, continuation and selected-response metadata.
Its cumulative prefix ledger includes retained continuation input; response counts
belong to the selected wave. Independent analysis and destination admission use
separate original readers. New callbacks use the same presentation extension and
need acceptance at their declared source and scope.

The supported repository registration and build route owns executable extensions.
Scientific files cannot select browser code or backend imports. Adapter-owned
descriptions and bounded presentation projections enter through closed generated
registration. Unknown records can have an identifiable generic view without
acquiring an interpretation or scientific standing.

The [presentation contract](workbench-presentations.md) uses the existing closed
API descriptor generator. Installed domain readers supply bounded data to the
same application, durable invocation, table and exact-record inspector.
Unsupported panel revisions retain a generic view after the same current owning read.
An unknown panel identity refuses before storage access.

The [historical source composition](../../src/empirical_lawhood/api/application_continuing.py)
reads original exposed sessions through the existing store.
Selected windows and finite requests retain their original clocks, dependence, gaps and uncertain effects.
Historical actor leases create no current handle or live source owner.

The [knowledge composition](../../src/empirical_lawhood/api/application_knowledge.py)
reuses certificate verification, exact store locators, replica recovery and guarded catalogue access.
Bounded queries describe only the selected import page. Current resolution repeats the original verifier.
Operational review binds exact transfers, current storage contracts and explicit destinations.
Apply repeats the owning checks before effects. Browser confirmation creates no scientific or access authority.
Partial reports omit transport diagnostics while original custodian notice reasons remain intact.

Source/session clocks, restricted actor information, dependent assessments,
revision coexistence, aggregate costs, certificates and two-store exchange remain
with their shared backend owners. The same operation/context/invocation model
exposes each accepted contract. A UI handler cannot replace
a missing scientific contract with a field or a status label.

## Verification scope

Run focused contract and browser controls for each new boundary, using inspected
bounded fixtures. Reuse unchanged retained lifecycle and artifact evidence.
Do not run a complete portable, integration, scale, native or held test profile
for this workbench selection. Software fixtures and original scientific studies
have separate authority and evidence limits.

## Inquiry application binding

The [inquiry application](../../src/empirical_lawhood/api/application_inquiry.py)
composes the existing versioned request decoder and decision/successor API.
`preview_inquiry_decision` is the original prepublication computation;
commitment repeats it and can require the reviewed packet digest.
`preview_inquiry_authoring` is the original initial or registered-supplier
validation. `read_inquiry_successor` is the original pre-execution admission join.
Execution continues through its existing owner after that same join.
No policy record, scientific identity or scheduler is added by the client.

The review digest binds the selected context, current storage contracts, input
bytes, destination and actual decision or successor draft. Application input
bindings use the existing contained reader and invocation-overlap checks.
Reads use the original exposed-custody owner and a complete closing byte check.
Historical decision inspection remains explicit and grants no current admission.
The client exposes commitment and authoring separately from scientific execution.

## Composite programme binding

The [programme application](../../src/empirical_lawhood/api/application_programme.py)
composes the existing closed codecs, input resolver, `ExecutionSelection` and
`ExperimentProgrammeService`. Its preparation and component reports retain their
original scope. The extracted `read_experiment_programme_descriptor` uses the
original canonical descriptor and exact installed protocol/revision checks
without constructing the selected service. Absence is an explicit composite
refusal in this client; the existing general programme service keeps its
single-campaign route.

Operation review never calls an unconfirmed run: a domain owner can legitimately
publish metadata during such a call. Review pins the exact descriptor and
selected copied request. Explicit apply repeats the review and delegates to the
original confirmed run or recovery owner. Review and browser confirmation grant
no component authority. The existing invocation, source, profile and output
containment controls remain in force. Copied control bytes are bounded to 1 MiB;
this does not enlarge an original scientific member or codec contract.
