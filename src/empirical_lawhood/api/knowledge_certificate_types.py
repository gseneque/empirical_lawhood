# SPDX-License-Identifier: MPL-2.0
"""Register the existing certificate/notice verifiers as exact store extensions."""

from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate, KnowledgeCertificateNotice
from empirical_lawhood.storage.contracts.knowledge_store import ScientificTypeDescriptor, object_key

from empirical_lawhood.api.knowledge_certificates import verify_assessment_certificate, verify_certificate_notice


def development_certificate_access(artifact_writer):
    """The existing exposed-example guard; original verifiers retain evidence ceilings.

    This fixed route accepts local development certificates and notices only.
    Restricted deployments must use their actual current access/reveal owner.
    """
    def require(identity, action):
        if identity.object_schema not in (KnowledgeAssessmentCertificate.SCHEMA, KnowledgeCertificateNotice.SCHEMA):
            raise PermissionError("development certificate route cannot admit another knowledge type")
        artifact_writer.root.verify(for_write=action == "IMPORT")
    return require


def _embedded_closure(record):
    # The certificate verifier authenticates its full embedded contribution.
    return ()


def _notice_dependencies(record):
    return tuple(sorted((record.predecessor, *(() if record.successor is None else (record.successor,))),
                        key=object_key))


def _certificate(context):
    return verify_assessment_certificate(directory=context.directory, artifact_writer=context.artifact_writer,
        expected_certificate=context.identity)


def _notice(context):
    dependencies = {value.identity: value.directory for value in context.dependencies}
    record = context.record
    return verify_certificate_notice(directory=context.directory, artifact_writer=context.artifact_writer,
        expected_notice=context.identity, predecessor_directory=dependencies[record.predecessor],
        successor_directory=None if record.successor is None else dependencies[record.successor])


def knowledge_certificate_descriptors():
    """Static code-owned declarations; construction opens no record or provider."""
    return (
        ScientificTypeDescriptor("knowledge.original-assessment", KnowledgeAssessmentCertificate,
            "certificate_id", "certificate.json", _embedded_closure, _certificate),
        ScientificTypeDescriptor("knowledge.local-notice", KnowledgeCertificateNotice,
            "notice_id", "notice.json", _notice_dependencies, _notice),
    )
