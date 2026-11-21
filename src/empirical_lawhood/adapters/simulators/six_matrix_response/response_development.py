"""Native acquisition and external-format binding for the domain science."""

from typing import Callable, cast

from empirical_lawhood.domains.matrix.six_matrix_response.response_development import (
    ResponseGeometryDevelopmentNativeConfig as _science_ResponseGeometryDevelopmentNativeConfig,
    ResponseGeometryDevelopmentNativeSegment as _science_ResponseGeometryDevelopmentNativeSegment,
    ResponseGeometryDevelopmentNativeSegmentResult as _science_ResponseGeometryDevelopmentNativeSegmentResult,
)

def execute_development_segment(
    config: _science_ResponseGeometryDevelopmentNativeConfig,
    segment: _science_ResponseGeometryDevelopmentNativeSegment,
    predecessor: _science_ResponseGeometryDevelopmentNativeSegmentResult | None,
    *,
    progress: Callable[[int], None] | None = None,
) -> tuple[_science_ResponseGeometryDevelopmentNativeSegmentResult, bytes]:
    from empirical_lawhood.adapters.simulators.six_matrix_response.response_source import _execute_response_segment

    if type(config) is not _science_ResponseGeometryDevelopmentNativeConfig or type(segment) is not _science_ResponseGeometryDevelopmentNativeSegment:
        raise ValueError("development execution requires its exact development config and segment types")
    result, payload = _execute_response_segment(
        config, segment, predecessor, progress=progress
    )
    return cast(_science_ResponseGeometryDevelopmentNativeSegmentResult, result), payload
