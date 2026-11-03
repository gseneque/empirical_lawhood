# SPDX-License-Identifier: MPL-2.0
"""Public preparation and early custody refusal over disclosed E4 metadata.

Run only after coordinator registration/generation, with pytest basetemp on EL.
This authors no scientific result, grants no protected authority and starts no
task/native worker. Original product descriptors remain deliberately unpublished.
"""

from tests.matrix_e4_structure_support import disclosed_structure, publish_secondary
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as public
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment, load_experiment_inputs, prepare_experiment
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentFileInputBinding, ExperimentFileInputSelection
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer, disclosed_operational_resources  # noqa: F401 - disclosed shared fixture
from tests.test_rubisco_gas_contrast import _real_plane

ROOT = Path(__file__).resolve().parents[1]


def test_actual_public_prepare_preserves_science_and_refuses_unpublished_parents_before_authoring(selected_bridge, tmp_path):  # noqa: F811
    f = selected_bridge
    campaign = campaign_fixture()[0].campaign
    spec = public.SelectedE3E4ExperimentSpecification("experiment.selected-e4.public-conformance", f.programme.identity, f.bank.identity,
        f.evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(f.bank, budget=dict(disclosed_operational_resources().phase_budgets)["collect"]))
    selected_root = tmp_path / "actual-selected-e4-development-custody"
    assert selected_root.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    plane = _real_plane(selected_root)
    _, secondary = publish_secondary(plane, f.bank, selected_root / "early-secondary")
    template = selected_root / "literal-templates.npz"
    template.write_bytes(f.template_raw)
    artifacts = dict(owner.contracts(f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()), produced_input_parents=f.evidence.produced_input_parents, secondary_readout=secondary)[4])
    records = {"programme": f.programme, "bank": f.bank, "evidence": f.evidence, "campaign": campaign,
        "resources": disclosed_operational_resources(), "secondary_readout": secondary}
    bindings = []
    for name, value in sorted(records.items()):
        payload = value.canonical_bytes()
        member = selected_root / (name + ".json")
        member.write_bytes(payload)
        reference = ObjectIdentity.from_record(getattr(value, {"programme": "programme_id", "bank": "bank_id",
            "evidence": "record_id", "campaign": "campaign_id", "resources": "record_id", "secondary_readout": "record_id"}[name]), value)
        bindings.append(ExperimentInputBinding(name, reference, member.name, len(payload)))
    selection = ExperimentFileInputSelection("inputs.selected-e4.public-conformance", public.PROTOCOL_ID, tuple(bindings),
        tuple(ExperimentFileInputBinding(name, artifact, "1.0.0", template.name, artifact.size_bytes)
            for name, artifact in sorted(artifacts.items())))
    input_path = selected_root / "sources.json"
    input_path.write_bytes(selection.canonical_bytes())
    before = tuple(sorted(str(path.relative_to(selected_root)) for path in selected_root.rglob('*')))
    with pytest.raises(PermissionError, match='protected copied inputs require their actual selected artifact writer'):
        load_experiment_inputs(spec, input_path)
    assert tuple(sorted(str(path.relative_to(selected_root)) for path in selected_root.rglob('*'))) == before
    with pytest.raises((FileNotFoundError, ArtifactIdentityConflict)):
        load_experiment_inputs(spec, input_path, artifact_writer=plane)
    assert tuple(sorted(str(path.relative_to(selected_root)) for path in selected_root.rglob('*'))) == before
    # Pure metadata binding exercises the complete graph and reservations only.
    # These unpublished parent descriptors establish no original custody or access.
    bound = public.bind_inputs(spec, records, files={
        name: PreparedExperimentFile(artifact, "1.0.0", template, artifact.size_bytes)
        for name, artifact in artifacts.items()})
    assert bound.method_inputs.resources == records["resources"]
    assert bound.method_inputs.operational_budgets
    source = implementation_binding(ROOT)
    execution = ExecutionSelection(workers=1, environment_id="main-locked",
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source), output_root=str(selected_root))
    method_inputs = bound.method_inputs
    preparation = prepare_experiment(spec, scientific_inputs=bound.scientific_inputs, method_inputs=method_inputs, execution=execution)
    assert preparation.executable
    assert len(preparation.draft.operations) == 3458
    assert dict(method_inputs.operational_budgets) == records['resources'].task_budgets(
        f.programme, f.bank, evidence=f.evidence)
    public.validate_instance(specification=spec, allocation=preparation.allocation,
        draft=preparation.draft, source_records=preparation.design_records)
    wave = selected_root / "authored-wave"
    with pytest.raises((FileNotFoundError, ArtifactIdentityConflict)):
        author_prepared_experiment(preparation=preparation, project_root=ROOT, artifact_writer=plane, output_dir=wave)
    assert not wave.exists()
    assert tuple(sorted(str(path.relative_to(selected_root)) for path in selected_root.rglob('*'))) == before
