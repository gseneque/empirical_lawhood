"""Native acquisition and external-format binding for the domain science."""

from decimal import Decimal
import hashlib
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import MetricSourceSemantics as _science_MetricSourceSemantics, OfficialMetricGaugeV2 as _science_OfficialMetricGaugeV2, OfficialMetricSetV2 as _science_OfficialMetricSetV2


def correct_historical_crosswired_metrics(
    payload: bytes, *, gauge: _science_OfficialMetricGaugeV2
):
    """Read only the original Arrow contract and produce a separate v2 record.

    Successor canonical records cannot enter this reader, preventing a second
    swap of an already corrected artifact. Optional Arrow dependencies are
    needed only when this explicitly selected historical reader is invoked.
    """
    if type(gauge) is not _science_OfficialMetricGaugeV2:
        raise TypeError("historical correction requires the selected v2 gauge")
    if payload.lstrip().startswith(b"{"):
        raise ValueError(
            "historical crossed reader refuses successor canonical records"
        )
    from empirical_lawhood.adapters.physical.virtual_cell.codecs import decode_official_metrics

    target_ids, old_des, old_pds, mae = decode_official_metrics(payload)
    return _science_OfficialMetricSetV2(
        gauge,
        _science_MetricSourceSemantics.HISTORICAL_CROSSED_V1,
        hashlib.sha256(payload).hexdigest(),
        tuple(target_ids),
        *(
            tuple(Decimal(str(value)) for value in values)
            for values in (old_pds, old_des, mae)
        ),
    )
