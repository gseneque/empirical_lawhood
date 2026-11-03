# SPDX-License-Identifier: MPL-2.0
"""Fixed exposed point for architectural conformance; never a fresh allocation."""

from decimal import Decimal as D

from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import (
    BetaCouplingRule, MatrixIntegratorKind, MatrixPrecision,
    SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView,
)
from empirical_lawhood.kernel.matrix_inputs import (
    MATRIX_NATIVE_PURPOSES, MatrixAllocation, MatrixPurposeSeed, MatrixRootAllocation,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff

from .records import (
    BRANCHES, MatrixOperandScope, MatrixProgrammeAllocation, MatrixProgrammeRole,
    MatrixProgrammeRoot, MatrixProspectiveSource, MatrixPublicProtocol,
)


def example_source():
    streams = tuple(sorted((*(MatrixPurposeSeed(name, number + 101)
        for number, name in enumerate(MATRIX_NATIVE_PURPOSES)),
        MatrixPurposeSeed("passive-probes", 10001, "PCG64DXSM")), key=lambda s: s.purpose_id))
    allocation = MatrixAllocation("allocation.matrix-prospective.exposed", (
        MatrixRootAllocation("root.matrix-prospective.exposed", "q2", streams),))
    root = MatrixProgrammeRoot(allocation.roots[0].root_id, "independent.matrix-prospective.exposed",
        "regime.matrix-prospective.exposed-positive", "coordinate.matrix-prospective.half",
        MatrixProgrammeRole.DEVELOPMENT, "clock.matrix-prospective.exposed")
    member = SixMatrixResponseModelFamilyMember("member.matrix-prospective.half", D("0.5"), D("0.5"),
        D("1"), BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    view = SixMatrixResponseNumericalView("view.matrix-prospective.exposed", MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
        D("0.001"), "dimensionless-langevin-time", D("1"), D("1"), MatrixPrecision.COMPLEX128,
        "PCG64", "1.0.0", "stream.matrix-prospective.exact-allocation-v1", 1)
    model = ObjectIdentity.from_record(member.member_id, member)
    numerical = ObjectIdentity.from_record(view.view_id, view)
    calibration = MatrixOperandScope("scope.matrix-prospective.numerical-calibration", "CALIBRATION",
        model, numerical, ("root.matrix-prospective.analytic-reference",), 2, BRANCHES,
        InformationCutoff("cutoff.matrix-prospective.numerical-calibration", "clock.matrix-prospective.reference",
                          CausalPhase.PRE_ACTION, D(0)))
    preparation = MatrixOperandScope("scope.matrix-prospective.preparation", "PRE_PREPARATION",
        model, numerical, (root.root_id,), 2, BRANCHES,
        InformationCutoff("cutoff.matrix-prospective.preparation", root.clock_id, CausalPhase.PRE_ACTION, D(0)))
    protocol = MatrixPublicProtocol("protocol.matrix-prospective.exposed", root, allocation.identity,
        member, view, D("1"), D("1"), 2, 2, calibration, preparation, D("1e-7"), D("1e-8"))
    return MatrixProspectiveSource("source.matrix-prospective.exposed", protocol,
        MatrixProgrammeAllocation("programme.matrix-prospective.exposed", allocation, (root,)))
