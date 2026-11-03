# SPDX-License-Identifier: MPL-2.0
"""Carry the same ordinary source metadata through sdist and wheel builds."""

from pathlib import Path
import runpy
from tempfile import TemporaryDirectory

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        owner = runpy.run_path(str(Path(self.root) / "scripts/build_source_metadata.py"))
        self._source_metadata_directory = TemporaryDirectory(prefix="el-build-source-")
        path = Path(self._source_metadata_directory.name) / owner["SOURCE_METADATA_FILENAME"]
        path.write_bytes(owner["build_source_metadata"](self.root))
        if self.target_name == "sdist":
            build_data["force_include"][str(path)] = owner["SOURCE_METADATA_FILENAME"]
        elif self.target_name == "wheel":
            build_data["extra_metadata"][str(path)] = "source.json"

    def finalize(self, version, build_data, artifact_path):
        self._source_metadata_directory.cleanup()
