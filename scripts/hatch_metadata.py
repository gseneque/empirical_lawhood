# SPDX-License-Identifier: MPL-2.0
"""Point installed recipients to the instructions for their exact source."""

import json
from pathlib import Path
import runpy

from hatchling.metadata.plugin.interface import MetadataHookInterface


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata):
        owner = runpy.run_path(str(Path(self.root) / "scripts/build_source_metadata.py"))
        source = json.loads(owner["build_source_metadata"](self.root))
        metadata["urls"] = owner["project_urls"](source["implementation_commit"])
