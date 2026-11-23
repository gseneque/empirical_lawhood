# SPDX-License-Identifier: MPL-2.0
"""Read-only receiver diagnostics over the ordinary complete, authenticated path result."""

from contextlib import ExitStack, closing
from hashlib import sha256
from empirical_lawhood.execution.execution import VerifiedArtifactInput
from empirical_lawhood.api.generated_experiment_protocols import (
    EXPERIMENT_PROTOCOL_DECLARATIONS,
)

from empirical_lawhood.api.experiment_scientific_read import (
    read_prepared_development_science,
)
from empirical_lawhood.api.recursive_execution import (
    _read_recursive_wave_with_retained_roots,
)
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.methods.path_likelihood import arrays
from empirical_lawhood.methods.path_likelihood.records import PathProduct


def _batches(context, records, phase):
    writer = context["artifact_writer"]
    outputs = context["products"]["outputs"]
    for record in sorted(records, key=lambda r: r.config.first):
        if record.config.phase != phase:
            continue
        pin = record.arrays
        original = outputs[pin.artifact_id]
        verified = VerifiedArtifactInput(original.logical, original.materialization)
        with closing(writer.open(verified, maximum_bytes=pin.size_bytes)) as port:
            raw = port.read()
            if (len(raw), sha256(raw).hexdigest()) != (pin.size_bytes, pin.sha256):
                raise PermissionError("receiver diagnostic changes an original array")
            values = arrays.decode(raw, record.measurement["array_manifest"])
            if values["root"].tolist() != list(
                range(record.config.first, record.config.first + record.config.count)
            ):
                raise ValueError("receiver diagnostic changes original assignment")
            yield values


def _consume(**context):
    science = read_prepared_development_science(**context)
    if science is None or science.get("scientific_completion") != "COMPLETED":
        raise ValueError(
            "receiver diagnostics require a complete original scientific result"
        )
    records = [
        v
        for task in context["products"]["records"].values()
        for v in task.values()
        if type(v) is PathProduct
    ]
    (freeze,) = [r for r in records if r.config.phase == "freeze"]
    options = dict(
        freeze.config.design.parameters, first_root=freeze.config.design.first_root
    )
    model = freeze.measurement["model"]
    (spec_type,) = (
        d.specification_type
        for d in EXPERIMENT_PROTOCOL_DECLARATIONS
        if d.specification_type.SCHEMA == freeze.config.specification.object_schema
    )
    diagnose = getattr(spec_type, "diagnose", None)
    if not callable(diagnose):
        raise ValueError("the selected study has no supplemental receiver diagnostic")
    with ExitStack() as lifetime:

        def batches(phase):
            return lifetime.enter_context(closing(_batches(context, records, phase)))

        values = diagnose(options, model, batches)
    return {
        "study": science["study"],
        "run_id": science["run_id"],
        "evidence_scope": science["evidence_scope"],
        "assessment": science["evaluation"]["identity"],
        "frozen_model": science["development"]["identity"],
        "diagnostics": values,
        "source_arrays": {
            r.config.node_id: r.arrays.to_document()
            for r in records
            if r.arrays is not None
        },
    }


def read_diagnostics(service, directory):
    """Perform one ordinary full read, keeping original inputs alive until reduction ends."""
    analysis_source = implementation_binding(service.project_root)
    report, _ = _read_recursive_wave_with_retained_roots(
        directory=directory,
        artifact_writer=service.artifact_writer,
        terminal_product_format="references",
        _scientific_consumer=_consume,
    )
    return {
        **report["scientific_result"],
        "original_producer": {
            k: report[k]
            for k in (
                "observed_producing_git_head",
                "producing_code_sha256",
                "dependency_lock_sha256",
                "execution_plan_sha256",
                "packet_sha256",
            )
        },
        "analysis_source": {
            "code_sha256": analysis_source.code_sources_sha256,
            "dependency_lock_sha256": analysis_source.dependency_lock_sha256,
            "git_head": analysis_source.observed_git_head,
            "checkout_clean": analysis_source.observed_checkout_clean,
        },
    }
