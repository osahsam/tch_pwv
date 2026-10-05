# Manuscript source map

This file identifies the repository products that support each major block of the revised manuscript.

| Manuscript content | Primary repository source |
|---|---|
| Station selection / data-completeness screening | `Analysis/Results_Preprocessing/station_inclusion.csv` |
| Figures 1–8 (network, completeness, preprocessing/detrending, workflow) | `Figures/Figure1...Figure8...` and preprocessing scripts in `Code/` |
| Figures 9–17 and core 3CH/ETC/DC comparison | `Analysis/Results_3CH, ETC & DC/STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx`, regional/overall summary CSVs, and `Code/TCH_*` plotting scripts |
| Figure 13 multiple-comparison analysis | `Data/MCT/MCTdata_RMSE-3CH_ETC_DC.csv` and `Code/mct.m` |
| Figures 18–22 and Section 3.7 nRMSE analysis | `Analysis/Results_3CH, ETC & DC/PWV_Statistics_Results_with_nRMSE2.csv` and `Code/etc_nrmse_figures.py` |
| Regional/continental/network-wide nRMSE summary tables | `Code/reproduce_manuscript_summaries.py` → `Analysis/Derived_nRMSE_Summaries/` |

The source map is intended to make it clear which saved analysis product underlies each manuscript figure/table and to prevent accidental mixing of intermediate outputs during future repository maintenance.
