# SPDX-License-Identifier: MPL-2.0
"""Explicit lossless conversion; the result checks it independently with fractions."""

from decimal import Decimal, localcontext

from empirical_lawhood.methods.mass_balance_revision.records import ForecastUpgradeConfig, ForecastUpgradeSource, GramPrediction, MassForecastV2


def convert(config, source):
    if type(config) is not ForecastUpgradeConfig or type(source) is not ForecastUpgradeSource:
        raise TypeError('forecast conversion requires its exact selected source and configuration')
    config.__post_init__()
    source.__post_init__()
    if config.specification.source != source.identity:
        raise ValueError('forecast conversion substitutes the selected original source')
    with localcontext() as context:
        context.prec = 100
        rows = tuple(GramPrediction(row.unit_id, row.final_kg,
            row.final_kg.scaleb(3) if row.final_kg else Decimal(0)) for row in source.forecast.rows)
    return MassForecastV2(config.node_id + '.product', config, source, rows)
