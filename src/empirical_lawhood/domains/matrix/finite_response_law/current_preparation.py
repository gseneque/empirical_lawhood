# SPDX-License-Identifier: MPL-2.0
"""Current preparation fold fitting with the frozen excluded-root recipe.

Inputs are already authenticated by the application. This numerical owner
keeps the original fold ordering, ridge, scientific census and precision.
"""
from collections.abc import Mapping
from hashlib import sha256
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.matrix.finite_response_law.transient_bridge import TransientBridgeInput, TransientBridgeSpec, current_root_fold_arrays, fit_hold
from empirical_lawhood.domains.matrix.finite_response_law.fitting import Normalizer
from empirical_lawhood.domains.matrix.preparation_applicability.measurement import validity
from empirical_lawhood.methods.response_formalization import affine_prediction, fit_affine_operator


def derive_preparation_operands(*, native, allocation, arrays, original_f, operand_id):
    """Return the exact bridge input, specification, arrays and native identity."""
    if native.original_f != original_f.identity or tuple(root.cohort for root in allocation.roots) != ("q2",) * 8 + ("cir1",) * 16:
        raise ValueError("Current preparation arrays change original F or ordered native prefix kinds")
    expected = {"x": (24, 24, 2), "z": (24, 9, 24, 2), "y": (24, 9, 4, 8, 2, 2), "work": (24, 9, 2), "features": (24, 9, 2, 26, 24), "positions": (24, 9, 2, 26, 2, 3, 4, 4), "momenta": (24, 9, 2, 26, 2, 3, 4, 4)}
    for name, shape in expected.items():
        if name not in arrays or arrays[name].shape != shape or not np.isfinite(arrays[name]).all() or arrays[name].dtype != np.dtype("complex128" if name in ("positions", "momenta") else "float64"):
            raise ValueError(f"UNEVALUABLE: incomplete required current {name} array")
    identity_bytes = native.canonical_bytes()
    native_record_artifact = ArtifactIdentity(f"{native.operand_id}.manifest", "current-native-array-manifest", native.SCHEMA, sha256(identity_bytes).hexdigest(), "application/json", len(identity_bytes))
    source = TransientBridgeInput(f"{operand_id}.input", allocation.identity, original_f.identity, native.array_artifact, native_record_artifact, tuple(root.root_id for root in allocation.roots), tuple(root.cohort for root in allocation.roots))
    fitted = current_root_fold_arrays(current_input=source, original_f=original_f, primary_prefix=arrays["x"][..., 0], native_handoff=arrays["z"], trajectories=arrays["features"])
    out = dict(arrays)
    out.update(fitted.arrays)
    out.update(center=np.asarray(original_f.center, dtype=np.float64), scale=np.asarray(original_f.scale, dtype=np.float64), operator=np.asarray(original_f.operator, dtype=np.float64).reshape(25, 32))
    # Current all-nine U2 baseline uses the same excluded-root ridge10 recipe.
    # It is a saved current fit, not an alias of an archival U2 prediction.
    upper_z = np.empty((24, 9, 24), dtype=np.float64)
    folds = fitted.arrays["folds"]
    prefix = arrays["x"][..., 0]
    for fold in range(4):
        train, test = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        normalizer = Normalizer.fit(prefix[train])
        operators = np.stack([fit_affine_operator(normalizer.apply(prefix[train]), arrays["z"][train, schedule, :, 0], ridge=10) for schedule in range(9)])
        upper_z[test] = np.stack([affine_prediction(operator, normalizer.apply(prefix[test])) for operator in operators], axis=1)
        if not np.allclose(upper_z[test, 0], fit_hold(prefix[train], arrays["z"][train, 0, :, 0], prefix[test]), rtol=1e-12, atol=1e-12):
            raise ValueError("Current excluded-root baseline changes the frozen hold-fit equivalence")
        for suffix, value in (("center", normalizer.center), ("scale", normalizer.scale), ("operator", operators), ("train", train), ("excluded", test)):
            out[f"u2.fold.{fold}.{suffix}"] = np.asarray(value)
    out["upper_z"] = upper_z
    out["upper_mean"] = original_f.predict(upper_z.reshape(-1, 24)).mean.reshape(24, 9, 4, 8)
    summaries = [validity(original_f, arrays["z"][root], arrays["y"][root], arrays["work"][root]) for root in range(24)]
    for index, name in enumerate(("maxima", "conjuncts", "margin", "mean", "width", "supported")):
        out[name] = np.stack([summary[index] for summary in summaries])
    for row in fitted.fits:
        for name in ("training_roots", "test_roots", "normalizer_center", "normalizer_scale", "kernel_scale", "operator"):
            out[f"radial.all.fold.{row['fold']}.{name}"] = np.asarray(row[name])
        out[f"radial.all.fold.{row['fold']}.kernel_rank"] = np.asarray(row["kernel_rank"], dtype=np.int64)
        out[f"radial.all.fold.{row['fold']}.training_modal_projection_mse"] = np.asarray(row["training_modal_projection_mse"], dtype=np.float64)
    spec = TransientBridgeSpec()
    return source, spec, out, native_record_artifact


def preparation_bridge_fits(arrays: Mapping[str, NDArray[np.generic]]) -> tuple[Mapping[str, object], ...]:
    """Restore the four exact saved radial.all fit records for readiness."""
    result = []
    for fold in range(4):
        row = {"model": "radial.all", "fold": fold}
        for name in ("training_roots", "test_roots", "normalizer_center", "normalizer_scale", "kernel_scale", "operator"):
            row[name] = arrays[f"radial.all.fold.{fold}.{name}"]
        row["kernel_rank"] = int(arrays[f"radial.all.fold.{fold}.kernel_rank"])
        row["training_modal_projection_mse"] = float(arrays[f"radial.all.fold.{fold}.training_modal_projection_mse"])
        result.append(row)
    return tuple(result)

