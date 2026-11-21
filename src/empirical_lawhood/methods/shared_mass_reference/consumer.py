# SPDX-License-Identifier: MPL-2.0
"""Independent assessor borrows the same immutable scope under its own inputs."""

from empirical_lawhood.methods.shared_mass_reference.provider import ScopeBoundProvider


class MassAssessmentProvider(ScopeBoundProvider):
    CAPABILITY = 'mass-balance.assess'
