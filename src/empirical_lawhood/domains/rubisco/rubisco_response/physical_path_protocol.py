# SPDX-License-Identifier: MPL-2.0
"""Select existing unbiased path mechanics without altering original records."""

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import ReferenceTrajectoryConfig, AcceleratedReferenceTrajectoryConfig, ReferenceTrajectoryResult, capability_for as trajectory_capability
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import ReferenceEquilibriumConfig, AcceleratedReferenceEquilibriumConfig, ReferenceEquilibriumResult, capability_for as equilibrium_capability


def stochastic_path(config):
    if type(config) in (ReferenceTrajectoryConfig,AcceleratedReferenceTrajectoryConfig):
        trajectory_capability(config)
        return False
    if type(config) in (ReferenceEquilibriumConfig,AcceleratedReferenceEquilibriumConfig):
        equilibrium_capability(config)
        return True
    raise TypeError('physical path requires its exact supported original trajectory configuration')


def physical_settings(config):
    return config.selection.settings.dynamics if stochastic_path(config) else config.selection.settings


def original_result_kind(config):
    return ReferenceEquilibriumResult if stochastic_path(config) else ReferenceTrajectoryResult


def read_physical_phase(config,representation,phase_bytes):
    if stochastic_path(config):
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import read_equilibrium_phase_space, validate_equilibrium_prototype
        validate_equilibrium_prototype(config.selection,config.original.selection)
        return read_equilibrium_phase_space(config.selection,representation,phase_bytes)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space, validate_trajectory_prototype
    validate_trajectory_prototype(config.selection,config.original.selection)
    return read_phase_space(config.selection,representation,phase_bytes)


def validate_path_model(config,ensemble):
    stochastic=stochastic_path(config)
    if stochastic != (ensemble.dynamics_model=='DECLARED_UNBIASED_LANGEVIN'):
        raise ValueError('physical path substitutes its selected NVE or declared stochastic dynamical model')
    if stochastic:
        selected,settings=config.selection,config.selection.settings
        if (selected.window is not None or selected.convention is not None
                or settings.bias_window is not None or settings.bias_convention is not None
                or settings.discard_initial_steps != 0 or settings.sample_interval_steps != 1
                or settings.temperature_kelvin != ensemble.temperature_kelvin
                or settings.friction_per_picosecond != ensemble.friction_per_picosecond):
            raise ValueError('physical stochastic path requires every unbiased frame and its declared bath without discarded time')


def read_physical_path(*,config,**kwargs):
    if stochastic_path(config):
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_read import read_reference_equilibrium
        return read_reference_equilibrium(config=config,verify_random_stream=True,**kwargs)
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_read import read_reference_trajectory
    return read_reference_trajectory(config=config,**kwargs)


def complete_horizon(config,assessment):
    return assessment['selected_sampling_horizon_complete' if stochastic_path(config) else 'selected_horizon_complete']


def mechanics_prefix_acceptable(config,assessment):
    return config.selection.criteria is not None and not set(assessment['findings'])-{
        'selected-physical-horizon-incomplete','selected-sampling-horizon-incomplete'}
