# A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa

This repository contains the data, code, statistical outputs, and figures supporting the manuscript **“A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa.”** The study evaluates GNSS/IGS-, ERA5-, and VMF3-derived precipitable water vapour (PWV) across Africa using Three-Cornered Hat (3CH), Extended Triple Collocation (ETC), and Direct Comparison (DC) methods, with additional normalised-RMSE (nRMSE) analysis.

## Study scope

- **Period:** 2015–2022
- **Final network:** 27 African IGS stations
- **Data-completeness criterion:** at least 700 valid collocated days
- **Core datasets:** GNSS/IGS PWV, ERA5 PWV, VMF3 PWV
- **Uncertainty methods:** 3CH, ETC, and ERA5-referenced DC
- **Relative-error metric:** ETC-derived nRMSE, normalised by station mean ERA5 PWV

Four stations considered during earlier screening (CGGN, DJIG, NURK, and RCMN) were excluded because they contained fewer than 700 valid collocated days. The screening record is provided in `Analysis/Results_Preprocessing/station_inclusion.csv`.

## Public source data

| Product | Use in the study | Public source |
|---|---|---|
| IGS tropospheric ZTD | GNSS-PWV retrieval | [NASA CDDIS](https://cddis.nasa.gov/archive/gnss/products/troposphere/zpd/) |
| VMF3_OP | Model-based tropospheric/PWV product | [TU Wien VMF3 products](https://vmf.geo.tuwien.ac.at/trop_products/GNSS/VMF3/VMF3_OP/daily/) |
| MERRA-2 M2I1NXASM v5.12.4 | Surface meteorological parameters used in GNSS-PWV retrieval | [NASA GES DISC](https://disc.gsfc.nasa.gov/datasets/M2I1NXASM_5.12.4/summary), DOI: [10.5067/3Z173KIE2TPD](https://doi.org/10.5067/3Z173KIE2TPD) |
| ERA5-based site product | Comparison PWV product | [Wuhan University NWM service](http://gmet.users.sgg.whu.edu.cn/en/customized/NWMs-based-site/submit/) |

## Repository structure

```text
tch_pwv/
├── Analysis/
│   ├── Results_Preprocessing/       # station screening and preprocessing outputs
│   ├── Results_3CH, ETC & DC/       # station, regional and continental statistics
│   └── Derived_nRMSE_Summaries/     # reproducible summaries generated from the final 27-station table
├── Code/                            # preprocessing, 3CH/ETC/DC, plotting and summary scripts
├── Data/
│   ├── Collocated_PWVs (unpreprocessed)/
│   │   └── PWVdata_27 stations(unpreprocessed).zip
│   ├── IGS STATIONS-Africa_27sta.csv/.xlsx
│   └── MCT/                         # multiple-comparison-test input
├── Figures/                         # manuscript figures
├── CITATION.cff
├── DATA_AVAILABILITY.md
├── REPRODUCIBILITY.md
├── LICENSE
├── LICENSES.md
├── requirements.txt
└── README.md
```

## Key analysis files

- `Analysis/Results_3CH, ETC & DC/STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx` — core station-level 3CH/ETC/DC statistics used for the main uncertainty-comparison figures.
- `Analysis/Results_3CH, ETC & DC/PWV_Statistics_Results_with_nRMSE2.csv` — integrated 27-station table containing mean ERA5 PWV, 3CH and ETC RMSE, ETC correlations, DC metrics, and nRMSE values used for the normalised-error analysis.
- `Analysis/Derived_nRMSE_Summaries/` — regional, continental, network-wide, and pooled correlation summaries regenerated directly from the integrated 27-station table.
- `Analysis/Results_Preprocessing/station_inclusion.csv` — final station-retention/exclusion record.
- [`MANUSCRIPT_SOURCE_MAP.md`](MANUSCRIPT_SOURCE_MAP.md) — maps manuscript figure/result blocks to their primary archived analysis sources.

## Reproduce the manuscript summaries

Create a Python environment and install the dependencies:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

Regenerate the regional, continental, network-wide, and RMSE–R/SNR summary tables:

```bash
python Code/reproduce_manuscript_summaries.py
```

Regenerate the ETC/nRMSE figure suite:

```bash
python Code/etc_nrmse_figures.py
```

Generated figures are written to `Figures/generated_etc_nrmse/`.

## Core processing workflow

1. **Collocated daily PWV input** — `Data/Collocated_PWVs (unpreprocessed)/PWVdata_27 stations(unpreprocessed).zip` contains the 27 station CSV files.
2. **Outlier detection and cleaning** — run `Code/OUTLIER_Detrending_nonlinear analysis_v3_5_1.py`. The default repository-relative configuration writes cleaned station files to `Analysis/Results_Preprocessing/Results_Outlier detection & removal/cleaned_per_station/`.
3. **3CH/ETC/DC analysis** — run `Code/PWV_Analysis_TCH_ETC_DC_updated4.m` in MATLAB and select the cleaned station folder when prompted. The final script analyses `IGS_Hampel_clean`, `VMF3_Hampel_clean`, and `ERA5_Hampel_clean` and generates 3CH, ETC, DC, correlation, mean-PWV, and nRMSE outputs.
4. **Detrending diagnostics/sensitivity analysis** — `Code/Detrending_analysis_stl_v3.py` evaluates temporal trends and STL components. It is retained for the preprocessing/sensitivity analysis and is not required as the direct input to the final 3CH/ETC/DC calculation in `PWV_Analysis_TCH_ETC_DC_updated4.m`.
5. **Figures and summaries** — the remaining Python scripts generate the manuscript plots and regional/continental summaries.

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) and [`Code/README.md`](Code/README.md) for detailed execution notes.

## nRMSE and ETC correlation analysis

The manuscript's relative-error analysis uses

`nRMSE_ETC (%) = ETC RMSE / mean ERA5 PWV × 100`.

The final summary script reproduces the reported station-to-region/continent aggregation, network-wide Pearson correlations with mean PWV, and the pooled relationships among absolute ETC RMSE, nRMSE, `R_ETC`, and the SNR-related quantity `1 − R_ETC²`.

## Citation and archive

Repository: https://github.com/osahsam/tch_pwv

A machine-readable citation file is provided in [`CITATION.cff`](CITATION.cff). 

## Licensing

- **Source code:** Apache License 2.0 (`LICENSE`)
- **Author-generated data, figures, and documentation:** CC BY 4.0, unless otherwise stated
- **External source datasets:** remain subject to the terms of their original providers

See [`LICENSES.md`](LICENSES.md) for details.

## Contact

**Samuel Osah**  
Department of Geomatic Engineering, Kwame Nkrumah University of Science and Technology (KNUST), Kumasi, Ghana  
ORCID: 0000-0002-6905-2082
