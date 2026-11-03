# Inspect and acquire a bounded FAIR-MAST source

SPDX-License-Identifier: CC-BY-4.0

Programme: [Fusion](../../README.md).

This guide selects public FAIR-MAST members and their separate custody requirements.
It distinguishes bounded source acquisition from plasma observation and qualification.
Select the [environment](../../../../../docs/using/environments.md) and preview the copied input first.

## Source and first action


[`fair-mast-level2.json`](fair-mast-level2.json) selects public shot 30421, campaign M9, `summary/time`, its Zarr v3 array metadata and first compressed chunk. This is a bounded source sample, not the complete shot or a scientific observation panel. The declaration follows the [MAST Data Catalog's Level 2 access guide](https://mastapp.site/level2-data.html) and [REST API guide](https://mastapp.site/rest_api.html). [UKAEA](https://www.ukaea.org/service/fair-mast/) identifies the public JSON and S3 services and the archive data license, CC BY-SA 4.0. Software and data have separate licenses.

From the selected source root, preview without network contact:

```sh
uv run --no-sync empirical-lawhood source preview --source-config programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json
```

For live acquisition, use the selected checkout's tracked package and tested Python environment.
Supply a strict `OperatorStorageProfile` for the guarded external mount.
Install separate typed `SOURCE_ACQUISITION` and `CUSTODY_PUBLICATION` records in its authority store. The two records must bind the exact selection, grantee, storage root and relative custody scope. They are researcher supplied. `--yes` confirms the already authorized effect. No owner key, mount or grant is installed by this package.

```sh
uv run --no-sync empirical-lawhood --project-root /path/to/clean-target \
  --operator-profile /path/to/operator-profile.json \
  source acquire --source-config /path/to/clean-target/programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json \
  --acquisition-authority-id SOURCE_AUTHORITY_ID \
  --custody-authority-id CUSTODY_AUTHORITY_ID --yes
```

`source recover` takes the same arguments and `--yes`. It verifies an existing receipt or completes the **same** durable attempt. It never silently starts a second selection. The gateway accepts only declared HTTPS hosts and exact URLs.

It refuses redirects and enforces per-member and aggregate byte limits. It validates shot/campaign metadata, Zarr metadata and the compressed chunk header. It stores raw bytes under the external custody root and hashes those bytes in the receipt. A changed response, missing member or changed local byte refuses verification.

It does not use the generic public-source service, which requires publisher checksums and has no Zarr member type.

To turn a verified receipt into a prospective design input, supply a strict `InformationCutoff` document and a UTC authoring time after custody:

```sh
uv run --no-sync empirical-lawhood --project-root /path/to/clean-target \
  --operator-profile /path/to/operator-profile.json \
  source design-input --source-config /path/to/clean-target/programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json \
  --cutoff /path/to/cutoff.json --input-id MY_INPUT_ID \
  --operator-id MY_OPERATOR_ID --authoring-at-utc 2026-09-28T12:00:00Z
```

The output is a strict `DesignInputRecord` binding the receipt identity and its hash. Put it in the new `StudyDraft.design_inputs` before candidate compilation. It is an outcome-blind motivation input. A later execution must declare and qualify its native observation input separately.
Receipt binding establishes no scientific fitness, issue authority or plasma result. The example acquisition receipt is external and is never shipped in the wheel or repository.


## References and research

The linked official catalogues define the public source interface and licence.
Read [source custody](../../../../../docs/using/sources.md) and the
[voltage-source assessment](../../records/mastu-voltage-source-assessment.md)
before treating archive values as a delivered physical intervention.

[Fusion programme](../../README.md).
