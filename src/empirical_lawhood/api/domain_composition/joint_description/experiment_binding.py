# SPDX-License-Identifier: MPL-2.0
"""Retained original results through the ordinary public investigation service."""
from empirical_lawhood.design.joint_description import PROTOCOL_ID,JointSpecification
from empirical_lawhood.execution.experiment_preparation import ExperimentRuntimeBinding
from empirical_lawhood.api.joint_description import read_result

EXPERIMENT_RUNTIME_BINDING=ExperimentRuntimeBinding(PROTOCOL_ID,None,
    read_development_result=read_result,specification_schema=JointSpecification.SCHEMA)
