# Integrity and bookkeeping performance

SPDX-License-Identifier: CC-BY-4.0

Scientific integrity work has three different owners: a scientific method establishes
what a result means, a read or publication owner establishes which original bytes
were consumed, and an application composes those owners into a researcher workflow.
Optimize repeated work inside one owner. Do not substitute a transport digest for
a scientific test, or retain an access decision as though it were immutable data.

This guide records the November 2026 profiling changes. Exact revision identifiers,
timings, benchmark inputs, failure logs and focused verification results travel in
the accompanying `handoff/` evidence packet. These observations do not establish
acceptance of a new molecular construction or a production deployment.

## What each check establishes

| Owner | Question answered | Reuse boundary |
| --- | --- | --- |
| Scientific record and method | Are units, scientific scope, denominators, thresholds, numerical values and complete adverse outcomes valid for this calculation? | Pure intrinsic checks may share deeply immutable records within the same numerical and implementation context. Contextual scientific joins remain with the consuming method. |
| Canonical representation | Are record shape, exact Decimal values and canonical identity unambiguous? | Reuse immutable encodings and type metadata. A projected mutable document remains an independent document. |
| Source admission | Is this the selected executable implementation, dependency selection and source closure? | An admitted source is useful only while its exact current source remains unchanged. |
| Publication custody | Are this payload, sidecar, complete sibling roster and commit the selected published objects? | One finite read can share a verified complete publication. Its owner retains the final byte and membership check. |
| Access and prospective controls | May this caller read these outcomes or perform this effect now? | Refresh at the owning access boundary; a cached scientific object is not permission. |
| Native execution and recovery | Was a native call entered, returned, interrupted or left uncertain? | Reuse durable original receipts, never infer completion from the presence of files or authorize replay from a cache hit. |
| Transfer and archive | Did the selected complete set arrive, and does the carrier contain the original members? | Hash physical bytes once within a census or a carrier stream, then perform the separate closing check owned by that operation. Transfer success conveys no scientific completion. |

TCP includes a checksum for its own segments. It does not name an EL experiment,
source revision, cutoff, atom ordering or publication roster. The application still
needs those identities. Conversely, repeatedly hashing one unchanged file in the
same already guarded pass does not create a new scientific assurance. See
[RFC 9293, section 3.1](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.1).

File metadata is useful for detecting changes cheaply during a read, but it is not
a substitute for all final content checks. Timestamp resolution depends on the
filesystem even when the interface reports nanoseconds; see the
[Python 3.11 `stat_result` documentation](https://docs.python.org/3.11/library/os.html#os.stat_result).

## Composition rules for efficient readers

Use the existing complete-selection methods when several selected records share
one publication. For an effect-free operation with several consumers, the existing
`ExternalArtifactPlane.read_context()` owns a finite shared read:

```python
with artifact_plane.read_context() as reading:
    members = reading.verify_manifests_members(
        selected_manifests,
        validate_members=lambda current_members: current_members,
    )
    # Consume within this owner. Every scientific consumer still performs its
    # contextual joins and current access checks.
    first = first_consumer(members)
    second = second_consumer(members)
# The enclosing owner has performed its final checks before results escape.
```

Do not widen this context across authoring effects, worker execution or an
indefinite interactive session just to keep a cache warm. An independent invocation,
a changed source or validation policy, an explicit traversal budget and a different
physical locator need their own checks. Worker delivery remains an independent
boundary with its own sealed inputs.

Every new `write`, `write_stream`, and `write_batch` publication uses compact
sidecars. Each sidecar contains its own logical and physical member facts and an
exact commit pin. The complete roster occurs once in the commit. There is one
publication API and no alternate expanded writer or compact-mode switch. Existing
closed full-manifest records keep their strict typed decoder; sealed historical
bytes are never rewritten. Readers of physical sidecars use `read_manifest`,
`read_artifact_sidecar`, or `resolve_artifact_sidecar_bytes` when a caller has
already pinned/accounted the bytes. A pure full-manifest record decoder does not
perform I/O and cannot resolve a physical reference.

The scope owner shares the exact resolved publication object across siblings.
Payload identity, complete sibling membership, current access and the final byte
census remain independent checks. The `publication.write` progress step advances
by examined stream bytes and reports an exact total only when one was supplied.
Unknown-size streams report processed bytes without pretending their allocation
bound is a completion estimate.

## Cache admission and lifetime

Recursive contribution and authored-wave caches retain metadata. Their allowance
must measure the Python object graph actually retained: containers, buffers,
canonical ropes and inherited encoding caches. The sum of external payload sizes
is a custody or traversal quantity, not the memory used by this metadata cache.

The implementation counts shared objects once within an entry, stops at explicit
byte and object limits, and declines optional reuse for an unknown data shape.
It does not read external files or flatten canonical encodings to count them.
Callers receive independent mutable report containers while deeply immutable
scientific records can remain shared. Both the enclosing authored-wave cache and
the active projection's wave cache now apply byte and entry admission, with
oldest-entry eviction. An unsupported or oversized graph takes the fresh read
route; it does not become a scientific refusal. Projection reuse therefore cannot
bypass the enclosing cache's accounting by retaining every wave in another map.

Final guards have a separate, mandatory lifetime. For stock payload readers the
current-access guard retains the original authority owner, and the member guard
retains only the selected logical/materialization facts. It does not retain the
reader's decoded indexes, packet, plans, or report graph after their consumers
release them. Inside one active byte owner, identical selections reuse the same
guard object only when their original authority and selected immutable fact
objects are identical, including their physical paths. Access is checked again
every time; the guard never memoizes a permission decision. Different authorities,
locators, selections, policies and read-scope bindings retain separate guards.
Custom replaced reader callbacks keep their actual state because the implementation
cannot safely infer which state their policy needs.

The cache allowance is not an RSS limit. Independent mandatory file snapshots,
current authority owners, scientific objects held by callers and process workers
still consume memory. Their minimum fact census grows with the number of distinct
consumed files and authorities. Per-entry accounting may conservatively charge a
shared immutable object again in another optional cache entry. Scope exit clears
both the optional metadata and the mandatory guard indexes.

Full recursive product reads compute each decoded product's exact identity and
then release its derived canonical encodings before retaining the population.
This includes encodings cached on nested array-manifest records. Scientific
fields, typed validation and identity remain intact; a later request for canonical
bytes reconstructs the same bytes. Both batch reads and custom-policy serial
reads use this boundary. The complete typed population still occupies memory
proportional to its scientific fields; this is not a constant-memory reader.

Pure intrinsic validation reuse is bound to its active process and thread, exact
validator and numerical policy. Copied closed contexts, different threads and
forked processes validate in fresh lifetimes. Decimal precision, rounding, exponent
limits, clamp/capital settings and traps remain part of the policy. Calls without
an owning reuse scope invoke the validator directly without constructing unused
cache keys.

## Transport composition

Local process workers emit bounded chunks to an exclusively created temporary
file. The parent hashes these chunks, flushes the file once, closes its writer,
and retains a read descriptor. This file owner belongs to one process and thread.
It cannot be copied, serialized, consumed twice, or used after closure.

The ordinary artifact publisher adopts this file when staging uses the same
filesystem. An exclusive rename transfers ownership without another payload
write or data flush. The publisher reads the actual bytes once and compares
their extent and digest with the original collection. It retains registered
codec and semantic validation, publication limits, lineage, and final byte
checks. Transfer supplies no scientific or access authority.

Cross-filesystem publication uses the existing bounded copy path. Other stream
sources keep that path. Both paths use the same publication intent, sidecars,
commit and receipt protocol. Source and destination directories are synchronized
after adoption. Producer cleanup cannot remove an adopted or published file.
Failed staging removes only the temporary file owned by that operation.

An interruption can occur after the commit rename but before its caller returns.
Rollback reacquires the publication locks and examines the commit path before
removing any member. A present commit prevents rollback. Recovery authenticates
the complete existing publication before it can report success.

The focused controls in `tests/test_owned_output_publication.py` compare exact
publications and count actual payload writes, flushes, validation and hash passes.
Same-filesystem adoption reduces two payload writes and data flushes to one each.
It retains one source read, one format validation and both final publication
hash passes. These counts exclude metadata writes and directory synchronization.
They are software controls, not a prediction of elapsed production time.
They include abrupt process exits around transfer, intent, final placement and commit.
An uncommitted temporary file does not establish publication success.
Ordinary retry authenticates the exact complete output and its original commit.

`FileHashCensus` has one owner per census. Every logical pathname still opens a
descriptor and applies its byte allowance. Unchanged hardlinks may share the
digest of their common physical file within that pass. Logical byte and member
bounds still count every declared name. A closing census starts fresh and reads
each physical body again. There is no persistent file-digest cache.
When the filesystem supplies no usable nonzero inode identity, every path is
hashed independently and no hardlink relationship is inferred from that identity.

An original-tree archive is verified by independently parsing every member and
hashing the same carrier stream. An archived hardlink has no body of its own; it
must reference an already verified ordinary member with the same declared digest
and length. Symlink targets remain uninterpreted link data. Extra members, altered
metadata, wrong targets, nonzero trailing data and changed source membership
refuse. The caller must first close native writers.

The return composition owns one opening package census, the carrier/member
comparison, and one closing package census. It does not nest two standalone
two-census verifiers. Standalone transfer verification keeps its own complete
opening and closing comparison.

## Repaired-wave control reads

A closed repaired wave contains both predecessor-owned events and events created
by its new attempts. The ordinary finite control batch now authenticates that
complete mixed population in one existing read scope. It derives a path-to-owner
map once, binds each owner's exact recovery-index identity once, and checks every
receipt against the owner that actually issued its event. The map is local to
the read and grants no replay, source substitution or native-contact authority.
Unrepaired waves retain their single-owner route without this additional map.

Every control batch retains the number of decoded receipt/event candidates,
including absent candidates, for its finite lifetime. Per-receipt guards still
recheck the current custody limit, current reader policy and exact live owner,
but do not rescan the full task roster to recompute that immutable count. A
stricter limit or closed scope still refuses immediately.

Output, controller and retained-adoption repair selectors search their validated
sorted immutable task rosters directly. A single lookup takes logarithmically
many indexed reads instead of rebuilding or scanning the full receipt census.
This removes a quadratic lookup component from full repaired-population reads;
it does not claim that every part of reconciliation has constant or linear cost.
Custom receipt/recovery readers keep their existing serial policy hooks. Changed
original receipts, new-wave events, previously absent controls, access and final
file snapshots still refuse the operation.

The focused controls in
[`test_development_output_repair.py`](../../tests/test_development_output_repair.py),
[`test_development_controller_repair.py`](../../tests/test_development_controller_repair.py),
[`test_retained_e3_control_repair.py`](../../tests/test_retained_e3_control_repair.py)
and [`test_recovery_control_batch.py`](../../tests/test_recovery_control_batch.py)
check original/new ownership, exact result parity, roster read counts, live-limit
and mutation refusal, and no duplicate completed work. They are software-conformance evidence.
Installed-source interruption acceptance and completed scientific-population
timings remain separate measurements at the final selected source.

## Rubisco source archives

The durable molecular archive producer first selects and hashes the complete
directory. The raw framer takes that explicit selected census and checks each
selected member's size and digest while emitting its framed bytes. Compression
flows once through `publish_output` into the artifact plane's exclusively owned
staged file descriptor. The plane hashes and measures that actual stream and
validates its format before commit. No private temporary compressed spool, second
copy, or speculative double-space requirement on the source volume remains.

`publish_directory` requires the typed selected census explicitly. The durable
call ledger passes the same census already bound into its request; it does not
resample the operand population for publication. Other callers select their
census immediately before invoking the publisher. Selected paths must belong to
the declared directory before a body opens. The generator performs the complete
closing directory census before it can finish; additions, removals and edits
still refuse. Failure closes the stream explicitly, and a publisher that reports
success without consuming the complete stream is rejected.

Source passes remain three per standalone publication and six for a durable call
whose pre-call and post-call populations are unchanged. The removed work is the
extra compressed-spool copy: the compressed carrier is written once. The outer
durable-call progress step reports operand publication, the engine call and
return publication separately. An opaque third-party engine phase is explicitly
indeterminate unless the engine supplies its own finer progress.

The original native-call cost still starts after operand publication and ends
before return publication. The actual operand-publication cost is now measured
separately; use the outer operational timer for the complete workflow. The
established native cost field has not been redefined. Retained completed-record
readers use the generic `execution.retained_native_records.decode_completed_record`
owner: a frame's declared length must agree with the receipted typed census before
its body is read. There is no arbitrary 32 MiB metadata ceiling in that route.

The raw framer does not claim to own directory membership. This removes a nested
closing census while preserving the publication-level closing check, including
new files and removed members. An early stream consumer cannot publish a successful
result. The old hidden SHA calculation in `file_chunks` is omitted when no expected
digest was requested; a caller that compares a digest still computes it exactly.

These changes concern byte ownership and CPU/read overhead. They do not alter
Amber/OpenMM scientific parameters, atom ordering, acceptance thresholds, original
negative findings or the distinction between a known native return and an
uncertain call. Molecular validity still requires the scientific preparation and
analysis owners and the actual WT/I95M execution described by the programme.

## Measure the right quantities

For each measured phase record wall time, main-process CPU, waited-child CPU,
process read/write traffic, physical storage counters where available, and peak
memory with its scope. Record source identity, environment, original input digest,
logical sizes, physical sizes, independent units and whether native work occurred.

Do not add nested phase durations to their enclosing duration. Linux `rchar`
includes reads satisfied by cache and reads from pipes; it is not disk traffic or
network transfer. A fresh Python owner does not imply a cold filesystem cache.
Use separate counter/profile passes where tracing would distort timings. Include
all final owner checks in the measured operation and preserve every repetition,
including regressions and failures.

Useful scenarios include a single record; repeated immutable subgraphs; distinct
records of the same size; one large publication and several small publications;
nested and independent readers; two physical locators for equal logical identity;
eviction and admission failure; changed access/validator/Decimal policy; explicit
ancestry limits; exceptions; copied contexts; hardlinks and ordinary unique files;
and publication/return after the producer has closed.

Focused software controls demonstrate these contracts. Numerical tests must name
their independent reference through the existing `numerical(oracle=...)` marker.
Neither a passing custody test nor a faster HOLD proves biological validity or
GPU utilization. Production M50 timings require the actual retained input closure
on the selected host; use the outer handoff's prioritized in-repository checklist.

## Reproduce publication and reader-lifetime measurements

Run `scripts/benchmark_publication_memory.py --repo CHECKOUT --label LABEL
--readers 64 --output RESULT.json` with the same locked interpreter against each
checkout. The default publication scenarios use 16, 64 and 256 canonical software
records, three repetitions and fresh output directories. Timings include the
complete publication owner; request construction and import time are excluded.
The separate memory scenario creates 64 actual readers of the same 64-member
publication under one original current-access owner. It adds no synthetic padding.
It measures surviving reader references and traced Python allocations while the
file/access guards are still live, then revokes access to ensure final exit refuses.

The accompanying handoff retains every raw sample, including the first diagnostic
pass in which reader release alone did not reduce total traced memory. The final
implementation additionally shares exact guard facts and bounds active projection
metadata. Peak traced allocation, retained traced bytes and process RSS have
different meanings; no production M50 memory or GPU throughput claim follows from
these software-only workloads.
