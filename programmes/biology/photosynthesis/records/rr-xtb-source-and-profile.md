# Official xTB source intake and isolated metadata profile

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026** on `recchain`.
State: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

Official xTB **6.7.1** is available in an independently selected local CLI
profile for a prospective, separately frozen GFN2 geometry-repair operation.
The actual work completed here is bounded source acquisition, full archive
inspection, private provisioning and **two metadata processes**. It supplies
no optimized structure, SCC result, response law, kinetic prediction or
scientific qualification. The [initial coupled geometry
result](rr-coupled-initial-geometry-result-v1.md) remains the chemical starting
state; [embedding design](rr-coupled-embedding-design.md) and [relaxation
feasibility](rr-coupled-relaxation-feasibility.md) remain distinct model choices.

## Exact official source custody

The closed ordinary raw-source packet is
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-rr-xtb-v1`:
**1,192 files / 60,845,375 bytes**, files `0444`, directories `0555`.
Its `official-xtb-source-register-v1.json` binds **1,191 payload members** and
counts its own bytes without a self-hash cycle. Register SHA-256:
`ebef595804e4e05bae39b7033e39c20a1d2d2bf4ced698673532f21b9cc5fccc`.
Root independently verified its complete file census, hashes and modes.

URLs came from the [official release
API](https://api.github.com/repos/grimme-lab/xtb/releases/tags/v6.7.1) and
[official release assets](https://github.com/grimme-lab/xtb/releases/expanded_assets/v6.7.1).
Both publisher checksum files agree with their exact downloaded archive
bodies and filenames. The exact official tag was authenticated through its
[tag-ref API](https://api.github.com/repos/grimme-lab/xtb/git/ref/tags/v6.7.1)
and the release's native `tarball_url`, rather than an inferred filename.

| Original body | Bytes | SHA-256 |
|---|---:|---|
| `xtb-6.7.1-linux-x86_64.tar.xz` | 27,128,568 | `62a8d18778286e815292ee53d76ce447daf460a4dea3782c0f25cbac7019b5df` |
| `xtb-6.7.1-source.tar.xz` | 6,657,708 | `79a2a2f50091b3b941e5139c1b38a53203d5d2e9ba496a7ad505d8c31ccd6013` |
| `official-tag-source-v6.7.1.tar.gz` | 1,681,436 | `b3b59c5fc7dc0b120180089740e50a146b9b72e400707a7a52988ecd49a168dd` |

The finite acquisition census is **eight unique HTTP attempts**: one retained
sandbox DNS refusal with no body and seven HTTP 200 responses. These include
the release metadata, two archives, two checksum files, tag-ref metadata and
tag source. Original failure/log/helper bytes remain unchanged; no automatic
retry or source replacement occurred. The successor acquisition log also
retains the initial refusal, so its duplicate row is not a ninth request.

Full decompression verified integrity, every regular-member hash, paths and
types. The native archive has **319 members / 301 regular files**; named
source **644 / 575**; exact tag source **601 / 549**. All three contain zero
links, special files or unsafe paths. The first two archives have
**178,092,568 regular-member bytes** and **178,810,880 decompressed TAR-stream
bytes**, the latter including headers and padding. With the tag source these
become **187,233,183** and **188,395,520**, respectively. These are separate
censuses, both within the **256 MiB expanded-source** ceiling.

The selected bounds were **32 MiB/download**, **64 MiB retained intake** and
**256 MiB expanded archive stream**. A first complete-source copy refused an
authentic **5,473,230-byte Git pack** at its 4 MiB copy ceiling. That helper
and documentary refusal transcription remain retained. The successor's
explicit **8 MiB source-copy ceiling** copied all 575 exact source files;
it did not overwrite the original refusal. The transcription is not claimed
to be an original stderr stream. No generic scientific operand limit changed.

## Version discrepancy and source correspondence

The publisher archive named `xtb-6.7.1-source.tar.xz` contains Git HEAD
`edcfbbe39d411edc225e27315fbda3a204ddb023` and CMake/meson version **6.7.0**.
Its packed refs do not include the requested tag. This original is preserved
as received. The official tag identifies commit
`26b28010e805f7d1aeeef39813feb473e69cc4be` and build version **6.7.1**.

Full path/hash comparison found **545 unchanged common files** and exactly
**four changed common files**: `CMakeLists.txt`, `README.md`, `meson.build`
and `src/esp.f`. The extra 26 named-source files are its embedded Git metadata.
The optimizer, embedding, CLI parser, parameter loader, SCC implementation
and relevant coordinate/gradient writers are byte-identical between the
retained source versions. Root independently reproduced this finite census.

The actual executable subsequently reported:

```text
xtb version 6.7.1 (edcfbbe) compiled by 'albert@albert-system' on 2024-07-22
```

Thus its declared commit agrees with the named publisher source, while its
declared version agrees with the release. The source match of the selected
operations is explicit; a reproducible binary build or complete dependency
source correspondence has not been demonstrated.

Complete inspectable sources remain in the closed packet at
`official-source-tree/xtb_6.7.1_source` and
`official-tag-source-tree/grimme-lab-xtb-26b2801`.
`official-xtb-source-facts-v1.json` binds selected source paths/hashes and
semantics, SHA-256
`b46bcdf7c09a6f6c1a613bc1801270f26eb8083264778bbccd4a280d9c4881f3`.

## Isolated provisioned profile

The selected profile is `/tmp/rubisco-xtb-6.7.1-native-env`, with **1,135 files
/ 87,746,706 bytes**. Its only selected executable is
`native/bin/xtb`, mode `0555`; other files are `0444`, directories `0555`.
It retains both complete source trees, native parameter data and native
license notices. The unused `cpx` executable, static libraries and compiled
module files were not provisioned. No package installation, dependency
synchronization or main-environment change occurred.

| Exact native member | Bytes | SHA-256 |
|---|---:|---|
| `xtb-dist/bin/xtb` | 63,253,248 | `debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a` |
| `xtb-dist/share/xtb/param_gfn2-xtb.txt` | 35,849 | `f6f05c6c5264cb2f75c54f8ac6838044541c1e493b16f1a4d4ee4fa64de5f545` |

Static ELF inspection found x86-64 `ET_EXEC`, **no `PT_INTERP`, `DT_NEEDED`,
RPATH or RUNPATH**. The original archive supplies static `.a` libraries and
no shared libraries. The two successful metadata processes demonstrate
metadata startup on this host; they do not establish scientific runtime
performance or solver behavior. Native provisioning has its own **70 MiB
member / 256 MiB aggregate** bounds. The 63 MB executable is an external
selected profile dependency, not a scientific ArtifactPlane operand under
the existing 16 MiB member contract.

The GFN2 parameter body is identical in the native archive and both source
trees. The exact parser accepts **`--vparam ABSOLUTE_FILE`** and passes the
filename into the calculator. Its built-in fallback recognizes only bare
known parameter filenames; a missing absolute selected path refuses. A later
scientific operation must bind and verify the exact parameter before and
after contact. The metadata checks do not exercise that scientific path.

Source notices state **LGPL-3.0-or-later**; `COPYING`, `COPYING.LESSER`, bundled
dependency notices and native jsonfortran `LICENSE` are preserved. This is
private provisioning. No blanket license is asserted for all statically
embedded Intel/MKL or other third-party components, and complete third-party
redistribution/source compliance has not been established. The note's own
CC-BY license does not replace the software or dependency licenses.

## Actual metadata processes and counters

Exactly **two native processes**, `--version` then `--help`, exited **0**.
Both raw stderrs retain `normal termination of xtb`; both selected working
directories remain empty. There were **zero metadata refusals/retries,
molecule inputs, SCC, gradient or optimization calls**. These counters cover
this selected xTB intake/profile work, not the earlier Rubisco native
experiments. Source-packet historical closure still correctly records zero
native processes before the later profile was provisioned.

Each subprocess had **one numerical/OpenMP thread**, **4 GiB address space**,
**10 CPU seconds / 30 wall seconds**, **8 MiB per output stream**, no core
dumps and a separate empty working directory. Its complete retained
environment fixes `XTBHOME`, `XTBPATH`, temporary storage and thread variables;
no external control, geometry or parameter calculation was submitted.

| Process | Waited child CPU seconds | Wall seconds | Raw stdout bytes / SHA-256 |
|---|---:|---:|---|
| `--version` | 0.001962 | 0.002820584 | 660 / `f47686023e4be88b6e2241c9a2660fffe132a193f8873d3890594b8f9ca0dd91` |
| `--help` | 0.002207 | 0.004271078 | 7,314 / `d50ddb81514f949bca0923dc8ead4dfab74bce22c323c1c4057fbd37e2874e39` |

The observed help explicitly lists `--gfn`, `--vparam`, `--grad`, `--input`,
`--parallel` and `--verbose`, and documents Turbomole coordinate files in
**Bohr**. It omits `--cycles` and `--iterations`/`--maxiterations`, whose
implementation is present in the exact retained parser. These flags are
source-supported, rather than help-observed or scientifically executed.

Prospective source findings are retained as findings, not executed controls:
point-charge rows accept an exact count including zero charges, default to
Bohr and interpret a fifth numeric `99` as chemical hardness. GFN2 combines
MM and shell hardness by the **arithmetic mean**; the harmonic expression
belongs to GFN1. This softened operator differs from bare PySCF point charges.
ANC optimization and fixed-gradient masking require their separately frozen
counter and unmasked-gradient rules; metadata success does not validate them.

The closed evidence is
`/tmp/rubisco-xtb-6.7.1-profile-evidence-v1`: **12 files / 621,763 bytes**, all
`0444`, directories `0555`. It retains helpers, exact raw streams, process
records, metadata summary and the complete provisioned profile hash census.

| Closure member | SHA-256 |
|---|---|
| `closed-profile-evidence-register-v1.json` | `0db52c7f1a1343b27f5df0c816d10a0f8de48865cd55c36b8a147094fac16e6c` |
| `provisioned-profile-census.json` | `46314923077279dd2f52ae8c56f270380988104183da173d8787715bb040afba` |

Timed provisioning/full-source verification used **2.074648746 CPU /
2.077580856 wall seconds**. Final full profile hash/mode/cap replay used
**0.248484134 CPU / 0.248552130 wall seconds**. The source packet separately
retains acquisition, full TAR inspection and source-copy windows, including
refusals. Caller startup, earlier interactive review, closure writes/mode
changes and final tails are excluded or separately recorded; their cost is
unknown where unmeasured, not zero. The child RSS field is the cumulative
`RUSAGE_CHILDREN` maximum, including pre-exec process overhead, rather than an
independent per-solver memory measurement.

Neither closed packet claims ArtifactPlane publication, registered task
receipts or scientific execution authority. The next chemical action still
requires the selected matched geometry-repair protocol, complete field and
fixed/free atom rules, native resource guards, independent controls and
retained refusals before any SCC/gradient/optimization contact.
