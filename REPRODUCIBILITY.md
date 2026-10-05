# Reproducibility guide

## 1. Environment

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

MATLAB R2016b or later is required for the core 3CH/ETC/DC and multiple-comparison scripts.

## 2. Final station cohort

The manuscript uses 27 stations satisfying the minimum threshold of **700 valid collocated days**. The screening table is:

`Analysis/Results_Preprocessing/station_inclusion.csv`

The raw collocated 27-station archive is:

`Data/Collocated_PWVs (unpreprocessed)/PWVdata_27 stations(unpreprocessed).zip`

## 3. Outlier cleaning

Run:

```bash
python "Code/OUTLIER_Detrending_nonlinear analysis_v3_5_1.py"
```

The script uses repository-relative defaults and writes cleaned station files under:

`Analysis/Results_Preprocessing/Results_Outlier detection & removal/cleaned_per_station/`

## 4. Core 3CH, ETC, DC and nRMSE analysis

Open MATLAB and run:

`Code/PWV_Analysis_TCH_ETC_DC_updated4.m`

When prompted, select the `cleaned_per_station` directory from Step 3. The script analyses the Hampel-cleaned IGS/VMF3/ERA5 PWV columns and generates station-level 3CH/ETC/DC statistics, ETC correlation, mean ERA5 PWV, and nRMSE.

The final integrated table archived with this repository is:

`Analysis/Results_3CH, ETC & DC/PWV_Statistics_Results_with_nRMSE2.csv`

## 5. Detrending/STL sensitivity analysis

The STL/detrending assessment can be run independently:

```bash
python Code/Detrending_analysis_stl_v3.py \
  --input "Analysis/Results_Preprocessing/Results_Outlier detection & removal/cleaned_per_station" \
  --output "Analysis/Results_Preprocessing/Results_Detrending"
```

This step quantifies trends, seasonal components, stationarity, and the effect of detrending. The final 3CH/ETC/DC script reads the Hampel-cleaned series directly; the STL workflow is therefore retained as a diagnostic/sensitivity analysis rather than a mandatory final-analysis input.

## 6. Manuscript summary tables

Run:

```bash
python Code/reproduce_manuscript_summaries.py
```

Outputs are saved to:

`Analysis/Derived_nRMSE_Summaries/`

The script also writes `validation_report.txt`, which verifies the 27-station cohort against the station-inclusion table and collocated-data archive.

## 7. ETC/nRMSE figures

Run:

```bash
python Code/etc_nrmse_figures.py
```

Outputs are saved as PNG and PDF under:

`Figures/generated_etc_nrmse/`

The script uses Pearson correlation for the reported network-wide and RMSE/R/SNR relationships.

## 8. Multiple-comparison test

Run MATLAB function `mct.m` using:

`Data/MCT/MCTdata_RMSE-3CH_ETC_DC.csv`

The analysis implements the manuscript's multiple-comparison testing of the RMSE estimates.

## 9. Reproducibility boundaries

Original source products remain available from the IGS/CDDIS, TU Wien VMF3, NASA GES DISC MERRA-2, and Wuhan University ERA5-related services listed in `DATA_AVAILABILITY.md`. This repository archives the collocated/processed station data and analysis materials required to reproduce the manuscript-level statistics and figures; users seeking to rebuild the PWV time series from the original external products should retrieve those source products from their official repositories.
