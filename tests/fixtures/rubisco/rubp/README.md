# Public RUB component fixture

This fixture retains the original public chemical component dictionary.
It supplies graph and source-custody controls without enzyme or rate evidence.
Use its exact bytes when checking the selected RuBP tetraanion construction.

`RUB.cif` came from the [RCSB ligand dictionary](https://files.rcsb.org/ligands/download/RUB.cif).
The source was retained on 28 October 2026.
Its SHA-256 is `f2082cdcf018061317e258742a92d6b4c4a7af9888bae02ac70e6557709c18c6`.
The original dictionary describes a neutral ligand and includes ideal coordinates.
The tests construct a distinct tetraanion and retain the original source unchanged.

The fixture supplies no Gp/Mg placement, force parameters, active assembly or physical rate.
