# SPDX-License-Identifier: MPL-2.0
"""Lossless domain operands for unchanged durable native-call custody."""

from decimal import Decimal

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import DurableCallLedger


def request_values(value):
    """Keep scientific Decimal spellings instead of a binary float conversion."""
    if type(value) is Decimal:
        return {"decimal":str(value)}
    if isinstance(value,(tuple,list)):
        return [request_values(row) for row in value]
    if type(value) is dict:
        return {key:request_values(row) for key,row in value.items()}
    return value


class ChemicalForceLedger(DurableCallLedger):
    def call(self, role, request, function, *, realization=None, files=()):
        return super().call(role,request_values(request),function,realization=realization,files=files)
