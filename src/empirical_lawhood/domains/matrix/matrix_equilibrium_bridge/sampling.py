# SPDX-License-Identifier: MPL-2.0
"""Bounded native sampling; source/stream authority and custody stay outside."""
from hashlib import sha256
import json
import time

import numpy as np

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_science import Computation, measurements
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import physics


def acquire(config, streams, *, progress=None):
    d, bank = config.design, config.root.bank
    centers = np.array(d.grid(bank), dtype='<f8')
    mult = d.reference_multiplier if bank == 'REFERENCE' else 1
    burn, horizon = d.burn_steps*mult, d.production_steps*mult
    count, nodes = horizon//d.sample_stride, len(centers)
    coupling = np.broadcast_to(np.array(d.couplings, dtype=float)[None, :, None], (2, 2, nodes))
    center = np.broadcast_to(centers, (2, 2, nodes))
    rngs = {s.purpose: np.random.Generator(np.random.PCG64DXSM(int(s.seed_sha256[:32], 16))) for s in streams}
    states_before = {k: r.bit_generator.state for k, r in rngs.items()}
    q = physics.initial_positions(d, nodes)
    # The two mutation-like arms share initial Maxwell momenta and noise.
    momentum = np.broadcast_to(physics.lift(rngs['INITIAL_MOMENTUM'].normal(size=(2, 1, nodes, 96))), q.shape).copy()*np.sqrt(float(d.temperature))
    g = physics.gradient(d, q, coupling, center)
    live = [(q.copy(), momentum.copy(), g.copy()) for _ in range(2)]
    arrays = {
        'centers': centers, 'sample_ticks': np.arange(burn+d.sample_stride, burn+horizon+1, d.sample_stride, dtype='<i8'),
        'positions': np.empty((2, 2, 2, nodes, count, 96), dtype='<f8'),
        'gradients': np.empty((2, 2, 2, nodes, count, 96), dtype='<f8'),
        'observables': np.empty((2, 2, 2, nodes, count, 5), dtype='<f8'),
        'kinetic_temperature': np.empty((2, 2, 2, nodes, count), dtype='<f8'),
        'warmup_radial': np.empty((2, 2, 2, nodes, burn//d.sample_stride), dtype='<f8'),
    }
    witnesses = []
    witness_ticks = set(range(1024, burn+horizon+1, 1024))
    tape = sha256()
    dt = float(d.timestep); a = np.exp(-float(d.friction)*dt/2); denom = np.sqrt(1+a*a)
    cpu, wall = time.process_time(), time.monotonic()
    for tick in range(1, burn+horizon+1):
        coarse = rngs['COARSE_INNOVATION'].normal(size=(2, 1, nodes, 96))
        bridge = rngs['FINE_BRIDGE'].normal(size=coarse.shape)
        tape.update(coarse.tobytes()); tape.update(bridge.tobytes())
        noise = physics.lift(coarse)
        first, second = physics.lift((a*coarse+bridge)/denom), physics.lift((coarse-a*bridge)/denom)
        before = tuple(v.copy() for v in live[0]) if tick in witness_ticks else None
        live[0] = physics.step(d, *live[0], noise, dt, coupling, center)
        live[1] = physics.step(d, *live[1], first, dt/2, coupling, center)
        live[1] = physics.step(d, *live[1], second, dt/2, coupling, center)
        if before is not None:
            witnesses.append(np.stack((*[physics.coordinates(v) for v in before],
                *[physics.coordinates(v) for v in live[0]], np.broadcast_to(coarse, (2, 2, nodes, 96)))))
        if tick % d.sample_stride == 0:
            for view, (q, p, g) in enumerate(live):
                if not np.isfinite(q).all() or not np.isfinite(g).all(): raise FloatingPointError('SCI02-D nonfinite native path')
                if tick <= burn:
                    arrays['warmup_radial'][view, ..., tick//d.sample_stride-1] = physics.receiver(d, q)
                else:
                    index = (tick-burn)//d.sample_stride-1
                    arrays['positions'][view, ..., index, :] = physics.coordinates(q)
                    arrays['gradients'][view, ..., index, :] = physics.coordinates(g)
                    arrays['observables'][view, ..., index, :] = physics.fields(d, q, g, center)
                    arrays['kinetic_temperature'][view, ..., index] = np.sum(abs(p)**2, axis=(-4, -3, -2, -1))/96
        if progress is not None and tick % 256 == 0: progress(3*tick)
    arrays['witness_ticks'] = np.array(sorted(witness_ticks), dtype='<i8')
    arrays['witnesses'] = np.asarray(witnesses, dtype='<f8')
    raw = json.dumps({'numpy': np.__version__, 'bit_generator': 'PCG64DXSM', 'before': states_before,
        'stream_identities': [s.identity.to_document() for s in streams],
        'after': {k: r.bit_generator.state for k, r in rngs.items()}, 'standard_noise_sha256': tape.hexdigest(),
        'coarse_draw_shape': [burn+horizon, 2, 1, nodes, 96], 'bridge_draw_shape': [burn+horizon, 2, 1, nodes, 96]}, sort_keys=True).encode()
    arrays['random_custody'] = np.frombuffer(raw, dtype='u1').astype('<i8')
    return Computation(arrays, measurements=measurements({'runtime.native_cpu_seconds': time.process_time()-cpu,
        'runtime.native_wall_seconds': time.monotonic()-wall, 'native.force_evaluations': (3*(burn+horizon)+1)*4*nodes,
        'native.burn_force_evaluations': (3*burn+1)*4*nodes, 'native.production_force_evaluations': 3*horizon*4*nodes,
        'native.integration_steps': 3*(burn+horizon)*4*nodes, 'native.retained_states': 8*nodes*count,
        'native.equation_witnesses': len(witness_ticks)*4*nodes}))
