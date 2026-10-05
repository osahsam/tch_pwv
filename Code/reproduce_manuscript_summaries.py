#!/usr/bin/env python3
"""Reproduce the manuscript's ETC/nRMSE summary tables from the final 27-station file.

Inputs
------
Analysis/Results_3CH, ETC & DC/PWV_Statistics_Results_with_nRMSE2.csv
Data/IGS STATIONS-Africa_27sta.csv

Outputs
-------
Analysis/Derived_nRMSE_Summaries/
    regional_ETC_summary.csv
    continental_ETC_summary.csv
    network_correlation_summary.csv
    regional_IGS_pwv_correlations.csv
    pooled_metric_relationships.csv
    validation_report.txt

The script uses Pearson correlation throughout, matching the values shown in the
network-wide and RMSE/R/SNR manuscript figures.
"""

from pathlib import Path
import io
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[1]
STATS_CSV = ROOT / "Analysis" / "Results_3CH, ETC & DC" / "PWV_Statistics_Results_with_nRMSE2.csv"
STATIONS_CSV = ROOT / "Data" / "IGS STATIONS-Africa_27sta.csv"
STATION_INCLUSION_CSV = ROOT / "Analysis" / "Results_Preprocessing" / "station_inclusion.csv"
COLLOCATED_ZIP = ROOT / "Data" / "Collocated_PWVs (unpreprocessed)" / "PWVdata_27 stations(unpreprocessed).zip"
OUTDIR = ROOT / "Analysis" / "Derived_nRMSE_Summaries"
OUTDIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["IGS", "ERA5", "VMF3"]
REGION_ORDER = [
    "Northern Africa",
    "Central Africa",
    "Southern Africa",
    "Eastern Africa",
    "Western Africa",
]


def load_final_table() -> pd.DataFrame:
    stats = pd.read_csv(STATS_CSV)
    stations = pd.read_csv(STATIONS_CSV)
    df = stats.merge(
        stations[["SITE", "AFRICAN REGION"]],
        left_on="STN",
        right_on="SITE",
        how="left",
        validate="one_to_one",
    )
    if len(df) != 27:
        raise ValueError(f"Expected 27 stations, found {len(df)}")
    if df["AFRICAN REGION"].isna().any():
        missing = df.loc[df["AFRICAN REGION"].isna(), "STN"].tolist()
        raise ValueError(f"Missing region assignments for: {missing}")
    return df


def regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["MEAN_PWV_ERA5"]
    for ds in DATASETS:
        cols += [f"RMSE_{ds}_ETC", f"nRMSE_{ds}_ETC_pct", f"R_{ds}_ETC"]
    out = df.groupby("AFRICAN REGION", sort=False)[cols].mean()
    out.insert(0, "N", df.groupby("AFRICAN REGION", sort=False).size())
    out = out.reindex(REGION_ORDER)
    return out.reset_index()


def continental_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ds in DATASETS:
        rows.append(
            {
                "Dataset": ds,
                "N_stations": len(df),
                "Mean_PWV_ERA5_mm": df["MEAN_PWV_ERA5"].mean(),
                "ETC_RMSE_mm": df[f"RMSE_{ds}_ETC"].mean(),
                "ETC_nRMSE_pct": df[f"nRMSE_{ds}_ETC_pct"].mean(),
                "ETC_R": df[f"R_{ds}_ETC"].mean(),
            }
        )
    return pd.DataFrame(rows)


def network_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ds in DATASETS:
        for metric, col in [
            ("Absolute ETC RMSE", f"RMSE_{ds}_ETC"),
            ("Normalised ETC nRMSE", f"nRMSE_{ds}_ETC_pct"),
            ("ETC correlation R", f"R_{ds}_ETC"),
        ]:
            r, p = pearsonr(df["MEAN_PWV_ERA5"], df[col])
            rows.append(
                {
                    "Dataset": ds,
                    "Metric": metric,
                    "Pearson_r_vs_mean_PWV": r,
                    "p_value": p,
                    "N": len(df),
                }
            )
    return pd.DataFrame(rows)


def regional_igs_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region in REGION_ORDER:
        g = df.loc[df["AFRICAN REGION"] == region]
        row = {"Region": region, "N": len(g)}
        if len(g) >= 2:
            row["Pearson_r_PWV_vs_IGS_abs_RMSE"] = pearsonr(
                g["MEAN_PWV_ERA5"], g["RMSE_IGS_ETC"]
            ).statistic
            row["Pearson_r_PWV_vs_IGS_nRMSE"] = pearsonr(
                g["MEAN_PWV_ERA5"], g["nRMSE_IGS_ETC_pct"]
            ).statistic
        else:
            row["Pearson_r_PWV_vs_IGS_abs_RMSE"] = np.nan
            row["Pearson_r_PWV_vs_IGS_nRMSE"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def pooled_relationships(df: pd.DataFrame) -> pd.DataFrame:
    long = []
    for ds in DATASETS:
        for _, r in df.iterrows():
            long.append(
                {
                    "Dataset": ds,
                    "Station": r["STN"],
                    "RMSE": r[f"RMSE_{ds}_ETC"],
                    "nRMSE": r[f"nRMSE_{ds}_ETC_pct"],
                    "R": r[f"R_{ds}_ETC"],
                }
            )
    long = pd.DataFrame(long)

    rows = []
    for label, x, y in [
        ("Pooled absolute RMSE vs ETC R", long["RMSE"], long["R"]),
        ("Pooled nRMSE vs ETC R", long["nRMSE"], long["R"]),
        ("Pooled nRMSE^2 vs 1-R^2", long["nRMSE"] ** 2, 1 - long["R"] ** 2),
    ]:
        r, p = pearsonr(x, y)
        rows.append({"Relationship": label, "Pearson_r": r, "p_value": p, "N": len(long)})

    for ds in DATASETS:
        g = long.loc[long["Dataset"] == ds]
        for label, x, y in [
            (f"{ds}: absolute RMSE vs ETC R", g["RMSE"], g["R"]),
            (f"{ds}: nRMSE vs ETC R", g["nRMSE"], g["R"]),
        ]:
            r, p = pearsonr(x, y)
            rows.append({"Relationship": label, "Pearson_r": r, "p_value": p, "N": len(g)})
    return pd.DataFrame(rows)


def validate_inputs(df: pd.DataFrame) -> str:
    lines = []
    lines.append("Repository validation report")
    lines.append("=" * 32)
    lines.append(f"Final station statistics: {len(df)} stations")
    lines.append(f"Unique station IDs: {df['STN'].nunique()}")

    if STATION_INCLUSION_CSV.exists():
        inc = pd.read_csv(STATION_INCLUSION_CSV)
        retained = inc.loc[inc["Status"].str.lower() == "retained"]
        lines.append(f"Retained stations in station_inclusion.csv: {len(retained)}")
        same = set(retained["STN"]) == set(df["STN"])
        lines.append(f"Retained station set matches final statistics: {same}")

    if COLLOCATED_ZIP.exists():
        with zipfile.ZipFile(COLLOCATED_ZIP) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            station_ids = {Path(n).name.split("_pwv_daily.csv")[0] for n in names}
            lines.append(f"Station CSVs in collocated archive: {len(names)}")
            lines.append(f"Collocated archive station set matches final statistics: {station_ids == set(df['STN'])}")
            # Confirm schema on all archived station files.
            expected = {"STN", "DOY", "YEAR", "MONTH", "DAY", "LAT", "LON", "H", "IGS_PWV", "VMF3_PWV", "ERA5_PWV"}
            bad = []
            for n in names:
                sample = pd.read_csv(io.BytesIO(zf.read(n)), nrows=1)
                if not expected.issubset(sample.columns):
                    bad.append(Path(n).name)
            lines.append(f"Station files with missing required columns: {len(bad)}")
            if bad:
                lines.append("  " + ", ".join(bad))
    return "\n".join(lines) + "\n"


def main() -> None:
    df = load_final_table()

    regional_summary(df).to_csv(OUTDIR / "regional_ETC_summary.csv", index=False, float_format="%.6f")
    continental_summary(df).to_csv(OUTDIR / "continental_ETC_summary.csv", index=False, float_format="%.6f")
    network_correlations(df).to_csv(OUTDIR / "network_correlation_summary.csv", index=False, float_format="%.6f")
    regional_igs_correlations(df).to_csv(OUTDIR / "regional_IGS_pwv_correlations.csv", index=False, float_format="%.6f")
    pooled_relationships(df).to_csv(OUTDIR / "pooled_metric_relationships.csv", index=False, float_format="%.6f")
    (OUTDIR / "validation_report.txt").write_text(validate_inputs(df), encoding="utf-8")

    print(f"Wrote manuscript summaries to: {OUTDIR}")


if __name__ == "__main__":
    main()
