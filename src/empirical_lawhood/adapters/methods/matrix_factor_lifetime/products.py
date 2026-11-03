"""Exact retained reading and complete-population descriptive uncertainty.

The caller selects guarded byte readers. This method has no native executor,
historical runner import, public registration or confirmation promotion route.
"""

from hashlib import sha256

import numpy as np
from scipy.stats import beta

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_dataset_readers import bridge_factor_diagnostics

from .records import FactorPopulationResult
from .science import align_factor, decimal_measurement, population_counts, risk_sets, validate_trace


def authenticate(identity, reader):
    """The selected custody reader must return the exact declared artifact bytes."""
    raw = reader(identity)
    if len(raw) != identity.size_bytes or sha256(raw).hexdigest() != identity.sha256:
        raise ValueError("retained factor artifact bytes differ from their declared identity")
    return raw


def _independent_leakage(basis):
    """Verify the retained closure equations without spectral reconstruction."""
    fields = np.einsum("ia,ijk->ajk", basis, algebra.BASIS)
    lie = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        commutator = -1j*(fields[i]@fields[j]-fields[j]@fields[i])
        coordinates = algebra.coords(commutator)
        residual = coordinates-basis@(basis.T@coordinates)
        lie.append(float(np.linalg.norm(residual)**2/max(float(coordinates@coordinates), 1e-30)))
    full = (algebra.IDENTITY/2, *fields)
    residuals, products = [], []
    for left in fields:
        for right in fields:
            product = left@right
            projected = sum(np.vdot(axis, product)*axis for axis in full)
            residuals.append(float(np.linalg.norm(product-projected)**2))
            products.append(float(np.linalg.norm(product)**2))
    return sum(residuals)/max(sum(products), 1e-30), max(lie)


def _diagnostic_shapes(spec):
    count = len(spec.lattice)
    return {"ticks": (count,), "spectrum": (count, 15),
        "projector": (count, 15, 15), "basis": (count, 15, 3),
        "factor": (count, 3, 4, 4), "aligned_factor": (count, 3, 4, 4),
        "available": (count,), "identifiable": (count,)}


def _validate_diagnostic_members(trace, spec):
    """Refuse documentary substitutions before opening their physical cursor."""
    shapes = _diagnostic_shapes(spec)
    members = {member.name: member for member in trace.diagnostic_members}
    if set(members) != set(shapes) or any(members[name].shape != shape for name, shape in shapes.items()):
        raise ValueError("factor diagnostics omit the complete spectrum/frame/lattice census")
    expected = {"ticks": "<i8", "available": "|b1", "identifiable": "|b1",
        **{key: "<f8" for key in ("spectrum", "projector", "basis")},
        **{key: "<c16" for key in ("factor", "aligned_factor")}}
    if any(members[name].dtype != dtype for name, dtype in expected.items()):
        raise ValueError("factor diagnostic declared numerical precision differs")
    if trace.diagnostics.media_type != "application/zip":
        raise ValueError("factor diagnostics change their original declared ZIP media")


def validate_diagnostics(arrays, trace, spec):
    """Check complete native-lattice diagnostics without recalculating spectra."""
    shapes = _diagnostic_shapes(spec)
    if set(arrays) != set(shapes) or any(arrays[k].shape != shape for k, shape in shapes.items()):
        raise ValueError("factor diagnostics omit the complete spectrum/frame/lattice census")
    if any(arrays["ticks"][i] != tick for i, tick in enumerate(spec.lattice)):
        raise ValueError("factor diagnostics substitute the common lattice")
    for k in ("ticks",):
        if arrays[k].dtype.str != "<i8":
            raise ValueError("factor diagnostic tick precision differs")
    for k in ("spectrum", "projector", "basis"):
        if arrays[k].dtype.str != "<f8":
            raise ValueError("factor diagnostic numerical precision differs")
    for k in ("factor", "aligned_factor"):
        if arrays[k].dtype.str != "<c16":
            raise ValueError("factor diagnostic frame precision differs")
    for k in ("available", "identifiable"):
        if arrays[k].dtype.str != "|b1":
            raise ValueError("factor diagnostic missingness precision differs")
    previous = None
    origin_basis = None
    for i, observation in enumerate(trace.observations):
        available = observation.status in ("AVAILABLE", "UNIDENTIFIABLE")
        identified = observation.identifiable is True
        if bool(arrays["available"][i]) != available or bool(arrays["identifiable"][i]) != identified:
            raise ValueError("factor diagnostics change identification or observation missingness")
        for key in ("spectrum", "projector", "basis"):
            value = arrays[key][i]
            if available and not np.isfinite(value).all() or not available and not np.isnan(value).all():
                raise ValueError("factor diagnostics manufacture or lose available spectral data")
        for key in ("factor", "aligned_factor"):
            value = arrays[key][i]
            if identified and not np.isfinite(value).all() or not identified and not np.isnan(value).all():
                raise ValueError("factor diagnostics manufacture an unidentifiable frame")
        if available:
            spectrum = arrays["spectrum"][i]
            gap_identified = (spectrum[3] - spectrum[2] > float(spec.identifiability_relative_gap)*spectrum[-1]
                              and spectrum[3] > float(spec.identifiability_absolute_fourth))
            if gap_identified != identified:
                raise ValueError("factor retained spectrum differs from the selected gap rule")
            basis = arrays["basis"][i]
            if not np.allclose(basis.T @ basis, np.eye(3), atol=1e-10, rtol=0) or not np.allclose(arrays["projector"][i], basis @ basis.T, atol=1e-10, rtol=0):
                raise ValueError("factor retained projector and component basis differ")
        if not identified:
            previous = None
            continue
        factor = arrays["factor"][i]
        coordinates = algebra.coords(factor)
        if not np.allclose(factor, factor.conj().swapaxes(-1, -2), atol=1e-10, rtol=0) or not np.allclose(coordinates@coordinates.T, np.eye(3), atol=1e-10, rtol=0) or not np.allclose(np.trace(factor, axis1=-2, axis2=-1), 0, atol=1e-10, rtol=0):
            raise ValueError("factor retained frame is not an orthonormal traceless Hermitian chart")
        associative, lie = _independent_leakage(basis)
        expected_metrics = tuple(decimal_measurement(x) for x in (
            associative, lie,
            algebra.principal_angle(basis, coordinates.T)))
        if expected_metrics != (observation.associative_leakage, observation.lie_leakage, observation.factor_fit_angle_degrees):
            raise ValueError("factor retained frame algebra differs from its compact measurements")
        aligned, ambiguous, angle = factor, False, None
        if previous is not None:
            old_basis, old_frame, prior_ambiguity = previous
            aligned, ambiguous, _ = align_factor(old_frame, factor, spec.frame_alignment_minimum_overlap)
            ambiguous = ambiguous or prior_ambiguity
            angle = decimal_measurement(algebra.principal_angle(old_basis, basis))
        if not np.allclose(arrays["aligned_factor"][i], aligned, atol=1e-12, rtol=0) or ambiguous != observation.alignment_ambiguous or angle != observation.adjacent_angle_degrees:
            raise ValueError("factor retained frame substitutes its causal adjacent alignment")
        if observation.tick == trace.moving_lifetime.origin_tick:
            origin_basis = basis
        expected_origin_angle = None if origin_basis is None else decimal_measurement(algebra.principal_angle(origin_basis, basis))
        if observation.origin_angle_degrees != expected_origin_angle:
            raise ValueError("factor retained origin-fixed comparison substitutes its actual origin")
        continuous = observation.raw_admitted and (angle is None or angle <= spec.adjacent_angle_maximum_degrees)
        previous = (basis, aligned, ambiguous) if continuous else None


def read_result(raw, *, expected_population, expected_rule, expected_provenance, artifact_reader):
    """Authenticate original sources and new products; never repeat acquisition."""
    result = decode_canonical_bytes(raw, FactorPopulationResult, maximum_bytes=None)
    if result.population != expected_population or result.rule != expected_rule:
        raise ValueError("retained factor result substitutes its source population or event rule")
    if result.producing_provenance != expected_provenance:
        raise ValueError("retained factor result substitutes its exact producing source/environment")
    authenticate(result.population.source_inventory, artifact_reader)
    if result.rule.scalar_closure is not None:
        authenticate(result.rule.scalar_closure.normalization_owner, artifact_reader)
    for root in result.population.roots:
        authenticate(root.native_arrays, artifact_reader)
        authenticate(root.native_result, artifact_reader)
    for trace in result.traces:
        validate_trace(trace, result.rule)
        if trace.diagnostics is None:
            if any(o.status in ("AVAILABLE", "UNIDENTIFIABLE") for o in trace.observations):
                raise ValueError("retained measured factor trace lacks its original diagnostic arrays")
        else:
            _validate_diagnostic_members(trace, result.rule)
            dataset = bridge_factor_diagnostics(trace, authenticate(trace.diagnostics, artifact_reader),
                maximum_chunk_bytes=65536, maximum_slice_bytes=65536)
            try:
                with dataset.reader.verified_session(block_size_bytes=65536) as reader:
                    validate_diagnostics(dataset.row_mapping(reader), trace, result.rule)
            finally:
                dataset.close()
    return result


def recurrence_intervals(result, *, confidence):
    """Binomial root intervals envelop every unresolved admission, by family.

    Root/view/sector strata remain separate. This is finite-horizon recurrence,
    not onset rate, useful response lifetime or simultaneous scientific coverage.
    """
    from decimal import Decimal
    if not isinstance(confidence, Decimal) or not confidence.is_finite() or not 0 < confidence < 1:
        raise ValueError("recurrence confidence must be explicitly between zero and one")
    counts = population_counts(result)
    output = {}
    tail = (1-float(confidence))/2
    for key, row in counts.items():
        n, k = row["requested_roots"], row["admitted_roots"]
        unresolved = row["unknown_roots"]
        # An admitted root can have an unknown later lifetime. Its recurrence
        # is already known; only roots without an admission widen this bound.
        unknown_admission = sum(t.moving_lifetime.origin_tick is None and t.moving_lifetime.disposition == "UNKNOWN"
            for t in result.traces if (t.root.family_id, t.view, t.sector) == key)
        upper_k = k+unknown_admission
        output[key] = {**row, "unknown_lifetime_roots": unresolved,
            "unknown_admission_roots": unknown_admission,
            "observed_admission_fraction_lower": k/n,
            "observed_admission_fraction_upper": upper_k/n,
            "recurrence_probability_interval_lower": 0.0 if k == 0 else float(beta.ppf(tail, k, n-k+1)),
            "recurrence_probability_interval_upper": 1.0 if upper_k == n else float(beta.ppf(1-tail, upper_k+1, n-upper_k)),
            "confidence": str(confidence), "simultaneous_coverage": False}
    return output


def residual_survival_intervals(result, *, confidence):
    """Finite-horizon survival conditional on observed admission at the cutoff.

    This is residual life on the common cadence, not a measured formation time.
    Missing persistence widens the survival envelope rather than being dropped
    or treated as censoring. Each interval is marginal within its root stratum.
    """
    from decimal import Decimal
    if not isinstance(confidence, Decimal) or not confidence.is_finite() or not 0 < confidence < 1:
        raise ValueError("survival confidence must be explicitly between zero and one")
    tail = (1-float(confidence))/2
    output = {}
    for key, rows in risk_sets(result).items():
        estimates = []
        for row in rows:
            n = row["left_present_roots"]
            k, u = row["left_present_surviving"], row["left_present_unknown"]
            estimates.append({**row, "conditional_risk_roots": n,
                "survival_fraction_lower": None if n == 0 else k/n,
                "survival_fraction_upper": None if n == 0 else (k+u)/n,
                "survival_probability_interval_lower": None if n == 0 else 0.0 if k == 0 else float(beta.ppf(tail, k, n-k+1)),
                "survival_probability_interval_upper": None if n == 0 else 1.0 if k+u == n else float(beta.ppf(1-tail, k+u+1, n-k-u)),
                "confidence": str(confidence), "simultaneous_coverage": False})
        output[key] = tuple(estimates)
    return output
