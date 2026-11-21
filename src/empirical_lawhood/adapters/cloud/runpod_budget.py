# SPDX-License-Identifier: MPL-2.0
"""Bounded Runpod billing observations behind the deployment observation port."""

from datetime import datetime, timezone
from decimal import Decimal
import json
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from empirical_lawhood.storage.transfer_files import encode_document as _encode
from empirical_lawhood.execution.deployment_budget import money
from empirical_lawhood.storage.artifact_replication import _durable_bytes


class RunpodBudgetObserver:
    """GET only, resource-filtered, bounded and separately retained original responses."""

    def __init__(self, selection, *, credential, opener=urlopen):
        self.selection, self.credential, self.opener = selection, credential, opener
        if not credential:
            raise ValueError('RUNPOD_API_KEY is absent from the selected environment')

    def get(self, endpoint, parameters, output, *, absent_ok=False):
        url = 'https://api.runpod.io/v2/'+endpoint+('?' + urlencode(parameters) if parameters else '')
        try:
            with self.opener(Request(url, headers={'Authorization': 'Bearer '+self.credential}),
                    timeout=self.selection.allocation.budget.request_timeout_seconds) as response:
                raw = response.read(8*2**20+1)
        except HTTPError as error:
            if error.code == 404 and absent_ok:
                _durable_bytes(output, _encode({'http_status': 404, 'url': url}))
                return None
            raise RuntimeError(f'provider observation failed with HTTP {error.code}') from None
        if len(raw) > 8*2**20:
            raise ValueError('provider response exceeds its selected observation bound')
        _durable_bytes(output, raw)
        return json.loads(raw, parse_float=Decimal)

    def require_volume(self, output):
        selected = self.selection.allocation
        volume = self.get('network-volumes/'+quote(selected.volume_id, safe=''), {}, output)
        if volume['id'] != selected.volume_id or volume['dataCenter'] != selected.zone:
            raise ValueError('retained volume identity or datacenter changed')

    def observe(self, output):
        selected = self.selection.allocation
        pod = self.get('pods/'+quote(selected.pod_id, safe=''), {}, output/'pod.json', absent_ok=True)
        if pod is None:
            self.require_volume(output/'retained-volume.json')
            return {'status': 'COMPUTE_ABSENT_VOLUME_RETAINED'}
        if (pod['id'] != selected.pod_id or pod['name'] != selected.pod_name
                or pod['dataCenterId'] != selected.zone
                or money(str(pod['cost'])) != money(selected.budget.compute_hourly_usd)
                or pod['mounts']['network'] != [{'path': selected.volume_mount, 'volumeId': selected.volume_id}]):
            raise ValueError('actual pod, compute rate or retained-volume binding changed')
        now = datetime.now(timezone.utc).isoformat()
        billing = {}
        for name, endpoint, identity, start in (
                ('pod', 'billing/pods', {'podId': selected.pod_id}, selected.compute_started_utc),
                ('volume', 'billing/network-volumes', {'networkVolumeId': selected.volume_id}, selected.volume_accounting_started_utc)):
            data = self.get(endpoint, {**identity, 'startTime': start, 'endTime': now, 'bucketSize': 'hour'},
                output/(name+'-billing.json'))
            billing[name+'_billed_usd'] = str(data['metadata']['totals']['totalAmount'])
            money(billing[name+'_billed_usd'])
        return {'status': 'OBSERVED', 'observed_utc': datetime.now(timezone.utc).isoformat(), **billing}


