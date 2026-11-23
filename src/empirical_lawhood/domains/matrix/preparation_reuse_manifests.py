# SPDX-License-Identifier: MPL-2.0
"""Published identities of the R23–R27 numerical operand manifests."""

from pathlib import Path

MANIFEST_FORMAT = 1
MANIFEST_SCHEMA = f"matrix-preparation-reuse.operand-manifest.v{MANIFEST_FORMAT}"
RELEASE_MANIFESTS = {
    "r23": "a706c66215de527a8bc5336f7d31a058d38fce7c000d440de0b238c41ac7871a",
    "r24": "d9dc7fcf0b49925b0a84bda397d935a71e2f1e9bb19d8b2fe08ecac702b33ea3",
    "r25": "572bcd7a3454fc2af732e25ae5b93435a45f873f8f48957215e8d476f9ec3969",
    "r26": "7641fc6fe16734bbd159e24cb689ccb3f6e5be6f39e37ac5d54a9ec36c300ada",
    "r27": "c869b4b96a39cbcf6331d664e3e3d5ebee6d48502f775b18e6f3befd7dd598a6",
}
STUDIES = tuple(RELEASE_MANIFESTS)
WORKFLOW = Path("programmes/foundations/emergent-structure/workflows/preparation-and-reuse")
