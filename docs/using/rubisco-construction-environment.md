# Install the local Rubisco construction environment

This guide installs the selected Python libraries and native Amber tools.
It preserves repository dependency ownership and original experimental installations.
Select the checkout, native source directory and external evidence destination before installation.
The [independent MolProbity runtime](rubisco-molprobity-environment.md) uses its own locked installation and reference data to assess a completed parent or material restart.

## Python installation

Use Linux x86-64 and CPython 3.11.14 for this selection.
Stop attempts that depend on the environment before you change it.
Run the following command from the selected checkout:

```sh
uv sync --locked --python 3.11.14 --no-default-groups \
  --group dev --group build --group reactor-example --group rubisco-construction
```

This selection uses the checkout's `.venv`.
It pins NumPy 2.4.6, SciPy 1.17.1, OpenMM 8.3.1 and PDBFixer 1.11.0.
The PDBFixer Git source has the immutable revision `199f03df6c50f7cf6120de766f4ccce426fda4e9`.
`pyproject.toml` and `uv.lock` own these selections.
The source guard requires committed packaging changes before an editable project rebuild.
Use `uv run --no-sync` after installation.

The [paired SSU forecast procedure](rubisco-interface-forecast.md) selects the observed-core path, standard periodic conditioning and independent endpoint checks for the in-silico specificity/turnover question.

## Native Amber installation

The selected AmberTools24 closure contains `teLeap`, force-field stock, runtime libraries and retained notices.
The [versioned manifest](../../configs/native/ambertools24-linux-x86_64.json) binds all 627 files and their executable modes.
The total selected size is 119,694,637 bytes.
The repository contains the manifest and installer, not the binaries.

Obtain an unchanged copy of this closure from its retained custodian.
Select any source directory that has the exact manifest layout and bytes.
No maintainer-specific mount is required by the installer.
Select a fresh destination beneath `.venv/native`:

```sh
uv run --no-sync python scripts/install_native_closure.py \
  --manifest configs/native/ambertools24-linux-x86_64.json \
  --source /absolute/path/to/retained-amber-closure \
  --destination /absolute/path/to/checkout/.venv/native/ambertools24 \
  > /absolute/external/checks/native-installation.json
```

The installer authenticates the complete source before and after copying.
It verifies destination bytes and publishes the directory without replacing an existing path.
Missing members, extra members, changed bytes, changed modes and symbolic links refuse installation.
The receipt records an authenticated restore, not an independently reproduced upstream build.
Original engine records and installations remain unchanged.

If this exact closure is unavailable, obtain AmberTools from its [upstream distribution](https://ambermd.org/GetAmber.php).
Select version 24 explicitly through its upstream release or retained package archive.
The current download page can offer a later version.
A new build requires a reviewed manifest, complete tool/library notices and new engine bindings.
Do not claim that a different binary build satisfies the existing manifest.
The current recipe does not reproduce the original build toolchain.

The retained closure includes notices for 20 dependency packages.
It does not include a separate AmberTools license file or a complete original compiler/build record.
Keep that limitation in the installation readout.
Do not treat this restore as a reviewed binary redistribution package.

## Scientific engine selection

Use the [local construction procedure](../../programmes/biology/photosynthesis/workflows/rubisco-response/local-cpu-construction.md).
Its `select-engines` operation derives new `GpAmberEngine` and `GpRepairNumericEngine` records.
The numeric record binds the actual interpreter and complete selected package directories.
The native entry authenticates those exact files again.
Set `PYTHONDONTWRITEBYTECODE=1` before selection and execution to prevent new interpreter-cache files in that closure.

LEaP runs with the selected copied Linux loader and runtime libraries.
The numeric construction uses the selected OpenMM CPU platform and explicit thread count.
Neither installation nor a small native control admits a molecular structure or kinetic result.

## SANDER for the gas-free precursor study

The gas-free precursor study used AmberTools 24.8 SANDER with the 3OB-3-1
tables. Its Linux x86-64 installation has 436 files and 263,473,024 bytes,
including the executable, loader, libraries, parameter tables, license
notices and the original installation manifest. All 132 native receipts
bind that original manifest to SHA-256
`8585c20d1f3afee2cae59e9721497fa5f06c24c497d06fd3828e36ac543ae073`.
The release manifest also binds the executable modes. An independent
reconstruction from the three recorded conda-forge packages and the selected
Amber runtime reproduced every file. [Release manifest](../../configs/native/sander-24.8-3ob-linux-x86_64.json) · [Scientific result](../../programmes/biology/photosynthesis/records/gp-precursor-release.md)

Set `sander_source` to the retained installation and `sander_prefix` to a
fresh directory under the selected checkout's `.venv/native`. Restore it
from the matching source distribution or checkout. For an existing
installation, run the second command with its actual prefix.

```sh
manifest=configs/native/sander-24.8-3ob-linux-x86_64.json
uv run --no-sync python scripts/install_native_closure.py \
  --manifest "$manifest" --source "$sander_source" --destination "$sander_prefix"
uv run --no-sync python scripts/install_native_closure.py \
  --manifest "$manifest" --verify-installed "$sander_prefix" \
  --manifest-sha256 6de2dbf6d89b0d4cee444c0964127cbed23c1116d7aa67af7ab61e637faab68f
```

## References and research

[AmberTools](https://ambermd.org/AmberTools.php) describes the upstream tools and component licensing.
[Amber distribution](https://ambermd.org/GetAmber.php) owns current source and binary installation instructions.
[PDBFixer 1.11.0 source](https://github.com/openmm/pdbfixer/tree/199f03df6c50f7cf6120de766f4ccce426fda4e9) owns the selected construction library.
The repository manifest identifies the exact restored Amber bytes independently of current upstream defaults.
