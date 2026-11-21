# SPDX-License-Identifier: MPL-2.0
"""Version negotiation for callback interfaces, separate from scientific schemas."""

from empirical_lawhood.science.records.serialization import validate_semantic_version


EXTENSION_CALLBACK_API_VERSION = "1.0.0"


def require_extension_callback_api(*, minimum: str, maximum_exclusive: str) -> str:
    """Select an explicit supported API range without invoking extension code.

    The selected installed source and record codecs remain independent pins.
    This result neither advertises a lifecycle nor establishes conformance.
    """
    def version(value):
        if type(value) is not str:
            raise TypeError("extension callback API bounds require exact version strings")
        validate_semantic_version(value)
        return tuple(int(part) for part in value.split("."))

    lower, upper = version(minimum), version(maximum_exclusive)
    if not lower < upper:
        raise ValueError("extension callback API range must have a higher exclusive upper bound")
    if not lower <= version(EXTENSION_CALLBACK_API_VERSION) < upper:
        raise ValueError("installed extension callback API is outside the requested compatibility range")
    return EXTENSION_CALLBACK_API_VERSION
