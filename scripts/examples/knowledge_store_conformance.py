# SPDX-License-Identifier: MPL-2.0
"""Disclosed dependency graph and static type declarations; no store or custody."""

from dataclasses import replace

from empirical_lawhood.api.knowledge_certificate_types import knowledge_certificate_descriptors
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate, KnowledgeCertificateNotice
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.extension_conformance import ConformanceCall as Call, ConformanceCase as Case, ConformanceProfile as Profile, ExtensionConformanceSelection
from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeStoreLimits, PortableKnowledgeObject, object_key


first = ObjectIdentity('disclosed.same-label', KnowledgeAssessmentCertificate.SCHEMA, KnowledgeAssessmentCertificate.VERSION, 'a' * 64)
second = replace(first, object_fingerprint='b' * 64)
notice = ObjectIdentity('disclosed.notice', KnowledgeCertificateNotice.SCHEMA, KnowledgeCertificateNotice.VERSION, 'c' * 64)
roots = (notice,)
dependencies = tuple(sorted((first, second), key=object_key))
facts = tuple(PortableKnowledgeObject(ref, 'disclosed.original', 'same.publisher', 'certificate.json', (), 'REGISTERED_COMPLETE')
              for ref in dependencies)
update = PortableKnowledgeObject(notice, 'disclosed.original', 'same.publisher', 'notice.json', dependencies, 'REGISTERED_COMPLETE')
objects = tuple(sorted((*facts, update), key=lambda row: object_key(row.identity)))
arguments = dict(objects=objects, roots=roots, limits=KnowledgeStoreLimits())
CONFORMANCE_SELECTION = ExtensionConformanceSelection('knowledge', 'empirical-lawhood/knowledge/', (),
    imported_record_types=(KnowledgeAssessmentCertificate, KnowledgeCertificateNotice, PortableKnowledgeObject),
    knowledge_types=knowledge_certificate_descriptors(), profile=Profile.KNOWLEDGE_STORE_CONTRACTS,
    cases=(Case('knowledge.complete-dependencies', Call.KNOWLEDGE_DEPENDENCIES, arguments, (*facts, update)),
        Case('knowledge.missing-dependency', Call.KNOWLEDGE_DEPENDENCIES,
            {**arguments, 'objects': (facts[0], update)}, 'ValueError', 'missing dependency'),
        Case('knowledge.depth-bound', Call.KNOWLEDGE_DEPENDENCIES,
            {**arguments, 'limits': KnowledgeStoreLimits(maximum_dependency_depth=1)}, 'ValueError', 'dependency depth')))
