# SPDX-License-Identifier: MPL-2.0
"""Pure monetary policy for an explicitly selected remote allocation.

These operational records grant no authority and impose no scientific deadline.
Provider I/O, owner authorization and upstream lifecycle actions stay outside.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
from fractions import Fraction
import re


def money(value):
    if type(value) is not str or len(value) > 100:
        raise ValueError('money requires a bounded exact Decimal string')
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('money requires a Decimal string') from error
    if not number.is_finite() or number < 0 or abs(number.as_tuple().exponent) > 100:
        raise ValueError('money must be finite, nonnegative and bounded')
    return Fraction(number)


def usd_upper(value):
    """Round only the displayed accounting result, conservatively to a picodollar."""
    with localcontext() as context:
        context.prec = 250
        context.rounding = ROUND_CEILING
        return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal('0.000000000001')))


def utc(value):
    if type(value) is not str:
        raise ValueError('observation time requires an explicit UTC string')
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise ValueError('observation time requires explicit UTC')
    return result


def seconds(start, end):
    delta = end-start
    return Fraction((delta.days*86400+delta.seconds)*1000000+delta.microseconds, 1000000)


def identity(value):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_-]+', value) is None:
        raise ValueError('allocation requires an explicit stable resource identity')


@dataclass(frozen=True, slots=True)
class DeploymentBudget:
    total_usd: str
    return_reserve_usd: str
    retirement_margin_usd: str
    previous_attempts_usd: str
    compute_hourly_usd: str
    container_hourly_upper_usd: str
    volume_hourly_upper_usd: str
    accounting_floor_usd: str = '0'
    poll_seconds: int = 30
    request_timeout_seconds: int = 20
    action_timeout_seconds: int = 180

    def __post_init__(self):
        for name in ('total_usd', 'return_reserve_usd', 'retirement_margin_usd', 'previous_attempts_usd',
                'compute_hourly_usd', 'container_hourly_upper_usd', 'volume_hourly_upper_usd', 'accounting_floor_usd'):
            money(getattr(self, name))
        if any(type(v) is not int or not 1 <= v <= 600 for v in (
                self.poll_seconds, self.request_timeout_seconds, self.action_timeout_seconds)):
            raise ValueError('supervision requires bounded positive observation and action timeouts')
        if not 0 < money(self.retirement_margin_usd) < money(self.return_reserve_usd) < money(self.total_usd):
            raise ValueError('select a positive retirement margin below the return reserve and total cap')
        if money(self.compute_hourly_usd) <= 0:
            raise ValueError('select the actual positive compute rate')
        # Three provider reads plus one lifecycle request can delay a stop.
        delay = self.poll_seconds+3*self.request_timeout_seconds+self.action_timeout_seconds
        headroom = Fraction(delay, 3600)*(money(self.compute_hourly_usd)+money(self.container_hourly_upper_usd))
        headroom += (delay//3600+2)*money(self.volume_hourly_upper_usd)
        if money(self.retirement_margin_usd) < headroom:
            raise ValueError('retirement margin does not cover the selected supervision latency estimate')


@dataclass(frozen=True, slots=True)
class DeploymentAllocation:
    deployment_id: str
    cluster_name: str
    cluster_hash: str
    pod_id: str
    pod_name: str
    volume_id: str
    volume_mount: str
    zone: str
    compute_started_utc: str
    volume_accounting_started_utc: str
    budget: DeploymentBudget

    def __post_init__(self):
        from pathlib import PurePosixPath
        for name in ('deployment_id', 'cluster_name', 'cluster_hash', 'pod_id', 'pod_name', 'volume_id', 'zone'):
            identity(getattr(self, name))
        mount = PurePosixPath(self.volume_mount)
        if not mount.is_absolute() or '..' in mount.parts or str(mount) != self.volume_mount or str(mount) == '/':
            raise ValueError('select the actual normalized persistent mount')
        utc(self.compute_started_utc)
        utc(self.volume_accounting_started_utc)
        if type(self.budget) is not DeploymentBudget:
            raise TypeError('allocation requires the shared monetary policy')
        self.budget.__post_init__()

    @classmethod
    def from_document(cls, document):
        values = dict(document)
        if values.pop('version', None) != '1.0.0':
            raise ValueError('unsupported deployment allocation revision')
        values['budget'] = DeploymentBudget(**values['budget'])
        return cls(**values)

    def to_document(self):
        return {'version': '1.0.0', **asdict(self)}


def account_deployment(allocation, *, observed_utc, pod_billed_usd, volume_billed_usd,
                       previous_accounted_usd='0', science_stopped=False):
    """Cover delayed billing, every selected storage bucket and earlier attempts.

The maximum is per resource, then summed. Accounting cannot fall when provider
billing lags, revisions decrease, or a previously returned reading was larger.
"""
    if type(allocation) is not DeploymentAllocation:
        raise TypeError('accounting requires the selected allocation')
    allocation.__post_init__()
    now = utc(observed_utc)
    start = utc(allocation.compute_started_utc)
    volume_start = utc(allocation.volume_accounting_started_utc)
    if now < start or now < volume_start:
        raise ValueError('observation precedes the selected allocation')
    policy = allocation.budget
    hours = seconds(start, now)/3600
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    first = seconds(epoch, volume_start)//3600
    last = -(-seconds(epoch, now)//3600)
    volume_hours = max(0, last-first)
    pod_upper = hours*(money(policy.compute_hourly_usd)+money(policy.container_hourly_upper_usd))
    volume_upper = volume_hours*money(policy.volume_hourly_upper_usd)
    total = max(money(previous_accounted_usd), money(policy.accounting_floor_usd), money(policy.previous_attempts_usd)
        + max(money(pod_billed_usd), pod_upper)+max(money(volume_billed_usd), volume_upper))
    science_threshold = money(policy.total_usd)-money(policy.return_reserve_usd)
    retirement_threshold = money(policy.total_usd)-money(policy.retirement_margin_usd)
    status = ('RETIRE_COMPUTE' if total >= retirement_threshold else
        'STOP_SCIENCE_RETURN_ONLY' if science_stopped or total >= science_threshold else 'CONTINUE')
    return {'status': status, 'observed_utc': observed_utc, 'accounted_usd': usd_upper(total),
        'remaining_usd': usd_upper(money(policy.total_usd)-total),
        'pod_elapsed_upper_usd': usd_upper(pod_upper), 'volume_bucket_upper_usd': usd_upper(volume_upper),
        'volume_billing_hours_upper': volume_hours, 'pod_billed_usd': pod_billed_usd,
        'volume_billed_usd': volume_billed_usd, 'previous_attempts_usd': policy.previous_attempts_usd,
        'science_stop_usd': usd_upper(science_threshold), 'retirement_threshold_usd': usd_upper(retirement_threshold),
        'native_deadline': None, 'native_work_dispatched': False, 'automatic_replay': False}
