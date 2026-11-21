# SPDX-License-Identifier: MPL-2.0
"""Operational selections separated from the scientific experiment definition."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.design.joint_description import JointSpecification, SelectedInputs
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.joint_description import PREFIX

PHASES = ("assess", "calibrate", "evaluate", "fit", "forecast", "prepare")
NATIVE_PHASES = ("calibrate", "evaluate", "prepare")
NAMESPACE = "joint-description"


@dataclass(frozen=True, slots=True)
class OperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    phase: str
    specification: JointSpecification
    selected_inputs: ObjectIdentity
    provenance: ObjectIdentity
    device: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.phase not in PHASES or not self.config_id.endswith("." + self.phase):
            raise ValueError("operation identity must match its declared scientific phase")
        if type(self.specification) is not JointSpecification:
            raise TypeError("operation needs its complete authored scientific specification")
        self.specification.__post_init__()
        for ref,kind in ((self.selected_inputs,SelectedInputs),(self.provenance,NumericalProducingProvenance)):
            if type(ref) is not ObjectIdentity or ref.object_schema != kind.SCHEMA or ref.object_version != kind.VERSION:
                raise ValueError("operation substituted a selected input/provenance role")
        if self.device not in ("cpu", "gpu") or (self.device == "gpu" and self.specification.family_id not in ("R17","R22")):
            raise ValueError("GPU acquisition is implemented only for the native JAX/TORAX families R17 and R22")

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id,self)


def config_for(specification, selected, provenance, phase):
    token = specification.fingerprint()[:24] + "." + selected.fingerprint()[:16] + "." + provenance.fingerprint()[:16]
    return OperationConfig("config.joint-description." + token + "." + phase, phase,
        specification,selected.identity,provenance.identity,selected.device)


def phase_config(config,phase):
    from dataclasses import replace
    return replace(config,config_id=config.config_id.rsplit(".",1)[0]+"."+phase,phase=phase)


def units(config):
    return config.specification.all_unit_ids


def acquisition_units(config):
    return config.specification.calibration_unit_ids if config.phase == "calibrate" else config.specification.evaluation_unit_ids


def effect_slots(config):
    return tuple("native."+config.node_id+"."+unit for unit in acquisition_units(config))


def operands(config):
    return tuple(sorted({config.specification.fingerprint(),config.selected_inputs.object_fingerprint,
        config.provenance.object_fingerprint}))
