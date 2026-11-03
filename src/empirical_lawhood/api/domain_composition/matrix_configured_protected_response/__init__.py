# SPDX-License-Identifier: MPL-2.0


def materialize_configured_protected_e3_inputs(**kwargs):
    """Public SDK input derivation; see the configured protected guide."""
    from .derivation import materialize_configured_protected_e3_inputs as materialize
    return materialize(**kwargs)
