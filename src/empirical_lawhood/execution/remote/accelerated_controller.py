# SPDX-License-Identifier: MPL-2.0
"""Pinned controller source inspection with no provider construction or contact."""


SKYPILOT_VERSION = '1.0.0.dev20261103'
SKYPILOT_COMMIT = '796c5bcc8041a9dcf92c1182fabbafd9a5ab9ed2'
RUNPOD_ACCELERATOR_MEMORY_GB = {
    'A100-80GB': 80, 'A100-80GB-SXM': 80,
    'H100': 80, 'H100-SXM': 80, 'H100-NVL': 94, 'H200-SXM': 141,
    'B200': 180, 'RTXPRO6000': 96, 'RTXPRO6000-WK': 96,
}
SKYPILOT_RUNPOD_FILES = {
    'sky/adaptors/runpod.py': '243f0e35047e3c85e0170aa2e97ba7eb1c76930e053a8a3c17d56ad3544d6e21',
    'sky/provision/runpod/utils.py': 'd3c4af278036efdd21e8a7d8cfd856a6ac3b7342718768a4b8bed82a31f4bf45',
    'sky/provision/runpod/instance.py': '001bdecd654043464a165d9282f5cdd4b19fae2bef90b7bf4a75cc955da9288f',
    'sky/clouds/runpod.py': '7159eade5ff3e356a6209587ca31f93e7802844e1b3f70641b7890f27ce0f4a0',
    'sky/templates/runpod-ray.yml.j2': 'eb5057ac8eb58621fabac7ad9a35b8a927e4dd9f28c5814810c87c79988f6b7d',
}


SKYPILOT_RUNPOD_DETAIL_PATCH = {
    'name': 'runpod-pod-detail',
    'path': 'sky/provision/runpod/utils.py',
    'sha256': '34095aa57b51c83385a3a491f08f1acb5d77fc08ab8d162f44a290abe1b33e22',
    'patch_sha256': '607fb462cf8654a93ce70a5d9a68183903f331472ddf448be7d1384c744dde20',
}
