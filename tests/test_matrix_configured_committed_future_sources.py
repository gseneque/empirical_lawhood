# SPDX-License-Identifier: MPL-2.0
"""Exact committed future source identities; metadata controls without contact.

The maintained exposed TRAIN fixture supplies typed C/publications and all four
future response roles. No native TRAIN is claimed by these controls. The pure
variants below are local adverse metadata, never replacement C publications or
current worker/provenance authority. Original canonical fixture bytes stay intact.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as native
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_future_response_selections
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.domain_composition.matrix_configured_protected_assembly import assembly as owner
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case

ROLES = ("CALIBRATION", "EVALUATION", "TRANSFER_NEARBY", "TRANSFER_SHIFTED")


@pytest.fixture(scope="module")
def committed_future(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        def forbidden(*args, **kwargs):
            pytest.fail("committed future descriptor test entered native acquisition")
        patch.setattr(native, "execute_parameter_native_work", forbidden)
        patch.setattr(native, "execute_paired_response_native_work", forbidden)
        case = fresh_training_metadata_case(tmp_path_factory.mktemp("committed-future-source"))
        phases = dict(authenticate_future_response_selections(case.plane, case.request))
        original = (case.request.canonical_bytes(), tuple((role, phases[role].canonical_bytes()) for role in ROLES))
        yield SimpleNamespace(case=case, manifest=case.request.future_manifest, phases=phases)
        assert original == (case.request.canonical_bytes(), tuple((role, phases[role].canonical_bytes()) for role in ROLES))


def _publics(phases):
    return {protocol.public_source.root.root_id: protocol.public_source
        for phase in phases.values() for protocol in phase.protocols}


def _replace_first_protocol(phases, change):
    selected = dict(phases)
    phase = selected["CALIBRATION"]
    selected["CALIBRATION"] = replace(phase, protocols=(change(phase.protocols[0]), *phase.protocols[1:]))
    return selected


def test_all_four_committed_roles_retain_nondefault_source_ids_and_full_pin_census(committed_future):
    control = committed_future
    index = ScheduledSourceIndex.from_shared(reservation=control.manifest.reservation,
        specification=control.manifest.native_specification, provenances=control.manifest.provenances)
    expected = _publics(control.phases)
    assert tuple((role, len(control.phases[role].protocols)) for role in ROLES) == (
        ("CALIBRATION", 20), ("EVALUATION", 8), ("TRANSFER_NEARBY", 2), ("TRANSFER_SHIFTED", 2))
    assert all(public.source.object_id != "source." + root for root, public in expected.items())
    sources = owner._committed_future_sources(control.manifest, control.phases)
    assert tuple(source.root_id for source in sources) == index.root_ids
    assert tuple(source.identity for source in sources) == tuple(expected[root].source for root in index.root_ids)
    for source in sources:
        expected[source.root_id].validate_source(index.resolve(source))


def test_declared_provenance_is_selected_by_exact_complete_source_pin(committed_future):
    original = committed_future.manifest.provenances[0]
    other = replace(original, observed_git_head="e" * 40 if original.observed_git_head != "e" * 40 else "d" * 40)
    provenances = tuple(sorted((original, other), key=lambda value: value.fingerprint()))
    assert len({value.identity for value in provenances}) == 2
    manifest = replace(committed_future.manifest, provenances=provenances)
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    chosen = provenances[-1]
    phases = {}
    # Local typed prospective controls deliberately select the last declared
    # provenance. They are not a change to actual C or an SDK compatibility act.
    for role, phase in committed_future.phases.items():
        protocols = []
        for protocol in phase.protocols:
            public = protocol.public_source
            reference = index.reference(source_id=public.source.object_id,
                root_id=public.root.root_id, provenance=chosen.identity)
            selected = ScheduledPublicSource.from_source(index.resolve(reference))
            protocols.append(replace(protocol, public_source=selected,
                templates=replace(protocol.templates, source=selected.source, producers=(selected.source,))))
        phases[role] = replace(phase, protocols=tuple(protocols))
    sources = owner._committed_future_sources(manifest, phases)
    assert sources and all(source.provenance == chosen.identity for source in sources)
    assert all(source.identity == _publics(phases)[source.root_id].source for source in sources)


@pytest.mark.parametrize("damage", ("missing-role", "missing-root", "duplicate-root", "foreign-root",
    "source-fingerprint", "public-policy"))
def test_committed_future_descriptor_substitution_refuses_without_native_work(committed_future, damage):
    control = committed_future
    phases = dict(control.phases)
    if damage == "missing-role":
        del phases["TRANSFER_SHIFTED"]
        message = "complete original phase census"
    elif damage == "missing-root":
        phase = phases["TRANSFER_SHIFTED"]
        removed = phase.protocols[-1].public_source.root.independent_group_id
        phases["TRANSFER_SHIFTED"] = replace(phase, protocols=phase.protocols[:-1],
            panels=tuple(row for row in phase.panels if row[0] != removed))
        message = "complete unique root census"
    elif damage == "duplicate-root":
        # Both whole typed roles remain individually valid; the same two
        # nearby roots cannot replace the separately reserved shifted roots.
        phases["TRANSFER_SHIFTED"] = phases["TRANSFER_NEARBY"]
        message = "complete unique root census"
    elif damage == "foreign-root":
        phases["TRANSFER_SHIFTED"] = control.case.programme_inputs.phase("train").responses
        message = "complete unique root census"
    elif damage == "source-fingerprint":
        def changed(protocol):
            pin = replace(protocol.public_source.source, object_fingerprint="f" * 64)
            return replace(protocol, public_source=replace(protocol.public_source, source=pin),
                templates=replace(protocol.templates, source=pin, producers=(pin,)))
        phases = _replace_first_protocol(phases, changed)
        message = "exact committed source pin"
    else:
        def changed(protocol):
            policy = replace(protocol.public_source.policy, policy_id="policy.foreign.current-source")
            return replace(protocol, public_source=replace(protocol.public_source, policy=policy))
        phases = _replace_first_protocol(phases, changed)
        message = "public descriptor differs"
    with pytest.raises(ValueError, match=message):
        owner._committed_future_sources(control.manifest, phases)


def test_public_assembly_uses_committed_future_source_owner_before_train_export(tmp_path, monkeypatch,
        committed_future):
    """Actual copied C/TRAIN metadata route stops before the unexecuted exporter.

    This source-aware control uses the existing public assembly fixture and
    real commitment/response/scientific guards. It fabricates no native outputs.
    """
    from empirical_lawhood.api import native_training_banks
    from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs
    from tests.test_matrix_configured_protected_assembly import _case
    seen = []
    actual = owner._committed_future_sources
    def committed_sources(manifest, phases):
        sources = actual(manifest, phases)
        index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
            specification=manifest.native_specification, provenances=manifest.provenances)
        assert set(phases) == set(ROLES)
        assert tuple(source.root_id for source in sources) == index.root_ids
        assert {source.identity for source in sources} == {public.source for public in _publics(phases).values()}
        seen.append(sources)
        raise ValueError("DISCLOSED_COMMITTED_SOURCE_OWNER_REACHED_BEFORE_EXPORT")
    monkeypatch.setattr(owner, "_committed_future_sources", committed_sources)
    monkeypatch.setattr(native_training_banks, "export_native_training_banks",
        lambda **_: pytest.fail("source identity wiring entered unexecuted TRAIN exporter"))
    _, _, _, _, _, kwargs = _case(tmp_path)
    with pytest.raises(ValueError, match="COMMITTED_SOURCE_OWNER_REACHED_BEFORE_EXPORT"):
        derive_experiment_inputs(**kwargs)
    assert seen and not kwargs["metadata_directory"].exists()
