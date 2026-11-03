# SPDX-License-Identifier: MPL-2.0
"""Explicit existing/geometry-reuse preparation admission, before native contact.

The caller authenticates original source and custody. This module preserves the
original 1.0.0 route and requires complete supplier/raw-operand joins for the
1.1.0 geometry-reuse successor; a schema/type alone grants no admission.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
from types import FunctionType
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurablePreparationPlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import (
    GeometryReusePlan, GeometryReuseSupply, REQUIRED_FILES, validate_reuse_assessment,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import PhysicalPreparationGeometry
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preparation_integrity import PreparationIntegrity
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_preparation_assessment import (
    SerializedPreparationGeometry, SerializedPreparationIntegrity,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from . import control_contracts as c
from .control_science import validate_operands as original_validate_operands


@dataclass(frozen=True, slots=True)
class SerializedDurableGeometrySupply(GeometryReuseSupply):
    """Newly completed durable geometry custody, joined to serialized assessment.

    This is not a geometry-reuse recipe. It shares the exact original complete
    receipt/manifest validator, selecting only its named assessment schema.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/serialized-durable-geometry-supply"

    def __post_init__(self):
        selected = FunctionType(GeometryReuseSupply.__post_init__.__code__,
            dict(GeometryReuseSupply.__post_init__.__globals__,
                INTEGRITY_SCHEMA=SerializedPreparationIntegrity.SCHEMA),
            GeometryReuseSupply.__post_init__.__name__)
        selected(self)
        if self.independent_integrity.object_version != SerializedPreparationIntegrity.VERSION:
            raise ValueError("durable geometry needs the exact serialized assignment revision")


def _validate_geometry_inputs(supplies, inputs, assessment_identity=None):
    if (type(inputs) is not tuple
            or any(type(row) is not tuple or len(row) != 2 for row in inputs)
            or tuple(row[0] for row in inputs) != tuple(row.identity for row in supplies)):
        raise ValueError("chemical preparation omits exact complete geometry operands")
    for supply, (_, operands) in zip(supplies, inputs, strict=True):
        supply.__post_init__()
        if (type(operands) is not tuple or len(operands) != 2
                or any(type(row) is not p.NativeTextFile for row in operands)
                or tuple(PurePosixPath(row.evidence.relative_path).name for row in operands) != REQUIRED_FILES
                or assessment_identity is not None and supply.independent_integrity != assessment_identity):
            raise ValueError("chemical preparation replaces its complete original geometry/assessment")
        for row in operands:
            row.__post_init__()
            if row.evidence not in supply.census.files:
                raise ValueError("chemical geometry operand replaces authenticated original census bytes")


@dataclass(frozen=True, slots=True, kw_only=True)
class SerializedDurableChemicalForcePlan(c.ChemicalForcePlan):
    """Explicit durable-plan admission using independently assessed 1.1 records."""

    VERSION: ClassVar[str] = "1.2.0"
    preparation_plan: DurablePreparationPlan
    geometry_supplies: tuple[SerializedDurableGeometrySupply, ...]
    geometry_inputs: tuple[tuple[ObjectIdentity, tuple[p.NativeTextFile, ...]], ...]

    def __post_init__(self):
        c.ChemicalForcePlan.__post_init__(self)
        if (type(self.preparation_plan) is not DurablePreparationPlan
                or type(self.geometry_supplies) is not tuple
                or any(type(row) is not SerializedDurableGeometrySupply for row in self.geometry_supplies)
                or self.preparation_plan.source != self.source
                or self.preparation_plan.engine_inventory_sha256 != self.engine_inventory_sha256
                or self.assignment_integrity.object_version != SerializedPreparationIntegrity.VERSION
                or self.mathematical_geometry.object_version != SerializedPreparationGeometry.VERSION
                or any(name not in self.preparation_plan.attempted_model_ids for name, _ in self.selected_assets)):
            raise ValueError("serialized durable chemical plan changes selected genuine preparation operands")
        self.preparation_plan.__post_init__()
        needed = tuple(sorted({"geometry." + name[len("model."):].rsplit(".", 1)[0]
            for name, _ in self.selected_assets}))
        if (tuple(row.definition.subwork_id for row in self.geometry_supplies) != needed
                or any(row.original_plan != self.preparation_plan or p.identity(row.original_source) != self.source
                    or row.original_source.engine_inventory_sha256 != self.engine_inventory_sha256
                    for row in self.geometry_supplies)):
            raise ValueError("serialized durable chemical plan substitutes completed geometry parents")
        _validate_geometry_inputs(self.geometry_supplies, self.geometry_inputs, self.assignment_integrity)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReusedGeometryChemicalForcePlan(c.ChemicalForcePlan):
    VERSION: ClassVar[str] = "1.1.0"
    preparation_plan: GeometryReusePlan
    geometry_supplies: tuple[GeometryReuseSupply, ...]
    geometry_assessments: tuple[PreAmberGeometryIntegrity, ...]
    geometry_inputs: tuple[tuple[ObjectIdentity, tuple[p.NativeTextFile, ...]], ...]

    def __post_init__(self):
        c.ChemicalForcePlan.__post_init__(self)
        if (type(self.preparation_plan) is not GeometryReusePlan
                or type(self.geometry_supplies) is not tuple
                or type(self.geometry_assessments) is not tuple
                or type(self.geometry_inputs) is not tuple
                or any(type(row) is not GeometryReuseSupply for row in self.geometry_supplies)
                or any(type(row) is not PreAmberGeometryIntegrity for row in self.geometry_assessments)
                or any(type(row) is not tuple or len(row) != 2 for row in self.geometry_inputs)
                or self.preparation_plan.source != self.source
                or tuple(row.identity for row in self.geometry_supplies) != self.preparation_plan.geometry_supplies
                or len(self.geometry_assessments) != len(self.geometry_supplies)
                or tuple(row[0] for row in self.geometry_inputs) != self.preparation_plan.geometry_supplies
                or self.assignment_integrity.object_version != "1.1.0"
                or self.mathematical_geometry.object_version != "1.1.0"
                or any(name not in self.preparation_plan.attempted_model_ids for name, _ in self.selected_assets)):
            raise ValueError("chemical reuse omits its exact independently assessed preparation suppliers")
        self.preparation_plan.__post_init__()
        for supply, assessment, (_, operands) in zip(self.geometry_supplies,
                self.geometry_assessments, self.geometry_inputs, strict=True):
            if type(supply) is not GeometryReuseSupply or type(assessment) is not PreAmberGeometryIntegrity:
                raise ValueError("chemical reuse changes actual original supplier/assessment types")
            supply.__post_init__()
            assessment.__post_init__()
            if (type(operands) is not tuple or len(operands) != 2
                    or any(type(row) is not p.NativeTextFile for row in operands)
                    or tuple(PurePosixPath(row.evidence.relative_path).name for row in operands) != REQUIRED_FILES):
                raise ValueError("chemical reuse needs both complete original materialized raw operands")
            for row in operands:
                row.__post_init__()
            if (operands[0].evidence != assessment.origin_file
                    or operands[1].evidence != assessment.heavy_file):
                raise ValueError("chemical reuse replaces independently assessed original operand bytes")


def decode_plan(value):
    from .derived_model_admission import DerivedChemicalForcePlan
    from .closed_raw_model_admission import InstanceChemicalForcePlan
    raw = value.encode()
    version = json.loads(raw).get("version")
    kind = {"1.0.0": c.ChemicalForcePlan, "1.1.0": ReusedGeometryChemicalForcePlan,
        "1.2.0": SerializedDurableChemicalForcePlan, "1.3.0": DerivedChemicalForcePlan,
        "1.4.0": InstanceChemicalForcePlan}.get(version)
    if kind is None:
        raise ValueError("unsupported selected chemical preparation plan revision")
    return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))


def decode_assessments(integrity_value, geometry_value):
    raw_integrity, raw_geometry = integrity_value.encode(), geometry_value.encode()
    version = json.loads(raw_integrity).get("version")
    if json.loads(raw_geometry).get("version") != version:
        raise ValueError("chemical preparation mixes independent assessment revisions")
    if version == "1.0.0":
        kinds = PreparationIntegrity, PhysicalPreparationGeometry
    elif version == "1.1.0":
        kinds = SerializedPreparationIntegrity, SerializedPreparationGeometry
    else:
        raise ValueError("unsupported selected independent preparation assessment revision")
    return tuple(decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        for raw, kind in zip((raw_integrity, raw_geometry), kinds, strict=True))


def validate_operands(plan, source, preparation, integrity, geometry, assets, custody):
    from .closed_raw_model_admission import InstanceChemicalForcePlan, validate_instance_operands
    if type(plan) is InstanceChemicalForcePlan:
        return validate_instance_operands(plan, source, preparation, integrity, geometry, assets, custody)
    from .derived_model_admission import DerivedChemicalForcePlan, validate_derived_operands
    if type(plan) is DerivedChemicalForcePlan:
        return validate_derived_operands(plan, source, preparation, integrity, geometry, assets, custody)
    if type(plan) is c.ChemicalForcePlan:
        if type(integrity) is not PreparationIntegrity or type(geometry) is not PhysicalPreparationGeometry:
            raise ValueError("original chemical plan needs its original independent assessment revision")
        return original_validate_operands(plan, source, preparation, integrity, geometry, assets, custody)
    if type(plan) is SerializedDurableChemicalForcePlan:
        if (type(integrity) is not SerializedPreparationIntegrity
                or type(geometry) is not SerializedPreparationGeometry):
            raise ValueError("serialized durable chemical plan requires exact independent assessment revisions")
        plan.__post_init__()
        _validate_model_geometry(plan, assets, custody)
        return original_validate_operands(plan, source, preparation, integrity, geometry, assets, custody)
    if (type(plan) is not ReusedGeometryChemicalForcePlan
            or type(integrity) is not SerializedPreparationIntegrity
            or type(geometry) is not SerializedPreparationGeometry):
        raise ValueError("chemical reuse needs its explicit selected plan and assessment revision")
    plan.__post_init__()
    for supply, assessment in zip(plan.geometry_supplies, plan.geometry_assessments, strict=True):
        validate_reuse_assessment(plan.preparation_plan, source, supply, assessment)
    _validate_model_geometry(plan, assets, custody)
    # All original numerical/receipt/selected-asset admission math is unchanged.
    # Its fixed plan-schema check selects only the demonstrated authenticated
    # reuse recipe here; no global mutation or general schema widening occurs.
    selected_math = FunctionType(original_validate_operands.__code__,
        dict(original_validate_operands.__globals__, DurablePreparationPlan=GeometryReusePlan),
        original_validate_operands.__name__, original_validate_operands.__defaults__,
        original_validate_operands.__closure__)
    return selected_math(plan, source, preparation, integrity, geometry, assets, custody)


def _validate_model_geometry(plan, assets, custody):
    suppliers = {row.definition.subwork_id: row for row in plan.geometry_supplies}
    operands = {row[0]: row[1] for row in plan.geometry_inputs}
    for name, definition, _, _, _, returned in custody:
        geometry_id = "geometry." + name[len("model."):].rsplit(".", 1)[0]
        supply = suppliers.get(geometry_id)
        if (supply is None or definition.configuration != plan.preparation_plan.identity
                or definition.code_sources_sha256 != sha256(canonical_json_bytes(plan.preparation_plan.code_sources)).hexdigest()
                or definition.dependency_lock_sha256 != plan.preparation_plan.dependency_lock_sha256
                or type(plan) is SerializedDurableChemicalForcePlan and not {
                    plan.preparation_plan.source, plan.preparation_plan.nomination,
                    plan.preparation_plan.inventory, plan.preparation_plan.coordinates}.issubset(definition.sources)
                or type(plan) is ReusedGeometryChemicalForcePlan and not {
                    supply.identity, supply.independent_integrity}.issubset(definition.sources)
                or returned.geometry != supply.definition.identity
                or returned.geometry_receipt != supply.geometry_receipt):
            raise ValueError("serialized durable chemical plan replaces genuine model/source/geometry receipt joins")
        asset = next(row for row in assets if c.model_id((row.construct_id, row.joint_view_id, row.parameter_view)) == name)
        by_name = {PurePosixPath(row.evidence.relative_path).name: row for row in asset.files}
        parent_origin, parent_heavy = operands[supply.identity]
        heavy, origin = by_name.get("complete-heavy.pdb"), by_name.get("atom-origin-provenance.json")
        if (heavy is None or origin is None or heavy.raw_utf8 != parent_heavy.raw_utf8
                or (heavy.evidence.byte_count, heavy.evidence.sha256)
                    != (parent_heavy.evidence.byte_count, parent_heavy.evidence.sha256)):
            raise ValueError("serialized durable chemical plan replaces completed original heavy geometry")
        realized = json.loads(origin.raw_utf8)
        if type(realized) is not dict or "amber_realization" not in realized:
            raise ValueError("serialized durable chemical plan lacks full genuine Amber origin realization")
        inherited = {key: value for key, value in realized.items() if key != "amber_realization"}
        if json.dumps(inherited, sort_keys=True, separators=(",", ":")) != json.dumps(
                json.loads(parent_origin.raw_utf8), sort_keys=True, separators=(",", ":")):
            raise ValueError("serialized durable chemical plan replaces original geometry atom origins")
