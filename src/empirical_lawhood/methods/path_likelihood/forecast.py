# SPDX-License-Identifier: MPL-2.0
"""Execute causal measurement, observation, forecast and reference on original batch parents."""

from time import process_time
import resource
import numpy as np

SPLITS = ("development", "train", "select", "calibrate")


def validate_splits(options):
    splits = options["splits"]
    if set(splits) != set(SPLITS) or any(
        type(v) is not int or v < 0 for v in splits.values()
    ):
        raise ValueError("declare the complete disjoint split census")
    if min(splits[k] for k in ("development", "train", "calibrate")) < 2:
        raise ValueError(
            "independent development, training and calibration roots are required"
        )


def role(root, options):
    end = options["first_root"]
    for i, name in enumerate(SPLITS):
        end += options["splits"][name]
        if root < end:
            return i
    return len(SPLITS)


def joined(batches, excluded=()):
    """Join original evaluable rows in strictly increasing independent-root order."""
    available = [values for _, values in batches if len(values["evaluable_root"])]
    if not available:
        return {}
    names = set(available[0]) - {"root"}
    if any(set(a) - {"root"} != names for a in available):
        raise ValueError("retained forecast batches have different measured fields")
    result = {
        key: np.concatenate([a[key] for a in available])
        for key in names.difference(excluded)
    }
    if np.any(np.diff(result["evaluable_root"]) <= 0):
        raise ValueError("forecast measurements repeat or reorder original roots")
    return result


def batch(phase, options, first, count, parents, frozen, *, source):
    """The forecasting callback receives only the observation and the fixed model.

    A reference requires both the original native checkpoint and the separate,
    receipted prediction. Training and calibration outcomes stay in development.
    """
    roots = np.arange(first, first + count, dtype="<i8")
    lookup = {
        name: {int(r): i for i, r in enumerate(a["evaluable_root"])}
        for name, a in parents.items()
    }
    saved, good, failures, updates = {}, [], [], 0
    cpu = {}

    def timed(name, fn, *args):
        start = process_time()
        try:
            return fn(*args)
        finally:
            cpu[name] = cpu.get(name, 0.0) + process_time() - start

    for r in roots:
        root = int(r)
        if any(root not in ids for ids in lookup.values()):
            failures.append({"root": root, "reason": "UNEVALUABLE_ORIGINAL_PARENT"})
            continue
        original = {
            name: {
                k: v[lookup[name][root]]
                for k, v in a.items()
                if k not in ("root", "evaluable_root", "split")
            }
            for name, a in parents.items()
        }
        try:
            if phase in ("develop", "prefix"):
                private, n = timed("native_prefix", source.prefix, root, options)
                updates += n
                values = private
                if phase == "develop":
                    observed = timed("observe", source.observe, private, options)
                    truth, n = timed(
                        "native_reference",
                        source.reference,
                        root,
                        private,
                        options,
                        True,
                    )
                    updates += n
                    values = source.training(private, observed, truth, options)
            elif phase == "observe":
                values = timed("observe", source.observe, original["prefix"], options)
            elif phase == "predict":
                args = (original["observe"], frozen["model"], options)
                if getattr(source, "STOCHASTIC_FORECAST", False):
                    args += (
                        np.random.default_rng(np.random.SeedSequence([root, 930163])),
                    )
                values = timed("issue_prediction", source.predict, *args)
            elif phase == "evaluate":
                truth, n = timed(
                    "native_reference",
                    source.reference,
                    root,
                    original["prefix"],
                    options,
                    False,
                )
                updates += n
                values = source.measured(
                    original["prefix"], original["predict"], truth, options
                )
            else:
                raise ValueError("unknown forecast lifecycle operation")
            values = dict(values, split=role(root, options))
            if not all(np.isfinite(v).all() for v in values.values()):
                raise FloatingPointError("nonfinite scientific measurement")
        except (FloatingPointError, np.linalg.LinAlgError, OverflowError) as exc:
            failures.append(
                {"root": root, "reason": type(exc).__name__, "detail": str(exc)}
            )
            continue
        good.append(root)
        for key, value in values.items():
            saved.setdefault(key, []).append(value)
    arrays = {k: np.stack(v) for k, v in saved.items()}
    arrays.update(root=roots, evaluable_root=np.asarray(good, dtype="<i8"))
    return {
        "native_intervals": updates,
        "root_failures": failures,
        "component_cpu_seconds": cpu,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, arrays


def reduce(options, batches, frozen, *, source):
    data = joined(batches, getattr(source, "EXCLUDE_REDUCTION", ()))
    assigned = sum(len(v["root"]) for _, v in batches)
    evaluable = len(data.get("evaluable_root", ()))
    if not evaluable:
        if frozen is None:
            raise ValueError("no evaluable development roots to freeze a model")
        return {"assigned": assigned, "evaluable": 0, "disposition": "UNEVALUABLE"}
    result = (
        source.fit(data, options)
        if frozen is None
        else source.assess(data, frozen["model"], options)
    )
    return dict(
        result,
        assigned=assigned,
        evaluable=evaluable,
        unevaluable=assigned - evaluable,
        root_ids=data["evaluable_root"].tolist(),
    )
