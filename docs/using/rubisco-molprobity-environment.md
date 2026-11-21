# Install the local MolProbity validation runtime

Use this independent structural validator for the exact locally constructed Rubisco models. The application runs in the checkout's locked Python environment. The scientific validator runs in a separate Linux x86-64 CCTBX 2026.10 installation under `.venv/native`. The selected conda-forge build includes the CCTBX Probe2 implementation and compiled libraries. Its reference rotamer and Ramachandran data come from the matching upstream release. Preserve both the application source revision and the validator installation receipt. [CCTBX release and chem_data](https://github.com/cctbx/cctbx_project/releases/tag/v2026.10) · [MolProbity validation guide](https://molprobity.lbl.gov/help/) · [Construction environment](rubisco-construction-environment.md)

## Restore the locked distribution

Select an empty absolute scratch directory and a fresh native prefix. Allow room for the 1.31 GB reference archive, the binary package cache, extracted tables, validation outputs and the installation. Select a scratch location with working space for all of them. The versioned lock contains 117 exact archives and their SHA-256 digests, including the interpreter. Micromamba uses the explicit lock without solving a new environment. The documented archive hashes are checked by the installer as well. [Binary distribution lock](../../configs/native/molprobity-cctbx-2026.10-linux-x86_64.lock) · [Upstream CCTBX distribution](https://anaconda.org/conda-forge/cctbx-base)

Set `CHECKOUT` to the absolute project path and `CACHE` to the selected absolute scratch directory. Run from the checkout. Preserve the installation output and its final JSON line in the selected evidence location. Use a fresh destination for each distinct installation.

```sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
PREFIX="$CHECKOUT/.venv/native/molprobity-cctbx-2026.10-r2"
LOCK="$CHECKOUT/configs/native/molprobity-cctbx-2026.10-linux-x86_64.lock"
mkdir -p "$CACHE/tools"
curl --fail --location --output "$CACHE/micromamba.tar.bz2" \
  https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.10.0-0.tar.bz2
printf '%s  %s\n' 9a97976244929bbae28fb1fae504e74a3e7e6d1932870e3a03321f01b7fbd07b "$CACHE/micromamba.tar.bz2" | sha256sum --check -
tar -xjf "$CACHE/micromamba.tar.bz2" -C "$CACHE/tools" bin/micromamba
curl --fail --location --output "$CACHE/chem_data-2026.10.conda" \
  https://github.com/cctbx/cctbx_project/releases/download/v2026.10/chem_data-2026.10-pyh962b75b_0.conda
printf '%s  %s\n' 16aa7bd57b53918135fa9c6002417933fbe15f9f185332508d11bc534f1d2d27 "$CACHE/chem_data-2026.10.conda" | sha256sum --check -
"$CACHE/tools/bin/micromamba" create --yes --no-rc --root-prefix "$CACHE/mamba" \
  --prefix "$PREFIX" --file "$LOCK"
uv run --no-sync python -B scripts/prepare_molprobity_runtime.py \
  --prefix "$PREFIX" --package-cache "$CACHE/mamba/pkgs" \
  --chem-data "$CACHE/chem_data-2026.10.conda" --lock "$LOCK"
```

The check of the original package archives requires the cache used for installation. The preparer checks the installed distribution files against their transaction fingerprints, installs the selected chemistry files and upstream notices, rebuilds CCTBX rotamer and CaBLAM lookup tables, and records the complete installed tree including data, runtime libraries, link targets and modes. The receipt binds its absolute location. Obtain its digest from the final installation return and select that digest at validation and readback. The recipe refuses to alter a sealed installation. The Amber construction environment has its own engine identity. [Preparation script](../../scripts/prepare_molprobity_runtime.py) · [Runtime verification](../../src/empirical_lawhood/adapters/rubisco/rubisco_response/molprobity_runtime.py)

## Scope of the reference data

The selection includes the full global monomer-library and geometry-standard link definitions needed even for protein-only material, scoring grids, and available upstream dictionaries for the common protein residues, CAP, RUB, KCX, water and selected ions. Review any molecule-specific missing reference against the authentic modeled species. A chemical-component dictionary can describe a differently protonated form. A supplied extra restraint needs a source, exact atom/charge mapping, independent justification and a frozen SHA-256. Record explicit hydrogens, their nuclear-distance convention and the selected protonation. The canonical material, restarts, atom/coordinate digest and force-field checks remain the source for those modeled quantities. [RUB component](https://www.rcsb.org/ligand/RUB) · [MolProbity chemistry and contact limitations](https://molprobity.lbl.gov/help/)

The validator accepts original local coordinates. Its reports identify the selected CCTBX components and their coverage. The LBL service has its own release, interactive options and retention policy. A full detailed report from that service requires a matching selected projection and an explicit external submission. [Local operator procedure](../../programmes/biology/photosynthesis/workflows/rubisco-response/local-cpu-construction.md) · [LBL MolProbity Next](https://molprobity.lbl.gov/)
