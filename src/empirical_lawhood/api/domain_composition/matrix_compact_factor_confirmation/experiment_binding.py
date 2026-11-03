# SPDX-License-Identifier: MPL-2.0
"""Compact E1 uses the ordinary protected lifecycle and a lazy retained reader."""
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_preparation import PROTOCOL_ID,E1CompactExperimentSpecification,selection_types
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def bind_handoff(handoff,*,specification,allocation,source_records,artifact_writer,reveal_authority_id=None):
    # The common loader has authenticated/validated the complete actual companion
    # and ordinary root. Preserve its supplier, current grants and native ports.
    if type(specification) is not E1CompactExperimentSpecification:raise TypeError('compact E1 handoff requires its exact specification')
    selections=tuple(value for _,value in source_records if type(value) in selection_types())
    if len(selections)!=1 or selections[0].identity!=specification.selection or tuple(row.root.root_id for row in selections[0].manifest.reservation.allocation.roots)!=specification.root_ids:
        raise PermissionError('compact E1 handoff changes exact actual frozen selection/root census')
    return handoff


def read_result(**kwargs):
    from empirical_lawhood.api.matrix_factor_confirmation_compact_read import read_result as read
    return read(**kwargs)


def prepare_authoring(*args,**kwargs):
    from empirical_lawhood.api.matrix_factor_confirmation_compact_authoring import prepare_authoring as prepare
    return prepare(*args,**kwargs)


def derive_prospective_design_inputs(preparation):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_preparation import derive_design_inputs
    return derive_design_inputs(preparation)


EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,bind_handoff,read_result=read_result,prepare_authoring=prepare_authoring,
    derive_prospective_design_inputs=derive_prospective_design_inputs,specification_schema=E1CompactExperimentSpecification.SCHEMA)
