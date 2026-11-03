# E2 inputs from the whole programme

SPDX-License-Identifier: CC-BY-4.0

The `matrix.programme.e2-input-assembly` operation authenticates the original
whole-programme commitment C and derives the existing
`matrix.factor-response.native-utility` inputs. It performs no native work,
fitting, stream allocation, issue or reveal. The ordinary
[native E2 lifecycle](../matrix-native-utility/guide.md) owns subsequent
preparation, authoring, execution and assessment.

Supply one `request` binding in an `ExperimentInputSelection` or
`ExperimentFileInputSelection`. The current consumers are:

| Consumer | Record |
| --- | --- |
| `matrix-programme-e2-assembly-request` | Version 2 request with explicit `NativeTrainingResources` and current campaign; no C handle |
| `matrix-programme-e2-assembly` | Version 2 specification selecting the actual C publication and binding that exact assembly request |

For standalone assembly, select C once in the assembly specification. The
whole-programme runner supplies this specification from its original C selection;
no C handle is copied into the E2 operational request.

The resources select all named native phase budgets and worker capacity. E2
uses the corresponding existing utility phases; it does not acquire a TRAIN
feature or fitted model. The selected entry budget must give finite positive
source, memory and output byte limits. The campaign must contain the aggregate
budget of every assigned E2 task. Assembly preserves its policy, decision rights
and resource ceiling; it derives the E2 question, system, world and claim pins.
These selections provide no execution authority.

Select the locked main environment, an operator profile with at least four
distinct physical cores, and explicit paths on the storage declared by that profile. Prepare the copied JSON through
[configuration](../../../../../docs/using/configuration.md), then use ordinary derivation:

Set `$PROJECT_ROOT` to your selected checkout or matching installed source distribution.
Use the same explicit operator profile, source and storage selections throughout the commands below.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$E2_ASSEMBLY" --sources "$E2_ASSEMBLY_SOURCES" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$E2_ASSEMBLY" --sources "$E2_ASSEMBLY_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$E2_METADATA" --output-selection "$E2_METADATA/inputs/sources.json"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$E2_METADATA/inputs/native-utility-specification.json" \
  --sources "$E2_METADATA/inputs/sources.json" --workers 4
```

Assembly authenticates all twelve C roles and the current selected producing
provenance. It derives E2's complete assigned population from its original
reservation, native specification, protocols and common/independent panels. The
exact mathematical protocol, criterion, coordinates, scalar, numerical design,
causal prefix policies and assay remain the choices in D and C. Scientific
counts are retained from the selected D; an exposed software control with fewer
units does not establish the selected 96-unit scientific result.

The output includes the ordinary native E2 specification, request and source
selector, plus an exact byte copy of the original template FILE. Its exposure
support is the original census publication alone. It does not require a TRAIN
request, old task roster, earlier issued package or operator-authored source
copies. Requirements retain the actual C and D identities and report that no
native contact or scientific qualification was established. Keep all missing
source, sampling, resource and genuine authority prerequisites visible before
acquisition; metadata derivation does not satisfy them.
