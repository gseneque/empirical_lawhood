# SPDX-License-Identifier: MPL-2.0
"""Disclosed original byte-custody controls, without native or source authority."""

from contextlib import contextmanager
from dataclasses import fields, replace
from decimal import Decimal
import errno
from hashlib import sha256
import pickle
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_original_publications as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_statistical_bindings as statistical
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import corpus_artifact, exposure_census_publication
from empirical_lawhood.api.domain_composition.matrix_protected_response.originals import bind_protected_e3_original_inputs
from empirical_lawhood.infrastructure import bounded_io
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.execution import prepare_task_runner
from tests.test_matrix_e3_statistical_bindings import config, prepared, sources
from tests.test_matrix_e3_statistical_bindings import build_statistical_case
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_e3_protected_prefix_science import forbid_native as forbid_native  # noqa: F401


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    return build_original_case(tmp_path_factory)


def build_original_case(tmp_path_factory, *, selected64=False):
    case = build_statistical_case(tmp_path_factory, selected64=selected64)
    # A separate literal FILE operand exercises the shared bounded-file owner.
    # It is not an exposure-census publication or an original-custody carrier.
    artifact = case.manifest.audit.census.factual_provenance[0]
    raw = b"exposed software audit"
    assert (len(raw), sha256(raw).hexdigest()) == (artifact.size_bytes, artifact.sha256)
    relative = "original-files/literal-operand.original"
    path = case.plane.root.resolve(relative, for_write=True)
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(raw)
    case.file_operand = ExperimentFileInputBinding("literal-operand", artifact, "1.0.0", relative, len(raw))
    original = owner.ProtectedE3OriginalPublications("originals.literal.e3", case.inputs.specification.identity,
        identity(case.manifest), case.inputs.training_allocation.identity,
        publish(case.plane, case.manifest, "literal.originals.source-manifest"),
        publish(case.plane, case.inputs.training_allocation, "literal.originals.training-allocation"),
        exposure_census_publication(case.manifest.audit))
    case.originals = original
    return case


def authenticate(case, *, originals=None, publications=None, **changes):
    arguments = dict(specification=case.inputs.specification.identity, allocation=case.allocation.identity,
        source_manifest=identity(case.manifest), training_allocation=case.inputs.training_allocation.identity,
        publications=case.publications if publications is None else publications, fit_cutoff=case.fit_cutoff)
    arguments.update(changes)
    return owner.authenticate_protected_e3_fit_originals(case.plane, case.originals if originals is None else originals,
        **arguments)


@contextmanager
def changed_file(path):
    original = path.read_bytes()
    path.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
    try:
        yield
    finally:
        path.write_bytes(original)


def test_global_carrier_has_only_exact_references_and_three_publications(case):
    value = case.originals
    assert tuple(field.name for field in fields(value)) == ("record_id", "specification", "source_manifest",
        "training_allocation", "manifest_publication", "training_allocation_publication", "exposure_census_publication")
    assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=len(value.canonical_bytes())) == value
    assert pickle.loads(pickle.dumps(owner.ORIGINAL_PUBLICATION_REQUIREMENT.validate)) is owner.authenticate_protected_e3_original_publications
    for invalid in (None, case.file_operand):
        with pytest.raises(TypeError, match="exact publication custody"):
            replace(value, exposure_census_publication=invalid)


def test_actual_originals_and_domain_projection_authenticate_without_train(case):
    originals = tuple(record.canonical_bytes() for record in (case.manifest, case.inputs.training_allocation,
        case.inputs.specification, case.allocation))
    assert authenticate(case) == (case.manifest, case.inputs.training_allocation)
    inputs, manifest = bind_protected_e3_original_inputs(case.plane, case.originals,
        specification=case.inputs.specification, allocation=case.allocation,
        publications=case.publications, fit_cutoff=case.fit_cutoff)
    assert inputs == case.inputs and manifest == case.manifest
    assert originals == tuple(record.canonical_bytes() for record in (case.manifest, case.inputs.training_allocation,
        case.inputs.specification, case.allocation))
    assert case.originals.exposure_census_publication == exposure_census_publication(case.manifest.audit)
    owner.authenticate_publication(case.plane, case.originals.exposure_census_publication, case.manifest.audit.census)


def test_registered_callback_requires_actual_one_global_fit_binding(case):
    callback = owner.ORIGINAL_PUBLICATION_REQUIREMENT.validate
    assert callback(case.plane, ()) is None
    fit = config(case, "fit")
    with pytest.raises(ValueError, match="SOFTWARE:.*global original-publication"):
        callback(case.plane, (SimpleNamespace(record=fit),))
    with pytest.raises(ValueError, match="one global"):
        callback(case.plane, (SimpleNamespace(record=fit), SimpleNamespace(record=fit)))


@pytest.mark.parametrize("target,sidecar", (("manifest", False), ("manifest", True), ("training", True),
    ("scheduled-audit", False), ("prior-corpus", False), ("scalar", False), ("roles", False)))
def test_all_declared_original_publications_reauthenticate_actual_bytes(case, target, sidecar):
    publication = {"manifest": case.originals.manifest_publication,
        "training": case.originals.training_allocation_publication, "scheduled-audit": case.manifest.audit_publication,
        "prior-corpus": case.manifest.audit.prior_corpus[0], "scalar": case.manifest.scalar_definition_publication,
        "roles": case.publications[-1][1]}[target]
    relative = publication.materialization.relative_path + (".manifest.json" if sidecar else "")
    with changed_file(case.plane.root.resolve(relative, for_write=False)):
        with pytest.raises((ValueError, RuntimeError)):
            authenticate(case)


@pytest.mark.parametrize("field", ("artifact_id", "payload_schema", "sha256", "media_type", "size_bytes", "role"))
def test_file_locator_preserves_every_original_artifact_identity_field(case, field):
    locator = case.file_operand
    values = dict(artifact_id="different.original.audit", payload_schema="empirical-lawhood/testing/other-audit",
        sha256="a" * 64, media_type="text/plain", size_bytes=locator.identity.size_bytes - 1,
        role="different-original-role")
    changed = replace(locator, identity=replace(locator.identity, **{field: values[field]}))
    with pytest.raises(ValueError, match="substitutes census audit/inventory identity"):
        owner._authenticate_artifact(case.plane, locator.identity, changed)


def test_publication_branch_uses_actual_sidecar_and_exact_artifact_contract(case):
    publication = case.manifest.audit.prior_corpus[0]
    artifact = corpus_artifact(publication)
    owner._authenticate_artifact(case.plane, artifact, publication)
    with pytest.raises(ValueError, match="substitutes census audit/inventory identity"):
        owner._authenticate_artifact(case.plane, replace(artifact, artifact_id="foreign.original.census"), publication)
    path = case.plane.root.resolve(publication.materialization.relative_path + ".manifest.json", for_write=False)
    with changed_file(path):
        with pytest.raises((ValueError, RuntimeError)):
            owner._authenticate_artifact(case.plane, artifact, publication)


@pytest.mark.parametrize("damage", ("census-body", "census-sidecar", "prior-corpus", "late", "missing"))
def test_custody_refusal_precedes_prepared_fit_payload_reads(case, damage):
    selected = prepared(case, config(case, "fit"), sources(case))
    rows = case.publications
    if damage == "late":
        rows = tuple((key, publication, replace(available, available_at=Decimal(2)) if key == "reservation" else available)
            for key, publication, available in rows)
    elif damage == "missing":
        rows = rows[:-1]
    paths = {"census-body": case.originals.exposure_census_publication.materialization.relative_path,
        "census-sidecar": case.originals.exposure_census_publication.materialization.relative_path + ".manifest.json",
        "prior-corpus": case.manifest.audit.prior_corpus[0].materialization.relative_path}
    class Supplier:
        def prepare_protected_e3_fit(self, context, runner):
            authenticate(case, publications=rows)
            return runner
    wrapper = statistical.prepare_for_invocation(Supplier(), selected.runner)
    def attempt():
        with pytest.raises((ValueError, RuntimeError)):
            runner = prepare_task_runner(wrapper, selected.context)
            runner.execute(selected.context)
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    try:
        if damage in paths:
            with changed_file(case.plane.root.resolve(paths[damage], for_write=False)):
                attempt()
        else:
            attempt()
    finally:
        for port in selected.context.input_ports:
            port.close()


def test_explicit_file_root_refuses_traversal(case):
    locator = case.file_operand
    with pytest.raises(ValueError):
        replace(locator, relative_path="../unselected-original")


def test_explicit_file_root_refuses_actual_symlink(case):
    locator = case.file_operand
    path = case.plane.root.resolve("original-files/audit-link", for_write=True)
    try:
        path.symlink_to(case.plane.root.resolve(locator.relative_path, for_write=False))
    except OSError as error:
        if error.errno not in (errno.EPERM, errno.EOPNOTSUPP, errno.ENOSYS):
            raise
        pytest.skip(f"selected filesystem lacks symlink creation capability: {error.strerror} (errno {error.errno})")
    with pytest.raises((ValueError, RuntimeError)):
        owner._authenticate_artifact(case.plane, locator.identity, replace(locator, relative_path="original-files/audit-link"))


@pytest.mark.parametrize("target,sidecar", (("manifest", True), ("prior-corpus", False)))
def test_missing_actual_sidecar_or_complete_corpus_member_refuses(case, target, sidecar):
    publication = (case.originals.manifest_publication if target == "manifest" else case.manifest.audit.prior_corpus[0])
    path = case.plane.root.resolve(publication.materialization.relative_path + (".manifest.json" if sidecar else ""),
        for_write=False)
    parked = path.with_name(path.name + ".literal-unavailable")
    path.rename(parked)
    try:
        with pytest.raises((ValueError, RuntimeError, FileNotFoundError)):
            authenticate(case)
    finally:
        parked.rename(path)


def test_file_mutation_during_original_hash_refuses_same_descriptor(case, monkeypatch):
    locator = case.file_operand
    path = case.plane.root.resolve(locator.relative_path, for_write=False)
    original, read, events = path.read_bytes(), bounded_io.os.read, []
    def change_during_read(descriptor, count):
        raw = read(descriptor, count)
        if raw and not events:
            events.append("original file changed after read")
            path.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
        return raw
    monkeypatch.setattr(bounded_io.os, "read", change_during_read)
    try:
        with pytest.raises(bounded_io.BoundedFileIOError, match="changed during"):
            owner._authenticate_artifact(case.plane, locator.identity, locator)
        assert events == ["original file changed after read"]
    finally:
        path.write_bytes(original)
