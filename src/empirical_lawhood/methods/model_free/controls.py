# SPDX-License-Identifier: MPL-2.0
"""Small known mechanisms exercised through the same observation pipeline."""
import numpy as np

from .memory import assess_root_memory, memory_diagnostics, root_lag_counts
from .observation import ObservationContract, discretize


CONTROL_NAMES = ("markov", "binned_markov", "inertial", "hidden_memory",
                 "nonstationary", "detector", "heterogeneous")


def hidden_memory_joint(lag=1):
    """Exact stationary three-emission law of the documented hidden control.

Each emission's conditional mean is zero, so all positive-lag linear
autocovariances vanish. Emission magnitude still reveals a persistent state.
"""
    if type(lag) is not int or lag < 1:
        raise ValueError("lag must be a positive integer")
    transition = np.array([[.99, .01], [.01, .99]])
    emission = np.array([[.05, .9, .05], [.45, .1, .45]])
    step = np.linalg.matrix_power(transition, lag)
    law = np.zeros((3, 3, 3))
    for a in range(2):
        for b in range(2):
            for c in range(2):
                law += .5*step[a, b]*step[b, c]*np.einsum("i,j,k->ijk", emission[a], emission[b], emission[c])
    return law


def control_sequence(name, *, length=4096, seed=0, persistence=None):
    """Return a disclosed synthetic observation and its mechanism identity.

Controls establish estimator behavior, not native matrix or molecular claims.
No finite random control draw is required to reject its null.
"""
    if name not in CONTROL_NAMES or type(length) is not int or length < 3:
        raise ValueError("unknown control or insufficient observation length")
    if persistence is not None and (name != "heterogeneous" or not 0 < float(persistence) < 1):
        raise ValueError("a fixed latent persistence is only valid for the heterogeneous control")
    rng = np.random.default_rng(seed)
    x = np.empty(length)
    mechanism = ""
    if name in {"markov", "hidden_memory", "nonstationary", "heterogeneous"}:
        state = int(rng.integers(2))
        persistence = (float(rng.choice([.55, .995])) if persistence is None else float(persistence)) if name == "heterogeneous" else .99
        emission = np.array([[.05, .9, .05], [.45, .1, .45]])
        for t in range(length):
            if name == "nonstationary":
                persistence = .99 if t < length//2 else .60
            if rng.random() > persistence:
                state = 1-state
            x[t] = rng.choice([-1., 0., 1.], p=emission[state]) if name == "hidden_memory" else state
        if name == "hidden_memory":
            edges = (-1.5, -.5, .5, 1.5)
            mechanism = "stationary hidden binary state with fresh symmetric sign; zero linear autocorrelation"
        else:
            edges = (-.5, .5, 1.5)
            mechanism = {"markov": "stationary fully observed binary Markov chain",
                         "nonstationary": "binary Markov chain with protocol-dependent persistence",
                         "heterogeneous": "each root has one fixed but root-dependent transition kernel"}[name]
    elif name == "binned_markov":
        x[0] = rng.normal()
        for t in range(1, length):
            x[t] = .95*x[t-1]+np.sqrt(1-.95**2)*rng.normal()
        edges = (-20., -.5, .5, 20.)
        mechanism = "stationary Gaussian AR(1), whose finite bins need not be Markov"
    elif name == "inertial":
        # Stable second-order position dynamics; use a long discarded pilot
        # only as a disclosed construction, not proof of exact stationarity.
        q, old = 0., 0.
        for t in range(length+2048):
            new = 1.5*q-.7*old+.4*rng.normal()
            old, q = q, new
            if t >= 2048:
                x[t-2048] = q
        edges = (-100., -.5, .5, 100.)
        mechanism = "stable second-order position recursion with omitted velocity; finite burn-in"
    else:
        state, filtered = 0, 0.
        for t in range(length+1024):
            if rng.random() > .95:
                state = 1-state
            filtered = .8*filtered+.2*(state+.35*rng.normal())
            if t >= 1024:
                x[t-1024] = filtered
        edges = (-100., .25, .75, 100.)
        mechanism = "noisy exponentially filtered binary Markov observation"
    contract = ObservationContract("control."+name, ("q",), ("control_units",), (edges,), 1.,
                                   "synthetic."+name, clock="algorithmic")
    output = discretize(x, contract)
    output.update(name=name, seed=int(seed), mechanism=mechanism,
                  scientific_scope="disclosed synthetic estimator control")
    if name == "heterogeneous":
        output["latent_persistence"] = persistence
    return output


def control_diagnostics(name, *, length=4096, seed=0, lags=(1, 2, 4)):
    observed = control_sequence(name, length=length, seed=seed)
    counts = root_lag_counts(observed["symbols"], lags, alphabet_size=observed["alphabet_size"],
                             root_id=f"control.{name}.{seed}")
    return {"name": name, "mechanism": observed["mechanism"], "counts": counts,
            "diagnostics": {lag: memory_diagnostics(row["joint_counts"])
                            for lag, row in counts["lags"].items() if row["observed_anchors"] > 0},
            "scientific_scope": observed["scientific_scope"]}


def binary_markov_joint(first_persistence, second_persistence):
    """Exact three-time law for two symmetric binary Markov transitions.

The initial distribution is uniform. The two transitions may have different
physical protocol ages; conditional independence still holds at that age.
"""
    values = (float(first_persistence), float(second_persistence))
    if any(not np.isfinite(p) or not 0 <= p <= 1 for p in values):
        raise ValueError("transition persistence must be a probability")
    first, second = (np.array([[p, 1-p], [1-p, p]]) for p in values)
    return .5 * np.einsum("ij,jk->ijk", first, second)


def protocol_age_joint(*, length, lag, future_anchor):
    """Known inhomogeneous Markov law, including transitions across the switch.

At transition ending at sample t, persistence is .99 for t < length//2 and
.60 thereafter. This is the actual ``control_sequence`` convention.
"""
    if any(type(v) is not int for v in (length, lag, future_anchor)) or lag < 1 or not 2*lag <= future_anchor < length:
        raise ValueError("a complete fixed protocol-age triple is required")

    def persistence(start, stop):
        early = max(0, min(stop, length//2 - 1) - start)
        late = stop-start-early
        return (1 + .98**early * .2**late)/2

    return binary_markov_joint(persistence(future_anchor-2*lag, future_anchor-lag),
                               persistence(future_anchor-lag, future_anchor))


def _population_readout(counts, *, alpha):
    """Equal-root laws, never a concatenation across independent trajectories."""
    diagnostics = {}
    for lag in counts[0]["lags"]:
        rows = [root["lags"][lag] for root in counts]
        if all(row["observed_anchors"] and not row["missing_anchors"] for row in rows):
            law = np.mean([np.asarray(row["joint_counts"])/row["attempted_anchors"] for row in rows], axis=0)
            diagnostics[lag] = memory_diagnostics(law)
    return {"root_counts": counts, "diagnostics": diagnostics,
            "assessment": assess_root_memory(counts, alpha=alpha),
            "independent_roots": len(counts), "root_ids": [row["root_id"] for row in counts]}


def population_control(name, *, length=4096, seed=0, lags=(1, 2, 4), roots=16):
    """Contrast pooled, latent-conditioned and protocol-age-conditioned laws.

Every repeated time origin remains inside its independently generated root.
Exact known laws explain the intended null; finite samples may be unresolved.
The balanced heterogeneous roster has independent, nonidentically distributed
roots, with the fixed latent parameter explicitly assigned before simulation.
"""
    if name not in {"heterogeneous", "nonstationary"} or type(roots) is not int or roots < 4 or roots % 2:
        raise ValueError("select a population control with an even roster of at least four roots")
    lags = tuple(lags)
    if not lags or any(type(lag) is not int or lag < 1 for lag in lags) or 2*max(lags) >= length:
        raise ValueError("control lags require complete three-time anchors")
    seeds = np.random.SeedSequence(seed).spawn(roots)
    observations, counts, roster = [], [], []
    for index, child in enumerate(seeds):
        local_seed = int(child.generate_state(1, dtype=np.uint64)[0])
        latent = (.55, .995)[index % 2] if name == "heterogeneous" else None
        observed = control_sequence(name, length=length, seed=local_seed, persistence=latent)
        root_id = f"control.{name}.{seed}.{index}"
        observations.append(observed)
        counts.append(root_lag_counts(observed["symbols"], lags, alphabet_size=2, root_id=root_id))
        roster.append({"root_id": root_id, "seed": local_seed, "latent_persistence": latent})
    conditioned, exact = [], {}
    if name == "heterogeneous":
        for latent in (.55, .995):
            subset = [row for row, assignment in zip(counts, roster) if assignment["latent_persistence"] == latent]
            conditioned.append({"conditioning": {"latent_persistence": latent},
                **_population_readout(subset, alpha=.05/3)})
        for lag in lags:
            laws = [binary_markov_joint((1+(2*p-1)**lag)/2, (1+(2*p-1)**lag)/2) for p in (.55, .995)]
            exact[str(lag)] = {"pooled": memory_diagnostics(np.mean(laws, axis=0)),
                "conditioned": [{"latent_persistence": p, "joint_law": law.tolist(),
                    "diagnostics": memory_diagnostics(law)} for p, law in zip((.55, .995), laws)]}
        null_scope = "Markov conditional on each fixed latent kernel; the equal-root mixed population need not be Markov"
    else:
        anchors = sorted({max(2*max(lags), length//4), max(2*max(lags), 3*length//4)})
        for age in anchors:
            age_counts = [root_lag_counts(observed["symbols"], lags, alphabet_size=2,
                root_id=assignment["root_id"], record_scope="protocol_age", anchor_indices=(age,))
                for observed, assignment in zip(observations, roster)]
            conditioned.append({"conditioning": {"future_anchor_sample": age},
                **_population_readout(age_counts, alpha=.05/(len(anchors)+1))})
        for lag in lags:
            law = np.mean([protocol_age_joint(length=length, lag=lag, future_anchor=age)
                           for age in range(2*lag, length)], axis=0)
            exact[str(lag)] = {"pooled": memory_diagnostics(law),
                "conditioned": [{"future_anchor_sample": age,
                    "joint_law": protocol_age_joint(length=length, lag=lag, future_anchor=age).tolist(),
                    "diagnostics": memory_diagnostics(protocol_age_joint(length=length, lag=lag, future_anchor=age))}
                    for age in anchors]}
        null_scope = "Time-inhomogeneous Markov conditional on exact protocol age; pooling ages is not its Markov null"
    return {"name": name, "mechanism": observations[0]["mechanism"],
        "root_roster": roster, "independent_roots": roots,
        "pooled": _population_readout(counts, alpha=.05/(len(conditioned)+1)),
        "conditioned": conditioned, "exact_known_laws": exact, "null_scope": null_scope,
        "clock": "algorithmic", "sample_interval": 1., "protocol_switch_sample": length//2 if name == "nonstationary" else None,
        "scientific_scope": "disclosed synthetic estimator control; finite draws need not reject or certify equivalence"}


def control_suite(*, seed=0, length=4096, lags=(1, 2, 4)):
    """Run all mechanisms, including actual population and time-aware nulls."""
    return {name: (population_control if name in {"heterogeneous", "nonstationary"} else control_diagnostics)(
        name, length=length, seed=seed+i, lags=lags) for i, name in enumerate(CONTROL_NAMES)}
