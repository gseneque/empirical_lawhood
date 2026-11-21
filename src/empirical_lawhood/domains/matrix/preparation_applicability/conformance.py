"""Native acquisition and external-format binding for the domain science."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.input_contracts import MatrixRootAllocation
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id, validate_sha256

@dataclass(frozen=True,slots=True)
class PreparationApplicabilityNativeConformance(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/preparation-applicability/native-conformance"
    conformance_id: str
    implementation: ObjectIdentity
    python_version: str
    numpy_version: str
    cells: tuple[tuple[str,int,int,str],...]
    allocation_sha256s: tuple[str,...]
    allocations: tuple[MatrixRootAllocation,...]
    ceiling: str="SOFTWARE_CONFORMANCE_NOT_SCIENTIFIC_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.conformance_id)
        for digest in self.allocation_sha256s:
            validate_sha256(digest)
        expected=tuple((cohort,view) for cohort in ("q2","cir1","constructed") for view in (1,2))
        if (tuple((row[0],row[1]) for row in self.cells)!=expected
            or any(row[2]!=16*row[1] or row[3]!="COMPLETE" for row in self.cells)
            or len(set(self.allocation_sha256s))!=3
            or tuple(root.cohort for root in self.allocations)!=("q2","cir1","constructed")
            or self.allocation_sha256s!=tuple(root.fingerprint() for root in self.allocations)
            or self.implementation.object_schema!="empirical-lawhood/preparation-applicability/native-implementation"
            or self.ceiling!="SOFTWARE_CONFORMANCE_NOT_SCIENTIFIC_QUALIFICATION"):
            raise ValueError("native conformance omits its actual source/view cells")


def reject_conformance_reuse(stage,conformance):
    """Actual short native checks expose their own root/stream allocations."""
    exposed={(seed.generator,seed.effective_seed) for root in conformance.allocations for seed in root.scientific_seeds}
    current={(seed.generator,seed.effective_seed) for root in stage.allocation.roots for seed in root.scientific_seeds}
    if stage.allocation.bootstrap_seed is not None:
        current.add(("PCG64",stage.allocation.bootstrap_seed))
    if (current&exposed or {root.root_id for root in stage.allocation.roots}&{root.root_id for root in conformance.allocations}):
        raise ValueError("current preparation reuses actually exposed native-conformance roots or effective streams")
