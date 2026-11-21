# SPDX-License-Identifier: MPL-2.0
"""Exchange selected development certificates between two explicit local stores."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationContext
from empirical_lawhood.api.knowledge_certificate_types import knowledge_certificate_descriptors, development_certificate_access
from empirical_lawhood.api.knowledge_store import KnowledgeObjectSource, KnowledgeStore, create_knowledge_transfer
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.guarded_catalog import select_operator_catalog
from empirical_lawhood.science.records.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate, KnowledgeCertificateNotice
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.knowledge_store import ScientificTypeRegistry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    for name in ("source-operator-profile", "store-a-operator-profile", "store-b-operator-profile",
                 "store-a-directory", "store-b-directory", "source-transfer-directory", "store-a-transfer-directory"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--certificate-directory", type=Path, action="append", required=True)
    parser.add_argument("--notice-directory", type=Path, action="append", default=[])
    parser.add_argument("--catalog-relative-path", required=True)
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)

    def storage(name, profile):
        return application_storage(ApplicationContext(context_id="knowledge.example." + name,
            label="Selected development certificate exchange", python_executable=Path(sys.executable),
            project_root=root, operator_profile=profile), for_write=True)

    _, _, source = storage("source", args.source_operator_profile)
    _, _, a = storage("store-a", args.store_a_operator_profile)
    _, profile_b, b = storage("store-b", args.store_b_operator_profile)
    if (a.root.contract.canonical_path == b.root.contract.canonical_path
            or a.root.contract.storage_root_id == b.root.contract.storage_root_id):
        raise ValueError("this example requires distinct selected store artifact roots and namespaces")
    registry = ScientificTypeRegistry(knowledge_certificate_descriptors())

    source_access, access_a, access_b = tuple(development_certificate_access(plane) for plane in (source, a, b))
    sources = []
    for directories, kind, filename in ((args.certificate_directory, KnowledgeAssessmentCertificate, "certificate.json"),
                                       (args.notice_directory, KnowledgeCertificateNotice, "notice.json")):
        for directory in directories:
            record = decode_canonical_bytes(read_bounded_bytes(directory / filename, maximum_bytes=1024**2),
                                             kind, maximum_bytes=1024**2)
            sources.append(KnowledgeObjectSource(record.identity, directory, "selected.original-custodian",
                "retained-assessment", filename))
    stores = tuple(KnowledgeStore(directory=directory, namespace=name, artifact_writer=plane,
        registry=registry, require_access=guard, project_root=root) for directory, name, plane, guard in (
            (args.store_a_directory, "knowledge.example.a", a, access_a),
            (args.store_b_directory, "knowledge.example.b", b, access_b)))
    measurements = []

    def run(name, callback):
        before = resource.getrusage(resource.RUSAGE_SELF)
        start = time.monotonic_ns()
        result = callback()
        after = resource.getrusage(resource.RUSAGE_SELF)
        measurements.append({"operation": name, "elapsed_ns": time.monotonic_ns() - start,
            "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime})
        return result

    roots = tuple(source.identity for source in sources)
    initial = run("create-original-transfer", lambda: create_knowledge_transfer(sources=tuple(sources), roots=roots,
        output_directory=args.source_transfer_directory, project_root=root, artifact_writer=source,
        registry=registry, require_access=source_access))
    run("initialize-a", stores[0].initialize)
    run("initialize-b", stores[1].initialize)
    a_import = run("import-a", lambda: stores[0].import_transfer(directory=Path(initial["directory"]),
        source_artifact_writer=source, source_require_access=source_access,
        expected_transfer=decode_canonical_record(initial["transfer"], ObjectIdentity)))
    a_export = run("export-a", lambda: stores[0].export(locators=a_import["locators"], roots=roots,
        output_directory=args.store_a_transfer_directory))
    b_import = run("import-b", lambda: stores[1].import_transfer(directory=Path(a_export["directory"]),
        source_artifact_writer=a, source_require_access=access_a,
        expected_transfer=decode_canonical_record(a_export["transfer"], ObjectIdentity)))
    catalog = select_operator_catalog(profile=profile_b, project_root=root,
        catalog_relative_path=args.catalog_relative_path)
    projection = run("rebuild-b", lambda: stores[1].rebuild_projection(catalog_access=catalog))
    discovery = run("query-b", lambda: stores[1].query(catalog_access=catalog))
    resolutions = tuple(run("resolve-b-" + str(index), lambda value=value: stores[1].resolve(value))
                        for index, value in enumerate(b_import["locators"]))
    # Report the actual original records retained in B, without forming a new
    # scientific cost total or upgrading the original evidence ceiling.
    result = {"status": "COMPLETED_LOCAL_EXCHANGE", "store_a": a_import, "store_b": b_import,
        "source_transfer": initial, "store_a_transfer": a_export, "projection": projection,
        "discovery": discovery, "resolved": resolutions, "operation_measurements": measurements,
        "measured_operation_cpu_seconds": sum(v["cpu_seconds"] for v in measurements),
        "cost_scope": "DISJOINT_LOCAL_COPY_AND_READ_WINDOWS_ONLY_ORIGINAL_SCIENTIFIC_COSTS_UNCHANGED",
        "new_native_contacts": 0, "consumer_admission": "NOT_EVALUATED", "authorship": "NOT_ATTESTED",
        "unseen_updates": "UNKNOWN", "selected_source_identity_digest": sha256(
            b"".join(value.canonical_bytes() for value in sorted(roots, key=lambda p: p.fingerprint()))).hexdigest()}
    print(json.dumps(result, default=lambda value: value.to_document(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
