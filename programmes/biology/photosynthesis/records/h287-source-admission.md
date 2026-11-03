# H287 primary-source admission and numerical limits

State: **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The historical finite native-source acquisition authenticated Harpel, Larimer and Hartman's
1998 article, *Multiple catalytic roles of His 287 of Rhodospirillum rubrum
ribulose 1,5-bisphosphate carboxylase/oxygenase*, **Protein Science 7(3):730–738**.
Its closed v1 admitted the official NCBI metadata and abstract, but **no full methods,
numerical tables, figure operands or native PDF**. This distinguishes the
then-available qualitative/censored constraints from its unresolved quantitative
assessment operands. A **separate user-supplied PDF successor**, described below,
now supplies the complete native article, methods and reported numerical
constraints. The earlier eight-request failures remain unchanged. Neither
intake makes exposed literature fresh or certifies a mutant forecast.
[Primary article](https://doi.org/10.1002/pro.5560070322),
[PubMed record](https://pubmed.ncbi.nlm.nih.gov/9541405/).

## Exact retained source and finite access scope

The closed private packet is
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-h287-native-v1`.
It contains **24 regular files / 157,551 bytes**, with files `0444` and its
directory `0555`. The register is a physical member census, **not an
ArtifactPlane publication or registered task receipt**:

- `h287-native-register-v1.json`: **7,180 bytes**, SHA-256
  `c7f9f9ac72eacf78afbfa84c1032cd5f85da2fde7b335b23dd9b73e25377be9c`.
- `h287-native-inspection-v1.json`: **13,787 bytes**, SHA-256
  `c49b5e0245859673889265d40bc4950d4d7d8f13a7d224df5fa26fc79d18319e`.
- `ncbi-efetch-pmc-original.xml`: **5,993 bytes**, SHA-256
  `da3e9408f8b5ea4bf006060b850fb931f72f1deec5c893a3db062ba232c93188`.

The XML binds DOI **10.1002/pro.5560070322**, PMID **9541405** and PMCID
**PMC2143942.1**. Its native `pmc-pdf` self-URI names **`9541405.pdf`**; that
filename came from the official XML, rather than a filename guess. It also
records **PDF-only**, **non-open-access**, **has PDF**, and **no supplement**.
Its explicit publisher notice excludes full-text XML downloading. The acquired
XML has no body, table or figure elements. These fields neither grant full
article redistribution permission nor demonstrate that the PDF was acquired.
[Official EFetch source](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=2143942).

Exactly **eight requests** were made, with **no automatic redirects or retries**,
at most **8 MiB per response** and **32 MiB for the packet**. Every response body,
including refusals, and every URL/status/header/size/hash/cost record are retained
under `acquisition-attempt-01.json` through `acquisition-attempt-08.json`. The
following is their complete census:

| Attempt | Official request | HTTP | Acquired native body role | Bytes |
|---|---|---:|---|---:|
| 1 | [NCBI OA API](https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC2143942) | 404 | HTML error; no article | 1,584 |
| 2 | [Europe PMC full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2143942/fullTextXML) | 500 | JSON error; no article XML | 150 |
| 3 | [PMC article index](https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/) | 200 | HTML browser challenge; no article body | 21,312 |
| 4 | [PMC OA API location](https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC2143942) | 404 | HTML error; no article | 48,716 |
| 5 | [Europe PMC article index](https://europepmc.org/articles/PMC2143942) | 403 | HTML browser challenge; no article body | 5,503 |
| 6 | [NCBI PMC EFetch](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=2143942) | 200 | Authenticated metadata/abstract XML | 5,993 |
| 7 | [PMC native PDF filename](https://pmc.ncbi.nlm.nih.gov/articles/PMC2143942/pdf/9541405.pdf) | 200 | HTML proof-of-work page; no PDF | 1,817 |
| 8 | [Europe PMC PDF endpoint](https://europepmc.org/articles/PMC2143942?pdf=render) | 403 | HTML browser challenge; no PDF | 5,572 |

Filename extensions and HTTP 200 do not determine scientific admission. In
particular, the response named `pmc-native-pdf-response-original.pdf` has native
`text/html` headers and an HTML proof-of-work body, rather than a PDF signature.
No browser challenge, proof-of-work script or access restriction was bypassed.
There are **zero preparation, simulation, SCF, endpoint-fit or publication calls**.
No additional request is part of this closed acquisition.

The packet retains both acquisition helper versions. The first five requests
preceded the single allowlist patch adding official `eutils.ncbi.nlm.nih.gov`;
the final three used that patch. The initial version is explicitly a post-hoc
reconstruction from the exact one-line patch, rather than a claimed pre-request
archive or custody receipt. Request, size, retry and logging logic are identical.

Measured request windows sum to **0.045902077 CPU seconds / 6.443598189 wall
seconds**. The inspection validation window measured **0.002671807 CPU /
0.002675111 wall seconds**, and closure validation measured **0.001244940 CPU /
0.001248004 wall seconds**. Interactive review, output serialization/writes and
final closure write/chmod/readback tails remain unmeasured; these are not a
claim about total end-to-end cost.

## Historical abstract-only projection under its own WT

The abstract explicitly names **H287N** and **H287Q**. This is the complete
abstract mutation roster, not a claim about the then-unseen full-paper table census.
Preserve the study's own wild-type reference; its exact sequence, tag, expression
construct, enzyme normalization and assay conditions were not admitted by v1.

| Case or scope | Supported constraint | Admission limit |
|---|---|---|
| H287N | Approximately **10³-fold** impairment in overall RuBP carboxylation | Approximate fold qualifier; no exact turnover point value or uncertainty |
| H287Q | **>10⁵-fold** impairment in overall RuBP carboxylation | Censored qualifier; no point value or numerical detection limit |
| Both mutants | RuBP enolization below the detection threshold | No invented zero or numerical LOD |
| Both mutants | **>10-fold** lower CO₂/O₂ specificities during prolonged turnover at high mutant concentrations | No absolute specificity point, exact concentration, duration or intrinsic endpoint mapping |
| H287N | Carboxylated intermediate preferentially decarboxylates rather than processing forward to phosphoglycerate | No rate or productive-commitment fraction |
| Both mutants | Elevated enediol misprotonation and oxygenated-intermediate misprocessing | No per-case rate or branching fraction |
| Both mutants | Assembly, activation and phosphorylated-ligand recognition are not adversely affected; activation refers to Mg²⁺ binding and Lys191 carbamylation | Qualitative controls; no quantitative activation or binding constants |
| Both mutants | CABP binding is more tenacious than for their WT | Qualitative retention control; no affinity or dissociation-rate point values |

Overall carboxylation loss is not an independently measured elemental
carboxylation barrier. Intermediate processing and prolonged substrate turnover
also retain their separate assay roles. The native constraints can challenge a
model that predicts only a shared common-mode rate change, but could not through v1
supply an exact paired-endpoint numerical assessment or a calibrated commitment
law. Native table values, units, LODs, temperature, pH, gases, concentration/time,
replication and uncertainty were missing from that packet. The separate
successor below admits the native full-source quantities and remaining limits.
Existing exposure is preserved; the later full-text intake does not make these
observations fresh.

## Separate user-PDF successor

The user supplied the native **nine-page** article as `9541405.pdf`,
**3,250,450 bytes**, SHA-256
`a7ce05fbcad008bb705d5017bd2eed972eab695f0c9ae3b8c45ef508d0570f3f`.
The selected successor source packet is
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-h287-user-pdf-v1`.
It retains the exact unchanged PDF as `9541405-original.pdf`, the original
official EFetch metadata, full/per-page text, all nine complete 150-dpi gray
PNG renders, source projections, native Poppler version/binary witnesses,
helpers and inspection logs. This successor made **zero HTTP requests** and
leaves every member of the historical packet above untouched. Its provenance
is the user-supplied download; no new origin-response capture is claimed.

The native first-page title/authors/year/journal and complete **730–738**
pagination match the retained official metadata. The DOI **10.1002/pro.5560070322**,
PMID **9541405**, PMCID **PMC2143942.1** and original `pmc-pdf` filename remain
bound through that original XML. Matching source identity does not grant new
redistribution permission; the native copyright notice is preserved.

The closed successor has **78 regular files / 5,169,130 bytes**, all files
`0444` and directories `0555`, within **8 MiB/member / 32 MiB/packet**.
Its physical register retains all **77 other member** hashes and exact names:

| Retained successor member | SHA-256 |
|---|---|
| `h287-user-pdf-register-v1.json` | `365eefd5cbf22362ea3249d40159f62281297470cd0a2751c3abb554a2298638` |
| `h287-source-projection-v1.json` | `748c12878b6f5d2d4aec8e4cb3d358fa42ce8a72cd2b8b05318c37c836075c72` |
| `inspection-observation-v1.json` | `417ae617633cf9ae60b0bc1e76473c454e820734a842281680230bbd54ab2e42` |

All **nine pages** were visually inspected. Root independently reviewed full
physical pages **3/4/5/7**, printed **732/733/734/736**. There are **seven
figures and no standalone numbered kinetic tables**. The native numerical
constraints are in prose, captions and the Figure 7 half-life inset. The
source projection preserves **21 explicit rows: seven endpoint classes ×
own-WT/H287N/H287Q**, including censored and unreported cells. These are a
documentary projection denominator, not 21 independent experiments or a
canonical scientific product.

Visual review resolves material extraction errors: printed page 732 states
**hydrolysis/decarboxylation ≤0.1 for H287N versus ≥0.9 for WT**; the extracted
text instead renders the inequality glyphs as `50.1 / 20.9`. Figure 7's
H287Q half-life is **120 h**, not extracted `123`. These native ratios are not
measured commitment fractions; CABP antagonist exchange is not productive
substrate release. The [kinetic panel](h287-kinetic-panel.md) gives the native
values, complete assay roles, construct/normalization and residual limits.

Capture used host **`/usr/bin/pdfinfo`, `/usr/bin/pdftotext` and
`/usr/bin/pdftoppm`**, Poppler **0.86.1**, under the selected locked EL
interpreter with `uv run --no-sync`. The native capture window measured
**0.235511 own CPU + 4.263930 child CPU seconds / 4.498825 wall seconds**;
the final documentary validation measured **0.029569 CPU / 0.029572 wall
seconds**. Interpreter startup, helper authoring, agent/human inspection and
transcription, final record writes/readback/chmod remain outside these
measured windows; total effort is not claimed or assigned zero.

One documentary closure check refused the OCR page-731 header `73 1`.
Its original helper and exact failure are retained; the successor closure
helper joins whitespace-separated numeric header tokens before checking
pagination. No native text or image was corrected. The refused check's full
cost was not captured and remains unknown. All source bounds and scientific
non-promotions are unchanged. The packet has **zero ArtifactPlane
publications, preparations, native scientific contacts, SCF calls, endpoint
fits or registered task receipts**. It closes source availability, not
scientific phases 2–9, an assay-parent join or an EL advantage claim.

## Separate D263 numerical source binding

The six D263 turnover/specificity pairs already used in the
[reactive-state supplier assessment](reactive-state-supplier-assessment.md) came
from **Liggins and Gready, 2009, native Table 1**; they did not come from this
H287 abstract or access packet. [Primary Liggins paper](https://doi.org/10.1021/bi802159e).

| Liggins context | Reported turnover, s⁻¹ | Specificity |
|---|---:|---:|
| WT | 6.28 | 9.2 |
| D263E | 0.94 | 8.6 |
| D263N | 0.82 | 8.8 |
| D263Q | 0.20 | 9.3 |
| D263S | 0.46 | 10.1 |
| D263A | 0.81 | 9.2 |

Their already-closed source packet is
`/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-mechanism-v1`.
The retained bindings are:

- `liggins-gready-2009-author.pdf`: **257,361 bytes**, SHA-256
  `541eccc5bc50d51fb6e548393faac656678982fd457e1dd72ce94ca1da34b089`.
- `liggins-gready-2009-author.txt`: **85,708 bytes**, SHA-256
  `6bd0c1d41a640c6f9956c4b7aa2776f9fc6b63145b8712ade3349c3fd81ead58`.
- Existing `mechanism-source-inspection-v1.json`: **15,491 bytes**, SHA-256
  `9caee541a9e42e7df2892382e4df6a2995dec8c27a51903b57cf9085fd0bdcef`.
- Existing `source-register-mechanism-v1.json`: **47,714 bytes**, SHA-256
  `2d27fb9fe0c9efe1ff80fcfb72194367f3c49b2ccf392971b4de2019aec6c6ad`.

This separate preparation is **N-terminal His₆-tagged R. rubrum**, **25 °C,
pH 8**, with **CABP active-site normalization**. Turnover uses RuBP titration
at approximately **835 µM CO₂**, while WT CO₂ K_M is **446 µM**; retain this
operational qualification instead of assigning fully CO₂-saturated turnover.
Specificity uses tritiated RuBP under **5,000 ppm CO₂ in O₂**. No native table
SD or replicate count is supplied. Its activation energies are transforms of
turnover labels, rather than independent computed inputs. This WT is not
silently substituted for the H287 WT or an unresolved deposited structure.
