"""
================================================================================
 ETC Absolute vs Normalized RMSE Analysis -- Publication Figures
 Manuscript: 3CH-Based Evaluation of GNSS, ERA5 and VMF3 PWV over Africa
 Author: S. Osah et al.  | Journal: Earth and Space Science
================================================================================

 Generates seven publication-grade figures (300 dpi) addressing the reviewer's
 concern about absolute vs normalised ETC error metrics across Africa's
 climatically diverse stations:

   Figure A1.  Station-level absolute ETC RMSE  vs  normalised ETC nRMSE
   Figure A2.  Regional-level absolute vs normalised ETC (spatial order)
   Figure A2b. Regional comparison ordered by humidity gradient  *** NEW ***
   Figure A3.  Continental-level absolute vs normalised ETC summary
   Figure A4.  Correlation matrix: MEAN_PWV_ERA5 vs ETC error metrics
   Figure A5.  Inter-product gap amplification (mm vs %)  *** NEW ***
   Figure A6.  Climatology-coloured scatter: nRMSE vs mean PWV  *** NEW ***
   Figure A2.1 Station-level abs/normalised ETC, transparent BG + latitude  *** NEW ***
   Figure A2.2 Station-level abs/normalised ETC, white BG (no latitude)     *** NEW ***
   Figure A2.3 Station-level abs/normalised ETC, white BG + mean PWV        *** NEW ***
   Figure A2.4 Station-level abs/normalised ETC, white BG + PWV dual-axis   *** NEW ***
   Figure A7.  RMSE / nRMSE relationship to ETC correlation R_ETC            *** NEW ***
   Figure A8.  Geographic station map coloured by IGS nRMSE                  *** NEW ***
   Figure A9.  Africa coastline map coloured by IGS nRMSE (a/b panels)       *** NEW ***

 Requirements: pandas, numpy, matplotlib, seaborn
 Tested on Python 3.10+, matplotlib >= 3.7
================================================================================
"""

from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 0. CONFIG -- edit input paths and output directory here
# ---------------------------------------------------------------------------
STATS_CSV = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "PWV_Statistics_Results_with_nRMSE2.csv"
STATIONS_CSV = REPO_ROOT / "Data" / "IGS STATIONS-Africa_27sta.csv"
OUTDIR = REPO_ROOT / "Figures" / "generated_etc_nrmse"
DPI = 600

os.makedirs(OUTDIR, exist_ok=True)

# Colour-blind-safe palette (Wong 2011 / Okabe-Ito; recommended by Nature MI)
# Absolute  metrics --> filled solid bars  (cool tones)
# Normalized metrics --> hatched bars      (warm tones)
COL_ABS  = {"IGS": "#0072B2", "ERA5": "#56B4E9", "VMF3": "#009E73"}
COL_NORM = {"IGS": "#D55E00", "ERA5": "#E69F00", "VMF3": "#CC79A7"}

# Unified per-dataset palette (used by the humidity-gradient and gap figures)
# Matches the reviewer's reference style: IGS blue, ERA5 amber, VMF3 teal.
COL_UNI  = {"IGS": "#2E86C1", "ERA5": "#E8A33D", "VMF3": "#1ABC9C"}

# Per-region categorical palette (Okabe-Ito-derived, distinct hues)
COL_REGION = {
    "Northern Africa": "#E69F00",
    "Central Africa" : "#009E73",
    "Southern Africa": "#0072B2",
    "Eastern Africa" : "#D55E00",
    "Western Africa" : "#CC79A7",
}

# -----------------------------------------------------------------------------
# Embedded Africa coastline (lon, lat).  Moderate-fidelity outline used as a
# backdrop for the station map (Figure A9).  Self-contained so the script needs
# no cartopy / geopandas / shapefile downloads.  Mainland + Madagascar.
# -----------------------------------------------------------------------------
AFRICA_MAINLAND = [
    (-5.9, 35.8), (-1.0, 35.9), (3.0, 36.8), (8.5, 37.3), (10.5, 37.2),
    (11.5, 33.8), (15.0, 32.4), (19.0, 30.5), (24.5, 31.5), (29.0, 31.0),
    (32.5, 31.5), (34.5, 28.0), (35.5, 23.0), (37.0, 18.0), (38.5, 15.5),
    (40.0, 15.0), (43.0, 11.5), (44.5, 10.5), (48.5, 8.0), (51.4, 11.5),
    (49.5, 7.0), (47.0, 4.0), (44.0, 1.5), (41.5, -1.5), (40.5, -4.5),
    (39.5, -8.0), (40.5, -11.0), (40.0, -15.0), (38.0, -17.5), (35.5, -19.5),
    (35.0, -22.5), (32.5, -25.5), (32.0, -28.5), (30.0, -31.0), (27.0, -33.5),
    (22.0, -34.8), (18.5, -34.4), (17.0, -32.0), (15.0, -27.0), (13.5, -23.0),
    (11.8, -18.0), (13.0, -12.5), (12.0, -8.0), (9.0, -1.0), (9.5, 3.0),
    (8.0, 4.5), (4.5, 6.5), (-2.0, 5.0), (-7.5, 4.5), (-13.0, 9.0),
    (-16.5, 13.5), (-17.5, 16.0), (-16.0, 21.0), (-13.0, 27.5), (-9.5, 30.5),
    (-9.8, 32.0), (-5.9, 35.8),
]
AFRICA_MADAGASCAR = [
    (49.5, -12.5), (50.5, -15.5), (49.8, -18.0), (48.0, -22.0), (45.2, -25.5),
    (44.0, -22.0), (43.3, -18.0), (46.0, -15.0), (49.5, -12.5),
]

# Region colour band for the station chart x-axis ribbon
REGION_BAND = {
    "Northern Africa": "#F0E5CC",
    "Central Africa" : "#CCE3D4",
    "Southern Africa": "#D4E2F0",
    "Eastern Africa" : "#F0D4D4",
    "Western Africa" : "#E5D4F0",
}

REGION_ORDER = ["Northern Africa", "Central Africa", "Southern Africa",
                "Eastern Africa",  "Western Africa"]

# Strict spatial station order requested by the manuscript
STATION_ORDER = [
    "RABT",
    "NKLG",
    "DEAR","HARB","HNUS","HRAO","MFKG","RBAY","SBOK","SUTH","SUTM",
    "TDOU","ULDI","WIND","ZAMB",
    "ABPO","ADIS","MAL2","MBAR","MOIU","SEY2","SEYG","VACS",
    "BJCO","CPVG","DAKR","YKRO",
]

# =============================================================================
#  USER STYLE CONFIGURATION
# -----------------------------------------------------------------------------
#  Adjust any of the values below to change the look of EVERY figure in this
#  script.  Each key controls a specific element of every plot; sizes are in
#  matplotlib points, weights follow matplotlib conventions
#  ("normal", "bold", or numeric 100-900).
# =============================================================================
USER_STYLE = {
    # ---- Global font family --------------------------------------------
    "font_family"            : "DejaVu Sans",

    # ---- Figure / panel titles ----------------------------------------
    "suptitle_fontsize"      : 14,
    "suptitle_fontweight"    : "bold",
    "panel_title_fontsize"   : 13,
    "panel_title_fontweight" : "bold",

    # ---- Axis labels (xlabel / ylabel) --------------------------------
    "axis_label_fontsize"    : 14,
    "axis_label_fontweight"  : "bold",

    # ---- Tick labels (numerical values on x/y axes) -------------------
    "tick_label_fontsize"    : 11,
    "tick_label_fontweight"  : "bold",

    # ---- Category tick labels (station IDs, region names) -------------
    "category_tick_fontsize" : 10,
    "category_tick_fontweight": "bold",

    # ---- Legend -------------------------------------------------------
    "legend_fontsize"        : 11,
    "legend_title_fontsize"  : 12,
    "legend_title_fontweight": "bold",
    "legend_frame_edgecolor" : "0.4",
    "legend_framealpha"      : 0.95,

    # ---- Values printed on top of bars -------------------------------
    "bar_value_fontsize"     : 8,
    "bar_value_fontweight"   : "normal",   # bars are dense; keep light
    "bar_value_color"        : "black",
    "bar_value_rotation"     : 90,         # 0 for horizontal, 90 for vertical

    # ---- Region headers (above station charts) -----------------------
    "region_header_fontsize" : 13,
    "region_header_narrow_fontsize" : 11,   # for single-station regions
    "region_header_fontweight": "bold",
    "region_header_color"    : "black",

    # ---- Gridlines ----------------------------------------------------
    "grid_alpha"             : 0.30,
    "grid_linestyle"         : "--",
    "grid_linewidth"         : 0.8,

    # ---- Spines (plot frame) ------------------------------------------
    "spine_linewidth"        : 1.1,
    "spine_color"            : "0.25",

    # ---- Bar styling -------------------------------------------------
    "bar_edgecolor"          : "black",
    "bar_edgewidth"          : 0.5,

    # ---- Region divider lines ----------------------------------------
    "divider_linewidth"      : 1.6,
    "divider_alpha"          : 0.85,
    "divider_linestyle"      : "--",

    # ---- Output ------------------------------------------------------
    "savefig_dpi"            : 600,
}

# Convenience accessors (used throughout the script).  Edit USER_STYLE above
# rather than these aliases.
US = USER_STYLE

# Global rcParams for journal-grade figures (driven by USER_STYLE)
plt.rcParams.update({
    "font.family"       : US["font_family"],
    "font.size"         : 10,
    "axes.titlesize"    : US["panel_title_fontsize"],
    "axes.titleweight"  : US["panel_title_fontweight"],
    "axes.labelsize"    : US["axis_label_fontsize"],
    "axes.labelweight"  : US["axis_label_fontweight"],
    "axes.spines.top"   : False,
    "axes.spines.right" : False,
    "axes.grid"         : True,
    "grid.alpha"        : US["grid_alpha"],
    "grid.linestyle"    : US["grid_linestyle"],
    "grid.linewidth"    : US["grid_linewidth"],
    "legend.frameon"    : True,
    "legend.framealpha" : US["legend_framealpha"],
    "legend.edgecolor"  : US["legend_frame_edgecolor"],
    "legend.fontsize"   : US["legend_fontsize"],
    "xtick.labelsize"   : US["tick_label_fontsize"],
    "ytick.labelsize"   : US["tick_label_fontsize"],
    "savefig.bbox"      : "tight",
    "savefig.dpi"       : US["savefig_dpi"],
})


def apply_tick_label_weight(ax, axis="both"):
    """Apply user-configured tick label weight to one or both axes."""
    weight = US["tick_label_fontweight"]
    if axis in ("x", "both"):
        for lbl in ax.get_xticklabels():
            lbl.set_fontweight(weight)
    if axis in ("y", "both"):
        for lbl in ax.get_yticklabels():
            lbl.set_fontweight(weight)


def apply_spines(ax):
    """Apply user-configured spine styling."""
    for spine in ax.spines.values():
        spine.set_linewidth(US["spine_linewidth"])
        spine.set_color(US["spine_color"])


# ---------------------------------------------------------------------------
# 1. LOAD AND PREPARE DATA
# ---------------------------------------------------------------------------
def load_data():
    stats    = pd.read_csv(STATS_CSV)
    stations = pd.read_csv(STATIONS_CSV)
    df = stats.merge(stations[["SITE", "AFRICAN REGION"]],
                     left_on="STN", right_on="SITE", how="left")
    df = df.rename(columns={"AFRICAN REGION": "REGION", "LAT": "STN_LAT"})

    keep = ["STN", "REGION", "STN_LAT", "MEAN_PWV_ERA5",
            "RMSE_IGS_ETC",  "RMSE_ERA5_ETC",  "RMSE_VMF3_ETC",
            "nRMSE_IGS_ETC_pct", "nRMSE_ERA5_ETC_pct", "nRMSE_VMF3_ETC_pct",
            "R_IGS_ETC",    "R_ERA5_ETC",    "R_VMF3_ETC"]
    df = df[keep]
    df["STN"]    = pd.Categorical(df["STN"], categories=STATION_ORDER, ordered=True)
    df["REGION"] = pd.Categorical(df["REGION"], categories=REGION_ORDER, ordered=True)
    return df.sort_values("STN").reset_index(drop=True)


def annotate_bars(ax, bars, fmt="{:.2f}", offset=0.01, fontsize=None,
                  rotation=None, color=None, fontweight=None):
    """Robust value-on-top annotation that scales with axis range.

    Any parameter left at None falls back to the corresponding USER_STYLE
    setting, so the appearance of all bar-value annotations across every
    figure can be tuned from a single place.
    """
    if fontsize   is None: fontsize   = US["bar_value_fontsize"]
    if rotation   is None: rotation   = US["bar_value_rotation"]
    if color      is None: color      = US["bar_value_color"]
    if fontweight is None: fontweight = US["bar_value_fontweight"]

    ymin, ymax = ax.get_ylim()
    pad = (ymax - ymin) * offset
    for b in bars:
        h = b.get_height()
        if np.isnan(h):
            continue
        ax.text(b.get_x() + b.get_width()/2, h + pad,
                fmt.format(h), ha="center", va="bottom",
                fontsize=fontsize, rotation=rotation, color=color,
                fontweight=fontweight)


# ---------------------------------------------------------------------------
# 2. FIGURE A1: STATION-LEVEL  (Absolute vs Normalised)
# ---------------------------------------------------------------------------
def figure_station_level(df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9), sharex=True)

    x = np.arange(len(df))
    w = 0.27  # bar width (3 datasets side-by-side)

    # ---------- top : absolute ETC RMSE ----------
    b1 = ax1.bar(x - w, df["RMSE_IGS_ETC"],  w, color=COL_ABS["IGS"],
                 label="IGS",  edgecolor="black", linewidth=0.4)
    b2 = ax1.bar(x,     df["RMSE_ERA5_ETC"], w, color=COL_ABS["ERA5"],
                 label="ERA5", edgecolor="black", linewidth=0.4)
    b3 = ax1.bar(x + w, df["RMSE_VMF3_ETC"], w, color=COL_ABS["VMF3"],
                 label="VMF3", edgecolor="black", linewidth=0.4)

    ax1.set_ylabel("Absolute ETC RMSE (mm)")
    ax1.set_title("(a) Station-Level Absolute ETC RMSE", loc="left")
    ax1.set_ylim(0, df[["RMSE_IGS_ETC","RMSE_ERA5_ETC","RMSE_VMF3_ETC"]].values.max() * 1.20)
    ax1.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0),
               fontsize=9, title="Dataset", title_fontsize=9, frameon=True)
    for bars in (b1, b2, b3):
        annotate_bars(ax1, bars, fmt="{:.2f}", fontsize=6.5, rotation=90,
                      offset=0.012)

    # ---------- bottom : normalised ETC nRMSE ----------
    b4 = ax2.bar(x - w, df["nRMSE_IGS_ETC_pct"],  w, color=COL_NORM["IGS"],
                 label="IGS",  hatch="//", edgecolor="black", linewidth=0.4)
    b5 = ax2.bar(x,     df["nRMSE_ERA5_ETC_pct"], w, color=COL_NORM["ERA5"],
                 label="ERA5", hatch="//", edgecolor="black", linewidth=0.4)
    b6 = ax2.bar(x + w, df["nRMSE_VMF3_ETC_pct"], w, color=COL_NORM["VMF3"],
                 label="VMF3", hatch="//", edgecolor="black", linewidth=0.4)

    ax2.set_ylabel("Normalised ETC nRMSE (%)")
    ax2.set_xlabel("IGS Station")
    ax2.set_title("(b) Station-Level Normalised ETC nRMSE", loc="left")
    ax2.set_ylim(0, df[["nRMSE_IGS_ETC_pct","nRMSE_ERA5_ETC_pct","nRMSE_VMF3_ETC_pct"]].values.max() * 1.20)
    ax2.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0),
               fontsize=9, title="Dataset", title_fontsize=9, frameon=True)
    for bars in (b4, b5, b6):
        annotate_bars(ax2, bars, fmt="{:.1f}", fontsize=6.5, rotation=90,
                      offset=0.012)

    # X axis -- station labels
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["STN"].astype(str), rotation=55, ha="right")

    # Regional bands on both axes
    region_groups = df.groupby("REGION", observed=True).indices
    # Abbreviations for narrow regions
    REGION_ABBR = {"Northern Africa": "N", "Central Africa": "C",
                   "Southern Africa": "SOUTHERN", "Eastern Africa": "EASTERN",
                   "Western Africa": "WESTERN"}
    for ax in (ax1, ax2):
        for region in REGION_ORDER:
            idx = region_groups[region]
            if len(idx) == 0:
                continue
            x0 = idx[0] - 0.5
            x1 = idx[-1] + 0.5
            ax.axvspan(x0, x1, color=REGION_BAND[region], alpha=0.35,
                       zorder=0, lw=0)
            # region label on the top panel only
            if ax is ax1:
                label = REGION_ABBR[region]
                # use small font for narrow bands (Northern, Central)
                fsz = 7 if (x1 - x0) < 2 else 8.5
                ax.text((x0 + x1) / 2, ax.get_ylim()[1] * 0.94,
                        label, ha="center", va="top", fontsize=fsz,
                        fontweight="bold", color="0.25",
                        bbox=dict(boxstyle="round,pad=0.18",
                                  facecolor="white",
                                  edgecolor="0.7", linewidth=0.5))

    fig.suptitle("Figure A1.  Station-Level Absolute vs Normalised ETC RMSE "
                 "across 27 African IGS Stations",
                 fontsize=12.5, fontweight="bold", y=1.005)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "FigureA1_Station_Level_ETC.png"))
    plt.savefig(os.path.join(OUTDIR, "FigureA1_Station_Level_ETC.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. FIGURE A2: REGIONAL-LEVEL
# ---------------------------------------------------------------------------
def figure_regional_level(df):
    reg = df.groupby("REGION", observed=True).mean(numeric_only=True).reindex(REGION_ORDER)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.2))
    x = np.arange(len(reg))
    w = 0.27

    # Left -- Absolute RMSE
    bA1 = axL.bar(x - w, reg["RMSE_IGS_ETC"],  w, color=COL_ABS["IGS"],
                  label="IGS",  edgecolor="black", linewidth=0.4)
    bA2 = axL.bar(x,     reg["RMSE_ERA5_ETC"], w, color=COL_ABS["ERA5"],
                  label="ERA5", edgecolor="black", linewidth=0.4)
    bA3 = axL.bar(x + w, reg["RMSE_VMF3_ETC"], w, color=COL_ABS["VMF3"],
                  label="VMF3", edgecolor="black", linewidth=0.4)
    axL.set_ylabel("Absolute ETC RMSE (mm)")
    axL.set_title("(a) Regional Absolute ETC RMSE", loc="left")
    axL.set_xticks(x)
    axL.set_xticklabels([r.replace(" Africa", "") for r in reg.index], rotation=20, ha="right")
    axL.set_ylim(0, reg[["RMSE_IGS_ETC","RMSE_ERA5_ETC","RMSE_VMF3_ETC"]].values.max() * 1.18)
    axL.legend(loc="upper left", ncol=3, fontsize=9)
    for bars in (bA1, bA2, bA3):
        annotate_bars(axL, bars, fmt="{:.2f}", fontsize=8, offset=0.012)

    # Right -- Normalised nRMSE
    bB1 = axR.bar(x - w, reg["nRMSE_IGS_ETC_pct"],  w, color=COL_NORM["IGS"],
                  label="IGS",  hatch="//", edgecolor="black", linewidth=0.4)
    bB2 = axR.bar(x,     reg["nRMSE_ERA5_ETC_pct"], w, color=COL_NORM["ERA5"],
                  label="ERA5", hatch="//", edgecolor="black", linewidth=0.4)
    bB3 = axR.bar(x + w, reg["nRMSE_VMF3_ETC_pct"], w, color=COL_NORM["VMF3"],
                  label="VMF3", hatch="//", edgecolor="black", linewidth=0.4)
    axR.set_ylabel("Normalised ETC nRMSE (%)")
    axR.set_title("(b) Regional Normalised ETC nRMSE", loc="left")
    axR.set_xticks(x)
    axR.set_xticklabels([r.replace(" Africa", "") for r in reg.index], rotation=20, ha="right")
    axR.set_ylim(0, reg[["nRMSE_IGS_ETC_pct","nRMSE_ERA5_ETC_pct","nRMSE_VMF3_ETC_pct"]].values.max() * 1.20)
    axR.legend(loc="upper right", ncol=3, fontsize=9)
    for bars in (bB1, bB2, bB3):
        annotate_bars(axR, bars, fmt="{:.1f}", fontsize=8, offset=0.012)

    fig.suptitle("Figure A2.  Regional Absolute vs Normalised ETC RMSE across "
                 "Five African Sub-Regions",
                 fontsize=12.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "FigureA2_Regional_Level_ETC.png"))
    plt.savefig(os.path.join(OUTDIR, "FigureA2_Regional_Level_ETC.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. FIGURE A3: CONTINENTAL SUMMARY
# ---------------------------------------------------------------------------
def figure_continental_level(df):
    means = df.mean(numeric_only=True)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5))
    datasets = ["IGS", "ERA5", "VMF3"]
    x = np.arange(len(datasets))

    abs_vals  = [means[f"RMSE_{d}_ETC"]       for d in datasets]
    norm_vals = [means[f"nRMSE_{d}_ETC_pct"]  for d in datasets]

    # Absolute
    bA = axL.bar(x, abs_vals, 0.55,
                 color=[COL_ABS[d]  for d in datasets],
                 edgecolor="black", linewidth=0.5)
    axL.set_xticks(x)
    axL.set_xticklabels(datasets)
    axL.set_ylabel("Absolute ETC RMSE (mm)")
    axL.set_title("(a) Continental Mean Absolute ETC RMSE", loc="left")
    axL.set_ylim(0, max(abs_vals) * 1.22)
    annotate_bars(axL, bA, fmt="{:.3f}", fontsize=10, offset=0.015)

    # Normalised
    bB = axR.bar(x, norm_vals, 0.55,
                 color=[COL_NORM[d] for d in datasets],
                 hatch="//", edgecolor="black", linewidth=0.5)
    axR.set_xticks(x)
    axR.set_xticklabels(datasets)
    axR.set_ylabel("Normalised ETC nRMSE (%)")
    axR.set_title("(b) Continental Mean Normalised ETC nRMSE", loc="left")
    axR.set_ylim(0, max(norm_vals) * 1.22)
    annotate_bars(axR, bB, fmt="{:.2f}", fontsize=10, offset=0.015)

    fig.suptitle("Figure A3.  Continental ETC Performance Summary "
                 "across the African Network (n = 27 stations)",
                 fontsize=12.5, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "FigureA3_Continental_Level_ETC.png"))
    plt.savefig(os.path.join(OUTDIR, "FigureA3_Continental_Level_ETC.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. FIGURE A4: CORRELATION MAP  -- MEAN_PWV_ERA5 vs ETC metrics
# ---------------------------------------------------------------------------
def figure_correlation_map(df):
    datasets   = ["IGS", "ERA5", "VMF3"]
    metric_map = {
        "Absolute RMSE (mm)": "RMSE_{}_ETC",
        "Normalised nRMSE (%)": "nRMSE_{}_ETC_pct",
        "ETC Correlation R":  "R_{}_ETC",
    }
    mat = pd.DataFrame(index=metric_map.keys(), columns=datasets, dtype=float)
    for d in datasets:
        for label, tmpl in metric_map.items():
            mat.loc[label, d] = df["MEAN_PWV_ERA5"].corr(df[tmpl.format(d)])

    # Two-panel figure: heatmap on the left, scatter exemplar on the right
    fig = plt.figure(figsize=(14.5, 5.6))
    gs  = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.3], wspace=0.30)

    # --- Heatmap ---
    axH = fig.add_subplot(gs[0, 0])
    sns.heatmap(mat.astype(float), annot=True, fmt="+.2f", cmap="RdBu_r",
                vmin=-1, vmax=1, center=0,
                cbar_kws={"label": r"Pearson $r$ vs MEAN PWV (ERA5)",
                          "shrink": 0.85},
                linewidths=1, linecolor="white", ax=axH,
                annot_kws={"fontweight": "bold", "fontsize": 12})
    axH.set_yticklabels(axH.get_yticklabels(), rotation=0, fontsize=10)
    axH.set_xticklabels(axH.get_xticklabels(), rotation=0, fontsize=10,
                         fontweight="bold")
    axH.set_xlabel("Dataset", fontweight="bold")
    axH.set_ylabel("ETC Metric", fontweight="bold")
    axH.set_title("(a) Correlation of ETC metrics with MEAN_PWV (ERA5)\n"
                  "Red = co-scales with humidity; Blue = decoupled / inverse",
                  loc="left", fontsize=10.5)

    # --- Scatter exemplar: IGS absolute vs normalised vs PWV ---
    axS = fig.add_subplot(gs[0, 1])
    # Build a tidy frame
    pwv = df["MEAN_PWV_ERA5"].values

    # Twin-axis scatter: absolute on left axis (blue), normalised on right (red)
    axS.scatter(pwv, df["RMSE_IGS_ETC"], s=55, color=COL_ABS["IGS"],
                marker="o", edgecolor="black", linewidth=0.5,
                label="Absolute RMSE (IGS)")
    # Trend line
    z = np.polyfit(pwv, df["RMSE_IGS_ETC"], 1)
    p = np.poly1d(z)
    xs = np.linspace(pwv.min(), pwv.max(), 100)
    axS.plot(xs, p(xs), "--", color=COL_ABS["IGS"], lw=1.4,
             label=fr"$r_{{abs}}$ = {df['MEAN_PWV_ERA5'].corr(df['RMSE_IGS_ETC']):+.2f}")
    axS.set_xlabel("Mean ERA5 PWV (mm)")
    axS.set_ylabel("Absolute ETC RMSE (mm)", color=COL_ABS["IGS"])
    axS.tick_params(axis="y", labelcolor=COL_ABS["IGS"])

    axS2 = axS.twinx()
    axS2.scatter(pwv, df["nRMSE_IGS_ETC_pct"], s=55, color=COL_NORM["IGS"],
                 marker="D", edgecolor="black", linewidth=0.5,
                 label="Normalised nRMSE (IGS)")
    z2 = np.polyfit(pwv, df["nRMSE_IGS_ETC_pct"], 1)
    p2 = np.poly1d(z2)
    axS2.plot(xs, p2(xs), "--", color=COL_NORM["IGS"], lw=1.4,
              label=fr"$r_{{norm}}$ = {df['MEAN_PWV_ERA5'].corr(df['nRMSE_IGS_ETC_pct']):+.2f}")
    axS2.set_ylabel("Normalised ETC nRMSE (%)", color=COL_NORM["IGS"])
    axS2.tick_params(axis="y", labelcolor=COL_NORM["IGS"])
    axS2.spines["right"].set_visible(True)
    axS2.spines["top"].set_visible(False)

    # Annotate driest stations for tour-guide effect
    dry = df.nsmallest(3, "MEAN_PWV_ERA5")
    for _, r in dry.iterrows():
        axS2.annotate(r["STN"], (r["MEAN_PWV_ERA5"], r["nRMSE_IGS_ETC_pct"]),
                      xytext=(5, 4), textcoords="offset points",
                      fontsize=8, fontweight="bold", color=COL_NORM["IGS"])

    # Combined legend
    h1, l1 = axS.get_legend_handles_labels()
    h2, l2 = axS2.get_legend_handles_labels()
    axS.legend(h1 + h2, l1 + l2, loc="upper center", fontsize=8.5,
               ncol=2, framealpha=0.95)
    axS.set_title("(b) IGS exemplar: opposing trends of absolute vs "
                  "normalised error with PWV",
                  loc="left", fontsize=11)
    axS.grid(True, alpha=0.25, linestyle="--")

    fig.suptitle("Figure A4.  Correlation Map -- Normalisation Decouples "
                 "Environmental Scale from ETC Error",
                 fontsize=12.5, fontweight="bold", y=1.04)
    plt.savefig(os.path.join(OUTDIR, "FigureA4_Correlation_Map.png"))
    plt.savefig(os.path.join(OUTDIR, "FigureA4_Correlation_Map.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5b. FIGURE A2b: REGIONAL CHART ORDERED BY HUMIDITY GRADIENT (Humid -> Arid)
# ---------------------------------------------------------------------------
def figure_regional_humidity_gradient(df):
    """Regional bar chart ordered by descending mean PWV.

    This is the rhetorical 'money plot' for the reviewer response: walking
    left-to-right (humid -> arid), absolute RMSE stays approximately flat
    while normalised RMSE rises sharply, making the inverse coupling
    between PWV magnitude and relative error visually self-evident.
    """
    reg = df.groupby("REGION", observed=True).mean(numeric_only=True)
    reg = reg.sort_values("MEAN_PWV_ERA5", ascending=False)
    region_labels = list(reg.index)
    pwv_values    = reg["MEAN_PWV_ERA5"].values

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9.5), sharex=True,
                                    gridspec_kw={"hspace": 0.18})
    x = np.arange(len(reg))
    w = 0.26
    datasets = ["IGS", "ERA5", "VMF3"]
    dataset_legend = {"IGS": "IGS (GNSS)", "ERA5": "ERA5", "VMF3": "VMF3"}

    # ---------- (a) Absolute RMSE ----------
    bars_top = []
    for i, d in enumerate(datasets):
        off = (i - 1) * w
        b = ax1.bar(x + off, reg[f"RMSE_{d}_ETC"], w,
                    color=COL_UNI[d], label=dataset_legend[d],
                    edgecolor="black", linewidth=0.6)
        bars_top.append(b)
    ax1.set_ylabel("Absolute RMSE (mm)")
    ax1.set_title("(a) Regional Comparison: Absolute ETC RMSE", loc="left")
    ax1.set_ylim(0, reg[["RMSE_IGS_ETC","RMSE_ERA5_ETC","RMSE_VMF3_ETC"]].values.max() * 1.20)
    ax1.legend(loc="upper right", fontsize=10, title="Dataset",
               title_fontsize=10, frameon=True, edgecolor="0.5",
               framealpha=0.95)
    for bars in bars_top:
        annotate_bars(ax1, bars, fmt="{:.1f}", fontsize=10, offset=0.014)
    ax1.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax1.set_axisbelow(True)

    # ---------- (b) Normalised nRMSE ----------
    bars_bot = []
    for i, d in enumerate(datasets):
        off = (i - 1) * w
        b = ax2.bar(x + off, reg[f"nRMSE_{d}_ETC_pct"], w,
                    color=COL_UNI[d], label=dataset_legend[d],
                    edgecolor="black", linewidth=0.6)
        bars_bot.append(b)
    ax2.set_ylabel("Normalised RMSE (%)")
    ax2.set_title("(b) Regional Comparison: Normalised ETC RMSE (nRMSE)",
                  loc="left")
    ax2.set_xlabel("Region (Ordered by Mean PWV: Humid \u2192 Arid)",
                   labelpad=22)
    ax2.set_xticks(x)
    ax2.set_xticklabels(region_labels, fontsize=11)
    ymax = reg[["nRMSE_IGS_ETC_pct","nRMSE_ERA5_ETC_pct","nRMSE_VMF3_ETC_pct"]].values.max()
    ax2.set_ylim(-ymax * 0.18, ymax * 1.20)  # negative headroom for PWV annotations
    for bars in bars_bot:
        annotate_bars(ax2, bars, fmt="{:.1f}%", fontsize=10, offset=0.014)
    ax2.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax2.set_axisbelow(True)
    ax2.axhline(0, color="0.5", linewidth=0.8)

    # Mean PWV annotations below x-axis baseline
    for xi, pwv in zip(x, pwv_values):
        ax2.text(xi, -ymax * 0.08, f"Mean PWV: {pwv:.1f} mm",
                 ha="center", va="top", fontsize=10, color="0.30",
                 fontweight="bold")

    fig.suptitle("Figure A2b.  Regional ETC Error along the African "
                 "Humidity Gradient",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.savefig(os.path.join(OUTDIR, "FigureA2b_Regional_Humidity_Gradient.png"),
                bbox_inches="tight")
    plt.savefig(os.path.join(OUTDIR, "FigureA2b_Regional_Humidity_Gradient.pdf"),
                bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5c. FIGURE A5: INTER-PRODUCT GAP AMPLIFICATION (mm vs %)
# ---------------------------------------------------------------------------
def figure_gap_amplification(df):
    """Quantify how the IGS-vs-reanalysis performance gap changes when
    expressed in absolute (mm) vs normalised (%) terms across regions.

    A flat gap in mm but an expanding gap in % is the empirical
    fingerprint of the SNR / scale-invariance story.
    """
    reg = df.groupby("REGION", observed=True).mean(numeric_only=True)
    reg = reg.sort_values("MEAN_PWV_ERA5", ascending=False)

    # IGS deficit relative to ERA5 (the best reanalysis baseline)
    gap_abs  = reg["RMSE_IGS_ETC"]      - reg["RMSE_ERA5_ETC"]
    gap_norm = reg["nRMSE_IGS_ETC_pct"] - reg["nRMSE_ERA5_ETC_pct"]
    region_labels = list(reg.index)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13.5, 5.5),
                                    gridspec_kw={"wspace": 0.28})
    x = np.arange(len(reg))

    # Left -- absolute gap (mm)
    bA = axL.bar(x, gap_abs.values, 0.55, color=COL_UNI["IGS"],
                 edgecolor="black", linewidth=0.6, alpha=0.92)
    axL.set_xticks(x)
    axL.set_xticklabels(region_labels, fontsize=10)
    axL.set_ylabel("IGS \u2212 ERA5 gap  (mm)", fontweight="bold")
    axL.set_title("(a) Absolute performance gap: IGS \u2212 ERA5",
                  loc="left", fontsize=11.5)
    axL.set_ylim(0, gap_abs.max() * 1.25)
    annotate_bars(axL, bA, fmt="{:.2f}", fontsize=10, offset=0.015)
    axL.grid(True, axis="y", alpha=0.3, linestyle="--")
    axL.set_axisbelow(True)

    # Right -- normalised gap (% pts)
    bB = axR.bar(x, gap_norm.values, 0.55, color=COL_UNI["ERA5"],
                 edgecolor="black", linewidth=0.6, hatch="//", alpha=0.92)
    axR.set_xticks(x)
    axR.set_xticklabels(region_labels, fontsize=10)
    axR.set_ylabel("IGS \u2212 ERA5 gap  (% pts)", fontweight="bold")
    axR.set_title("(b) Normalised performance gap: IGS \u2212 ERA5",
                  loc="left", fontsize=11.5)
    axR.set_ylim(0, gap_norm.max() * 1.25)
    annotate_bars(axR, bB, fmt="{:.2f}", fontsize=10, offset=0.015)
    axR.grid(True, axis="y", alpha=0.3, linestyle="--")
    axR.set_axisbelow(True)

    # Common x-axis annotation: mean PWV (placed in a dedicated lower row to
    # avoid clashing with the rotated region labels)
    for ax in (axL, axR):
        ax.set_xlabel("Region (Humid \u2192 Arid)", fontweight="bold",
                      labelpad=42)
        # Rotate region labels slightly for readability
        for tick in ax.get_xticklabels():
            tick.set_rotation(15)
            tick.set_ha("right")
        # PWV annotations sit well below the rotated tick labels
        for xi, region in zip(x, region_labels):
            pwv = reg.loc[region, "MEAN_PWV_ERA5"]
            ax.annotate(f"{pwv:.1f} mm",
                        xy=(xi, 0), xycoords=("data", "axes fraction"),
                        xytext=(0, -34), textcoords="offset points",
                        ha="center", va="top",
                        fontsize=9, color="0.30", fontweight="bold")

    fig.suptitle("Figure A5.  Gap Amplification -- How Normalisation "
                 "Re-Scales the IGS Deficit across Regions",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.savefig(os.path.join(OUTDIR, "FigureA5_Gap_Amplification.png"),
                bbox_inches="tight")
    plt.savefig(os.path.join(OUTDIR, "FigureA5_Gap_Amplification.pdf"),
                bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5d. FIGURE A6: CLIMATOLOGY-COLOURED SCATTER (nRMSE vs PWV)
# ---------------------------------------------------------------------------
def figure_climatology_scatter(df):
    """A single, compact 'graphical abstract'-style scatter:
       x-axis (log): mean ERA5 PWV
       y-axis:       normalised IGS nRMSE
       colour:       region
       marker size:  proportional to absolute IGS RMSE_ETC

    Captures the entire reviewer concern in a single panel.
    """
    fig, ax = plt.subplots(figsize=(11.5, 6.8))

    # Plot one region at a time so each ends up in the legend
    for region in REGION_ORDER:
        sub = df[df["REGION"] == region]
        sizes = (sub["RMSE_IGS_ETC"] - 1.0).clip(lower=0.1) * 350 + 70
        ax.scatter(sub["MEAN_PWV_ERA5"], sub["nRMSE_IGS_ETC_pct"],
                   s=sizes, color=COL_REGION[region],
                   edgecolor="black", linewidth=0.6, alpha=0.85,
                   label=region)
        # Station labels for outliers (top-3 highest nRMSE per region)
        top = sub.nlargest(min(3, len(sub)), "nRMSE_IGS_ETC_pct")
        for _, r in top.iterrows():
            ax.annotate(r["STN"],
                        (r["MEAN_PWV_ERA5"], r["nRMSE_IGS_ETC_pct"]),
                        xytext=(7, 4), textcoords="offset points",
                        fontsize=8.5, fontweight="bold",
                        color="0.20")

    # Power-law trend fit on log-x
    logx = np.log(df["MEAN_PWV_ERA5"])
    y    = df["nRMSE_IGS_ETC_pct"]
    slope, intercept = np.polyfit(logx, y, 1)
    xs = np.linspace(df["MEAN_PWV_ERA5"].min() * 0.92,
                     df["MEAN_PWV_ERA5"].max() * 1.05, 200)
    ys = intercept + slope * np.log(xs)
    rho = df["MEAN_PWV_ERA5"].corr(df["nRMSE_IGS_ETC_pct"])
    ax.plot(xs, ys, "--", color="0.25", lw=1.6,
            label=fr"log-x fit  ($r$ = {rho:+.2f})")

    ax.set_xscale("log")
    ax.set_xlabel("Mean ERA5 PWV (mm, log scale)", fontweight="bold")
    ax.set_ylabel("Normalised IGS nRMSE$_{ETC}$ (%)", fontweight="bold")
    ax.set_title("Figure A6.  Climatology-coloured scatter: relative IGS "
                 "uncertainty inflates as PWV decreases\n"
                 "(marker size \u221d absolute IGS RMSE$_{ETC}$; n = 27 stations)",
                 fontsize=11.5, fontweight="bold", loc="left", pad=14)

    ax.grid(True, which="both", alpha=0.28, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_xlim(df["MEAN_PWV_ERA5"].min() * 0.85,
                df["MEAN_PWV_ERA5"].max() * 1.08)
    ax.set_ylim(0, df["nRMSE_IGS_ETC_pct"].max() * 1.15)

    # Build a tidy combined legend (regions + trend)
    handles, labels = ax.get_legend_handles_labels()
    leg = ax.legend(handles, labels, loc="upper right", fontsize=9.5,
                    framealpha=0.95, edgecolor="0.5",
                    title="Region / Fit", title_fontsize=10)

    # Size-scale guide placed in the data-empty lower-left corner using
    # axes-fraction coordinates so it never overlaps the points.
    ref_vals  = [1.2, 1.6, 2.0]
    ref_sizes = [(v - 1.0) * 350 + 70 for v in ref_vals]
    # Background box for the size legend
    ax.text(0.02, 0.13, "Marker size \u2192 abs IGS RMSE (mm)",
            transform=ax.transAxes, fontsize=8.8, fontweight="bold",
            color="0.20",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="0.6", alpha=0.92))
    for i, (v, s) in enumerate(zip(ref_vals, ref_sizes)):
        xf = 0.045 + i * 0.075
        yf = 0.06
        ax.scatter(xf, yf, s=s, color="white",
                   edgecolor="0.25", linewidth=0.8, alpha=0.95,
                   transform=ax.transAxes, zorder=5)
        ax.text(xf, yf - 0.045, f"{v:.1f}", transform=ax.transAxes,
                ha="center", fontsize=8.3, color="0.20", zorder=5)

    plt.savefig(os.path.join(OUTDIR, "FigureA6_Climatology_Scatter.png"),
                bbox_inches="tight")
    plt.savefig(os.path.join(OUTDIR, "FigureA6_Climatology_Scatter.pdf"),
                bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5e. FIGURE A2.1 / A2.2: STATION-LEVEL WITH REGIONAL DIVIDERS (redesigned A1)
# ---------------------------------------------------------------------------
def figure_station_level_v2(df, *, background="transparent",
                            xtick_mode="station+lat",
                            pwv_overlay=False,
                            outfile_basename="FigureA2_1_Station_Level_with_Dividers",
                            fig_title_prefix="Figure A2.1"):
    """Station-level absolute vs normalised ETC RMSE, redesigned in the
    style of the reference Mean-PWV figure: bold region headers at the top,
    coloured dashed vertical dividers between sub-regions, and bold tick
    labels.

    Parameters
    ----------
    background : {"transparent", "white"}
        Figure / axes background. "transparent" matches the reference image
        styling (A2.1). "white" gives a solid white background (A2.2 / A2.3).
    xtick_mode : {"station", "station+lat", "station+pwv"}
        Controls the x-axis tick-label format:
          - "station"      \u2192 just the four-letter station code (A2.2 / A2.4)
          - "station+lat"  \u2192 "RABT (+34.00)\u00b0"  (A2.1)
          - "station+pwv"  \u2192 "RABT (20.8 mm)"     (A2.3)
        The corresponding x-axis title is set automatically.
    pwv_overlay : bool
        If True (A2.4), overlay a Mean PWV curve on a dual right-hand y-axis
        in each of the two panels, in the style of Figure A4(b). The right
        y-axis is colour-keyed (green) so the reader can tell the bars from
        the overlay at a glance.
    outfile_basename : str
        Filename stem (without extension) for the PNG and PDF output.
    fig_title_prefix : str
        Leading label of the suptitle (e.g. "Figure A2.1" / "A2.2" / "A2.3").
    """
    # Bold defaults for this figure only (saved/restored locally)
    saved_rc = {k: plt.rcParams[k] for k in
                ("axes.spines.top", "axes.spines.right",
                 "axes.grid", "grid.alpha")}
    plt.rcParams.update({
        "axes.spines.top"   : True,
        "axes.spines.right" : True,
        "axes.grid"         : True,
        "grid.alpha"        : 0.30,
    })

    # ---- Region divider colours (one per sub-region boundary) ----
    # Mirrors the reference figure: black, blue, green, red, purple
    DIVIDER_COLORS = ["black", "blue", "green", "red", "purple"]
    # Header text colour for each region (black, as in reference)
    HEADER_COLOR = "black"

    # Sort by STATION_ORDER (already enforced in load_data)
    df = df.sort_values("STN").reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(17, 11), sharex=True,
        gridspec_kw={"hspace": 0.32}
    )
    # Figure / axes background
    if background == "transparent":
        fig.patch.set_alpha(0.0)
    else:
        fig.patch.set_facecolor("white")

    x = np.arange(len(df))
    w = 0.27

    # ---------- top : absolute ETC RMSE ----------
    b1 = ax1.bar(x - w, df["RMSE_IGS_ETC"],  w, color=COL_ABS["IGS"],
                 label="IGS",  edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    b2 = ax1.bar(x,     df["RMSE_ERA5_ETC"], w, color=COL_ABS["ERA5"],
                 label="ERA5", edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    b3 = ax1.bar(x + w, df["RMSE_VMF3_ETC"], w, color=COL_ABS["VMF3"],
                 label="VMF3", edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    if background == "transparent":
        ax1.patch.set_alpha(0.0)
    else:
        ax1.set_facecolor("white")

    ax1.set_ylabel("Absolute ETC RMSE (mm)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    # Panel (a) label placed INSIDE the plot area (top-left), so the
    # region-header band above can use the full plot width without collision.
    ax1.text(0.005, 0.95, "(a) Station-Level Absolute ETC RMSE",
             transform=ax1.transAxes, ha="left", va="top",
             fontsize=US["panel_title_fontsize"],
             fontweight=US["panel_title_fontweight"],
             bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                       edgecolor="0.5", alpha=0.92))
    abs_max = df[["RMSE_IGS_ETC","RMSE_ERA5_ETC","RMSE_VMF3_ETC"]].values.max()
    ax1.set_ylim(0, abs_max * 1.22)
    leg1 = ax1.legend(loc="upper right", ncol=1,
                      fontsize=US["legend_fontsize"],
                      title="Dataset",
                      title_fontsize=US["legend_title_fontsize"],
                      frameon=True,
                      edgecolor=US["legend_frame_edgecolor"],
                      framealpha=US["legend_framealpha"],
                      bbox_to_anchor=(0.999, 0.999))
    leg1.get_title().set_fontweight(US["legend_title_fontweight"])
    for bars in (b1, b2, b3):
        annotate_bars(ax1, bars, fmt="{:.2f}", offset=0.010)
    ax1.tick_params(axis="y", labelsize=US["tick_label_fontsize"])
    apply_tick_label_weight(ax1, axis="y")

    # ---------- Optional: dual-axis PWV overlay on panel (a) -----------
    if pwv_overlay:
        ax1R = ax1.twinx()
        ax1R.plot(x, df["MEAN_PWV_ERA5"].values,
                  color=COL_UNI["VMF3"], marker="o", markersize=5,
                  linewidth=1.6, linestyle="-",
                  markeredgecolor="black", markeredgewidth=0.4,
                  label="Mean PWV", zorder=5)
        ax1R.set_ylabel("Mean ERA5 PWV (mm)",
                        fontsize=US["axis_label_fontsize"],
                        fontweight=US["axis_label_fontweight"],
                        color=COL_UNI["VMF3"])
        ax1R.tick_params(axis="y", labelsize=US["tick_label_fontsize"],
                         labelcolor=COL_UNI["VMF3"])
        for lbl in ax1R.get_yticklabels():
            lbl.set_fontweight(US["tick_label_fontweight"])
        ax1R.spines["right"].set_visible(True)
        ax1R.spines["right"].set_color(COL_UNI["VMF3"])
        ax1R.spines["right"].set_linewidth(US["spine_linewidth"])
        ax1R.grid(False)
        # match y-limits to leave headroom for region headers
        pwv_max = df["MEAN_PWV_ERA5"].max()
        ax1R.set_ylim(0, pwv_max * 1.30)
        # add PWV to the legend by collecting both axes' handles
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax1R.get_legend_handles_labels()
        leg1.remove()
        leg_combined = ax1.legend(h1 + h2, l1 + l2,
                                  loc="upper right", ncol=1,
                                  fontsize=US["legend_fontsize"],
                                  title="Dataset",
                                  title_fontsize=US["legend_title_fontsize"],
                                  frameon=True,
                                  edgecolor=US["legend_frame_edgecolor"],
                                  framealpha=US["legend_framealpha"],
                                  bbox_to_anchor=(0.999, 0.999))
        leg_combined.get_title().set_fontweight(US["legend_title_fontweight"])

    # ---------- bottom : normalised ETC nRMSE ----------
    b4 = ax2.bar(x - w, df["nRMSE_IGS_ETC_pct"],  w, color=COL_NORM["IGS"],
                 label="IGS",  hatch="//", edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    b5 = ax2.bar(x,     df["nRMSE_ERA5_ETC_pct"], w, color=COL_NORM["ERA5"],
                 label="ERA5", hatch="//", edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    b6 = ax2.bar(x + w, df["nRMSE_VMF3_ETC_pct"], w, color=COL_NORM["VMF3"],
                 label="VMF3", hatch="//", edgecolor=US["bar_edgecolor"],
                 linewidth=US["bar_edgewidth"])
    if background == "transparent":
        ax2.patch.set_alpha(0.0)
    else:
        ax2.set_facecolor("white")

    ax2.set_ylabel("Normalised ETC nRMSE (%)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    if xtick_mode == "station+lat":
        xlabel_text = "IGS Station (Latitude)"
    elif xtick_mode == "station+pwv":
        xlabel_text = "IGS Station (Mean PWV)"
    else:
        xlabel_text = "IGS Station"
    ax2.set_xlabel(xlabel_text,
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"],
                   labelpad=8)
    ax2.text(0.005, 0.95, "(b) Station-Level Normalised ETC nRMSE",
             transform=ax2.transAxes, ha="left", va="top",
             fontsize=US["panel_title_fontsize"],
             fontweight=US["panel_title_fontweight"],
             bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                       edgecolor="0.5", alpha=0.92))
    norm_max = df[["nRMSE_IGS_ETC_pct","nRMSE_ERA5_ETC_pct",
                   "nRMSE_VMF3_ETC_pct"]].values.max()
    ax2.set_ylim(0, norm_max * 1.22)
    leg2 = ax2.legend(loc="upper right", ncol=1,
                      fontsize=US["legend_fontsize"],
                      title="Dataset",
                      title_fontsize=US["legend_title_fontsize"],
                      frameon=True,
                      edgecolor=US["legend_frame_edgecolor"],
                      framealpha=US["legend_framealpha"],
                      bbox_to_anchor=(0.999, 0.999))
    leg2.get_title().set_fontweight(US["legend_title_fontweight"])
    for bars in (b4, b5, b6):
        annotate_bars(ax2, bars, fmt="{:.1f}", offset=0.010)
    ax2.tick_params(axis="y", labelsize=US["tick_label_fontsize"])
    apply_tick_label_weight(ax2, axis="y")

    # ---------- Optional: dual-axis PWV overlay on panel (b) -----------
    if pwv_overlay:
        ax2R = ax2.twinx()
        ax2R.plot(x, df["MEAN_PWV_ERA5"].values,
                  color=COL_UNI["VMF3"], marker="o", markersize=5,
                  linewidth=1.6, linestyle="-",
                  markeredgecolor="black", markeredgewidth=0.4,
                  label="Mean PWV", zorder=5)
        ax2R.set_ylabel("Mean ERA5 PWV (mm)",
                        fontsize=US["axis_label_fontsize"],
                        fontweight=US["axis_label_fontweight"],
                        color=COL_UNI["VMF3"])
        ax2R.tick_params(axis="y", labelsize=US["tick_label_fontsize"],
                         labelcolor=COL_UNI["VMF3"])
        for lbl in ax2R.get_yticklabels():
            lbl.set_fontweight(US["tick_label_fontweight"])
        ax2R.spines["right"].set_visible(True)
        ax2R.spines["right"].set_color(COL_UNI["VMF3"])
        ax2R.spines["right"].set_linewidth(US["spine_linewidth"])
        ax2R.grid(False)
        pwv_max = df["MEAN_PWV_ERA5"].max()
        ax2R.set_ylim(0, pwv_max * 1.30)
        h1, l1 = ax2.get_legend_handles_labels()
        h2, l2 = ax2R.get_legend_handles_labels()
        leg2.remove()
        leg_combined2 = ax2.legend(h1 + h2, l1 + l2,
                                   loc="upper right", ncol=1,
                                   fontsize=US["legend_fontsize"],
                                   title="Dataset",
                                   title_fontsize=US["legend_title_fontsize"],
                                   frameon=True,
                                   edgecolor=US["legend_frame_edgecolor"],
                                   framealpha=US["legend_framealpha"],
                                   bbox_to_anchor=(0.999, 0.999))
        leg_combined2.get_title().set_fontweight(US["legend_title_fontweight"])

    # X-axis tick labels: station name (+ latitude or PWV when requested)
    if xtick_mode == "station+lat":
        xtick_labels = [f"{r['STN']} ({r['STN_LAT']:+.2f})\u00b0"
                        for _, r in df.iterrows()]
    elif xtick_mode == "station+pwv":
        xtick_labels = [f"{r['STN']} ({r['MEAN_PWV_ERA5']:.1f} mm)"
                        for _, r in df.iterrows()]
    else:
        xtick_labels = [str(r["STN"]) for _, r in df.iterrows()]
    ax2.set_xticks(x)
    ax2.set_xticklabels(xtick_labels, rotation=90, ha="center",
                        fontsize=US["category_tick_fontsize"],
                        fontweight=US["category_tick_fontweight"])

    # ---------- Region dividers and headers ----------
    region_groups = df.groupby("REGION", observed=True).indices

    # Compute each region's left edge, right edge, centre on the x-axis
    region_spans = []
    for region in REGION_ORDER:
        if region not in region_groups:
            continue
        idx = region_groups[region]
        if len(idx) == 0:
            continue
        x0 = idx[0]  - 0.5
        x1 = idx[-1] + 0.5
        region_spans.append((region, x0, x1))

    # Vertical dashed dividers between adjacent regions, plus the two outer
    # edges of the plot, each in a distinct colour from DIVIDER_COLORS.
    for ax in (ax1, ax2):
        boundaries = [region_spans[0][1]] + \
                     [r[2] for r in region_spans]
        for i, xb in enumerate(boundaries):
            color = DIVIDER_COLORS[i % len(DIVIDER_COLORS)]
            ax.axvline(xb, color=color,
                       linestyle=US["divider_linestyle"],
                       linewidth=US["divider_linewidth"],
                       alpha=US["divider_alpha"], zorder=0)

    # Region headers placed in a clean band ABOVE the upper panel.
    NARROW_REGIONS = {"Northern Africa", "Central Africa"}
    NARROW_LABEL = {"Northern Africa": "Northern Africa",
                    "Central Africa":  "Central Africa"}
    x_total = region_spans[-1][2] - region_spans[0][1]
    x_start = region_spans[0][1]

    narrow_y_levels = {"Northern Africa": 1.04, "Central Africa": 1.18}
    for region, x0, x1 in region_spans:
        xc = (x0 + x1) / 2
        xf = (xc - x_start) / x_total
        if region in NARROW_REGIONS:
            yf = narrow_y_levels[region]
            ax1.text(xf, yf, NARROW_LABEL[region],
                     ha="center", va="bottom",
                     fontsize=US["region_header_narrow_fontsize"],
                     fontweight=US["region_header_fontweight"],
                     color=US["region_header_color"],
                     transform=ax1.transAxes, clip_on=False)
            ax1.annotate("", xy=(xf, 1.005), xytext=(xf, yf - 0.005),
                         xycoords=ax1.transAxes,
                         arrowprops=dict(arrowstyle="-", color="0.4",
                                         lw=0.8))
        else:
            ax1.text(xf, 1.04, region,
                     ha="center", va="bottom",
                     fontsize=US["region_header_fontsize"],
                     fontweight=US["region_header_fontweight"],
                     color=US["region_header_color"],
                     transform=ax1.transAxes, clip_on=False)

    # Tight x-axis to avoid extra whitespace on either edge
    ax2.set_xlim(region_spans[0][1] - 0.05,
                 region_spans[-1][2] + 0.05)

    # Apply user-configured spine styling
    for ax in (ax1, ax2):
        apply_spines(ax)

    fig.suptitle(f"{fig_title_prefix}.  Station-Level Absolute vs Normalised "
                 f"ETC RMSE across 27 African IGS Stations\n"
                 f"(grouped by sub-region; coloured dashed lines mark region boundaries)",
                 fontsize=US["suptitle_fontsize"],
                 fontweight=US["suptitle_fontweight"], y=0.998)

    plt.subplots_adjust(top=0.84, bottom=0.16, left=0.07, right=0.99)

    transparent_save = (background == "transparent")
    plt.savefig(os.path.join(OUTDIR, f"{outfile_basename}.png"),
                bbox_inches="tight", transparent=transparent_save,
                facecolor=("none" if transparent_save else "white"))
    plt.savefig(os.path.join(OUTDIR, f"{outfile_basename}.pdf"),
                bbox_inches="tight", transparent=transparent_save,
                facecolor=("none" if transparent_save else "white"))
    plt.close(fig)

    # Restore rcParams
    plt.rcParams.update(saved_rc)


# ---------------------------------------------------------------------------
# 5f. FIGURE A7: HOW RMSE / nRMSE RELATE TO THE ETC CORRELATION R
# ---------------------------------------------------------------------------
def figure_rmse_R_relationship(df):
    """Visualise how the ETC error metrics (absolute RMSE, normalised nRMSE)
    relate to the ETC correlation R for each of the three PWV products.

    Two panels:
      (a) R_ETC vs absolute RMSE_ETC  -- weak coupling within products,
          stronger coupling when pooled (because pooling samples across
          systematic product-quality differences).
      (b) R_ETC vs normalised nRMSE_ETC  -- tighter relationship, because
          both quantities are scaled by the local signal and thus reflect
          the same SNR information from two angles.
      (c) Empirical test of the McColl identity (1 - R^2) versus nRMSE^2.
    """
    saved_rc = {k: plt.rcParams[k] for k in
                ("axes.spines.top", "axes.spines.right")}
    plt.rcParams.update({"axes.spines.top": True,
                         "axes.spines.right": True})

    # Stack into long format
    records = []
    for d in ["IGS", "ERA5", "VMF3"]:
        for _, r in df.iterrows():
            records.append({
                "DATASET": d,
                "STN":     r["STN"],
                "REGION":  r["REGION"],
                "MEAN_PWV": r["MEAN_PWV_ERA5"],
                "RMSE":    r[f"RMSE_{d}_ETC"],
                "nRMSE":   r[f"nRMSE_{d}_ETC_pct"],
                "R":       r[f"R_{d}_ETC"],
            })
    long = pd.DataFrame(records)
    long["R2"] = long["R"] ** 2
    long["one_minus_R2"] = 1 - long["R2"]

    # Per-dataset markers/colours
    MARK   = {"IGS": "o",  "ERA5": "s",  "VMF3": "D"}
    COLOR  = {"IGS": COL_UNI["IGS"], "ERA5": COL_UNI["ERA5"],
              "VMF3": COL_UNI["VMF3"]}

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6),
                             gridspec_kw={"wspace": 0.32})
    axA, axB, axC = axes
    fig.patch.set_facecolor("white")
    for ax in axes:
        ax.set_facecolor("white")

    # ---------- (a) R vs Absolute RMSE ----------
    for d in ["IGS", "ERA5", "VMF3"]:
        sub = long[long.DATASET == d]
        rho = sub["R"].corr(sub["RMSE"])
        axA.scatter(sub["RMSE"], sub["R"],
                    s=55, marker=MARK[d], color=COLOR[d],
                    edgecolor="black", linewidth=0.5, alpha=0.85,
                    label=f"{d}  (r = {rho:+.2f})")
    # Pooled regression line
    rho_pool_abs = long["R"].corr(long["RMSE"])
    z = np.polyfit(long["RMSE"], long["R"], 1)
    xs = np.linspace(long["RMSE"].min() * 0.95, long["RMSE"].max() * 1.05, 100)
    axA.plot(xs, np.poly1d(z)(xs), "--", color="0.30", lw=1.6,
             label=f"Pooled fit  (r = {rho_pool_abs:+.2f})")

    axA.set_xlabel("Absolute ETC RMSE (mm)", fontsize=12, fontweight="bold")
    axA.set_ylabel(r"ETC Correlation  $R_{ETC}$", fontsize=12, fontweight="bold")
    axA.set_title("(a) $R_{ETC}$ vs Absolute RMSE", loc="left",
                  fontsize=12, fontweight="bold")
    axA.legend(loc="lower left", fontsize=9, frameon=True, edgecolor="0.5",
               framealpha=0.95)
    axA.grid(True, alpha=0.3, linestyle="--")
    axA.set_axisbelow(True)

    # ---------- (b) R vs Normalised nRMSE ----------
    for d in ["IGS", "ERA5", "VMF3"]:
        sub = long[long.DATASET == d]
        rho = sub["R"].corr(sub["nRMSE"])
        axB.scatter(sub["nRMSE"], sub["R"],
                    s=55, marker=MARK[d], color=COLOR[d],
                    edgecolor="black", linewidth=0.5, alpha=0.85,
                    label=f"{d}  (r = {rho:+.2f})")
    rho_pool_norm = long["R"].corr(long["nRMSE"])
    z = np.polyfit(long["nRMSE"], long["R"], 1)
    xs = np.linspace(long["nRMSE"].min() * 0.95, long["nRMSE"].max() * 1.05, 100)
    axB.plot(xs, np.poly1d(z)(xs), "--", color="0.30", lw=1.6,
             label=f"Pooled fit  (r = {rho_pool_norm:+.2f})")

    axB.set_xlabel("Normalised ETC nRMSE (%)", fontsize=12, fontweight="bold")
    axB.set_ylabel(r"ETC Correlation  $R_{ETC}$", fontsize=12, fontweight="bold")
    axB.set_title("(b) $R_{ETC}$ vs Normalised nRMSE", loc="left",
                  fontsize=12, fontweight="bold")
    axB.legend(loc="lower left", fontsize=9, frameon=True, edgecolor="0.5",
               framealpha=0.95)
    axB.grid(True, alpha=0.3, linestyle="--")
    axB.set_axisbelow(True)

    # ---------- (c) McColl identity check: (1 - R^2) vs nRMSE^2 ----------
    for d in ["IGS", "ERA5", "VMF3"]:
        sub = long[long.DATASET == d]
        axC.scatter(sub["nRMSE"]**2, sub["one_minus_R2"],
                    s=55, marker=MARK[d], color=COLOR[d],
                    edgecolor="black", linewidth=0.5, alpha=0.85,
                    label=d)
    rho_pool_id = (long["nRMSE"]**2).corr(long["one_minus_R2"])
    z = np.polyfit(long["nRMSE"]**2, long["one_minus_R2"], 1)
    xs = np.linspace((long["nRMSE"]**2).min() * 0.95,
                     (long["nRMSE"]**2).max() * 1.05, 100)
    axC.plot(xs, np.poly1d(z)(xs), "--", color="0.30", lw=1.6,
             label=f"Pooled fit\n(r = {rho_pool_id:+.2f})")

    axC.set_xlabel(r"$\mathrm{nRMSE}_{ETC}^{\,2}$  (%$^2$)",
                   fontsize=12, fontweight="bold")
    axC.set_ylabel(r"$1 - R_{ETC}^{\,2}$  $\propto$  $1/(\mathrm{SNR}+1)$",
                   fontsize=12, fontweight="bold")
    axC.set_title("(c) McColl SNR identity test", loc="left",
                  fontsize=12, fontweight="bold")
    axC.legend(loc="upper left", fontsize=9, frameon=True, edgecolor="0.5",
               framealpha=0.95)
    axC.grid(True, alpha=0.3, linestyle="--")
    axC.set_axisbelow(True)

    fig.suptitle("Figure A7.  How Absolute and Normalised ETC RMSE Relate to "
                 "the ETC Correlation Coefficient $R_{ETC}$",
                 fontsize=13.5, fontweight="bold", y=1.02)

    plt.savefig(os.path.join(OUTDIR, "FigureA7_RMSE_R_Relationship.png"),
                bbox_inches="tight", facecolor="white")
    plt.savefig(os.path.join(OUTDIR, "FigureA7_RMSE_R_Relationship.pdf"),
                bbox_inches="tight", facecolor="white")
    plt.close(fig)

    plt.rcParams.update(saved_rc)


# ---------------------------------------------------------------------------
# 5g. FIGURE A8: GEOGRAPHIC STATION MAP COLOURED BY IGS nRMSE
# ---------------------------------------------------------------------------
def figure_station_map(df):
    """Geographic distribution of the 27 stations, coloured by normalised
    IGS ETC error (nRMSE) and sized by absolute IGS ETC RMSE.

    Two panels:
      (a) Map (longitude vs latitude) with a light graticule and schematic
          equator / tropic lines; marker colour = nRMSE, marker size = abs RMSE.
      (b) Companion lollipop ranked by nRMSE for precise, unambiguous reading
          (a map alone makes exact values hard to compare).

    No coastline library is required; the panel is a clean station-distribution
    map in the style accepted by most Earth-science journals for network plots.
    """
    saved_rc = {k: plt.rcParams[k] for k in
                ("axes.spines.top", "axes.spines.right",
                 "axes.grid", "grid.alpha")}
    plt.rcParams.update({"axes.spines.top": True,
                         "axes.spines.right": True})

    # Build a plotting frame with coordinates (LAT/LON come from stations CSV)
    stations = pd.read_csv(STATIONS_CSV)
    g = df.merge(stations[["SITE", "LON"]], left_on="STN",
                 right_on="SITE", how="left")
    # STN_LAT is already in df (loaded earlier); rename LON for clarity
    g = g.rename(columns={"LON": "STN_LON"})

    # Jitter co-located SUTH / SUTM so both are visible
    mask_sutm = g["STN"] == "SUTM"
    g.loc[mask_sutm, "STN_LON"] = g.loc[mask_sutm, "STN_LON"] + 1.4
    g.loc[mask_sutm, "STN_LAT"] = g.loc[mask_sutm, "STN_LAT"] - 1.1

    fig = plt.figure(figsize=(16, 8.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.22)
    axM = fig.add_subplot(gs[0, 0])
    axL = fig.add_subplot(gs[0, 1])
    fig.patch.set_facecolor("white")
    axM.set_facecolor("white")
    axL.set_facecolor("white")

    # ---- colour + size encodings ----
    nrmse = g["nRMSE_IGS_ETC_pct"].values
    absr  = g["RMSE_IGS_ETC"].values
    sizes = (absr - absr.min()) / (absr.max() - absr.min()) * 320 + 90
    cmap  = plt.cm.YlOrRd
    vmin, vmax = nrmse.min(), nrmse.max()

    # ---------- (a) MAP ----------
    # Light graticule
    axM.grid(True, which="both", alpha=US["grid_alpha"],
             linestyle=US["grid_linestyle"], linewidth=US["grid_linewidth"])
    axM.set_axisbelow(True)
    # Reference lines: equator and tropics
    for yval, lab in [(0, "Equator"), (23.44, "Tropic of Cancer"),
                      (-23.44, "Tropic of Capricorn")]:
        axM.axhline(yval, color="0.55", linestyle=":", linewidth=1.0,
                    zorder=1)
        axM.text(-29, yval + 0.8, lab,
                 fontsize=8.5, color="0.45", style="italic",
                 va="bottom", ha="left", clip_on=False, zorder=2)

    sc = axM.scatter(g["STN_LON"], g["STN_LAT"], c=nrmse, s=sizes,
                     cmap=cmap, vmin=vmin, vmax=vmax,
                     edgecolor="black", linewidth=0.7, alpha=0.92,
                     zorder=5)

    # Station labels with per-station offsets to reduce overlap in the
    # crowded Southern-African cluster.
    LABEL_OFFSETS = {
        "HRAO": (4, -9), "MFKG": (-26, 4), "HARB": (5, 5),
        "ULDI": (5, 4),  "RBAY": (6, -8), "DEAR": (6, -2),
        "SUTH": (7, 2),  "SUTM": (8, -8), "HNUS": (-10, -11),
        "SBOK": (-30, 2), "TDOU": (5, 3), "SEYG": (6, 5),
        "SEY2": (6, -9), "MBAR": (-6, 6), "MOIU": (5, 4),
        "VACS": (6, 2),  "BJCO": (5, -9), "YKRO": (-6, 8),
    }
    for _, r in g.iterrows():
        dx, dy = LABEL_OFFSETS.get(r["STN"], (4, 4))
        axM.annotate(r["STN"], (r["STN_LON"], r["STN_LAT"]),
                     xytext=(dx, dy), textcoords="offset points",
                     fontsize=7.5, fontweight="bold", color="0.15",
                     zorder=6)

    axM.set_xlabel("Longitude (\u00b0E)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axM.set_ylabel("Latitude (\u00b0N)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axM.set_title("(a) Station network coloured by IGS nRMSE",
                  loc="left", fontsize=US["panel_title_fontsize"],
                  fontweight=US["panel_title_fontweight"])
    axM.set_xlim(-30, 62)
    axM.set_ylim(-40, 40)
    apply_tick_label_weight(axM)
    apply_spines(axM)

    # Colourbar
    cbar = fig.colorbar(sc, ax=axM, fraction=0.046, pad=0.13)
    cbar.set_label("Normalised IGS nRMSE$_{ETC}$ (%)",
                   fontsize=12, fontweight="bold")
    for lbl in cbar.ax.get_yticklabels():
        lbl.set_fontweight(US["tick_label_fontweight"])

    # Size-reference legend (proxy handles)
    for ref in [1.2, 1.6, 2.0]:
        s = (ref - absr.min()) / (absr.max() - absr.min()) * 320 + 90
        axM.scatter([], [], s=s, color="0.75", edgecolor="black",
                    linewidth=0.6, label=f"{ref:.1f} mm")
    szleg = axM.legend(loc="lower left", fontsize=8.5,
                       title="abs RMSE", title_fontsize=9,
                       frameon=True, edgecolor="0.5", framealpha=0.95,
                       labelspacing=1.1, borderpad=0.8)
    szleg.get_title().set_fontweight("bold")

    # ---------- (b) LOLLIPOP ranked by nRMSE ----------
    gl = g.sort_values("nRMSE_IGS_ETC_pct", ascending=True).reset_index(drop=True)
    yy = np.arange(len(gl))
    colors = cmap((gl["nRMSE_IGS_ETC_pct"] - vmin) / (vmax - vmin))
    axL.hlines(yy, 0, gl["nRMSE_IGS_ETC_pct"], color="0.7", linewidth=1.2,
               zorder=1)
    axL.scatter(gl["nRMSE_IGS_ETC_pct"], yy, c=colors, s=110,
                edgecolor="black", linewidth=0.6, zorder=3)
    for i, r in gl.iterrows():
        axL.text(r["nRMSE_IGS_ETC_pct"] + 0.18, i,
                 f"{r['nRMSE_IGS_ETC_pct']:.1f}", va="center",
                 fontsize=8, fontweight="bold", color="0.2")
    axL.set_yticks(yy)
    axL.set_yticklabels(gl["STN"], fontsize=8.5,
                        fontweight=US["category_tick_fontweight"])
    axL.set_xlabel("Normalised IGS nRMSE$_{ETC}$ (%)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axL.set_title("(b) Stations ranked by IGS nRMSE",
                  loc="left", fontsize=US["panel_title_fontsize"],
                  fontweight=US["panel_title_fontweight"])
    axL.set_xlim(0, gl["nRMSE_IGS_ETC_pct"].max() * 1.16)
    axL.grid(True, axis="x", alpha=US["grid_alpha"],
             linestyle=US["grid_linestyle"], linewidth=US["grid_linewidth"])
    axL.set_axisbelow(True)
    apply_tick_label_weight(axL, axis="x")
    apply_spines(axL)

    fig.suptitle("Figure A8.  Geographic Distribution of Normalised IGS ETC "
                 "Error \u2014 Relative Uncertainty Concentrates in the Arid South",
                 fontsize=US["suptitle_fontsize"],
                 fontweight=US["suptitle_fontweight"], y=0.97)

    plt.savefig(os.path.join(OUTDIR, "FigureA8_Station_Map_nRMSE.png"),
                bbox_inches="tight", facecolor="white")
    plt.savefig(os.path.join(OUTDIR, "FigureA8_Station_Map_nRMSE.pdf"),
                bbox_inches="tight", facecolor="white")
    plt.close(fig)

    plt.rcParams.update(saved_rc)


# ---------------------------------------------------------------------------
# 5h. FIGURE A9: AFRICA COASTLINE MAP COLOURED BY IGS nRMSE
# ---------------------------------------------------------------------------
def figure_station_map_geo(df):
    """Same content as Figure A8, but with an embedded Africa coastline
    backdrop and prominent, highlighted latitude reference lines (Equator,
    Tropic of Cancer, Tropic of Capricorn).

    Two panels:
      (a) Africa map with land polygon, highlighted tropics/equator, stations
          coloured by normalised IGS nRMSE and sized by absolute IGS RMSE.
      (b) Companion lollipop ranked by nRMSE for precise reading.

    Self-contained: the coastline is a built-in polygon (AFRICA_MAINLAND /
    AFRICA_MADAGASCAR), so no cartopy / shapefile downloads are needed.
    """
    saved_rc = {k: plt.rcParams[k] for k in
                ("axes.spines.top", "axes.spines.right",
                 "axes.grid", "grid.alpha")}
    plt.rcParams.update({"axes.spines.top": True,
                         "axes.spines.right": True})

    stations = pd.read_csv(STATIONS_CSV)
    g = df.merge(stations[["SITE", "LON"]], left_on="STN",
                 right_on="SITE", how="left")
    g = g.rename(columns={"LON": "STN_LON"})

    # Jitter co-located SUTH / SUTM so both are visible
    mask_sutm = g["STN"] == "SUTM"
    g.loc[mask_sutm, "STN_LON"] = g.loc[mask_sutm, "STN_LON"] + 1.4
    g.loc[mask_sutm, "STN_LAT"] = g.loc[mask_sutm, "STN_LAT"] - 1.1

    fig = plt.figure(figsize=(16, 8.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.22)
    axM = fig.add_subplot(gs[0, 0])
    axL = fig.add_subplot(gs[0, 1])
    fig.patch.set_facecolor("white")
    axM.set_facecolor("#EAF2FA")   # light "ocean" background
    axL.set_facecolor("white")

    # ---- colour + size encodings ----
    nrmse = g["nRMSE_IGS_ETC_pct"].values
    absr  = g["RMSE_IGS_ETC"].values
    sizes = (absr - absr.min()) / (absr.max() - absr.min()) * 320 + 90
    cmap  = plt.cm.YlOrRd
    vmin, vmax = nrmse.min(), nrmse.max()

    # ---------- (a) AFRICA MAP ----------
    # Land polygons (drawn first, behind everything)
    for poly in (AFRICA_MAINLAND, AFRICA_MADAGASCAR):
        xs, ys = zip(*poly)
        axM.fill(xs, ys, facecolor="#EDE8DA", edgecolor="0.35",
                 linewidth=1.3, zorder=1)

    # Highlighted reference lines: Equator (blue) + Tropics (red), with
    # shaded tropical band to make the climatic zones pop.
    axM.axhspan(-23.44, 23.44, color="#FCEFC7", alpha=0.35, zorder=0)
    ref_lines = [
        (0.0,    "Equator",             "#1F6FB2"),
        (23.44,  "Tropic of Cancer",    "#C0392B"),
        (-23.44, "Tropic of Capricorn", "#C0392B"),
    ]
    for yval, lab, col in ref_lines:
        axM.axhline(yval, color=col, linestyle="--", linewidth=1.8,
                    alpha=0.9, zorder=4)
        axM.text(-29.2, yval + 0.9, lab, fontsize=9, fontweight="bold",
                 color=col, style="italic", va="bottom", ha="left",
                 zorder=6,
                 bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                           edgecolor=col, linewidth=0.7, alpha=0.9))

    # Light graticule on top of land but below markers
    axM.grid(True, which="both", alpha=US["grid_alpha"],
             linestyle=US["grid_linestyle"], linewidth=US["grid_linewidth"],
             zorder=2)
    axM.set_axisbelow(False)

    sc = axM.scatter(g["STN_LON"], g["STN_LAT"], c=nrmse, s=sizes,
                     cmap=cmap, vmin=vmin, vmax=vmax,
                     edgecolor="black", linewidth=0.7, alpha=0.95,
                     zorder=5)

    # Station labels with the same offsets used in A8 to reduce overlap
    LABEL_OFFSETS = {
        "HRAO": (4, -9), "MFKG": (-26, 4), "HARB": (5, 5),
        "ULDI": (5, 4),  "RBAY": (6, -8), "DEAR": (6, -2),
        "SUTH": (7, 2),  "SUTM": (8, -8), "HNUS": (-10, -11),
        "SBOK": (-30, 2), "TDOU": (5, 3), "SEYG": (6, 5),
        "SEY2": (6, -9), "MBAR": (-6, 6), "MOIU": (5, 4),
        "VACS": (6, 2),  "BJCO": (5, -9), "YKRO": (-6, 8),
    }
    for _, r in g.iterrows():
        dx, dy = LABEL_OFFSETS.get(r["STN"], (4, 4))
        axM.annotate(r["STN"], (r["STN_LON"], r["STN_LAT"]),
                     xytext=(dx, dy), textcoords="offset points",
                     fontsize=7.5, fontweight="bold", color="0.12",
                     zorder=7)

    axM.set_xlabel("Longitude (\u00b0E)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axM.set_ylabel("Latitude (\u00b0N)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axM.set_title("(a) African station network coloured by IGS nRMSE",
                  loc="left", fontsize=US["panel_title_fontsize"],
                  fontweight=US["panel_title_fontweight"])
    axM.set_xlim(-30, 62)
    axM.set_ylim(-40, 40)
    axM.set_aspect(1.0)            # geographically faithful aspect ratio
    apply_tick_label_weight(axM)
    apply_spines(axM)

    cbar = fig.colorbar(sc, ax=axM, fraction=0.046, pad=0.13)
    cbar.set_label("Normalised IGS nRMSE$_{ETC}$ (%)",
                   fontsize=12, fontweight="bold")
    for lbl in cbar.ax.get_yticklabels():
        lbl.set_fontweight(US["tick_label_fontweight"])

    # Size-reference legend (proxy handles)
    for ref in [1.2, 1.6, 2.0]:
        s = (ref - absr.min()) / (absr.max() - absr.min()) * 320 + 90
        axM.scatter([], [], s=s, color="0.75", edgecolor="black",
                    linewidth=0.6, label=f"{ref:.1f} mm")
    szleg = axM.legend(loc="lower left", fontsize=8.5,
                       title="abs RMSE", title_fontsize=9,
                       frameon=True, edgecolor="0.5", framealpha=0.95,
                       labelspacing=1.1, borderpad=0.8)
    szleg.get_title().set_fontweight("bold")

    # ---------- (b) LOLLIPOP ranked by nRMSE ----------
    gl = g.sort_values("nRMSE_IGS_ETC_pct", ascending=True).reset_index(drop=True)
    yy = np.arange(len(gl))
    colors = cmap((gl["nRMSE_IGS_ETC_pct"] - vmin) / (vmax - vmin))
    axL.hlines(yy, 0, gl["nRMSE_IGS_ETC_pct"], color="0.7", linewidth=1.2,
               zorder=1)
    axL.scatter(gl["nRMSE_IGS_ETC_pct"], yy, c=colors, s=110,
                edgecolor="black", linewidth=0.6, zorder=3)
    for i, r in gl.iterrows():
        axL.text(r["nRMSE_IGS_ETC_pct"] + 0.18, i,
                 f"{r['nRMSE_IGS_ETC_pct']:.1f}", va="center",
                 fontsize=8, fontweight="bold", color="0.2")
    axL.set_yticks(yy)
    axL.set_yticklabels(gl["STN"], fontsize=8.5,
                        fontweight=US["category_tick_fontweight"])
    axL.set_xlabel("Normalised IGS nRMSE$_{ETC}$ (%)",
                   fontsize=US["axis_label_fontsize"],
                   fontweight=US["axis_label_fontweight"])
    axL.set_title("(b) Stations ranked by IGS nRMSE",
                  loc="left", fontsize=US["panel_title_fontsize"],
                  fontweight=US["panel_title_fontweight"])
    axL.set_xlim(0, gl["nRMSE_IGS_ETC_pct"].max() * 1.16)
    axL.grid(True, axis="x", alpha=US["grid_alpha"],
             linestyle=US["grid_linestyle"], linewidth=US["grid_linewidth"])
    axL.set_axisbelow(True)
    apply_tick_label_weight(axL, axis="x")
    apply_spines(axL)

    fig.suptitle("Figure A9.  Africa Station Map of Normalised IGS ETC Error "
                 "\u2014 Relative Uncertainty Concentrates in the Arid Subtropics",
                 fontsize=US["suptitle_fontsize"],
                 fontweight=US["suptitle_fontweight"], y=0.97)

    plt.savefig(os.path.join(OUTDIR, "FigureA9_Africa_Map_nRMSE.png"),
                bbox_inches="tight", facecolor="white")
    plt.savefig(os.path.join(OUTDIR, "FigureA9_Africa_Map_nRMSE.pdf"),
                bbox_inches="tight", facecolor="white")
    plt.close(fig)

    plt.rcParams.update(saved_rc)


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------
def main():
    df = load_data()
    figure_station_level(df)
    # A2.1 -- transparent background, station name + latitude
    figure_station_level_v2(
        df,
        background="transparent",
        xtick_mode="station+lat",
        outfile_basename="FigureA2_1_Station_Level_with_Dividers",
        fig_title_prefix="Figure A2.1",
    )
    # A2.2 -- white background, station name only (no latitude)
    figure_station_level_v2(
        df,
        background="white",
        xtick_mode="station",
        outfile_basename="FigureA2_2_Station_Level_with_Dividers_white",
        fig_title_prefix="Figure A2.2",
    )
    # A2.3 -- white background, station name + mean PWV (mm)
    figure_station_level_v2(
        df,
        background="white",
        xtick_mode="station+pwv",
        outfile_basename="FigureA2_3_Station_Level_with_PWV_white",
        fig_title_prefix="Figure A2.3",
    )
    # A2.4 -- white background, station name only, with PWV on right axis
    figure_station_level_v2(
        df,
        background="white",
        xtick_mode="station",
        pwv_overlay=True,
        outfile_basename="FigureA2_4_Station_Level_with_PWV_dual_axis",
        fig_title_prefix="Figure A2.4",
    )
    figure_regional_level(df)
    figure_regional_humidity_gradient(df)   # A2b -- NEW
    figure_continental_level(df)
    figure_correlation_map(df)
    figure_gap_amplification(df)            # A5  -- NEW
    figure_climatology_scatter(df)          # A6  -- NEW
    figure_rmse_R_relationship(df)          # A7  -- NEW
    figure_station_map(df)                  # A8  -- NEW
    figure_station_map_geo(df)              # A9  -- NEW
    print(f"All thirteen figures saved (PNG + PDF, {DPI} dpi) under: {OUTDIR}/")


if __name__ == "__main__":
    main()
