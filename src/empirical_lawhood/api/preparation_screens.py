"""Ordinary32D/64E panel exports and their two exposed development screens."""

import json
from pathlib import Path

from empirical_lawhood.domains.matrix.preparation_applicability.screen_analysis import reduce_ordinary_panels, validate_screen_input, ordinary_screen_analysis

from empirical_lawhood.api.finite_operands import saved_matrix_arrays_export, saved_matrix_arrays_import, _read_selected
from empirical_lawhood.api.authoring_output import report_incomplete_output
from empirical_lawhood.domains.matrix.preparation_applicability.config import PreparationApplicabilityStage
from empirical_lawhood.domains.matrix.preparation_applicability.readout import PreparationApplicabilityScreenReport
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.task_records import artifact_identity
from empirical_lawhood.api.preparation_result_access import authenticate_preparation_input


def ordinary_preparation_operands_export(*, stage, original_f, panels, destination: Path, artifact_writer):
    """Authenticate and reduce all assigned ordinary native panels without fitting."""
    if not isinstance(artifact_writer,ExternalArtifactPlane):
        raise TypeError("ordinary panel export requires the actual guarded custody plane")
    if ".." in destination.parts or any(path.is_symlink() for path in (destination,*destination.parents)):
        raise ValueError("ordinary panel export refuses parent traversal and symbolic links")
    destination=destination.absolute()
    guarded=Path(artifact_writer.root.contract.canonical_path)
    if not destination.is_relative_to(guarded):
        raise ValueError("ordinary panel export must stay under its selected guarded custody root")
    artifact_writer.root.resolve(destination.relative_to(guarded).as_posix(),for_write=True)
    if not destination.is_dir() or any(destination.iterdir()):
        raise FileExistsError("ordinary operands require an explicitly selected empty directory")
    receipts = ExternalTaskReceiptStore(artifact_writer)
    for value in panels:
        authenticate_preparation_input(value, artifact_writer, receipts)
    arrays, summary = reduce_ordinary_panels(stage, original_f, panels)
    with report_incomplete_output(destination):
        for name,record in (("stage.canonical.json",stage),("screen-report.canonical.json",summary)):
            with (destination/name).open("xb") as handle:
                handle.write(record.canonical_bytes())
        result=saved_matrix_arrays_export(destination,operand_id=f"{stage.config_id}.screen-operands",
            allocation=stage.allocation,arrays=arrays,
            producers=(ObjectIdentity.from_record(stage.config_id,stage),ObjectIdentity.from_record(f"{stage.config_id}.report",summary)),
            source_artifacts=tuple(artifact_identity(manifest,role="ordinary-native-panel") for value in panels for manifest in value.manifests),
            source_receipts=tuple(ObjectIdentity.from_record(receipt.receipt_id,receipt) for value in panels for receipt in value.receipts),
            original_f=original_f.identity)
    return result


def ordinary_preparation_screens(*, development_directory: Path,evaluation_directory: Path,
                                  original_f,output_dir: Path):
    """Run finite-menu headroom on E64 and whole-root LOO nomination on D32+E64."""
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError("ordinary screen output must use a fresh directory")
    retained=[]
    for directory,count,phase in ((development_directory,32,"D"),(evaluation_directory,64,"E")):
        manifest,allocation,arrays=saved_matrix_arrays_import(directory/"arrays.canonical.json",arrays_path=directory/"arrays.npz",allocation_path=directory/"allocation.canonical.json")
        stage=decode_canonical_bytes(_read_selected(directory/"stage.canonical.json",maximum_bytes=4*1024**2),PreparationApplicabilityStage,maximum_bytes=4*1024**2)
        summary=decode_canonical_bytes(_read_selected(directory/"screen-report.canonical.json",maximum_bytes=4*1024**2),PreparationApplicabilityScreenReport,maximum_bytes=4*1024**2)
        validate_screen_input(manifest, allocation, arrays, stage, summary, count, phase, original_f)
        retained.append((manifest,allocation,arrays))
    result = ordinary_screen_analysis(retained, original_f)
    output_dir.mkdir(parents=True,exist_ok=False)
    with report_incomplete_output(output_dir):
        with (output_dir/"ordinary-screens.json").open("xb") as handle:
            handle.write((json.dumps(result,sort_keys=True,allow_nan=False)+"\n").encode())
    return result
