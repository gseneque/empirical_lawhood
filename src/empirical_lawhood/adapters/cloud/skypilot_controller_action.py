# SPDX-License-Identifier: MPL-2.0
"""Narrow subprocess entry in the separately selected pinned SkyPilot interpreter."""

import argparse
from pathlib import Path
from hashlib import sha256
import json

from empirical_lawhood.execution.remote.accelerated_controller import SKYPILOT_RUNPOD_FILES, SKYPILOT_RUNPOD_DETAIL_PATCH
from empirical_lawhood.adapters.cloud.skypilot_installation import verify_controller_installation
from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.execution.remote.deployment_supervision_selection import SupervisionSelection


def require_cluster_identity(selected, record):
    allocation = selected.allocation
    if (record is None or record['name'] != allocation.cluster_name
            or record['cluster_hash'] != allocation.cluster_hash
            or str(record['handle'].launched_resources.cloud).lower() != 'runpod'):
        raise ValueError('upstream cluster does not bind the selected original pod and cluster generation')
    # SkyPilot's public handle instance_ids are node IDs ("<pod>-0"),
    # not provider Pod IDs. Use its original provider census and verify the
    # corresponding single head node as well; never strip an arbitrary suffix.
    handle = record['handle']
    info = handle.cached_cluster_info
    if (info is None or info.head_instance_id != allocation.pod_id
            or set(info.instances) != {allocation.pod_id}
            or len(info.instances[allocation.pod_id]) != 1
            or info.instances[allocation.pod_id][0].instance_id != allocation.pod_id
            or tuple(handle.instance_ids or ()) != (allocation.pod_id+'-0',)):
        raise ValueError('upstream cluster does not bind exactly one selected original provider pod and head node')


def act(selection_path, action, *, expected_selection_sha256=None):
    raw = read_bounded_bytes(Path(selection_path), maximum_bytes=128*1024)
    if expected_selection_sha256 is not None and sha256(raw).hexdigest() != expected_selection_sha256:
        raise ValueError('controller action changes the original supervision selection bytes')
    selected = SupervisionSelection.from_document(json.loads(raw))
    selected.require_authorization()
    if action not in ('cancel', 'retire'):
        raise ValueError('unsupported financial lifecycle action')
    verify_controller_installation()
    import sky
    from sky import core, global_user_state
    # PYTHONPATH may select the separately retained detail correction. Check the
    # actually imported sources as well as the installed distribution metadata.
    root = Path(sky.__file__).resolve().parent.parent
    for name, expected in SKYPILOT_RUNPOD_FILES.items():
        digest = bounded_file_sha256(root/name, maximum_bytes=2**20)[1]
        allowed = {expected}
        if name == SKYPILOT_RUNPOD_DETAIL_PATCH['path']:
            allowed.add(SKYPILOT_RUNPOD_DETAIL_PATCH['sha256'])
        if digest not in allowed:
            raise ValueError('actual controller source differs from the selected upstream binding')
    # Immutable allocation generation and provider ID are checked immediately
    # before calling the existing owner. No wildcard or forced purge is used.
    require_cluster_identity(selected, global_user_state.get_cluster_from_name(selected.allocation.cluster_name))
    selected.require_authorization()
    if action == 'cancel':
        core.cancel(selected.allocation.cluster_name, all=True, all_users=False)
    else:
        core.down(selected.allocation.cluster_name, purge=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--action', choices=('cancel', 'retire'), required=True)
    parser.add_argument('--expected-selection-sha256')
    args = parser.parse_args()
    act(args.selection, args.action, expected_selection_sha256=args.expected_selection_sha256)
