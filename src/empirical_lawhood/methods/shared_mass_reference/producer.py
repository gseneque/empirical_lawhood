# SPDX-License-Identifier: MPL-2.0
"""Forecast owner borrows common scope without receiving observed outcomes."""

from empirical_lawhood.methods.shared_mass_reference.provider import ScopeBoundProvider


class MassForecastProvider(ScopeBoundProvider):
    CAPABILITY = 'mass-balance.predict'
