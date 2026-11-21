"""Registered services and closed composition for the sole controller route."""

from empirical_lawhood.methods.control.composition import ControllerStudyComposition, controller_capability_manifest, controller_capability_registry
from empirical_lawhood.methods.control.evidence_services import AtlasAdmissionDeriver, AtlasReachabilityDeriver

__all__ = [
    'ControllerStudyComposition',
    'AtlasAdmissionDeriver',
    'AtlasReachabilityDeriver',
    "controller_capability_manifest",
    "controller_capability_registry",
]
