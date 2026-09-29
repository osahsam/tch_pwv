# Code directory

## Recommended entry points for the revised manuscript

- `PWV_Analysis_TCH_ETC_DC.m` — original MATLAB implementation of the 3CH, ETC, and ERA5-referenced direct-comparison calculations. It is retained for methodological transparency; the archived daily PWV files are from an earlier processing stage and do not exactly reproduce the revised validated statistics.
- `final_manuscript/nrmse_summary_analysis.py` — portable Python script that reproduces the revised regional, continental, network-wide, and pooled ETC/nRMSE summary tables from the validated 27-station statistics file.
- `mct.m` — Scheffé multiple-comparison analysis used with the prepared MCT input data.

## Historical plotting scripts

The remaining top-level Python scripts are the original plotting/analysis scripts from the earlier workflow. Several retain absolute Windows paths from the author's local environment and some correspond to the pre-screening 31-station analysis. They are preserved for provenance, not as the recommended reproduction route for the final revised manuscript.

Future maintenance should progressively replace these historical paths with repository-relative paths if exact regeneration of every legacy figure is required.
