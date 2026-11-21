# SPDX-License-Identifier: MPL-2.0
"""Code-owned configured protected task derivation, never a supplied roster."""
from hashlib import sha256
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.experiments.experimental_design import UnitAllocation
from empirical_lawhood.domains.matrix.matrix_prospective.records import MatrixProgrammeRoot, MatrixProgrammeRole
from empirical_lawhood.domains.matrix.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
NAMESPACE = "matrix-e3-configured-protected"
KINDS = ("fit", "freeze", "forecast", "calibrate", "assess")


def _reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("configured protected task requires exact selected original types and revisions")
    value.__post_init__()


def statistical_task_id(specification, allocation, operation, *, mode="", root=None):
    _reference(specification, ConfiguredProtectedE3Specification)
    _reference(allocation, UnitAllocation)
    if (operation not in KINDS or operation == "freeze" and mode not in ("model", "calibration")
            or operation == "forecast" and mode not in ("calibration", "evaluation")
            or operation not in ("freeze", "forecast") and mode
            or (root is not None) != (operation == "forecast")):
        raise ValueError("protected E3 statistical task changes its exact operation/mode/root")
    if root is not None:
        if type(root) is not MatrixProgrammeRoot:
            raise TypeError("protected E3 forecast task requires its exact seedless root")
        root.__post_init__()
        expected = MatrixProgrammeRole.CALIBRATION if mode == "calibration" else MatrixProgrammeRole.CONFIRMATION
        if root.role is not expected:
            raise ValueError("protected E3 statistical forecast changes its allocated root role")
    digest = sha256(canonical_json_bytes((specification, allocation, operation, mode, root))).hexdigest()
    return NAMESPACE + ".statistical." + operation + "." + digest



def feature_task_id(root_id):
    from empirical_lawhood.science.records.serialization import validate_stable_id
    validate_stable_id(root_id)
    return NAMESPACE + "." + root_id + ".feature"
