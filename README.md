![Empirical Lawhood: light passes through two stone rings.](assets/empirical-lawhood-hero.jpg)

# Empirical Lawhood

How can reliable scientific capabilities accumulate when the conditions required to use one result must themselves be discovered or constructed?

Empirical Lawhood represents that work as a recursive investigation.
A question declares its required conditions, selected suppliers and assessments.
The framework prepares and executes the work, retains its evidence and makes assessed contributions available to subsequent investigations.

[Read the preprint (edition 0.60, PDF)](paper/editions/v0.60-deposit/Empirical_Lawhood_Manuscript_v0.60.pdf) · [Explore the study results by programme](programmes/README.md)

**Version 1.0 release candidate 2 is under review.**
[Release notes](docs/release/1.0.0.md) · [Migration guide](docs/v1.0/migration.md) · [Earlier RC1 tag](https://github.com/gseneque/empirical_lawhood/tree/1.0.0-RC1)

[Joint descriptions (R01–R22)](programmes/shared-records/joint-description-results.md) · [Preparation and reuse (R23–R27)](programmes/foundations/emergent-structure/records/preparation-and-reuse-results.md) · [Foundations synthesis (Studies 1–5)](programmes/foundations/README.md#foundations-synthesis-studies)

## Run a first investigation

Does a sample’s initial mass plus the mass added agree with its observed final mass within 0.01 kg?
This example predicts the final mass for three supplied samples, assesses the observations and prints the path to the retained result.

From a clean Linux x86-64 checkout with uv installed, choose a new workspace outside the checkout.
The command below creates `el-mass-balance-example` in your home directory.

```sh
uv sync --locked --python 3.11.14
uv run --no-sync python scripts/examples/v1_investigation.py \
  --project-root "$PWD" --workspace "$HOME/el-mass-balance-example" \
  --case positive --tolerance-kg 0.01
```

The expected assessment is `SATISFIED` for the three supplied samples.
The investigation guide also shows what happens when one observation disagrees or is missing. [Investigation guide](docs/v1.0/define-investigation.md) · [Installation and wheel usage](docs/getting-started.md)

## Find your way

| What you want to do | Where to start |
| --- | --- |
| Turn a scientific question into an investigation | [From a question to an investigation](docs/v1.0/from-question-to-investigation.md) |
| Define an investigation, contribute a reusable calculation or add a domain | [Public contributor guides](docs/v1.0/README.md) |
| Find a runnable workflow or inspect retained results | [Workflow catalogue](docs/reference/workflows.md) · [Research workbench](docs/using/research-workbench.md) |

## Citation and licensing

The software and the selected preprint edition (0.60) have separate citations.
Code is licensed under MPL-2.0 and project documentation under CC-BY-4.0.
Evidence and third-party materials carry their own terms. [Citation guide](CITATION.md) · [Reproducibility](REPRODUCIBILITY.md) · [Licensing](docs/reference/licensing.md) · [AI usage](docs/reference/ai-usage.md) · [Project website](https://empiricallawhood.org/)

SPDX-License-Identifier: CC-BY-4.0
