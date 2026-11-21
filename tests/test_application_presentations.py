# SPDX-License-Identifier: MPL-2.0
"""Bounded presentation boundaries; retained scientific acceptance is separate."""

from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import application_context, application_presentations as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, response_bytes, load_application_json
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def request(**parameters):
    return ApplicationRequest("presentation.control", "selected", "presentation.read", tuple({
        "panel_id": "fixture.findings", "panel_version": "1.0.0", "directory": "/selected/original", **parameters}.items()))


@pytest.fixture
def boundary(monkeypatch):
    identity = ObjectIdentity("original", "empirical-lawhood/fixture/original", "1.0.0", "a"*64).to_document()
    rows = tuple({"opportunity_id": str(index), "status": "MISSING" if index == 3 else "OBSERVED",
        "independent_unit": "one.original.root", "value": None if index == 3 else Decimal("0.10000000000000000001")}
        for index in range(4))
    data = owner.PresentationData(identity, "DISCLOSED_SOFTWARE_CONTROL",
        {"assigned_opportunities": 4, "independent_units": 1, "nested_views": 2, "claim_disposition": "UNEVALUABLE"},
        rows, {"original_identity": identity, "opportunities": rows}, {"original": identity}, "No scientific qualification.")
    class Plane:
        reads = 0
        checks = 0
        refused = False
        revoked = False
        @contextmanager
        def read_context(self):
            yield self
        def require_verification_snapshot(self):
            self.checks += 1
            if self.revoked:
                raise PermissionError("original byte changed after projection")
    plane = Plane()
    selected = {"data": data}
    def read(context, directory, artifact_writer):
        assert directory == Path("/selected/original") and artifact_writer is plane
        plane.reads += 1
        if plane.refused:
            raise PermissionError("private access owner refused")
        return selected["data"]
    declaration = owner.ApplicationPresentation("fixture.findings", "1.0.0", "Original findings", "fixture",
        "docs/using/research-workbench.md", ("opportunity_id", "status", "value"), 4, read)
    monkeypatch.setattr(owner, "application_presentations", lambda: (declaration,))
    monkeypatch.setattr(application_context, "application_storage", lambda *a, **k: (None, None, plane))
    return ApplicationContext("selected", "Selected control", Path("/selected/python")), plane, selected, declaration


def test_filter_and_unknown_panel_revision_keep_original_scope_and_exact_denominator(boundary):
    context, plane, selected, _ = boundary
    current = execute_application(context, request(filter="MISSING"))
    assert current.succeeded and current.payload["page"]["total"] == 4
    assert current.payload["page"]["matching_total"] == 1
    assert current.payload["summary"]["independent_units"] == 1
    fallback = execute_application(context, request(panel_version="99.0.0"))
    assert fallback.succeeded and fallback.payload["kind"] == "presentation-generic"
    assert fallback.payload["presentation"]["status"] == "GENERIC_UNSUPPORTED_PANEL_REVISION"
    assert fallback.payload["identity"] == selected["data"].identity
    assert fallback.payload["summary"] == current.payload["summary"]
    assert fallback.payload["presentation"]["original_report"] == selected["data"].original_report
    transported = load_application_json(response_bytes(fallback))["payload"]
    assert transported["presentation"]["original_report"]["opportunities"][0]["value"] == {
        "decimal": "0.10000000000000000001"}
    assert plane.reads == plane.checks == 2


def test_unknown_panel_or_executable_parameters_refuse_before_storage(boundary, monkeypatch):
    context, plane, _, _ = boundary
    monkeypatch.setattr(application_context, "application_storage", lambda *a, **k: pytest.fail("invalid selection opened storage"))
    for parameters in ({"panel_id": "os.system"}, {"panel_version": "execute()"}, {"module": "os"}):
        result = execute_application(context, request(**parameters))
        assert not result.succeeded and result.payload is None
    assert plane.reads == plane.checks == 0


def test_fallback_and_repeated_reads_never_reuse_access_or_skip_final_bytes(boundary):
    context, plane, _, _ = boundary
    assert execute_application(context, request()).succeeded
    plane.refused = True
    refusal = execute_application(context, request(panel_version="99.0.0"))
    assert refusal.reason_codes == ("CURRENT_CUSTODY_REFUSED",) and refusal.payload is None
    assert b"private" not in response_bytes(refusal)
    plane.refused, plane.revoked = False, True
    refusal = execute_application(context, request())
    assert refusal.reason_codes == ("CURRENT_CUSTODY_REFUSED",) and refusal.payload is None
    assert plane.reads == 3 and plane.checks == 2


def test_complete_record_bound_refuses_before_returning_a_truncated_result(boundary):
    context, plane, selected, _ = boundary
    selected["data"] = replace(selected["data"], records=selected["data"].records * 2)
    result = execute_application(context, request())
    assert not result.succeeded and result.payload is None and plane.reads == 1


def test_static_discovery_checks_closed_descriptors_without_reading_prerequisites(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("static discovery inspected storage or a scientific result")
    monkeypatch.setattr(application_context, "application_storage", forbidden)
    rows = owner.application_presentations()
    assert {row.panel_id: row.maximum_records for row in rows} == {
        "mass-balance.findings": 16, "assigned-opportunity.findings": 16, "rubisco.initial-root": 256,
        "rubisco.preparation-response": 32}
    request = ApplicationRequest("static", "selected", "presentation.list")
    result = execute_application(ApplicationContext("selected", "Selected", Path("/selected/python")), request)
    assert result.succeeded and result.payload["summary"]["prerequisites_inspected"] is False
    assert {row["panel_id"] for row in result.payload["page"]["rows"]} == {
        "mass-balance.findings", "assigned-opportunity.findings", "rubisco.initial-root",
        "rubisco.preparation-response"}


def test_descriptor_collisions_bad_columns_and_wrong_reader_signature_are_not_installed(boundary):
    _, _, _, descriptor = boundary
    with pytest.raises(ValueError, match="repeats"):
        owner.validate_presentations((descriptor, descriptor))
    for change in ({"columns": ("status", "status")}, {"columns": ("<script>",)},
                   {"maximum_records": True}, {"guide": "../outside.py"}):
        with pytest.raises((TypeError, ValueError)):
            replace(descriptor, **change)
    with pytest.raises(TypeError):
        replace(descriptor, read=lambda argument: pytest.fail("invalid callback ran"))


def test_draft_bound_and_exact_domain_refuse_before_scientific_read(monkeypatch):
    from empirical_lawhood.api import application_development, recursive_authoring
    from empirical_lawhood.storage import recursive_custody
    packet = SimpleNamespace(members=(SimpleNamespace(filename="draft.json", size_bytes=100),))
    monkeypatch.setattr(recursive_custody, "read_recursive_bootstrap_record", lambda *a, **k: packet)
    plane = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path="/selected")))
    def forbidden(**kwargs):
        pytest.fail("oversized draft entered owning loader")
    monkeypatch.setattr(recursive_authoring, "load_authored_wave", forbidden)
    with pytest.raises(ValueError, match="exceeds"):
        application_development.load_bounded_development(directory=Path("/selected/retained"), plane=plane,
            maximum_draft_bytes=99, accept_draft=lambda draft: True)
    draft = SimpleNamespace(development_study=object(), prospective_draft=None)
    monkeypatch.setattr(recursive_authoring, "load_authored_wave", lambda **k: (packet, draft, None, None))
    with pytest.raises(ValueError, match="declared exposed"):
        application_development.load_bounded_development(directory=Path("/selected/retained"), plane=plane,
            maximum_draft_bytes=100, accept_draft=lambda draft: False)


def test_generator_uses_closed_owned_modules_and_refuses_duplicate_panels(boundary, monkeypatch):
    from scripts import generate_extension_bundle_aggregate as generator
    _, _, _, descriptor = boundary
    paths = (Path("first.py"), Path("second.py"))
    monkeypatch.setattr(generator, "_discover_descriptors", lambda **k: paths)
    monkeypatch.setattr(generator, "_module_name", lambda p: p.stem)
    monkeypatch.setattr(generator.importlib, "import_module", lambda name: SimpleNamespace(APPLICATION_PRESENTATION=descriptor))
    with pytest.raises(ValueError, match="repeats"):
        generator.render_application_presentations()
