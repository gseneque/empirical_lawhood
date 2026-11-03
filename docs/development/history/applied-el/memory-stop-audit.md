# Applied EL memory stop audit

SPDX-License-Identifier: CC-BY-4.0

**Availability:** the historical `memory-import-probe.py`, `pybamm-memory-import-probe.py`, JSON observations and separately hashed acceptance script are not distributed.
Their commands and hashes describe the original external engineering packet.
This release supplies neither that packet nor a public retrieval route for it.

11 October 2026. This is bounded engineering triage of the first operational
Rubisco failure. It supplies no scientific retry, resource amendment, provider
execution, biological result or qualification. The original allocation remains
stopped at one failed attempt, with zero scientific products and native contacts.
Original attempt CPU, wall time and peak RSS remain unknown. See the
[allocation closeout](../../../../programmes/shared-records/applied-el/closeout.md) and its [exact record](../../../../programmes/shared-records/applied-el/closeout.json).

## Retained failure and resource ordering

The retained recovery event is
`runs/recursive.59509ef5afa9c577c84c8866/recovery/wave.development/events/rubisco-inquiry.supply/attempt-001.json`
under `/dev/shm/empirical-lawhood-applied-el-20261011/artifacts`, SHA256
`8781151c4825f8f3b55ba4eec14af4bfe29ef808f4d25407b43aaff007cc706b`.
It records ordinal 1, `FAILED`, `RETRY_EXHAUSTION`, nonretryable `MemoryError`,
sanitized message `child process memory failure`, no output materializations and
`scientific_evidence: false`. It does not identify the failing allocation or retain
a child traceback or memory sample. The authenticated no-product STOP therefore
remains an operational unresolved outcome, not enzyme failure.

The execution plan binds `rubisco-inquiry.supply`, one maximum attempt and
`memory_bytes: 536870912` (512 MiB). The
[operation contract](../../../../src/empirical_lawhood/adapters/methods/rubisco_inquiry/operation_bindings.py)
declares the same bound. Existing
[process execution](../../../../src/empirical_lawhood/infrastructure/execution.py)
defaults to multiprocessing `spawn`. Python reconstructs the main module and
imports the runner before entering `_execute_in_child`. That target calls
`_sanitize_worker_process` before `runner.execute`; sanitization limits already
loaded numerical pools and then calls `_apply_resource_limits`, which applies
`RLIMIT_AS` to the declared memory bytes. Thus the enforced value constrains
virtual address space, not solely resident RAM, and pretarget imports already
occupy part of that space. The
[spawn environment](../../../../src/empirical_lawhood/infrastructure/worker_bootstrap.py)
sets all five numerical thread variables to 1 before the interpreter starts.

The acceptance main module imports both selected scientific adapters and the
composed authoring/execution services at module scope. Its main guard prevents
spawn from launching the acceptance loop again, but does not avoid those imports.
An existing material-family registration already documents the same distinction
between spawned scientific-runtime address space and RSS; its separate 8 GiB
contract grants this failed episode no extra allowance.

Reviewed source SHA256 values:

| Owner | SHA256 |
|---|---|
| `infrastructure/execution.py` | `7e6958aa83563ddc9f47030506e99c7695dc33f0c8154ef2836d43a4ba8f0bf5` |
| `infrastructure/worker_bootstrap.py` | `c075182b19f9a945be013a8b97c097b4dea7b4dfd7d0b3b81cd23d1238d694e0` |
| `rubisco_inquiry/operation_bindings.py` | `ba1ed948302f12cfb1c4145fca3def88e573cf3f2207c0c0e7dae1898d5d0ec9` |

## Engineering import measurements

Two fresh import-only processes used the installed CPython 3.11.14 locked
environment via `uv run --no-sync`, with `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` and
`NUMEXPR_NUM_THREADS` all 1, and `PYTHONHASHSEED=0`. No limits were changed:
both engineering processes inherited `RLIMIT_AS=(-1,-1)`. Neither constructed a
provider/model, solved a model, invoked a task or made a native scientific contact.
These are engineering measurements, not measurements of the failed attempt.
Linux `/proc/self/status` labels its KiB values `kB` below.

| Probe stage | VmSize, KiB | VmRSS, KiB | VmPeak, KiB | Threads |
|---|---:|---:|---:|---:|
| Rubisco probe: cold standard library | 33,872 | 17,384 | 51,224 | 1 |
| Selected Rubisco operation import only | 155,580 | 64,012 | 155,580 | 1 |
| Acceptance main imports and worker infrastructure, no execution | 650,208 | 326,428 | 650,208 | 2 |
| PyBaMM probe: cold standard library | 33,744 | 16,244 | 51,224 | 1 |
| Pinned PyBaMM 26.6.2.0 import only | 696,596 | 238,072 | 761,848 | 3 |

The Rubisco probe took 4.426 seconds wall and 4.425 seconds process CPU. The
separate PyBaMM probe took 1.728 seconds wall and 1.142 seconds process CPU.
Extra observed threads do not contradict the five numerical thread settings:
those variables do not promise a single thread for every imported runtime.

Probe scripts and logs are retained in
`/tmp/empirical-lawhood-applied-el-20261011`:

| Member | SHA256 |
|---|---|
| `memory-import-probe.py` | `b5288b70173d6c762b76f2d09ce3cea5fc95234a7a760b02e371af47dcb47d2c` |
| `memory-import-probe.json` | `5a2d05906ec6f9b18917ce64ccfbc487539e37cb2979121fc2e4f9ecb28fcac7` |
| `pybamm-memory-import-probe.py` | `9c794a341d949f835dac2432e2cb32bc5de2b9e1d79159db1720b122f191dcdf` |
| `pybamm-memory-import-probe.json` | `c2e47e6bbad2159ba724308c07bd1d2307bfb52cf397b46110d765a379b48d46` |

The probed acceptance script SHA256 was
`605eedaa137db58a217e60a496a47c58f3e4eb7125c4e9104648fde47bf31a0a`.
The probe executes its top-level imports under `engineering_import_probe`, not
its guarded `main`. It approximates the import footprint visible to a spawned
worker; it does not reproduce multiprocessing unpickling, input decoding or the
failed child exactly. Imports can map libraries and initialize runtime state even
when no scientific operation is invoked.

## Bounded interpretation and future engineering options

The main/worker import probe occupies about 634.97 MiB virtual address space
before task execution, about 122.97 MiB above the frozen 512 MiB address-space
ceiling, while RSS is about 318.78 MiB. Applying that ceiling after such imports
can leave subsequent allocations unable to grow. This source ordering and
measured footprint explain a plausible `MemoryError` mechanism without proving
its exact allocation site or replacing unknown original measurements.

A concrete future engineering option is a small standard-library launcher whose
spawn main module does not eagerly import both scientific domains and composed
API services; selected worker imports can then remain narrow. The selected
Rubisco-module probe used about 151.93 MiB virtual address space, showing that
the unavoidable selected module alone was below 512 MiB in this observation.
This establishes an import-pruning opportunity, not successful science under
that limit. Any source change needs ordinary focused software checks and its own
newly authorized scientific allocation before execution; this audit changes no
package code and spends no additional original attempt.

If the broad startup path is retained, a future operational address-space
declaration must exceed its measured approximately 635 MiB baseline and reserve
separately justified headroom for inputs, IPC and selected computation. This is
a lower-bound observation, not a recommendation to increase the frozen ceiling.
Likewise PyBaMM import alone used about 680.27 MiB VmSize and 743.99 MiB
VmPeak (RSS about 232.49 MiB). These measurements do not establish that the old
proposed 1 GiB battery ceiling covers composed startup, model construction,
continuation or solve. Battery allocation must remain separate and bind actual
supported startup and workload evidence before any native contact.
