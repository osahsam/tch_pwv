#!/usr/bin/env python3
"""Reproduce the final 27-station ETC/nRMSE summary tables.

This script operates on the validated station-level statistics used in the
revised manuscript. It does not recompute 3CH/ETC from raw PWV time series;
it reproduces the station-to-region/continent summaries and the correlation
analyses reported in the nRMSE section.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "Analysis" / "final_27_station" / "PWV_Statistics_Results_with_nRMSE.csv"
OUT = ROOT / "Analysis" / "final_27_station"

REGIONS = {
    "North Africa": {"RABT"},
    "Central Africa": {"NKLG"},
    "Southern Africa": {"DEAR","HARB","HNUS","HRAO","MFKG","RBAY","SBOK","SUTH","SUTM","TDOU","ULDI","WIND","ZAMB"},
    "East Africa": {"ABPO","ADIS","MAL2","MBAR","MOIU","SEY2","SEYG","VACS"},
    "West Africa": {"BJCO","CPVG","DAKR","YKRO"},
}
ORDER = ["North Africa","Central Africa","Southern Africa","East Africa","West Africa"]


def main():
    df = pd.read_csv(INPUT)
    if len(df) != 27:
        raise ValueError(f"Expected 27 retained stations; found {len(df)}")

    station_region = {s:r for r, stations in REGIONS.items() for s in stations}
    df["Region"] = df["STN"].map(station_region)
    if df["Region"].isna().any():
        missing = df.loc[df["Region"].isna(), "STN"].tolist()
        raise ValueError(f"Region mapping missing for: {missing}")
    df["Region"] = pd.Categorical(df["Region"], categories=ORDER, ordered=True)

    regional = (df.groupby("Region", observed=True)
        .agg(N=("STN","count"), Mean_PWV_mm=("MEAN_PWV_ERA5","mean"),
             RMSE_IGS_mm=("RMSE_IGS_ETC","mean"), RMSE_ERA5_mm=("RMSE_ERA5_ETC","mean"), RMSE_VMF3_mm=("RMSE_VMF3_ETC","mean"),
             nRMSE_IGS_pct=("nRMSE_IGS_ETC_pct","mean"), nRMSE_ERA5_pct=("nRMSE_ERA5_ETC_pct","mean"), nRMSE_VMF3_pct=("nRMSE_VMF3_ETC_pct","mean"),
             R_IGS_ETC=("R_IGS_ETC","mean"), R_ERA5_ETC=("R_ERA5_ETC","mean"), R_VMF3_ETC=("R_VMF3_ETC","mean"))
        .reset_index())
    regional.to_csv(OUT / "regional_ETC_summary.csv", index=False, float_format="%.6f")

    continental = pd.DataFrame([{
        "Scale":"Continental (n=27)", "N":len(df), "Mean_PWV_mm":df.MEAN_PWV_ERA5.mean(),
        "RMSE_IGS_mm":df.RMSE_IGS_ETC.mean(), "RMSE_ERA5_mm":df.RMSE_ERA5_ETC.mean(), "RMSE_VMF3_mm":df.RMSE_VMF3_ETC.mean(),
        "nRMSE_IGS_pct":df.nRMSE_IGS_ETC_pct.mean(), "nRMSE_ERA5_pct":df.nRMSE_ERA5_ETC_pct.mean(), "nRMSE_VMF3_pct":df.nRMSE_VMF3_ETC_pct.mean(),
        "R_IGS_ETC":df.R_IGS_ETC.mean(), "R_ERA5_ETC":df.R_ERA5_ETC.mean(), "R_VMF3_ETC":df.R_VMF3_ETC.mean()}])
    continental.to_csv(OUT / "continental_ETC_summary.csv", index=False, float_format="%.6f")

    rows=[]
    for ds in ["IGS","ERA5","VMF3"]:
        rows.append({
            "Dataset":ds,
            "Pearson_r_MeanPWV_vs_abs_ETC_RMSE":pearsonr(df.MEAN_PWV_ERA5, df[f"RMSE_{ds}_ETC"]).statistic,
            "Pearson_r_MeanPWV_vs_ETC_nRMSE":pearsonr(df.MEAN_PWV_ERA5, df[f"nRMSE_{ds}_ETC_pct"]).statistic,
            "Pearson_r_MeanPWV_vs_R_ETC":pearsonr(df.MEAN_PWV_ERA5, df[f"R_{ds}_ETC"]).statistic,
            "Pearson_r_R_ETC_vs_abs_ETC_RMSE":pearsonr(df[f"RMSE_{ds}_ETC"], df[f"R_{ds}_ETC"]).statistic,
            "Pearson_r_R_ETC_vs_ETC_nRMSE":pearsonr(df[f"nRMSE_{ds}_ETC_pct"], df[f"R_{ds}_ETC"]).statistic,
        })
    pd.DataFrame(rows).to_csv(OUT / "network_correlation_summary.csv", index=False, float_format="%.6f")

    abs_all=np.concatenate([df[f"RMSE_{ds}_ETC"].to_numpy() for ds in ["IGS","ERA5","VMF3"]])
    nrm_all=np.concatenate([df[f"nRMSE_{ds}_ETC_pct"].to_numpy() for ds in ["IGS","ERA5","VMF3"]])
    r_all=np.concatenate([df[f"R_{ds}_ETC"].to_numpy() for ds in ["IGS","ERA5","VMF3"]])
    pooled=pd.DataFrame([{
        "Pearson_r_R_ETC_vs_abs_ETC_RMSE_pooled":pearsonr(abs_all,r_all).statistic,
        "Pearson_r_R_ETC_vs_ETC_nRMSE_pooled":pearsonr(nrm_all,r_all).statistic,
        "Pearson_r_nRMSE2_vs_1_minus_R2_pooled":pearsonr(nrm_all**2,1-r_all**2).statistic,
    }])
    pooled.to_csv(OUT / "pooled_metric_relationships.csv", index=False, float_format="%.6f")

    print("Wrote final 27-station summary tables to", OUT)

if __name__ == "__main__":
    main()
