# Final-manuscript analysis code

This folder contains portable scripts added for the revised **27-station** manuscript analysis.

## `nrmse_summary_analysis.py`
Reads `Analysis/final_27_station/PWV_Statistics_Results_with_nRMSE.csv` and reproduces:

- regional ETC RMSE, nRMSE, and `R_ETC` summaries;
- continental ETC RMSE, nRMSE, and `R_ETC` summaries;
- network-wide Pearson correlations with mean PWV; and
- pooled relationships among absolute ETC RMSE, nRMSE, `R_ETC`, and the SNR-related quantity `1-R_ETC^2`.

Run from any working directory:

```bash
python Code/final_manuscript/nrmse_summary_analysis.py
```

The earlier plotting scripts are retained in `Code/` for provenance. Several of those scripts contain historical local Windows paths and correspond to the earlier 31-station analysis; use the final-manuscript script above for the revised nRMSE summaries.
