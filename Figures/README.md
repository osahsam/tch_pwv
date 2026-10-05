# Manuscript figures

This directory contains the publication figures associated with the revised 27-station manuscript.

- Figures 1–8: study network, data-completeness/preprocessing, sensitivity/detrending, and methodological workflow.
- Figures 9–17: 3CH/ETC/DC uncertainty, method comparison, correlations, and regional ranking.
- Figures 18–22: station-, regional-, continental-, RMSE/R/SNR-, and network-wide ETC/nRMSE analyses.

The ETC/nRMSE figure suite can be regenerated with:

```bash
python Code/etc_nrmse_figures.py
```

Generated files are written to `Figures/generated_etc_nrmse/` to avoid silently overwriting the manuscript-ready versions.
