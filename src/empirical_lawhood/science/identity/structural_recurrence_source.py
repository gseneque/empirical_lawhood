"""Pure source-census identities for the bounded structural-recurrence method."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id, validate_nonempty, validate_sha256

@dataclass(frozen=True, slots=True)
class MarginStructuralRecurrenceForecastFrozenSourceFile(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/margin-structural-recurrence-forecast-frozen-source-file'

    source_id: str
    repository_path: str
    sha256: str

    def __post_init__(self) -> None:
        validate_stable_id(self.source_id, field_name="source_id")
        validate_nonempty(self.repository_path, field_name="repository_path")
        validate_sha256(self.sha256, field_name="sha256")
        if (
            self.repository_path.startswith(("/", "."))
            or ".." in self.repository_path.split("/")
            or not self.repository_path.startswith("src/empirical_lawhood/methods/")
        ):
            raise ValueError('frozen structural recurrence source path escapes the method package')


_METHOD_FILES = (
    "structural_recurrence.py",
    "structural_recurrence_targets.py",
    "action_fiber_structural_recurrence.py",
    "action_fiber_structural_recurrence_conformance.py",
    "margin_structural_recurrence_forecast.py",
    "margin_structural_recurrence_conformance.py",
    "structural_bootstrap_inputs.py",
)


@dataclass(frozen=True, slots=True)
class MarginStructuralRecurrenceForecastMethodSourceManifest(CanonicalRecord):
    'Current target source bytes of the structural forecast method.'

    SCHEMA: ClassVar[str] = 'empirical-lawhood/methods/margin-structural-recurrence-forecast-method-source-manifest'

    manifest_id: str
    source_files: tuple[MarginStructuralRecurrenceForecastFrozenSourceFile, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.manifest_id, field_name="manifest_id")
        require_sorted_unique_ids(
            self.source_files, attribute="source_id", field_name="source_files"
        )
        expected = {
            f"src/empirical_lawhood/methods/{name}" for name in _METHOD_FILES
        }
        if {row.repository_path for row in self.source_files} != expected:
            raise ValueError('structural recurrence method source roster differs from the shipped package')

