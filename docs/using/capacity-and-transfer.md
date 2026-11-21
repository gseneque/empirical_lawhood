# Capacity, preparation and transfer

The workflow records the bytes actually selected and produced. A large authoring
record, complete scientific population, native return or evidence census does not
need another decoder profile merely because it crosses 16, 32, 64, 128 or
256 MiB. Recursive prospective authoring uses one scientific selection decoder
and the original typed specification. There are no size-tier envelopes.

Each retained member still has an exact schema, revision, byte count and digest.
The authenticated member inventory provides its read extent. A reader opens a
regular file without following links, checks the descriptor's actual extent,
and verifies that its identity remains stable through the read. Growing,
truncated, replaced, noncanonical or wrongly bound files remain invalid.

## Selecting resource allowances

`ArtifactCustodyLimits` allows an operator to select optional bounds for control
records, in-memory publication, metadata, publication membership and aggregate
bytes. `None` means that no extra operational ceiling is imposed. The observed
extent remains finite and authenticated. A selected bound is enforced before
publication or allocation where the owning API has that information.

Task `ResourceBudget` allowances and the selected scientific execution envelope
still apply. Increasing a PURE-output reservation does not grant execution,
spending, source access or scientific authority. IPC transports large PURE
outputs in bounded chunks; crossing 256 MiB no longer causes an unrelated global
refusal. Native readers likewise retain exact returned file censuses and typed
array shapes instead of treating an arbitrary archive size as a validity test.

`RecursiveClosureLimits` exposes optional member, aggregate, metadata and hash
byte allowances. Its optional count/depth controls are traversal work selections. Selected positive limits can exceed the previous hard-coded upper
clamps. Closure walks preserve every selected member; exceeding a selected
allowance causes a visible refusal rather than truncation.

Memory is still needed for JSON/YAML parsing and libraries that require a whole
array. Removing a hidden byte ceiling does not make those operations streaming.
Select an appropriate host or an explicit operator allowance for such work.
Bounded stream buffers, strict canonical structure, path containment, object
identity and declared scientific resource budgets remain independent controls.

## Preparing inputs, evidence or logs for any host

Use one generic operation for ordinary files in either direction:

```bash
empirical-lawhood deployment prepare-files \
  --root /absolute/selected-inputs \
  --output-dir /absolute/prepared-transfer
```

The output directory contains `payload.tar`, `payload-manifest.json` and
`SHA256SUMS`. The command prints the manifest SHA-256, observed source file and
byte counts, and the verified carrier size and digest. It makes no network
connection. Canonical Unicode names and spaces are supported. The common
relative-locator contract still excludes traversal, control characters,
backslashes and ambiguous Unicode normalization.

For an explicitly chosen transport allowance, add `--maximum-bytes` and/or
`--maximum-files`. Omitting them selects the observed complete census; it does
not silently substitute another global maximum.

Preparation uses one opening source census, one streamed archive write and
independent archive read, and one closing source census. This checks that every
archive member matches the selected original bytes and that the selected source
population did not change during preparation. A failed preparation leaves its
partial directory visible and does not publish a successful manifest. It does
not delete the original files or claim scientific completion.

After the host's normal transfer mechanism has moved and extracted the package,
verify the selected directory using the separately retained manifest digest:

```bash
empirical-lawhood deployment verify-files \
  --root /absolute/received-inputs \
  --manifest /absolute/prepared-transfer/payload-manifest.json \
  --sha256 EXACT_MANIFEST_DIGEST_FROM_PREPARATION
```

This is an identity/custody check against the selected scientific input
population. It does not duplicate a transport checksum simply to re-establish
that the network moved some bytes. It checks that the receiving workflow will
use the exact selected members and that no member was omitted or substituted.

The accelerated `deployment prepare` command uses this same owner for its
payload. Runpod/SkyPilot-specific code only supplies placement, resources and
launch configuration. For return, select the original evidence and logs as the
`--root` of `prepare-files` on the worker; transfer and verify the result through
the same procedure. Primary receipts and scientific qualification remain
unchanged by transport.

When preserving an original tree's symbolic/hard links and directory metadata
is required, use `deployment archive-originals` and `verify-originals` with the
explicit tree allowances. That archive includes a complete original-tree census.
Its metadata no longer has an unrelated 16 MiB limit.

Source capture and release retention also stream the committed archive. Complete
Git status/tree observations and source identity reports have no additional
fixed byte ceiling. The source tar parser still refuses unsupported/sparse
member types and limits a single extended header and nested header depth; these
are parser safeguards, separate from the total source population. Git commands
retain their process-management timeout and bounded diagnostic stderr.

## Progress and machine readers

The CLI reports progress on stderr while keeping its JSON result on stdout.
Census phases report processed paths; carrier writing and verification report
bytes against the selected totals. The global `--progress-file` option exposes
the same operational events/snapshot for a future UI. A tar library call may
report its member boundary rather than every internal block; the lifecycle
heartbeat still shows the active phase, elapsed time and time since the last
work report. Progress is operational observability, not a scientific receipt or
a claim that an external library has completed unobservable work.

See [results and failures](results-and-failures.md) for the lifecycle contract
and [testing](../development/testing.md) for the focused conformance tests.
