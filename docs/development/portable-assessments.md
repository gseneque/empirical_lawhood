# Retain a portable assessment certificate

SPDX-License-Identifier: CC-BY-4.0

This guide gives the procedure for a portable assessment certificate.
It preserves the original scoped finding, evidence and producing receipts.
Use it after the selected assessment completes through its supported workflow.

## Prerequisites and first action

Select the [locked environment](../using/environments.md), original result and current operator profile.
Read the [contribution procedure](../using/recursive-inquiry.md#carry-a-contribution-into-another-investigation).
Select a new destination beneath the guarded artifact root.

The worked route uses an actual result from the [dependent-assessment example](inquiry-assessment-extensions.md).
It needs that domain's registered contribution description and exact claim assessor.
It performs no new acquisition or task execution.

```sh
uv run --no-sync python scripts/examples/assigned_opportunity_certificate.py produce \
  --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json \
  --authoring-directory /selected/artifact-root/opportunity-positive/wave \
  --output-directory /selected/artifact-root/certificate-positive
```

Use the returned directory and complete certificate identity for later verification.
Preserve the complete directory, including its contribution custody.
Do not copy only the certificate envelope.

```sh
uv run --no-sync python scripts/examples/assigned_opportunity_certificate.py verify \
  --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json \
  --certificate-directory /selected/artifact-root/certificate-positive
```

The same commands preserve adverse and unevaluable original results.
Select their actual authoring directories and separate output destinations.
An unsuccessful production retains its incomplete destination for diagnosis.
Select another destination after resolving the cause.

## Original records and verification

The [certificate API](../../src/empirical_lawhood/api/knowledge_certificates.py) composes existing contribution export, authentication and registered claim assessment.
The [reference envelope](../../src/empirical_lawhood/science/evidence/knowledge_certificates.py) adds no source, inference or execution authority.
The original numerical result and its producing receipts retain their exact bytes.

| Member | Meaning |
| --- | --- |
| `certificate.json` | Complete references to the original contribution, transport, source, subject, contract, method and assessment projection |
| `assessment-projection.json` | The existing `InquiryClaimAssessment` projected from actual original products and receipts |
| `replay-specification.json` | An explicit retrospective read selection, with exact target, requirements and adverse outcomes |
| `contribution/` | The existing complete authoring, input, product, receipt and transitive parent closure |

The replay specification is not an earlier commitment.
It authorizes no new inquiry or execution.
Each certificate control member has a 1 MiB limit.
The complete contribution closure retains its existing transport contracts.

The original assessment contract retains estimand, outcome bounds, allocation, stopping, missingness and permitted consumer parameters.
The original source retains dependence roots, assigned opportunities and nested views.
Scope retains quantities, units, receiver, horizon and information cutoff.
The contribution retains remaining requirements and original evidence roles.
Producing receipts and their complete closure retain original cost observations.
The certificate invents no new aggregate cost or missing measurement.

The verifier repeats the installed domain assessment projection.
It validates the actual producing receipt, selected configuration, exact result and evidence ceiling.
Changed outer hashes cannot replace that scientific verification.
An absent or unsupported original decoder stops interpreted verification.

| Verification result | Meaning |
| --- | --- |
| `byte_identity` | Canonical identity, or equality with the caller's complete selected identity |
| `producing_custody` | Current verification of the original contribution and complete producing receipt closure |
| `scientific_assessment` | Agreement between the retained projection and the current registered original assessor |
| `authorship` | `NOT_ATTESTED`: this route carries no authorship signature |
| `consumer_admission` | `NOT_EVALUATED`: the later consumer retains its current admission procedure |
| `update_freshness` | Which update sources this verification actually queried |

The Python verifier accepts `expected_certificate` as an exact `ObjectIdentity`.
Use that argument when a prior selection supplies the complete identity.
A filename, publisher label or catalogue entry cannot replace it.

Use `verify --allow-incomplete` to retain an identifiable envelope when its dependencies cannot be verified.
This report separates the envelope's declared disposition from a successfully replayed scientific finding.
Missing, restricted, unsupported or invalid evidence cannot receive a verified scientific verdict.

## Supported, adverse and unevaluable findings

The supported knowledge label is reserved for `SUPPORTED_SCOPED_ASSESSMENT`.
That label retains the original scientific scope and evidence ceiling.
The common certificate envelope also carries adverse, refused, unsupported and unevaluable assessments.
Their original evidence censuses remain equally portable.

An exposed finite-census result remains `NON_PROMOTABLE` after export.
It supplies no population confidence, physical qualification or new independent unit.
It cannot become a supported `ResponseLaw` through format conversion.
The response-law contract retains its original scientific obligations.

The verifier authenticates producing custody without asserting a person's identity.
Existing approval and dataset signatures retain their own authority records and trust roots.
They are not knowledge-authorship credentials.
Current access, freshness, operating conditions and consumer compatibility remain separate decisions.

## Corrections and history

Use `produce_certificate_notice` for an exact correction, supersession, withdrawal or contrary-assessment assertion.
Select the original certificate directory, a new output directory and an explicit publisher label.
A correction, supersession or contrary assessment also requires an actual successor certificate.
Both certificates must have the same exact subject and scope.
A withdrawal assertion has no successor.

The following example assumes the same explicitly selected artifact plane used for certificate verification:

```python
from empirical_lawhood.api.knowledge_certificates import produce_certificate_notice
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeNoticeKind

notice = produce_certificate_notice(
    predecessor_directory=original_certificate,
    successor_directory=corrected_certificate,
    kind=KnowledgeNoticeKind.CORRECTION,
    publisher_label="selected-local-custodian",
    reason="The successor records the explicitly corrected original assessment.",
    output_directory=new_notice_directory,
    project_root=selected_checkout,
    artifact_writer=selected_artifact_plane,
)
```

Retain the returned notice identity and both complete certificate directories.
Use `verify_certificate_notice` with that identity and the selected predecessor and successor directories.
The verifier authenticates the selected notice bytes and both referenced assessments.
It does not authenticate the publisher label as a person's identity.

A notice is a local custodian assertion.
It cannot automatically revoke another publisher's record or grant consumer admission.
The original certificate, assessment and receipt bytes remain unchanged.
An offline reader cannot assert that no unseen correction or revocation exists.
Keep the observed notices and freshness limits beside any current status projection.

## Extension and acceptance boundaries

Register the domain's `contribution_describer` and `inquiry_claim_assessment_projector` through existing inquiry hooks.
Use its actual scientific identity projector and exact record revisions.
The certificate service accepts one exact target claim per certificate.
It requires the selected assessment to appear in the contribution's original assessment census.
An unsupported domain receives an explicit refusal.

The shared [per-wave claim verifier](../../src/empirical_lawhood/api/recursive_inquiry_claims.py) also serves ordinary inquiry commitment and readback.
It creates no second scheduler, scientific evaluator or transport protocol.
New domain science remains with its independent assessment owner.

Focused certificate controls use disclosed receipt stand-ins at the contribution boundary.
They exercise semantic substitution, adverse findings and immutable update history.
Installed lifecycle acceptance separately verifies actual original producing receipts and portable custody.
Neither form of software acceptance establishes scientific qualification.

Use the [portable store procedure](portable-knowledge-stores.md) to exchange certificates and notices between explicit guarded roots.
It adds bounded dependency selection, durable import recovery and rebuildable physical catalogue locations while retaining this original verifier.
