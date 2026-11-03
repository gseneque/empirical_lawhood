# SPDX-License-Identifier: MPL-2.0
"""Exposed conformance only: no native import, model, solve or test qualification."""

from dataclasses import fields, replace
from decimal import Decimal as D
import subprocess
import json
import sys
from types import SimpleNamespace as N
import pytest
from empirical_lawhood.adapters.methods.battery_thermal_inquiry import (
    native as original_native,
    science as original_science,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySource,
    BatteryInquirySupply,
    BatteryInquiryTrace,
    BatteryInquiryChargingAttempt,
)
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import (
    science,
    native,
    operation_bindings as owner,
)
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import (
    DiagnosticSource,
    DiagnosticChargingAttempt,
    DiagnosticTrace,
    DiagnosticResult,
)
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.recursive_translation import (
    draft_from_config,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_thermal_inquiry import _exposed_trace
from tests.test_inquiry_successor_compilation import compile_complete_draft


def config_rows():
    source = DiagnosticSource()
    prior = ObjectIdentity(
        "product.battery-thermal-inquiry.supply",
        BatteryInquirySupply.SCHEMA,
        "1.1.0",
        source.prior_supply_sha256,
    )
    return science.configurations(source, prior)


def exposed(config):
    old_config = original_science.native_config(
        BatteryInquirySource(),
        "supply",
        config.initial_temperature_k,
        config.recipe,
        "oregan-dfn",
    )
    old = _exposed_trace(
        old_config,
        magnitude=D("3.395")
        if config.initial_temperature_k > D("298.15")
        else D("1.455"),
    )
    attempts = tuple(
        DiagnosticChargingAttempt(
            configuration=config,
            **{
                f.name: (
                    config.localization_epsilon_k
                    if f.name == "localization_epsilon_k"
                    else json.dumps(
                        dict(
                            type="IDAKLUSolver",
                            rtol=float(config.rtol),
                            atol=float(config.atol),
                        )
                    )
                    if f.name == "solver_configuration_json"
                    else getattr(row, f.name)
                )
                for f in fields(row)
            },
        )
        for row in old.charging_attempts
    )
    return DiagnosticTrace(
        **{
            f.name: (
                config
                if f.name == "config"
                else attempts
                if f.name == "charging_attempts"
                else "trace." + config.config_id
                if f.name == "trace_id"
                else getattr(old, f.name)
            )
            for f in fields(old)
        }
    )


def test_original_defaults_and_factories_remain_exact(monkeypatch):
    calls = []
    monkeypatch.setattr(
        original_native, "acquire_with_numerics", lambda *a, **k: calls.append((a, k))
    )
    for model, nx, nr, rtol, atol in [
        ("oregan-dfn", 30, 40, D("1e-7"), D("1e-8")),
        ("oregan-dfn-refined", 60, 80, D("1e-9"), D("1e-10")),
    ]:
        config = original_science.native_config(
            BatteryInquirySource(), "supply", D("278.15"), "chamber-40c", model
        )
        original_native.acquire(config)
        assert calls[-1] == (
            (config,),
            dict(
                electrode_points=nx,
                particle_points=nr,
                rtol=rtol,
                atol=atol,
                trace_factory=BatteryInquiryTrace,
                charging_attempt_factory=BatteryInquiryChargingAttempt,
            ),
        )


def test_complete_numerics_and_native_boundary_are_distinct(monkeypatch):
    rows = config_rows()
    assert len(rows) == 12
    calls = []
    monkeypatch.setattr(
        native, "acquire_with_numerics", lambda *a, **k: calls.append((a, k))
    )
    for config in rows:
        native.acquire(config)
        actual = calls[-1][1]
        factory = actual.pop("charging_attempt_factory")
        assert factory.func is DiagnosticChargingAttempt and factory.keywords == {
            "configuration": config
        }
        assert actual == dict(
            additional_source_members=config.source.additional_source_members,
            electrode_points=config.electrode_points,
            particle_points=config.particle_points,
            rtol=config.rtol,
            atol=config.atol,
            trace_factory=DiagnosticTrace,
        )
    with pytest.raises(ValueError):
        replace(rows[0], localization_epsilon_k=D(".001"))
    with pytest.raises(ValueError):
        replace(
            rows[0],
            prior_supply=replace(rows[0].prior_supply, object_fingerprint="0" * 64),
        )


def test_registered_compiler_keeps_actual_outcome_distinct_and_twelve_slots():
    row = config_rows()[0]
    config = owner.DiagnosticOperationConfig(
        "config." + owner.NAMESPACE,
        row.source,
        tuple(
            sorted(
                (science.identity(row.source), row.prior_supply),
                key=lambda x: x.object_id,
            )
        ),
    )
    draft = draft_from_config(config, parent=unsigned_parent(config_rows()[0]))
    compile_complete_draft(draft, owner)
    assert {x.scientific_role for x in draft.external_inputs} == {"SOURCE", "MODEL"}
    assert len(owner.native_effect_slot_ids(config)) == 12
    links = tuple(
        replace(x, scientific_role="SOURCE") if x.consumer_input_id == "prior" else x
        for x in draft.links
    )
    with pytest.raises(ValueError):
        compile_complete_draft(replace(draft, links=links), owner)


def test_receiver_sensitivity_is_strict_and_no_hidden_denominator():
    rows = tuple(exposed(c) for c in config_rows())
    assert all(science.check_trace(t).disposition is A.SATISFIED for t in rows)
    assert all(x.disposition is A.SATISFIED for x in science.comparisons(rows))
    b = rows[1]
    changed = replace(
        b,
        times_s=(b.times_s[0], b.times_s[-1] / 2, b.times_s[-1]),
        voltage_v=(b.voltage_v[0], D("4.1989"), b.voltage_v[-1]),
        current_a=(b.current_a[0],) * 3,
        capacity_ah=(D(0), D("-1.25"), D("-2.5")),
        mean_temperature_k=(b.mean_temperature_k[0],) * 3,
        ambient_temperature_k=(b.ambient_temperature_k[0],) * 3,
        control_modes=("CC",) * 3,
        temperature_regimes=(b.temperature_regimes[0],) * 3,
    )
    check = science.compare_reference(rows[0], changed)
    assert check.disposition is A.UNEVALUABLE
    assert "reference-voltage-precision-unresolved" in check.reason_codes
    prior = rows[0].config.prior_supply
    result = DiagnosticResult(
        "product.battery-dfn-precision-diagnostic",
        rows[0].config.source,
        prior,
        rows,
        tuple(science.check_trace(t) for t in rows),
        science.comparisons(rows),
        A.SATISFIED,
    )
    assert (
        decode_canonical_bytes(
            result.canonical_bytes(), DiagnosticResult, maximum_bytes=None
        )
        == result
    )
    with pytest.raises(ValueError):
        replace(result, traces=rows[:-1])
    with pytest.raises(ValueError):
        replace(result, qualification=True)
    corrupt = replace(rows[0], capacity_ah=(D(0), -D("2.4")))
    assert science.check_trace(corrupt).disposition is A.UNEVALUABLE


def test_cold_discovery_has_no_native_import():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.executable_binding import EXECUTABLE_BINDING_FACTORIES; assert len(EXECUTABLE_BINDING_FACTORIES)==1; assert 'pybamm' not in sys.modules",
        ],
        check=True,
    )


def test_actual_product_hooks_require_receipt_and_export_only_analysis():
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import (
        recursive_translation as drafts,
    )
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole

    rows = tuple(exposed(c) for c in config_rows())
    result = DiagnosticResult(
        "product.battery-dfn-precision-diagnostic",
        rows[0].config.source,
        rows[0].config.prior_supply,
        rows,
        tuple(science.check_trace(t) for t in rows),
        science.comparisons(rows),
        A.SATISFIED,
    )
    config = owner.DiagnosticOperationConfig(
        "config." + owner.NAMESPACE,
        result.source,
        tuple(
            sorted(
                (science.identity(result.source), result.prior_supply),
                key=lambda x: x.object_id,
            )
        ),
    )
    draft = draft_from_config(config, parent=unsigned_parent(config_rows()[0]))
    node = draft.operations[0].node_id
    # Explicit unsigned metadata seam fixture; never a production signer or receipt.
    logical = N(
        logical_artifact_id="artifact.exposed-diagnostic",
        payload_schema=result.SCHEMA,
        content_sha256=result.fingerprint(),
        media_type="application/json",
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
    )
    receipt = N(
        receipt_id="receipt.exposed-diagnostic",
        SCHEMA="empirical-lawhood/testing/unsigned-metadata",
        VERSION="1.0.0",
        fingerprint=lambda: "a" * 64,
        operational_status=OperationalStatus.SUCCEEDED,
        output_logical_artifacts=(logical,),
    )
    products = dict(
        records={node: {node + ".product": result}},
        receipts={node: receipt},
        outputs={
            logical.logical_artifact_id: N(
                logical=logical,
                materialization=N(size_bytes=len(result.canonical_bytes())),
            )
        },
    )
    manifest = drafts.describe_contributions(draft, products)[0]
    assert manifest.products[0].role is ContributionRole.RETAINED_ANALYSIS_INPUT
    assert len(manifest.assessments) == 21
    specification = N(
        endpoint=drafts.scope(result.source.original),
        distinguishing_assessment=draft.operations[0].config_identity,
    )
    assert (
        drafts.inquiry_outcome_projector(draft, specification, products)
        == "useful-supply"
    )
    receipt.operational_status = OperationalStatus.FAILED
    with pytest.raises(ValueError):
        drafts.describe_contributions(draft, products)


def test_solver_configuration_and_initial_state_mutations_remain_unevaluable():
    trace = exposed(config_rows()[0])
    attempt = trace.charging_attempts[0]
    changed = replace(
        attempt,
        solver_configuration_json='{"type":"IDAKLUSolver","rtol":1e-7,"atol":1e-8}',
    )
    assert (
        science.check_trace(replace(trace, charging_attempts=(changed,))).disposition
        is A.UNEVALUABLE
    )
    changed = replace(trace, mean_temperature_k=(D("279.15"),) * 2)
    assert science.check_trace(changed).disposition is A.UNEVALUABLE
    with pytest.raises(ValueError):
        replace(attempt, configuration=config_rows()[1])


def service_negative(config):
    trace = exposed(config)
    current0 = trace.current_a[0]
    last_current = -D(".05")
    end = -D(8640) / ((current0 + last_current) / 2)
    reason = "event: Inquiry source minimum charging magnitude [A]"
    attempt = trace.charging_attempts[0]
    last = (last_current, D("4.2"), config.initial_temperature_k, -D("2.4"))
    attempt = replace(
        attempt,
        native_times_s=(D(0), end),
        termination=reason,
        end_receivers=last,
        end_differential_state=(-D("2.4"), D(1)),
        realized_end_state_sha256="",
    )
    return replace(
        trace,
        disposition="SERVICE_TERMINATED",
        termination=reason,
        times_s=(D(0), end),
        current_a=(current0, last_current),
        capacity_ah=(D(0), -D("2.4")),
        control_modes=("CC", "CV"),
        charging_attempts=(attempt,),
    )


def test_converged_service_negative_resolves_precision_without_delivery():
    rows = tuple(service_negative(c) for c in config_rows())
    checks = tuple(science.check_trace(t) for t in rows)
    assert all(c.disposition is A.FALSIFIED for c in checks)
    assert all(
        c.reason_codes == ("operational-soc80-target-not-delivered",) for c in checks
    )
    pairs = science.comparisons(rows)
    assert all(p.disposition is A.SATISFIED for p in pairs)
    result = DiagnosticResult(
        "product.battery-dfn-precision-diagnostic",
        rows[0].config.source,
        rows[0].config.prior_supply,
        rows,
        checks,
        pairs,
        A.SATISFIED,
    )
    assert not result.qualification
    integrity = replace(rows[0], capacity_ah=(D(0), -D("2.3")))
    assert science.compare_reference(integrity, rows[1]).reason_codes == (
        "reference-native-integrity-unresolved",
    )
    feasible = exposed(rows[1].config)
    assert (
        "reference-feasibility-disagrees"
        in science.compare_reference(rows[0], feasible).reason_codes
    )
    different = replace(rows[1], termination="event: Minimum voltage [V]")
    assert (
        "reference-termination-event-disagrees"
        in science.compare_reference(rows[0], different).reason_codes
    )


def unsigned_parent(row):
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.scientific_contributions import (
        ContributionProduct,
        ContributionManifest,
    )
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.kernel.evidence import (
        EvidenceCeiling,
        OutcomeAccess,
        VisibilityCeiling,
    )
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
        scope,
    )

    # Unsigned portable metadata seam only: known actual operand identity, no invented scientific payload.
    product = ContributionProduct(
        "product.exposed-precision.design-operand",
        row.prior_supply,
        ArtifactIdentity(
            "artifact.exposed-precision.prior",
            "scientific-product",
            BatteryInquirySupply.SCHEMA,
            row.prior_supply.object_fingerprint,
            "application/json",
            137856045,
        ),
        ObjectIdentity(
            "receipt.exposed-precision",
            "empirical-lawhood/testing/unsigned-metadata",
            "1.0.0",
            "a" * 64,
        ),
        ContributionRole.DESIGN_OPERAND,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
    )
    parent = ContributionManifest(
        "contribution.exposed-precision",
        "Exposed compile-only role check.",
        "Unsigned metadata fixture; no receipt authentication or scientific qualification.",
        scope(row.source.original),
        (product,),
        (
            ObjectIdentity(
                "assessment.exposed-precision",
                "empirical-lawhood/testing/assessment",
                "1.0.0",
                "b" * 64,
            ),
        ),
        (),
    )
    return parent


def test_parent_origin_preserves_negative_procedure_design_role_and_model_graph():
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.scientific_contributions import (
        ContributionProduct,
        ContributionManifest,
    )
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.kernel.evidence import (
        EvidenceCeiling,
        OutcomeAccess,
        VisibilityCeiling,
    )
    from empirical_lawhood.planning.recursive_input_origins import (
        RecursiveInputOrigin,
        RecursiveInputOriginKind,
        RecursiveInputOrigins,
    )
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
        scope,
    )

    row = config_rows()[0]
    # Unsigned portable metadata seam only: known actual operand identity, no invented scientific payload.
    product = ContributionProduct(
        "product.exposed-precision.design-operand",
        row.prior_supply,
        ArtifactIdentity(
            "artifact.exposed-precision.prior",
            "scientific-product",
            BatteryInquirySupply.SCHEMA,
            row.prior_supply.object_fingerprint,
            "application/json",
            137856045,
        ),
        ObjectIdentity(
            "receipt.exposed-precision",
            "empirical-lawhood/testing/unsigned-metadata",
            "1.0.0",
            "a" * 64,
        ),
        ContributionRole.DESIGN_OPERAND,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
    )
    parent = ContributionManifest(
        "contribution.exposed-precision",
        "Exposed compile-only role check.",
        "Unsigned metadata fixture; no receipt authentication or scientific qualification.",
        scope(row.source.original),
        (product,),
        (
            ObjectIdentity(
                "assessment.exposed-precision",
                "empirical-lawhood/testing/assessment",
                "1.0.0",
                "b" * 64,
            ),
        ),
        (),
    )
    config = owner.DiagnosticOperationConfig(
        "config." + owner.NAMESPACE,
        row.source,
        tuple(
            sorted(
                (science.identity(row.source), row.prior_supply),
                key=lambda x: x.object_id,
            )
        ),
    )
    draft = draft_from_config(config, parent=parent)
    origins = RecursiveInputOrigins(
        tuple(
            sorted(
                (
                    RecursiveInputOrigin(
                        x.input_id,
                        RecursiveInputOriginKind.CONTRIBUTION,
                        x.expected_content_sha256,
                        product.role.value,
                        ObjectIdentity.from_record(parent.contribution_id, parent),
                        product.product_id,
                        product.producing_receipt,
                    )
                    if x.input_id.endswith(".prior")
                    else RecursiveInputOrigin(
                        x.input_id,
                        RecursiveInputOriginKind.SOURCE,
                        x.expected_content_sha256,
                        x.scientific_role,
                    )
                    for x in draft.external_inputs
                ),
                key=lambda x: x.input_id,
            )
        )
    )
    origins.validate_draft(draft)
    compile_complete_draft(draft, owner)
    changed = replace(
        draft,
        external_inputs=tuple(
            replace(x, scientific_role="OUTCOME")
            if x.input_id.endswith(".prior")
            else x
            for x in draft.external_inputs
        ),
    )
    with pytest.raises(ValueError):
        origins.validate_draft(changed)


def test_exact_evidential_condition_and_precision_phases_do_not_qualify_delivery():
    from empirical_lawhood.kernel.recursive_requirements import AssessmentPhase

    row = config_rows()[0]
    config = owner.DiagnosticOperationConfig(
        "config." + owner.NAMESPACE,
        row.source,
        tuple(
            sorted(
                (science.identity(row.source), row.prior_supply),
                key=lambda x: x.object_id,
            )
        ),
    )
    draft = draft_from_config(config, parent=unsigned_parent(row))
    bad = replace(draft.requirements[0], condition="different scientific condition")
    with pytest.raises(ValueError):
        compile_complete_draft(replace(draft, requirements=(bad,)), owner)
    wrong = replace(draft.connections[0], consumer_input_id="source")
    with pytest.raises(ValueError):
        compile_complete_draft(replace(draft, connections=(wrong,)), owner)
    rows = tuple(service_negative(c) for c in config_rows())
    checks = tuple(science.check_trace(t) for t in rows)
    result = DiagnosticResult(
        "product.battery-dfn-precision-diagnostic",
        row.source,
        row.prior_supply,
        rows,
        checks,
        science.comparisons(rows),
        A.SATISFIED,
    )
    projections = owner.project_assessments(
        result, draft.requirements[0], draft.connections[0]
    )
    assert {x.phase for x in projections} == set(AssessmentPhase)
    assert all(x.disposition is A.SATISFIED for x in projections)
    assert all(x.disposition is A.FALSIFIED for x in result.checks)
    assert not result.qualification
