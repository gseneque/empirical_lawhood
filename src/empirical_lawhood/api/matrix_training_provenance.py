# SPDX-License-Identifier: MPL-2.0
"""TRAIN declarations from authenticated fitted products, without array replay.

Callers own current authority and retained product authentication. Bank editions
identify their declared contracts; neither edition establishes data origin,
freshness or scientific qualification by itself.
"""

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as configured
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as legacy
from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_value


def fitted_training_provenance(specification, allocation, models, frozen):
    """Project complete fitted TRAIN denominators after exact model/freeze joins."""
    family = selected_e3_product_family(specification)
    owner = configured if family.configured else legacy
    model_type = owner.ConfiguredProtectedE3ModelSet if family.configured else owner.ProtectedE3ModelSet
    frozen_type = owner.ConfiguredProtectedE3FrozenProducts if family.configured else owner.ProtectedE3FrozenProducts
    if type(models) is not model_type or type(frozen) is not frozen_type:
        raise PermissionError('PROTECTED_E3_READ_EXACT_FITTED_TRAINING_REQUIRED')
    models.__post_init__()
    frozen.__post_init__()
    model_pin = ObjectIdentity.from_record(models.record_id, models)
    units = allocation.unit_ids('train')
    if ((models.specification, models.allocation) != (specification.identity, allocation.identity)
            or (frozen.specification, frozen.allocation) != (specification.identity, allocation.identity)
            or frozen.models != model_pin or frozen.reservation_join != models.reservation_join
            or any(model.training_unit_ids != units for model in models.models)):
        raise PermissionError('PROTECTED_E3_READ_EXACT_FITTED_TRAINING_REQUIRED')
    # The fixed historical scientific family keeps its own original bank pins.
    # It cannot supply banks to the current configured native-only fitter.
    bank_edition = 'NATIVE_BANKS' if family.configured else 'LEGACY_BANKS'
    matched = family.configured and specification.measurement.is_matched
    fit_details = tuple({'method': model.method_key, 'feature_names': model.feature_names,
        'assigned_folds': model.folds, 'common_complete_units': model.complete_group_ids,
        'excluded_units': model.exclusions, 'training_prerequisite_reasons': model.prerequisite_reasons,
        'final_fit': None if model.parameters is None else model.parameters.diagnostics,
        'cross_validation': model.cross_validation, 'fit_attempts': model.fit_attempts} for model in models.models) if matched else ()
    return canonical_value({'bank_edition': bank_edition,
        'evidence_basis': 'FITTED_PRODUCT_BANK_DECLARATIONS',
        'data_origin': 'NOT_REESTABLISHED_BY_THIS_READ',
        'model_set': model_pin, 'allocation': allocation.identity, 'reservation_join': models.reservation_join,
        'feature_bank': models.training_features, 'outcome_bank': models.training_outcomes,
        'assigned_units': len(units), 'units': units,
        'finite_endpoint_counts': tuple((model.method_key, model.finite_counts) for model in models.models),
        **({'matched_fit_details': fit_details} if matched else {})})


def original_comparator_training(public):
    """Propagate the exact original comparator in an authenticated E4 input bank."""
    family = selected_e3_product_family(public.specification)
    if type(public) is not family.public_type:
        raise PermissionError('SELECTED_E4_READ_EXACT_ORIGINAL_COMPARATOR_REQUIRED')
    public.__post_init__()
    return {'original_package': public.original_package.to_document(),
        **fitted_training_provenance(public.specification, public.allocation, public.models, public.calibrated_freeze)}
