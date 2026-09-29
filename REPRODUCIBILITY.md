# Reproducibility guide

## Scope

The revised manuscript uses 27 stations that meet the >=700 valid-collocated-day criterion. The final station-level statistics are stored in `Analysis/final_27_station/PWV_Statistics_Results_with_nRMSE.csv`.

## Reproduce manuscript summary tables

1. Create a Python environment and install `requirements.txt`.
2. Run:

```bash
python Code/final_manuscript/nrmse_summary_analysis.py
```

3. Compare the regenerated CSV files in `Analysis/final_27_station/` with the manuscript tables/figures.

## Core 3CH/ETC/DC implementation

The original MATLAB implementation is `Code/PWV_Analysis_TCH_ETC_DC.m`. It expects one collocated station CSV per file, with PWV values in metres; the script converts PWV to millimetres internally. The daily station files bundled in the original ZIP are preserved under `Data/legacy_collocated_PWVs/` and correspond to an earlier processing stage. They should not be assumed to reproduce the revised 27-station numerical results exactly. The final validated station-level statistics are stored in `Analysis/final_27_station/`.

## Data completeness

`Data/station_inclusion.csv` lists all originally considered stations, the valid-day counts in the archived files, and their final inclusion/exclusion status. The archived time series are separated into retained and excluded subfolders under `Data/legacy_collocated_PWVs/`.

## Legacy materials

Earlier 31-station outputs and figures are preserved in `Analysis/legacy_31_station/` and `Figures/legacy_31_station/`. They are provided only for provenance and should not be used to reproduce the revised manuscript's numerical results.

## External source data

See the data-source table in the root `README.md` for the IGS, VMF3, MERRA-2, and ERA5 access points.

## Important version note

The original repository materials and the revised 27-station statistics are not numerically identical, indicating that the manuscript revision incorporated an updated processing/QC/collocation stage that was not included in the uploaded ZIP. Before final public release, add the exact final post-QC station time series and any preprocessing code required to regenerate `PWV_Statistics_Results_with_nRMSE.csv` from those time series.
