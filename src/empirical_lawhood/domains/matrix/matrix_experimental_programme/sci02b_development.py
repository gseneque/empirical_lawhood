# SPDX-License-Identifier: MPL-2.0
"""Bounded SCI02-B development computations and independent result checks."""
from dataclasses import replace
from decimal import Decimal

import numpy as np

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as original_reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import RECIPES
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import Sci02BFrozenDescription


def subset(values, prefix):
    return {name[len(prefix):]: value for name, value in values.items() if name.startswith(prefix)}


def retained_operands(record, values):
    instrument = subset(values, 'instrument.')
    handoffs, observations, native = {}, {}, {}
    for recipe in RECIPES:
        prefix = recipe.lower() + '.'
        handoffs[recipe] = subset(values, prefix + 'handoff.')
        observations[recipe] = subset(values, prefix + 'observation.')
        native[recipe] = subset(values, prefix + 'assess.')
    if any(not x[r] for x in (handoffs, observations, native) for r in RECIPES):
        raise ValueError('SCI02-B retained development omits an original arm')
    return instrument, handoffs, observations, native


def diagnose(config, retained, values):
    if retained.root != config.root or retained.design != config.design:
        raise ValueError('SCI02-B diagnosis substitutes original physical operands')
    instrument, handoffs, observations, native = retained_operands(retained, values)
    if 'forces' not in instrument:
        return original.unavailable('ORIGINAL_SOURCE_INSTRUMENT_UNAVAILABLE')
    arrays, costs, models = {}, {}, {}
    for recipe in RECIPES:
        origin = science.origin_model(config.design, handoffs[recipe], instrument, config.candidate_dimension)
        refreshed = science.refresh_model(config.design, origin.arrays, observations[recipe])
        # The NPZ contract stores C-order values. Assess those same operands so
        # independent residual witnesses do not depend on transient BLAS layout.
        refreshed = replace(refreshed, arrays={k: np.ascontiguousarray(v) for k, v in refreshed.arrays.items()})
        models[recipe] = refreshed.arrays
        prefix = recipe.lower() + '.model.'
        arrays.update({prefix + key: value for key, value in refreshed.arrays.items()})
        arrays[recipe.lower() + '.independent_residuals'] = reader.model_checks(config.design,
            handoffs[recipe], observations[recipe], refreshed.arrays)
        costs.update({recipe + '.' + key: value for key, value in (*origin.measurements, *refreshed.measurements)})
        for view, _ in science.VIEWS:
            previous = values.get(recipe.lower() + '.origin.' + view + '.basis.input_krylov48')
            if previous is not None:
                current = refreshed.arrays[view + '.basis']
                costs[recipe + '.' + view + '.old_projector_distance'] = Decimal(repr(float(
                    np.linalg.norm(previous @ previous.T - current @ current.T))))
    assessed = reader.assess_pair(config.design, native, models)
    arrays.update({'assessment.' + key: value for key, value in assessed.arrays.items()})
    arrays['features'] = science.description({recipe: models[recipe] for recipe in science.PAIR})
    frozen = {recipe: {f'{view}.p{panel}.updated': models[recipe][view + '.frozen']
        for view, _ in science.VIEWS for panel in (0, 1)} for recipe in RECIPES}
    frozen_assessed = reader.assess_pair(config.design, native, frozen)
    measurements = tuple(sorted((*assessed.measurements, *costs.items(),
        *(('frozen.' + key, value) for key, value in frozen_assessed.measurements))))
    return original.Computation(arrays, measurements=measurements)


def verify_diagnosis(config, retained, retained_values, product, arrays):
    """Recheck equations and scalar criteria without producing a new basis."""
    instrument, handoffs, observations, native = retained_operands(retained, retained_values)
    if product.disposition == 'UNAVAILABLE':
        if 'forces' in instrument or product.reasons != ('ORIGINAL_SOURCE_INSTRUMENT_UNAVAILABLE',):
            raise ValueError('SCI02-B unavailable diagnosis has no matching physical reason')
        return
    models = {recipe: subset(arrays, recipe.lower() + '.model.') for recipe in RECIPES}
    for recipe in RECIPES:
        model = models[recipe]
        for key in ('forces', 'receivers'):
            original_reader.same(model[key], instrument[key], 'SCI02-B original fixed instrument')
        for view, _ in science.VIEWS:
            for name in ('positions', 'momenta'):
                original_reader.same(model[view + '.handoff_' + name], handoffs[recipe][view + '_' + name], 'SCI02-B original handoff')
            if model[view + '.basis'].shape[1] > config.candidate_dimension:
                raise ValueError('SCI02-B exceeds its selected representation dimension')
        residuals = reader.model_checks(config.design, handoffs[recipe], observations[recipe], model)
        original_reader.same(arrays[recipe.lower() + '.independent_residuals'], residuals, 'SCI02-B independent equation residuals')
    assessed = reader.assess_pair(config.design, native, models)
    actual = subset(arrays, 'assessment.')
    if set(actual) != set(assessed.arrays):
        raise ValueError('SCI02-B read changes the signed endpoint or finite-contrast census')
    for key, value in assessed.arrays.items():
        original_reader.same(actual[key], value, 'SCI02-B signed finite-error ' + key)
    measured = dict(product.measurements)
    if any(measured.get(k) != v for k, v in assessed.measurements):
        raise ValueError('SCI02-B read changes the independently measured paired criteria')
    original_reader.same(arrays['features'], science.description({r: models[r] for r in science.PAIR}), 'SCI02-B causal description')
    frozen = {recipe: {f'{v}.p{p}.updated': models[recipe][v + '.frozen']
        for v, _ in science.VIEWS for p in (0, 1)} for recipe in RECIPES}
    frozen_assessed = reader.assess_pair(config.design, native, frozen)
    if any(measured.get('frozen.' + k) != v for k, v in frozen_assessed.measurements):
        raise ValueError('SCI02-B read substitutes frozen representation controls')


def selection(products):
    if len(products) != 16 or {(p.config.root.ordinal, p.config.candidate_dimension) for p in products} != {
            (i, d) for i in range(8) for d in (24, 32)}:
        raise ValueError('SCI02-B decision omits an original assigned root or candidate')
    for dimension in (24, 32):
        selected = tuple(sorted((p for p in products if p.config.candidate_dimension == dimension), key=lambda p: p.config.root.ordinal))
        if all(p.disposition == 'AVAILABLE' and dict(p.measurements).get('primary.joint_success') == 1 for p in selected):
            return dimension, selected
    return 0, ()


def fit(config, products, values):
    dimension, selected = selection(tuple(products.values()))
    measurements = {'assigned_roots': Decimal(8), 'assigned_candidates': Decimal(2), 'selected_dimension': Decimal(dimension)}
    for dim in (24, 32):
        measurements[f'd{dim}.passing_roots'] = Decimal(sum(dict(p.measurements).get('primary.joint_success') == 1
            for p in products.values() if p.config.candidate_dimension == dim))
    if not dimension:
        return replace(original.unavailable('NO_SELECTED_REPRESENTATION_MEETS_COMPLETE_DEV8_PAIRED_CRITERIA'),
            measurements=tuple(sorted(measurements.items()))), None
    features = np.stack([values[p.config.node_id]['features'] for p in selected])
    targets = np.asarray([float(dict(p.measurements)['primary.log_risk']) for p in selected], dtype='<f8')
    fitted = science.fit_accounts(features, targets)
    reader.check_fit(features, targets, fitted)
    exact = lambda v: Decimal(repr(float(v)))
    description = Sci02BFrozenDescription('description.' + config.study.fingerprint(), config.study.identity, dimension,
        config.roots, tuple(p.identity for p in selected), tuple(map(exact, fitted['feature_mean'])),
        tuple(map(exact, fitted['feature_scale'])), tuple(tuple(map(exact, row)) for row in fitted['coefficients']),
        tuple(map(exact, fitted['intercepts'])))
    return original.Computation({**fitted, 'training_features': features, 'training_log_risk': targets},
        measurements=tuple(sorted(measurements.items()))), description


def verify_fit(config, products, values, product, arrays):
    dimension, selected = selection(tuple(products.values()))
    if not dimension:
        if (product.disposition != 'UNAVAILABLE' or product.frozen_description is not None
                or product.reasons != ('NO_SELECTED_REPRESENTATION_MEETS_COMPLETE_DEV8_PAIRED_CRITERIA',)):
            raise ValueError('SCI02-B frozen fit ignores its bounded representation stop')
        return
    description = product.frozen_description
    if description is None or description.dimension != dimension or description.diagnosis_products != tuple(p.identity for p in selected):
        raise ValueError('SCI02-B fit changes the original selected complete training population')
    features = np.stack([values[p.config.node_id]['features'] for p in selected])
    targets = np.asarray([float(dict(p.measurements)['primary.log_risk']) for p in selected], dtype='<f8')
    original_reader.same(arrays['training_features'], features, 'SCI02-B training descriptions')
    original_reader.same(arrays['training_log_risk'], targets, 'SCI02-B original development targets')
    reader.check_fit(features, targets, description.numerical_arrays())
    for key, expected in description.numerical_arrays().items():
        original_reader.same(arrays[key], expected, 'SCI02-B exact frozen coefficients')
