# Compile the whole programme inputs

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for the public programme input compiler.
It supports prospective whole-programme commitments without native acquisition.
Select the current scientific design D, exposure census and copied original support files.

First run the [prospective E1 allocation operation](e1-inputs.md). It binds E1's
selected mathematics to its actual allocation before D is frozen. Retain that
criterion in D and use the same census, namespace, coordinates and root stream
material in the whole-programme request. C's compiler independently checks the
actual allocation pin. This ordering removes any need for a private compiler
call or an invented allocation fingerprint when authoring D.

The `matrix.programme.input-assembly` operation publishes whole-programme
commitment C, version 2. Its publication records the selected inputs and the
original E4 history, future and family-draw stream recipe. Independent readers
recheck each assigned family's draw and both stream roles from that recipe;
an IID bank may legitimately contain no group from a particular family.
Freshness requires a complete exclusion census and disjoint assignments.
Model fitting, issue, reveal and source qualification retain their separate requirements.

Prepare the copied JSON through [configuration](../../../../../docs/using/configuration.md).
The current consumers are:

| Consumer | Record |
| --- | --- |
| `matrix-programme-scientific-design` | Complete current D version 3, including all twelve phase counts, exact dense mathematical choices, fixed E4 SR/BR relation and the E1 criterion bound to its actual allocation |
| `matrix-factor-exposure-census` | Current exposure census |
| `matrix-programme-allocation-request` | Exact D and census identities, namespace, distinct explicit stream materials, support FILE bindings and finite metadata resources |
| `matrix-programme-input-assembly` | Specification binding the exact allocation request |

Supply the canonical request, D and census as `request`, `scientific-design`
and `exposure-census` in an `ExperimentFileInputSelection`. Include exactly
the request's FILE bindings: the TRAIN and E2 template NPZ artifacts and the
original normalization Python source. A shared NPZ requires one FILE binding.
Both assay declarations are checked against its bytes. Keep the canonical
request and the original FILEs at their exact request-relative copied paths.
No old issued package or previously published support artifact is required.
Select E4's complete `e4_structure.secondary_target` before publishing C; the
[full-factor guide](../matrix-response-experiment/full-factor-followup.md) gives
its exact accuracy/grid fields. The ordinary DEV deriver later publishes this
same declared target before authoring. The four-field operational programme
specification remains version 4. Current D binds the amended FACTOR58 mathematics;
an earlier ALL15 design cannot substitute for it.

The [complete exposed D example](scientific-design.example.json) uses the current
owners for all mathematical identities and constructs its actual exposed E1
allocation. Replace its E1 criterion with the result of your public E1 operation,
and retain the exact new D and C bytes. Its public streams and zero-valued
template FILE are software examples, not fresh allocations or a usable assay.
Select the actual precommitted template bytes and member digests for both E2
and TRAIN. The public native checks still decide instrument availability.

The amended allocation selects seven distinct random materials: ordinary
history and future; E4 history, future and family allocation; and E5 history
and future. Set `e4_streams.family_seed_material_sha256` explicitly. Each CAL
and CONF group uses its original uniform four-family draw with no balance
redraw. DEV retains four groups per family. The compiler checks complete
cross-phase group and effective-stream exclusion, including the held-out E6
temperatures 1.125 and 3.25. A disjoint stream does not itself prove the
independence or exchangeability assumptions used for inference.

Select the locked main environment, a current source snapshot, environment,
operator profile and explicit guarded EL output. The request's metadata budget
must admit source bytes, complete output bytes and the current process memory.
These limits do not admit the later scientific execution graph.

Compile C with the installation and locked environment that will execute the
programme. For a wheel installation, finish installing it first, use its CLI,
and select the matching extracted source distribution with `--project-root`.
C retains the actual loaded numerical-library paths as well as source and lock
identities. A change of installation location requires a new C before phase
input derivation; retain earlier C publications unchanged.

Set `$PROJECT_ROOT` to your selected checkout or matching installed source distribution.
Use the same explicit operator profile, source and storage selections throughout the commands below.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$INPUT_ASSEMBLY" --sources "$INPUT_ASSEMBLY_SOURCES" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$INPUT_ASSEMBLY" --sources "$INPUT_ASSEMBLY_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$PROGRAMME_METADATA" \
  --output-selection "$PROGRAMME_METADATA/inputs/sources.json"
```

The compiler validates the complete source plan, exposure exclusions, E1
allocation/criterion and original mathematical projections before its first
publication. It publishes exact support bytes and the twelve role records,
reservations, future selectors, E6 policy and C. All copied records and FILEs,
current producing source and the published C closure remain guarded through
the final selector and requirements publication. Exact retries reuse the same
complete publication batches and original availability records.

The resulting `inputs/input-commitments.json` holds the actual C publication
selection. Use it with the [E1](e1-inputs.md), [E2](e2-inputs.md) and
[native TRAIN](../matrix-response-experiment/input-assembly.md) input operations.
They retain their own scientific preparation, authority and execution
requirements. The compiler does not select an active phase or advance a
programme from results.
