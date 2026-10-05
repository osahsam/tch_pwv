# -*- coding: utf-8 -*-
"""
================================================================================
 Detrending_analysis_stl_v3.py
 STL / Hampel Detrending Analysis for PWV Inter-comparison (AGU-quality output)
================================================================================

PURPOSE
-------
Decompose daily Precipitable Water Vapour (PWV) time series from several
products (e.g. IGS, VMF3, ERA5) into Trend, Seasonal and Residual components
using Seasonal-Trend decomposition based on Loess (STL), and quantify how much
the long-term trend actually influences the short-term variability that
3-Cornered-Hat (3CH) / Extended-Triple-Collocation (ETC) analyses rely on.

Central question:
    "Is trend removal (detrending) necessary before 3CH / ETC variability
     analysis, or does the trend contribute so little variance it can be
     safely ignored?"

For every station and product the script reports: STL decomposition, variance
decomposition, trend slope + significance, trend/seasonality strength F_T, F_S
(Wang, Smith & Hyndman, 2006), ADF stationarity before/after detrending, and
the change in short-term variability caused by detrending (delta-sigma).

--------------------------------------------------------------------------------
 WHAT IS NEW IN v3  (relative to v2)
--------------------------------------------------------------------------------
 New visualizations
   * Seasonal climatology (per station): the mean annual cycle of every product
     folded onto day-of-year with an inter-quartile envelope.
   * Spatial metric maps (cohort): station markers coloured by trend slope,
     trend strength F_T and variance reduction (requires a station-coordinate
     CSV; uses Cartopy if installed, otherwise a clean lon/lat scatter).
   * Metric heatmaps (cohort): station x product grids of F_T, F_S, variance
     reduction and delta-sigma for a one-glance overview of the whole cohort.
   * Residual diagnostics (per station x product): residual ACF, distribution
     vs. a fitted normal, and a normal Q-Q plot to demonstrate whitening.
   * Gap-marking bands: long data gaps are highlighted on the per-station
     decomposition panels with a transparent slate band, dashed edges and a
     duration label (configurable; --no-gap-shading to disable).

 New outputs / usability
   * Excel summary workbook (STL_Summary_Workbook.xlsx) with formatted,
     frozen-header sheets (Detailed results, per-product summary, ANOVA, and
     metric pivots) - values only, so zero formula errors.
   * Vector figure export: every figure can additionally be saved as PDF and/or
     SVG (publication-grade) alongside the PNG.
   * Command-line interface + optional YAML config, so paths and options no
     longer need editing in the file.  Precedence: built-in defaults < YAML
     config < command-line flags.  Overrides propagate correctly into the
     parallel worker processes.

 All v2 functionality is preserved (gap-aware plotting, per-station STL
 decomposition + variance-component figures, parallel STL+figure rendering,
 component CSV export, and every original table/figure/report).

--------------------------------------------------------------------------------
 INPUT DIRECTORY TREE  (INPUT_PATH may be a folder OR a .zip of that folder)
--------------------------------------------------------------------------------
 INPUT_PATH/
 |-- DAKR_cleaned_allmethods.csv
 |-- BJCO_cleaned_allmethods.csv
 |-- ...
 |   Each CSV: a 'DATE' column + one cleaned column per product named
 |   "<PRODUCT><CLEAN_SUFFIX>" (e.g. IGS_Hampel_clean). Extra columns are kept.

 OPTIONAL station-coordinate CSV (for the spatial maps), pointed to by
 COORDS_CSV / --coords. Must contain a station column plus latitude/longitude,
 recognised from any of these (case-insensitive) header names:
       station | site | code      (station id, matched to the CSV file prefix)
       lat | latitude
       lon | long | longitude

--------------------------------------------------------------------------------
 OUTPUT DIRECTORY TREE  (created under OUTPUT_ROOT)
--------------------------------------------------------------------------------
 OUTPUT_ROOT/
 |-- STL_Detailed_Results.csv             <- one row per station x product
 |-- Table1_Statistical_Summary.csv       <- per-product summary
 |-- Table2_ANOVA_Tests.csv               <- ANOVA / Kruskal-Wallis across products
 |-- Key_Findings_Report.txt              <- plain-text narrative report
 |-- STL_Summary_Workbook.xlsx            <- formatted multi-sheet workbook  [NEW]
 |
 |-- aggregate_figures/                   <- cohort-level figures
 |   |-- Fig1_Variance_Decomposition.png
 |   |-- Fig2_Trend_Slopes.png
 |   |-- Fig3_Stationarity_ADF.png
 |   |-- Fig4_Std_Comparison.png
 |   |-- Fig5_Variance_Reduction.png
 |   |-- Fig6_Aggregated_Variance_Reduction.png
 |   |-- Fig7_Strength_Metrics.png
 |   |-- Fig8_Metric_Heatmaps.png                                          [NEW]
 |   |-- Fig9_Spatial_Maps.png            (only if COORDS_CSV supplied)    [NEW]
 |   |-- Figure_Multipanel_Summary.png
 |   |   (+ .pdf / .svg copies of each, if VECTOR_FORMATS set)             [NEW]
 |
 |-- station_components/                  <- one enhanced CSV per station
 |   |-- DAKR_detrended.csv               (original cols + <PROD>_Trend,
 |   |-- ...                               _Seasonal, _Residual, _Trend_Detrended)
 |
 |-- station_figures/                     <- per-station, per-product figures
 |   |-- DAKR/
 |   |   |-- DAKR_IGS_decomposition.png
 |   |   |-- DAKR_IGS_variance_components.png
 |   |   |-- DAKR_IGS_residual_diagnostics.png                            [NEW]
 |   |   |-- DAKR_VMF3_...   DAKR_ERA5_...
 |   |   |-- DAKR_climatology.png         (all products, one figure)      [NEW]
 |   |-- ...

--------------------------------------------------------------------------------
 USAGE
--------------------------------------------------------------------------------
   # 1) simplest - just edit the USER CONFIGURATION block and run:
   python Detrending_analysis_stl_v3.py

   # 2) override paths / options on the command line:
   python Detrending_analysis_stl_v3.py -i ./cleaned_per_station -o ./out \\
          --products IGS,VMF3,ERA5 --vector pdf,svg --coords ./coords.csv

   # 3) drive everything from a YAML file:
   python Detrending_analysis_stl_v3.py --config run.yaml
   #   run.yaml keys are the lower-case names of the config variables, e.g.:
   #     input_path: ./cleaned_per_station
   #     output_root: ./out
   #     products: [IGS, VMF3, ERA5]
   #     vector_formats: [pdf]
   #     coords_csv: ./coords.csv

 DEPENDENCIES
   Required : pandas, numpy, matplotlib, statsmodels, scipy, seaborn, joblib,
              Pillow, openpyxl
   Optional : pyyaml   (only for --config),
              cartopy  (nicer spatial maps; falls back to plain scatter)

 METHOD NOTE
   STL components are not strictly orthogonal, so per-station component
   variances need not sum exactly to the original variance; variance
   *contributions* (%) are therefore reported after normalising T+S+R to 100 %.
   The Excel workbook stores computed result values (not live formulas) - these
   are scientific outputs, not a financial model, so they are intentionally
   static and error-free.

 Author : (PWV analysis pipeline)
 Version: 3.0
================================================================================
"""

# =============================================================================
# SECTION 0 - RUNTIME / BACKEND SET-UP  (must run BEFORE numpy / pyplot import)
# =============================================================================
# (a) Cap BLAS/OpenMP threads to 1 per process so that N worker *processes* do
#     not each spawn N math threads (catastrophic over-subscription).
# (b) Force Matplotlib's headless 'Agg' backend so figures render inside worker
#     processes with no display.
from pathlib import Path
import os

for _env_var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_env_var, "1")

import matplotlib
matplotlib.use("Agg")


# =============================================================================
# SECTION 1 - IMPORTS
# =============================================================================
import sys
import glob
import zipfile
import tempfile
import shutil
import argparse
import warnings
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.transforms import blended_transform_factory
from matplotlib.patches import Patch
import seaborn as sns

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller
from scipy import stats
from scipy.stats import f_oneway, kruskal
from joblib import Parallel, delayed
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]


warnings.filterwarnings("ignore")


# =============================================================================
# SECTION 2 - USER CONFIGURATION  (defaults; override via YAML or CLI)
# =============================================================================
# ---- I/O paths -------------------------------------------------------------
INPUT_PATH = REPO_ROOT / "Analysis" / "Results_Preprocessing" / "Results_Outlier detection & removal" / "cleaned_per_station"
OUTPUT_ROOT = REPO_ROOT / "Analysis" / "Results_Preprocessing" / "Results_Detrending"

COORDS_CSV = None                           # optional station-coordinate CSV

# ---- Products and column naming -------------------------------------------
PRODUCTS = ["IGS", "VMF3", "ERA5"]
CLEAN_SUFFIX = "_Hampel_clean"
DETREND_SUFFIX = "_Trend_Detrended"

# ---- STL parameters --------------------------------------------------------
STL_PERIOD = 365
STL_SEASONAL = 13
STL_ROBUST = True
GAP_INTERP_LIMIT = 7
MIN_OBS_FOR_STL = 60
MIN_OBS_FOR_TREND = 30

# ---- Parallelism / performance --------------------------------------------
N_JOBS = -1
PARALLEL_BACKEND = "loky"

# ---- Figure / output toggles ----------------------------------------------
MAKE_STATION_FIGURES = True                 # decomposition + variance-components
MAKE_DIAGNOSTICS = True                     # residual ACF/hist/QQ per product
MAKE_CLIMATOLOGY = True                     # per-station seasonal climatology
EXCEL_SUMMARY = True                        # write the Excel workbook
VECTOR_FORMATS: List[str] = []              # e.g. ["pdf"] or ["pdf", "svg"]
ACF_NLAGS = 60                              # lags for residual ACF
FIG_DPI = 300
EXCEL_FONT = "Arial"

# ---- Gap-marking bands (per-station decomposition figures) ----------------
GAP_SHADE = True                            # draw transparent bands over gaps
GAP_MARK_MIN_DAYS = 14                      # min missing run (days) to mark
GAP_LABEL = True                            # annotate bands with duration
GAP_LABEL_MIN_DAYS = 45                     # only label bands at least this wide
GAP_COLOR = "#7C8B9A"                       # soft slate fill (cool vs goldenrod)
GAP_EDGE = "#54616E"                        # darker slate for edges + labels
GAP_ALPHA = 0.16                            # band transparency

# ---- Climatology coverage indication --------------------------------------
CLIM_COVERAGE_STRIP = True                  # slim "years per day-of-year" strip
CLIM_LOWCOV_FRAC = 0.6                       # shade DOY where coverage < frac*max

# ---- Output sub-directory names -------------------------------------------
SUBDIR_AGG = "aggregate_figures"
SUBDIR_COMPONENTS = "station_components"
SUBDIR_STATION_FIGS = "station_figures"

# ---- Misc ------------------------------------------------------------------
STATION_NAME_SPLIT = "_cleaned_allmethods.csv"
ALPHA = 0.05

# Names that may be overridden through YAML / CLI (used by the config loader).
_CONFIGURABLE = [
    "INPUT_PATH", "OUTPUT_ROOT", "COORDS_CSV", "PRODUCTS", "CLEAN_SUFFIX",
    "DETREND_SUFFIX", "STL_PERIOD", "STL_SEASONAL", "STL_ROBUST",
    "GAP_INTERP_LIMIT", "MIN_OBS_FOR_STL", "MIN_OBS_FOR_TREND", "N_JOBS",
    "PARALLEL_BACKEND", "MAKE_STATION_FIGURES", "MAKE_DIAGNOSTICS",
    "MAKE_CLIMATOLOGY", "EXCEL_SUMMARY", "VECTOR_FORMATS", "ACF_NLAGS",
    "FIG_DPI", "EXCEL_FONT", "SUBDIR_AGG", "SUBDIR_COMPONENTS",
    "SUBDIR_STATION_FIGS", "STATION_NAME_SPLIT", "ALPHA",
    "GAP_SHADE", "GAP_MARK_MIN_DAYS", "GAP_LABEL", "GAP_LABEL_MIN_DAYS",
    "GAP_COLOR", "GAP_EDGE", "GAP_ALPHA",
    "CLIM_COVERAGE_STRIP", "CLIM_LOWCOV_FRAC",
]


# =============================================================================
# SECTION 3 - PLOT STYLE & COLOUR CONSTANTS  (AGU look-and-feel)
# =============================================================================
AGU_STYLE = {
    "figure.dpi": 300, "savefig.dpi": 600, "font.size": 10,
    "axes.labelsize": 11, "axes.titlesize": 12, "xtick.labelsize": 9,
    "ytick.labelsize": 9, "legend.fontsize": 9, "figure.figsize": (7, 5),
    "axes.linewidth": 0.8, "grid.linewidth": 0.5, "lines.linewidth": 1.5,
    "patch.linewidth": 0.8, "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
}
plt.rcParams.update(AGU_STYLE)
sns.set_palette("colorblind")

# Goldenrod used for single-series per-station decomposition panels (matches the
# study's reference figures).
DECOMP_COLOR = "#E8A317"
# Stable per-product colours for cohort/comparison figures.
PRODUCT_COLORS = {"IGS": "#1f77b4", "VMF3": "#ff7f0e", "ERA5": "#2ca02c"}
# Month boundaries (approx. day-of-year) for climatology x-axis ticks.
_MONTH_DOY = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
_MONTH_LBL = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# =============================================================================
# SECTION 4 - RESULT CONTAINER
# =============================================================================
@dataclass
class STLResults:
    """One record of all metrics for a single (station, product) pair.

    A list of these becomes the master results DataFrame, so each attribute is
    a column in STL_Detailed_Results.csv.
    """
    station: str
    product: str
    n_obs: int
    period_used: int
    # Original-series statistics
    orig_mean: float
    orig_std: float
    orig_range: float
    # Trend-component statistics
    trend_mean: float
    trend_std: float
    trend_range: float
    trend_slope: float          # mm/year (slope of the STL trend)
    trend_pvalue: float
    # Seasonal-component statistics
    seasonal_amplitude: float
    seasonal_std: float
    # Residual-component statistics
    resid_mean: float
    resid_std: float
    resid_range: float
    # Stationarity (ADF p-values)
    adf_orig: float
    adf_resid: float
    # Variance / variability metrics
    trend_contribution: float
    seasonal_contribution: float
    resid_contribution: float
    variance_reduction: float
    delta_sigma_percent: float
    # Strength metrics
    trend_strength: float       # F_T
    seasonal_strength: float    # F_S
    # Raw component variances (mm^2)
    orig_var: float
    trend_var: float
    seasonal_var: float
    resid_var: float


# =============================================================================
# SECTION 5 - RUNTIME CONFIG RESOLUTION (defaults < YAML < CLI)
# =============================================================================
def apply_runtime_config(overrides: Dict) -> None:
    """Write resolved configuration values into this module's globals.

    Called once in the parent process AND at the top of every worker process,
    so command-line / YAML overrides reach the workers (which re-import this
    module fresh and would otherwise only see the built-in defaults).
    """
    g = globals()
    for key, val in (overrides or {}).items():
        if key in _CONFIGURABLE:
            g[key] = val


def load_yaml_config(path: str) -> Dict:
    """Load a YAML config file into an overrides dict keyed by GLOBAL names.

    YAML keys are the lower-case versions of the configuration variables
    (e.g. `stl_period`, `products`, `vector_formats`).  Unknown keys are
    ignored with a warning.  Requires PyYAML (only when --config is used).
    """
    try:
        import yaml  # local import: optional dependency
    except ImportError as exc:
        raise ImportError("PyYAML is required for --config "
                          "(install with: pip install pyyaml)") from exc
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    overrides: Dict = {}
    for key, val in raw.items():
        gkey = key.upper()
        if gkey in _CONFIGURABLE:
            overrides[gkey] = val
        else:
            print(f"[WARN] Unknown config key ignored: {key}")
    return overrides


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Define and parse the command-line interface."""
    p = argparse.ArgumentParser(
        description="STL/Hampel detrending analysis for PWV inter-comparison.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("-i", "--input", dest="input", default=None,
                   help="Input folder (or .zip) of cleaned per-station CSVs.")
    p.add_argument("-o", "--output", dest="output", default=None,
                   help="Output root directory.")
    p.add_argument("-c", "--config", dest="config", default=None,
                   help="Optional YAML config file (keys override defaults).")
    p.add_argument("--products", dest="products", default=None,
                   help="Comma-separated product list, e.g. IGS,VMF3,ERA5.")
    p.add_argument("--coords", dest="coords", default=None,
                   help="CSV of station coordinates (enables spatial maps).")
    p.add_argument("--n-jobs", dest="n_jobs", type=int, default=None,
                   help="Parallel jobs (-1 = all cores).")
    p.add_argument("--backend", dest="backend", default=None,
                   choices=["loky", "threading", "multiprocessing"],
                   help="joblib parallel backend.")
    p.add_argument("--stl-period", dest="stl_period", type=int, default=None,
                   help="STL seasonal period in days.")
    p.add_argument("--gap-limit", dest="gap_limit", type=int, default=None,
                   help="Max gap length (days) to interpolate.")
    p.add_argument("--vector", dest="vector", default=None,
                   help="Comma-separated vector formats, e.g. pdf,svg.")
    p.add_argument("--no-station-figures", dest="no_station_figures",
                   action="store_true", default=None,
                   help="Disable per-station decomposition/variance figures.")
    p.add_argument("--no-diagnostics", dest="no_diagnostics",
                   action="store_true", default=None,
                   help="Disable per-station residual diagnostic figures.")
    p.add_argument("--no-climatology", dest="no_climatology",
                   action="store_true", default=None,
                   help="Disable per-station seasonal climatology figures.")
    p.add_argument("--no-excel", dest="no_excel",
                   action="store_true", default=None,
                   help="Disable the Excel summary workbook.")
    p.add_argument("--no-gap-shading", dest="no_gap_shading",
                   action="store_true", default=None,
                   help="Disable transparent gap-marking bands on decomposition figures.")
    return p.parse_args(argv)


def resolve_config(args: argparse.Namespace) -> Dict:
    """Merge YAML then CLI flags into a single overrides dict (CLI wins)."""
    overrides: Dict = {}
    if args.config:
        overrides.update(load_yaml_config(args.config))

    # CLI flags (only applied when actually provided / not None).
    if args.input is not None:
        overrides["INPUT_PATH"] = args.input
    if args.output is not None:
        overrides["OUTPUT_ROOT"] = args.output
    if args.coords is not None:
        overrides["COORDS_CSV"] = args.coords
    if args.products is not None:
        overrides["PRODUCTS"] = [s.strip() for s in args.products.split(",") if s.strip()]
    if args.n_jobs is not None:
        overrides["N_JOBS"] = args.n_jobs
    if args.backend is not None:
        overrides["PARALLEL_BACKEND"] = args.backend
    if args.stl_period is not None:
        overrides["STL_PERIOD"] = args.stl_period
    if args.gap_limit is not None:
        overrides["GAP_INTERP_LIMIT"] = args.gap_limit
    if args.vector is not None:
        overrides["VECTOR_FORMATS"] = [s.strip().lower()
                                       for s in args.vector.split(",") if s.strip()]
    if args.no_station_figures:
        overrides["MAKE_STATION_FIGURES"] = False
    if args.no_diagnostics:
        overrides["MAKE_DIAGNOSTICS"] = False
    if args.no_climatology:
        overrides["MAKE_CLIMATOLOGY"] = False
    if args.no_excel:
        overrides["EXCEL_SUMMARY"] = False
    if args.no_gap_shading:
        overrides["GAP_SHADE"] = False
    return overrides


# =============================================================================
# SECTION 6 - FILESYSTEM UTILITIES
# =============================================================================
def ensure_outdir(path: str) -> str:
    """Create `path` (and parents) if needed and return it."""
    os.makedirs(path, exist_ok=True)
    return path


def prepare_input_dir(input_path: str) -> Tuple[str, bool]:
    """Resolve INPUT_PATH to a directory, extracting a .zip if necessary.

    Returns (directory, is_temporary); the caller deletes the temp dir when
    is_temporary is True.
    """
    if os.path.isdir(input_path):
        return input_path, False
    if os.path.isfile(input_path) and input_path.lower().endswith(".zip"):
        tmpdir = tempfile.mkdtemp(prefix="stl_hampel_")
        with zipfile.ZipFile(input_path, "r") as z:
            z.extractall(tmpdir)
        entries = [os.path.join(tmpdir, x) for x in os.listdir(tmpdir)]
        only_dirs = [p for p in entries if os.path.isdir(p)]
        if len(only_dirs) == 1:
            tmpdir = only_dirs[0]
        return tmpdir, True
    raise FileNotFoundError(f"INPUT_PATH not found: {input_path}")


def discover_csvs(in_dir: str) -> List[str]:
    """Return a sorted list of station CSVs (recursing if the top level is empty)."""
    csvs = glob.glob(os.path.join(in_dir, "*.csv"))
    if not csvs:
        csvs = glob.glob(os.path.join(in_dir, "**", "*.csv"), recursive=True)
    return sorted(csvs)


def load_station_csv(path: str) -> pd.DataFrame:
    """Load one station CSV into a date-indexed, chronologically sorted frame."""
    df = pd.read_csv(path, parse_dates=["DATE"])
    return df.set_index("DATE").sort_index()


def load_station_coords(path: Optional[str]) -> Dict[str, Tuple[float, float]]:
    """Read a station-coordinate CSV into {station: (lat, lon)}.

    Header names are matched case-insensitively from a small set of aliases
    (see the module docstring).  Returns {} if the path is missing/unreadable.
    """
    if not path or not os.path.isfile(path):
        if path:
            print(f"[WARN] Coordinate file not found: {path} (spatial maps skipped)")
        return {}
    try:
        cdf = pd.read_csv(path)
    except Exception as exc:
        print(f"[WARN] Could not read coordinate file: {exc}")
        return {}

    lut = {c.lower().strip(): c for c in cdf.columns}
    s_col = next((lut[k] for k in ("station", "site", "code") if k in lut), None)
    lat_col = next((lut[k] for k in ("lat", "latitude") if k in lut), None)
    lon_col = next((lut[k] for k in ("lon", "long", "longitude") if k in lut), None)
    if not (s_col and lat_col and lon_col):
        print("[WARN] Coordinate CSV needs station/lat/lon columns (maps skipped)")
        return {}

    coords: Dict[str, Tuple[float, float]] = {}
    for _, row in cdf.iterrows():
        try:
            coords[str(row[s_col]).strip()] = (float(row[lat_col]), float(row[lon_col]))
        except (TypeError, ValueError):
            continue
    return coords


# =============================================================================
# SECTION 7 - CORE STATISTICS
# =============================================================================
def compute_trend_stats(trend: pd.Series) -> Tuple[float, float]:
    """Linear slope (mm/year) and OLS p-value of the STL trend component.

    NOTE: the p-value here is the OLS p-value of a regression on the *smoothed*
    trend; it is retained unchanged from earlier versions for continuity.
    """
    tc = trend.dropna()
    if len(tc) < MIN_OBS_FOR_TREND:
        return np.nan, np.nan
    t_years = (tc.index - tc.index[0]).days / 365.25
    slope, _b, _r, p_value, _se = stats.linregress(t_years, tc.values)
    return slope, p_value


def adf_test(x: np.ndarray) -> float:
    """Augmented Dickey-Fuller p-value (AIC lag selection). nan on failure."""
    xc = pd.Series(x).dropna()
    if len(xc) < MIN_OBS_FOR_TREND:
        return np.nan
    try:
        return adfuller(xc, maxlag=None, autolag="AIC")[1]
    except Exception:
        return np.nan


def variance_decomposition(trend: pd.Series, seasonal: pd.Series,
                           resid: pd.Series) -> Tuple[float, float, float]:
    """Component variances normalised to sum to 100 % (handles non-orthogonality)."""
    tv, sv, rv = trend.var(), seasonal.var(), resid.var()
    total = tv + sv + rv
    if not (total > 0):
        return np.nan, np.nan, np.nan
    return tv / total * 100.0, sv / total * 100.0, rv / total * 100.0


def compute_strength_metrics(s: pd.Series, trend: pd.Series,
                             seasonal: pd.Series, resid: pd.Series
                             ) -> Tuple[float, float]:
    """Trend/seasonal strength F_T, F_S in [0, 1] (Wang, Smith & Hyndman 2006)."""
    var_y = s.var()
    if not (var_y > 0):
        return np.nan, np.nan
    var_ys = (s - seasonal).var()    # Var(T + R)
    var_yt = (s - trend).var()       # Var(S + R)
    var_r = resid.var()
    return (max(0.0, (var_ys - var_r) / var_y),
            max(0.0, (var_yt - var_r) / var_y))


def acf_numpy(x: np.ndarray, nlags: int) -> np.ndarray:
    """Biased autocorrelation function up to `nlags` (no extra dependency)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom == 0 or len(x) < 2:
        return np.array([1.0])
    nlags = int(min(nlags, len(x) - 1))
    out = [1.0]
    for k in range(1, nlags + 1):
        out.append(float(np.dot(x[:-k], x[k:]) / denom))
    return np.array(out)


def acf_gap_aware(series_daily: pd.Series, nlags: int
                  ) -> Tuple[np.ndarray, np.ndarray]:
    """Pairwise-complete (gap-aware) sample ACF on a daily-reindexed series.

    Unlike `acf_numpy`, which collapses gaps and so pairs observations that are
    actually months apart, this estimator works on the continuous daily
    calendar (NaN at gaps) and, for each lag k, uses only the pairs
    (x_t, x_{t+k}) where BOTH days are observed:

        gamma(k) = mean over valid pairs of (x_t - xbar)(x_{t+k} - xbar)
        r(k)     = gamma(k) / gamma(0),   gamma(0) = sample variance

    so genuine gaps never contribute a spurious cross-boundary correlation.
    Returns (acf_values, valid_pair_counts); r(0) = 1.  Like any gap-aware
    estimate it is not guaranteed positive-definite, which is acceptable for a
    descriptive whitening diagnostic.
    """
    x = np.asarray(series_daily, dtype=float)
    valid = ~np.isnan(x)
    n_valid = int(valid.sum())
    if n_valid < 2:
        return np.array([1.0]), np.array([n_valid])
    xc = x - np.nanmean(x)
    gamma0 = float(np.nansum(xc[valid] ** 2) / n_valid)   # sample variance
    if gamma0 == 0:
        return np.array([1.0]), np.array([n_valid])
    nlags = int(min(nlags, len(x) - 1))
    acf = [1.0]
    counts = [n_valid]
    for k in range(1, nlags + 1):
        m = valid[:-k] & valid[k:]
        cnt = int(m.sum())
        counts.append(cnt)
        if cnt > 0:
            gamma_k = float(np.sum(xc[:-k][m] * xc[k:][m]) / cnt)
            acf.append(gamma_k / gamma0)
        else:
            acf.append(np.nan)
    return np.array(acf), np.array(counts)


# =============================================================================
# SECTION 8 - STL DECOMPOSITION
# =============================================================================
def stl_decompose(s_clean: pd.Series, period: int = None
                  ) -> Tuple[pd.Series, pd.Series, pd.Series, int]:
    """Run STL on an ALREADY gap-handled daily series.

    `s_clean` must already be daily with short gaps interpolated and remaining
    NaNs dropped (done once in process_station), so no interpolation is repeated
    here.  Period adapts when the record is shorter than two cycles and is
    forced odd.  On failure/short series, trend & seasonal are all-NaN.
    """
    if period is None:
        period = STL_PERIOD
    n = len(s_clean)
    if n < MIN_OBS_FOR_STL:
        empty = pd.Series(index=s_clean.index, data=np.nan)
        return empty, empty, s_clean, period

    period_used = period if n >= period * 2 else max(30, min(180, n // 3))
    if period_used % 2 == 0:
        period_used += 1
    try:
        res = STL(s_clean, period=period_used, seasonal=STL_SEASONAL,
                  trend=None, robust=STL_ROBUST).fit()
        return res.trend, res.seasonal, res.resid, period_used
    except Exception:
        empty = pd.Series(index=s_clean.index, data=np.nan)
        return empty, empty, s_clean, period_used


# =============================================================================
# SECTION 9 - PLOTTING HELPERS  (gap-aware + vector-capable saving)
# =============================================================================
def save_fig(fig, out_png_path: str, close: bool = True) -> str:
    """Save a figure as PNG (always) plus any configured vector formats.

    Returns the PNG path.  Vector copies (.pdf/.svg) are written next to the
    PNG when VECTOR_FORMATS is non-empty.  Any vector failure is non-fatal.
    """
    fig.savefig(out_png_path, dpi=FIG_DPI, bbox_inches="tight")
    base, _ext = os.path.splitext(out_png_path)
    for fmt in VECTOR_FORMATS:
        try:
            fig.savefig(f"{base}.{fmt}", bbox_inches="tight")
        except Exception as exc:
            print(f"[WARN] vector save ({fmt}) failed for "
                  f"{os.path.basename(base)}: {exc}")
    if close:
        plt.close(fig)
    return out_png_path


def find_gap_spans(series: pd.Series, min_days: int) -> List[Tuple]:
    """Return [(start_ts, end_ts), ...] for each run of >= `min_days` NaNs.

    Operates on a daily-reindexed series, where short gaps (<= GAP_INTERP_LIMIT)
    have already been interpolated away, so the remaining NaN runs are exactly
    the long gaps that break the plotted lines.
    """
    isna = series.isna().to_numpy()
    idx = series.index
    spans: List[Tuple] = []
    i, n = 0, len(isna)
    while i < n:
        if isna[i]:
            j = i
            while j < n and isna[j]:
                j += 1
            if (j - i) >= min_days:
                spans.append((idx[i], idx[j - 1]))
            i = j
        else:
            i += 1
    return spans


def _true_runs(mask, index) -> List[Tuple]:
    """Return [(index[start], index[end]), ...] for each contiguous True run."""
    runs: List[Tuple] = []
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            runs.append((index[i], index[j - 1]))
            i = j
        else:
            i += 1
    return runs


def _gap_label_text(days: int) -> str:
    """Compact human-readable gap duration (e.g. '17-mo gap', '52-d gap')."""
    if days >= 60:
        return f"{round(days / 30.4)}-mo gap"
    return f"{days}-d gap"


def shade_gaps(ax, spans: List[Tuple], label: bool = True) -> None:
    """Draw a transparent slate band (+ dashed edges + optional duration label)
    over each gap span on a time-series axis.

    Bands sit behind the data (zorder 0) so the goldenrod traces stay crisp;
    edges are faint dashed verticals and the duration label is set vertically
    near the top of the band using a data-x / axes-y blended transform.
    """
    if not spans:
        return
    trans = blended_transform_factory(ax.transData, ax.transAxes)
    for a, b in spans:
        ax.axvspan(a, b, facecolor=GAP_COLOR, alpha=GAP_ALPHA,
                   edgecolor="none", zorder=0)
        for edge in (a, b):
            ax.axvline(edge, color=GAP_EDGE, linewidth=0.6,
                       linestyle=(0, (4, 3)), alpha=0.55, zorder=1)
        days = int((b - a).days) + 1
        if label and GAP_LABEL and days >= GAP_LABEL_MIN_DAYS:
            mid = a + (b - a) / 2
            ax.text(mid, 0.96, _gap_label_text(days), transform=trans,
                    rotation=90, va="top", ha="center", fontsize=7.5,
                    style="italic", color=GAP_EDGE, alpha=0.95, zorder=3)


def build_plot_series(s_interp: pd.Series, trend: pd.Series,
                      seasonal: pd.Series, resid: pd.Series
                      ) -> Optional[Tuple[pd.Series, pd.Series, pd.Series, pd.Series]]:
    """Re-index components onto one continuous daily calendar so gaps break lines.

    Short gaps (<= GAP_INTERP_LIMIT) are already filled in `s_interp`; gaps
    longer than the interpolation limit stay NaN and therefore break every
    panel at the same place.  Returns None when there is no valid data.
    """
    start, end = s_interp.first_valid_index(), s_interp.last_valid_index()
    if start is None or end is None:
        return None
    idx = pd.date_range(start=start, end=end, freq="D")
    return (s_interp.reindex(idx), trend.reindex(idx),
            seasonal.reindex(idx), resid.reindex(idx))


def _style_timeseries_axis(ax, ylabel: str, title: str) -> None:
    """Shared cosmetic styling for a decomposition time-series panel."""
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def create_agu_figure(nrows: int = 1, ncols: int = 1,
                      figsize: Optional[Tuple[float, float]] = None, **kwargs):
    """Create a despined, lightly-gridded AGU-style figure/axes pair."""
    if figsize is None:
        width = 7.0 if ncols > 1 else 3.5
        height = 5.0 * nrows / ncols if nrows > 1 else 5.0
        figsize = (width, height)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    ax_iter = axes.flat if isinstance(axes, np.ndarray) else [axes]
    for ax in ax_iter:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    return fig, axes


# =============================================================================
# SECTION 10 - PER-STATION VISUALISATIONS
# =============================================================================
def plot_station_decomposition(station: str, product: str, period_used: int,
                               orig_p: pd.Series, trend_p: pd.Series,
                               seasonal_p: pd.Series, resid_p: pd.Series,
                               out_path: str) -> None:
    """4-panel STL decomposition (Original / Trend / Seasonal / Residual)."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 7.5))
    tag = f"{station} \u2014 {product}_PWV"
    ax = axes[0, 0]
    ax.plot(orig_p.index, orig_p.values, color=DECOMP_COLOR, linewidth=0.7)
    _style_timeseries_axis(ax, "PWV (mm)", f"{tag}: Original")
    ax = axes[0, 1]
    ax.plot(trend_p.index, trend_p.values, color=DECOMP_COLOR, linewidth=1.8)
    _style_timeseries_axis(ax, "PWV (mm)", f"{tag}: STL Trend (period={period_used})")
    ax = axes[1, 0]
    ax.plot(seasonal_p.index, seasonal_p.values, color=DECOMP_COLOR, linewidth=0.7)
    _style_timeseries_axis(ax, "PWV (mm)", f"{tag}: STL Seasonal (period={period_used})")
    ax = axes[1, 1]
    ax.plot(resid_p.index, resid_p.values, color=DECOMP_COLOR, linewidth=0.7)
    _style_timeseries_axis(ax, "PWV anomaly (mm)", f"{tag}: Residual (Anomaly)")

    # Highlight long data gaps consistently across all four panels so the eye
    # reads the breaks as intentional rather than as artefacts.
    if GAP_SHADE:
        spans = find_gap_spans(orig_p, GAP_MARK_MIN_DAYS)
        if spans:
            for _ax in axes.flat:
                shade_gaps(_ax, spans)
            axes[0, 0].legend(
                handles=[Patch(facecolor=GAP_COLOR, alpha=GAP_ALPHA,
                               edgecolor=GAP_EDGE, label="Data gap")],
                loc="upper right", frameon=True, fancybox=False,
                edgecolor="black", fontsize=8)

    fig.tight_layout()
    save_fig(fig, out_path)


def plot_station_variance_components(station: str, product: str,
                                     orig_var: float, trend_var: float,
                                     seasonal_var: float, resid_var: float,
                                     out_path: str) -> None:
    """Bar chart of Original/Trend/Seasonal/Residual variance (mm^2)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(["Original", "Trend", "Seasonal", "Residual"],
           [orig_var, trend_var, seasonal_var, resid_var],
           color=DECOMP_COLOR, width=0.6, edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Variance (mm$^2$)", fontweight="bold")
    ax.set_title(f"{station} \u2014 {product}_PWV: Variance Components",
                 fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    fig.tight_layout()
    save_fig(fig, out_path)


def plot_station_climatology(station: str,
                             seasonal_by_product: Dict[str, pd.Series],
                             out_path: str) -> None:
    """Mean annual cycle (folded on day-of-year) per product with an IQR band,
    plus a coverage indicator for the folded view.

    The STL seasonal component of each product is grouped by day-of-year; the
    median line and 25-75 % envelope summarise the typical seasonal swing and
    how consistent it is from year to year.  Because folding hides where the
    record is thin, a slim strip beneath the panel shows the number of years
    contributing to each day-of-year (minimum across products), and day-of-year
    ranges sampled by fewer than CLIM_LOWCOV_FRAC of the peak coverage are
    lightly shaded so the reader can see which parts of the cycle are
    least-constrained (e.g. the months most affected by a long data gap).
    """
    show_strip = CLIM_COVERAGE_STRIP
    if show_strip:
        fig, (ax, axc) = plt.subplots(
            2, 1, figsize=(8.5, 5.6), sharex=True,
            gridspec_kw={"height_ratios": [5, 1], "hspace": 0.08})
    else:
        fig, ax = plt.subplots(figsize=(8.5, 5))
        axc = None

    full_doy = pd.RangeIndex(1, 367)
    coverage_cols = []
    for product, seas in seasonal_by_product.items():
        s = seas.dropna()
        if s.empty:
            continue
        doy = s.index.dayofyear
        grp = pd.DataFrame({"doy": doy, "val": s.values}).groupby("doy")["val"]
        med, q1, q3 = grp.median(), grp.quantile(0.25), grp.quantile(0.75)
        coverage_cols.append(grp.count().reindex(full_doy))
        color = PRODUCT_COLORS.get(product, None)
        ax.plot(med.index, med.values, label=product, color=color, linewidth=1.6)
        ax.fill_between(med.index, q1.values, q3.values, color=color, alpha=0.18)

    ax.axhline(0, color="0.4", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.set_xlim(1, 366)
    ax.set_ylabel("Seasonal PWV component (mm)", fontweight="bold")
    ax.set_title(f"{station}: Mean Seasonal Cycle (median \u00b1 IQR)",
                 fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)

    handles, labels = ax.get_legend_handles_labels()

    # --- coverage: min years-with-data per day-of-year across products ---
    if coverage_cols:
        cov = pd.concat(coverage_cols, axis=1).min(axis=1).reindex(full_doy)
        cov_vals = cov.to_numpy(dtype=float)
        max_cov = np.nanmax(cov_vals) if np.isfinite(cov_vals).any() else 0.0

        # Thin shading of under-sampled day-of-year ranges on the main panel.
        if GAP_SHADE and max_cov > 0:
            low_mask = np.nan_to_num(cov_vals, nan=0.0) < (CLIM_LOWCOV_FRAC * max_cov)
            # Keep only substantial runs (a lone leap-day DOY 366 is not a gap).
            runs = [(a, b) for a, b in _true_runs(low_mask, full_doy.to_numpy())
                    if (b - a + 1) >= GAP_MARK_MIN_DAYS]
            for a, b in runs:
                ax.axvspan(a, b, facecolor=GAP_COLOR, alpha=GAP_ALPHA * 0.7,
                           edgecolor="none", zorder=0)
            if runs:
                handles.append(Patch(facecolor=GAP_COLOR, alpha=GAP_ALPHA * 0.7,
                                     edgecolor=GAP_EDGE,
                                     label=f"< {CLIM_LOWCOV_FRAC:.0%} coverage"))

        # Slim coverage strip beneath the main panel.
        if axc is not None and max_cov > 0:
            axc.fill_between(full_doy, 0, np.nan_to_num(cov_vals, nan=0.0),
                             step="mid", color=GAP_EDGE, alpha=0.35, linewidth=0)
            axc.plot(full_doy, np.nan_to_num(cov_vals, nan=0.0), drawstyle="steps-mid",
                     color=GAP_EDGE, linewidth=0.7)
            axc.set_ylim(0, max_cov * 1.18)
            axc.set_yticks([0, int(round(max_cov))])
            axc.set_ylabel("yrs", fontsize=8)
            axc.spines["top"].set_visible(False)
            axc.spines["right"].set_visible(False)
            axc.grid(True, axis="y", alpha=0.25, linestyle="--", linewidth=0.4)

    ax.legend(handles=handles, frameon=True, fancybox=False, edgecolor="black",
              title="Product", fontsize=8)

    # Month ticks/labels live on the bottom-most axis.
    bottom_ax = axc if (show_strip and axc is not None) else ax
    if show_strip and axc is not None:
        ax.tick_params(labelbottom=False)
    bottom_ax.set_xlim(1, 366)
    bottom_ax.set_xticks(_MONTH_DOY)
    bottom_ax.set_xticklabels(_MONTH_LBL)
    bottom_ax.set_xlabel("Month", fontweight="bold")

    fig.tight_layout()
    save_fig(fig, out_path)


def plot_residual_diagnostics(station: str, product: str,
                              resid_clean: pd.Series, out_path: str) -> None:
    """Residual ACF + distribution-vs-normal + normal Q-Q for one product.

    These three panels show whether detrending whitened the series (flat ACF
    within the +/-1.96/sqrt(N) band) and whether the anomalies are close to
    Gaussian - both relevant to 3CH/ETC error assumptions.
    """
    r_series = resid_clean.dropna()
    r = r_series.values
    n = len(r)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.9))

    # (a) Gap-aware (pairwise-complete) ACF with white-noise confidence band.
    #     The ACF is computed on the continuous daily calendar so that genuine
    #     gaps never pair observations that are months apart.
    ax = axes[0]
    if n >= 2:
        idx_daily = pd.date_range(r_series.index.min(), r_series.index.max(), freq="D")
        r_daily = r_series.reindex(idx_daily)
        acf_vals, _pair_counts = acf_gap_aware(r_daily, min(ACF_NLAGS, max(1, n // 2)))
    else:
        acf_vals = np.array([1.0])
    lags = np.arange(len(acf_vals))
    ax.bar(lags, acf_vals, width=0.8, color=PRODUCT_COLORS.get(product, "#444"),
           alpha=0.85)
    if n > 0:
        conf = 1.96 / np.sqrt(n)
        ax.axhline(conf, color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.axhline(-conf, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Lag (days)", fontweight="bold")
    ax.set_ylabel("Autocorrelation", fontweight="bold")
    ax.set_title("(a) Residual ACF", fontweight="bold")
    # No time axis here, so gap *bands* don't apply; instead note the sample
    # size and that the ACF is the gap-aware (pairwise-complete) estimate.
    ax.text(0.97, 0.95, f"n = {n}\ngap-aware ACF", transform=ax.transAxes,
            ha="right", va="top", fontsize=7.5, style="italic", color="0.35",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.8",
                      alpha=0.75))

    # (b) Histogram vs fitted normal.
    ax = axes[1]
    ax.hist(r, bins=40, density=True, color=PRODUCT_COLORS.get(product, "#888"),
            alpha=0.6, edgecolor="white", linewidth=0.4)
    if n > 1:
        mu, sigma = float(np.mean(r)), float(np.std(r))
        xs = np.linspace(r.min(), r.max(), 200)
        ax.plot(xs, stats.norm.pdf(xs, mu, sigma), color="black", linewidth=1.5,
                label=f"N({mu:.2f}, {sigma:.2f})")
        ax.legend(frameon=True, fancybox=False, edgecolor="black", fontsize=8)
    ax.set_xlabel("Residual (mm)", fontweight="bold")
    ax.set_ylabel("Density", fontweight="bold")
    ax.set_title("(b) Residual Distribution", fontweight="bold")

    # (c) Normal Q-Q.
    ax = axes[2]
    if n > 2:
        stats.probplot(r, dist="norm", plot=ax)
        ax.get_lines()[0].set_markerfacecolor(PRODUCT_COLORS.get(product, "#888"))
        ax.get_lines()[0].set_markeredgecolor("none")
        ax.get_lines()[0].set_markersize(3)
        ax.get_lines()[1].set_color("black")
    ax.set_title("(c) Normal Q-Q", fontweight="bold")
    ax.set_xlabel("Theoretical quantiles", fontweight="bold")
    ax.set_ylabel("Ordered residuals", fontweight="bold")

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)

    fig.suptitle(f"{station} \u2014 {product}_PWV: Residual diagnostics",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save_fig(fig, out_path)


# =============================================================================
# SECTION 11 - PER-STATION PROCESSING (PARALLEL WORKER)
# =============================================================================
def process_station(csv_path: str, components_dir: str, station_figs_dir: str,
                    overrides: Dict) -> List[STLResults]:
    """Process ONE station end-to-end inside a parallel worker.

    Steps: apply runtime config -> load CSV -> for each product: build daily
    series (interpolate short gaps once), STL-decompose, compute metrics,
    accumulate component columns, render per-station figures -> write the
    enhanced component CSV -> render the station climatology -> return a list of
    STLResults.  Each product and figure is guarded so one failure never aborts
    the station.
    """
    # Make CLI/YAML overrides effective inside this worker process.
    apply_runtime_config(overrides)

    results: List[STLResults] = []
    fname = os.path.basename(csv_path)
    station_code = fname.split(STATION_NAME_SPLIT)[0]

    try:
        df = load_station_csv(csv_path)
    except Exception as exc:
        print(f"[WARN] Failed to load {fname}: {exc}")
        return results

    detrend_df = df.copy()
    components: Dict[str, pd.Series] = {}
    seasonal_by_product: Dict[str, pd.Series] = {}
    station_fig_dir = os.path.join(station_figs_dir, station_code)

    for product in PRODUCTS:
        col = f"{product}{CLEAN_SUFFIX}"
        if col not in df.columns:
            continue
        try:
            # Daily series with short gaps interpolated ONCE (reused for STL
            # and for gap-aware plotting).
            s_interp = (df[col].asfreq("D")
                        .interpolate(method="linear", limit=GAP_INTERP_LIMIT))
            s_clean = s_interp.dropna()
            if len(s_clean) < MIN_OBS_FOR_STL:
                continue

            trend, seasonal, resid, period_used = stl_decompose(s_clean, STL_PERIOD)
            if trend.isna().all():
                continue

            trend_c, seasonal_c, resid_c = trend.dropna(), seasonal.dropna(), resid.dropna()
            detrended = s_clean - trend

            # --- statistics ---
            orig_mean, orig_std = float(s_clean.mean()), float(s_clean.std())
            orig_range = float(s_clean.max() - s_clean.min())
            trend_mean, trend_std = float(trend_c.mean()), float(trend_c.std())
            trend_range = float(trend_c.max() - trend_c.min())
            trend_slope, trend_pval = compute_trend_stats(trend)
            seasonal_amp = float(seasonal_c.max() - seasonal_c.min())
            seasonal_std = float(seasonal_c.std())
            resid_mean, resid_std = float(resid_c.mean()), float(resid_c.std())
            resid_range = float(resid_c.max() - resid_c.min())
            adf_orig = adf_test(s_clean.values)
            adf_resid = adf_test(resid_c.values)
            t_contrib, s_contrib, r_contrib = variance_decomposition(
                trend_c, seasonal_c, resid_c)
            variance_reduction = ((orig_std ** 2 - resid_std ** 2) / orig_std ** 2) * 100.0
            delta_sigma_percent = ((resid_std - orig_std) / orig_std) * 100.0
            f_t, f_s = compute_strength_metrics(s_clean, trend, seasonal, resid)
            orig_var, trend_var = float(s_clean.var()), float(trend_c.var())
            seasonal_var, resid_var = float(seasonal_c.var()), float(resid_c.var())

            # --- accumulate component columns + seasonal for climatology ---
            components[f"{product}_Trend"] = trend
            components[f"{product}_Seasonal"] = seasonal
            components[f"{product}_Residual"] = resid
            components[f"{product}{DETREND_SUFFIX}"] = detrended
            seasonal_by_product[product] = seasonal

            # --- per-station, per-product figures ---
            if MAKE_STATION_FIGURES:
                pack = build_plot_series(s_interp, trend, seasonal, resid)
                if pack is not None:
                    os.makedirs(station_fig_dir, exist_ok=True)
                    o_p, t_p, s_p, r_p = pack
                    try:
                        plot_station_decomposition(
                            station_code, product, period_used, o_p, t_p, s_p, r_p,
                            os.path.join(station_fig_dir,
                                         f"{station_code}_{product}_decomposition.png"))
                        plot_station_variance_components(
                            station_code, product, orig_var, trend_var,
                            seasonal_var, resid_var,
                            os.path.join(station_fig_dir,
                                         f"{station_code}_{product}_variance_components.png"))
                    except Exception as fx:
                        print(f"[WARN] figure {station_code}/{product}: {fx}")

            if MAKE_DIAGNOSTICS:
                try:
                    os.makedirs(station_fig_dir, exist_ok=True)
                    plot_residual_diagnostics(
                        station_code, product, resid_c,
                        os.path.join(station_fig_dir,
                                     f"{station_code}_{product}_residual_diagnostics.png"))
                except Exception as fx:
                    print(f"[WARN] diagnostics {station_code}/{product}: {fx}")

            results.append(STLResults(
                station=station_code, product=product, n_obs=len(s_clean),
                period_used=period_used, orig_mean=orig_mean, orig_std=orig_std,
                orig_range=orig_range, trend_mean=trend_mean, trend_std=trend_std,
                trend_range=trend_range, trend_slope=trend_slope,
                trend_pvalue=trend_pval, seasonal_amplitude=seasonal_amp,
                seasonal_std=seasonal_std, resid_mean=resid_mean,
                resid_std=resid_std, resid_range=resid_range, adf_orig=adf_orig,
                adf_resid=adf_resid, trend_contribution=t_contrib,
                seasonal_contribution=s_contrib, resid_contribution=r_contrib,
                variance_reduction=variance_reduction,
                delta_sigma_percent=delta_sigma_percent, trend_strength=f_t,
                seasonal_strength=f_s, orig_var=orig_var, trend_var=trend_var,
                seasonal_var=seasonal_var, resid_var=resid_var,
            ))
        except Exception as prod_exc:
            print(f"[WARN] {station_code}/{product} failed: {prod_exc}")
            continue

    # --- write enhanced component CSV (original columns preserved) ---
    if components:
        for comp_col, series in components.items():
            aligned = pd.Series(index=df.index, dtype=float)
            common = series.index.intersection(df.index)
            aligned.loc[common] = series.loc[common]
            detrend_df[comp_col] = aligned
        out_csv = os.path.join(components_dir, f"{station_code}_detrended.csv")
        detrend_df.to_csv(out_csv)
        print(f"  [ok] components -> {os.path.basename(out_csv)}")

    # --- per-station seasonal climatology (all products in one figure) ---
    if MAKE_CLIMATOLOGY and seasonal_by_product:
        try:
            os.makedirs(station_fig_dir, exist_ok=True)
            plot_station_climatology(
                station_code, seasonal_by_product,
                os.path.join(station_fig_dir, f"{station_code}_climatology.png"))
        except Exception as fx:
            print(f"[WARN] climatology {station_code}: {fx}")

    return results


# =============================================================================
# SECTION 12 - AGGREGATE (COHORT) FIGURES
# =============================================================================
def plot_variance_contributions(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 1 - grouped bars of mean Trend/Seasonal/Residual variance share."""
    fig, ax = create_agu_figure(figsize=(7, 5))
    data = []
    for product in PRODUCTS:
        sub = df[df["product"] == product]
        data.append({"Trend": sub["trend_contribution"].values,
                     "Seasonal": sub["seasonal_contribution"].values,
                     "Residual": sub["resid_contribution"].values})
    x = np.arange(len(PRODUCTS))
    w = 0.25
    cols = ["#d62728", "#2ca02c", "#1f77b4"]
    for i, d in enumerate(data):
        ax.bar(x[i] - w, np.nanmean(d["Trend"]), w, yerr=np.nanstd(d["Trend"]),
               label="Trend" if i == 0 else "", color=cols[0], alpha=0.8, capsize=3)
        ax.bar(x[i], np.nanmean(d["Seasonal"]), w, yerr=np.nanstd(d["Seasonal"]),
               label="Seasonal" if i == 0 else "", color=cols[1], alpha=0.8, capsize=3)
        ax.bar(x[i] + w, np.nanmean(d["Residual"]), w, yerr=np.nanstd(d["Residual"]),
               label="Residual" if i == 0 else "", color=cols[2], alpha=0.8, capsize=3)
    ax.set_ylabel("Variance Contribution (%)", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(PRODUCTS)
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    ax.set_title(" (a) Variance Decomposition: Trend vs. Seasonal vs. Residual",
                 fontweight="bold", pad=10)
    max_trend = max(np.nanmean(d["Trend"]) for d in data)
    ax.text(0.98, 0.98,
            f"Max trend contribution: {max_trend:.1f}%\n(Negligible for short-term variability)",
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5), fontsize=8)
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig1_Variance_Decomposition.png"))


def plot_trend_slopes(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 2 - histogram + box-plot of linear trend slopes (mm/yr)."""
    fig, axes = create_agu_figure(nrows=1, ncols=2, figsize=(7, 3.5))
    ax = axes[0]
    for product in PRODUCTS:
        ax.hist(df[df["product"] == product]["trend_slope"].dropna(), bins=20,
                alpha=0.6, label=product, edgecolor="black", linewidth=0.5)
    ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Zero trend")
    ax.set_xlabel("Trend Slope (mm/year)", fontweight="bold")
    ax.set_ylabel("Frequency", fontweight="bold")
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    ax.set_title("(b) Distribution of Linear Trends", fontweight="bold")
    ax = axes[1]
    data = [df[df["product"] == p]["trend_slope"].dropna() for p in PRODUCTS]
    bp = ax.boxplot(data, labels=PRODUCTS, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="red", markersize=5))
    for patch in bp["boxes"]:
        patch.set_facecolor("#1f77b4")
        patch.set_alpha(0.6)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.7)
    ax.set_ylabel("Trend Slope (mm/year)", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_title("(c) Trend Magnitude by Product", fontweight="bold")
    summary = "Mean slopes:\n" + "\n".join(
        f"{p}: {np.nanmean(d):.3f} mm/yr" for p, d in zip(PRODUCTS, data))
    ax.text(0.02, 0.98, summary, transform=ax.transAxes, va="top", ha="left",
            fontsize=7, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig2_Trend_Slopes.png"))


def plot_stationarity_comparison(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 3 - ADF p-value before vs. after detrending (scatter + violin)."""
    fig, axes = create_agu_figure(nrows=1, ncols=2, figsize=(7, 3.5))
    ax = axes[0]
    for product in PRODUCTS:
        sub = df[df["product"] == product]
        ax.scatter(sub["adf_orig"], sub["adf_resid"], label=product, alpha=0.7,
                   s=40, color=PRODUCT_COLORS[product], edgecolors="black",
                   linewidth=0.5)
    lims = [1e-10, 1]
    ax.plot(lims, lims, "k--", alpha=0.5, linewidth=1, label="No change")
    ax.axhline(ALPHA, color="red", linestyle=":", linewidth=1.5, alpha=0.7,
               label=f"\u03b1 = {ALPHA}")
    ax.axvline(ALPHA, color="red", linestyle=":", linewidth=1.5, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("ADF p-value (Original)", fontweight="bold")
    ax.set_ylabel("ADF p-value (Detrended)", fontweight="bold")
    ax.legend(frameon=True, fancybox=False, edgecolor="black", fontsize=8)
    ax.set_title("(d) Stationarity: Original vs. Detrended", fontweight="bold")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax = axes[1]
    improvements = []
    for product in PRODUCTS:
        sub = df[df["product"] == product]
        improvements.append(
            (np.log10(sub["adf_resid"]) - np.log10(sub["adf_orig"])).dropna().values)
    ax.violinplot(improvements, positions=range(len(PRODUCTS)),
                  showmeans=True, showmedians=True)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.7,
               label="No change")
    ax.set_xticks(range(len(PRODUCTS)))
    ax.set_xticklabels(PRODUCTS)
    ax.set_ylabel("Log10(p-value) Change", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_title("(e) Stationarity Improvement", fontweight="bold")
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig3_Stationarity_ADF.png"))


def plot_std_comparison(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 4 - original vs residual std (scatter) and relative change (box)."""
    fig, axes = create_agu_figure(nrows=1, ncols=2, figsize=(7, 3.5))
    ax = axes[0]
    for product in PRODUCTS:
        sub = df[df["product"] == product]
        ax.scatter(sub["orig_std"], sub["resid_std"], label=product, alpha=0.7,
                   s=40, color=PRODUCT_COLORS[product], edgecolors="black",
                   linewidth=0.5)
    lims = [ax.get_xlim()[0], ax.get_xlim()[1]]
    ax.plot(lims, lims, "k--", alpha=0.5, linewidth=1.5, label="1:1 line")
    ax.set_xlabel("Original Std Dev (mm)", fontweight="bold")
    ax.set_ylabel("Residual Std Dev (mm)", fontweight="bold")
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    ax.set_title("(f) Variability: Original vs. Detrended", fontweight="bold")
    ax = axes[1]
    data = [df[df["product"] == p]["delta_sigma_percent"].dropna() for p in PRODUCTS]
    bp = ax.boxplot(data, labels=PRODUCTS, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="red", markersize=5))
    for patch in bp["boxes"]:
        patch.set_facecolor("#ff7f0e")
        patch.set_alpha(0.6)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.7)
    ax.set_ylabel("\u0394\u03c3 = (\u03c3_resid - \u03c3_orig)/\u03c3_orig \u00d7 100 (%)",
                  fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_title("(g) Relative Change in Variability", fontweight="bold")
    summary = "Mean \u0394\u03c3%:\n" + "\n".join(
        f"{p}: {np.nanmean(d):.2f}%" for p, d in zip(PRODUCTS, data))
    ax.text(0.02, 0.98, summary, transform=ax.transAxes, va="top", ha="left",
            fontsize=7, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig4_Std_Comparison.png"))


def plot_variance_reduction(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 5 - per-station variance reduction (%), grouped by product."""
    fig, ax = create_agu_figure(figsize=(7, max(4, 0.25 * df["station"].nunique())))
    stations = sorted(df["station"].unique())
    y_base = np.arange(len(stations))
    n_p = len(PRODUCTS)
    offset0 = (n_p - 1) / 2.0
    bh = 0.6
    for i, product in enumerate(PRODUCTS):
        sub = (df[df["product"] == product].set_index("station")["variance_reduction"]
               .reindex(stations))
        ax.barh(y_base + (i - offset0) * (bh / n_p), sub.values, height=bh / n_p,
                alpha=0.7, label=product, color=PRODUCT_COLORS[product],
                edgecolor="black", linewidth=0.3)
    ax.axvline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.7)
    ax.set_xlabel("Variance Reduction (%) = [(\u03c3\u00b2_orig - \u03c3\u00b2_resid)/\u03c3\u00b2_orig] \u00d7 100",
                  fontweight="bold")
    ax.set_ylabel("Station", fontweight="bold")
    ax.set_yticks(y_base)
    ax.set_yticklabels(stations)
    ax.set_title(" (h) Variance Reduction After Trend Removal",
                 fontweight="bold", pad=10)
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    stats_text = "Variance Reduction:\n" + "".join(
        f"{p}: {df[df['product']==p]['variance_reduction'].mean():.2f}% "
        f"\u00b1 {df[df['product']==p]['variance_reduction'].std():.2f}%\n"
        for p in PRODUCTS)
    ax.text(0.98, 0.02, stats_text.strip(), transform=ax.transAxes, va="bottom",
            ha="right", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5))
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig5_Variance_Reduction.png"))


def plot_aggregated_variance_reduction(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 6 - aggregated mean variance reduction by product."""
    fig, ax = create_agu_figure(figsize=(7, 5))
    x = np.arange(len(PRODUCTS))
    cols = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for i, product in enumerate(PRODUCTS):
        sub = df[df["product"] == product]
        mean_vr, std_vr = np.nanmean(sub["variance_reduction"]), np.nanstd(sub["variance_reduction"])
        ax.bar(x[i], mean_vr, yerr=std_vr, capsize=3, color=cols[i], alpha=0.8, label=product)
        ax.text(x[i], mean_vr + std_vr + 0.5, f"{mean_vr:.1f}%", ha="center",
                va="bottom", fontsize=9)
    ax.set_ylabel("Mean Variance Reduction (%)", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(PRODUCTS)
    ax.legend(frameon=True, fancybox=False, edgecolor="black")
    ax.set_title("(i) Overall Variance Reduction After Trend Removal",
                 fontweight="bold", pad=10)
    stats_text = "Per Product Mean \u00b1 Std:\n" + "\n".join(
        f"{p}: {np.nanmean(df[df['product']==p]['variance_reduction']):.2f}% "
        f"\u00b1 {np.nanstd(df[df['product']==p]['variance_reduction']):.2f}%"
        for p in PRODUCTS)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, va="top", ha="left",
            fontsize=8, bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig6_Aggregated_Variance_Reduction.png"))


def plot_strength_metrics(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 7 - box-plots of trend strength F_T and seasonal strength F_S."""
    fig, axes = create_agu_figure(nrows=1, ncols=2, figsize=(7, 3.5))
    ax = axes[0]
    d_t = [df[df["product"] == p]["trend_strength"].dropna() for p in PRODUCTS]
    bp = ax.boxplot(d_t, labels=PRODUCTS, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="red", markersize=5))
    for patch in bp["boxes"]:
        patch.set_facecolor("#d62728")
        patch.set_alpha(0.6)
    ax.set_ylabel("Trend Strength Ft", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_title("(a) Trend Strength", fontweight="bold")
    ax.set_ylim(0, 1)
    ax = axes[1]
    d_s = [df[df["product"] == p]["seasonal_strength"].dropna() for p in PRODUCTS]
    bp = ax.boxplot(d_s, labels=PRODUCTS, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="red", markersize=5))
    for patch in bp["boxes"]:
        patch.set_facecolor("#2ca02c")
        patch.set_alpha(0.6)
    ax.set_ylabel("Seasonal Strength Fs", fontweight="bold")
    ax.set_xlabel("PWV Product", fontweight="bold")
    ax.set_title("(b) Seasonal Strength", fontweight="bold")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    return save_fig(fig, os.path.join(out_dir, "Fig7_Strength_Metrics.png"))


def plot_metric_heatmaps(df: pd.DataFrame, out_dir: str) -> str:
    """Fig 8 - station x product heatmaps of four key metrics.

    A compact whole-cohort overview: each cell is one station-product value,
    annotated, with its own colour map (diverging for delta-sigma about zero).
    """
    metrics = [
        ("trend_strength", "Trend strength F$_T$", "viridis", None),
        ("seasonal_strength", "Seasonal strength F$_S$", "viridis", None),
        ("variance_reduction", "Variance reduction (%)", "cividis", None),
        ("delta_sigma_percent", "\u0394\u03c3 (%)", "coolwarm", 0.0),
    ]
    stations = sorted(df["station"].unique())
    n_s = len(stations)
    fig_h = max(6.0, 0.32 * n_s + 2.0)
    fig, axes = plt.subplots(2, 2, figsize=(max(9.0, len(PRODUCTS) * 2.2 + 5.0), fig_h))

    for ax, (col, label, cmap, center) in zip(axes.flat, metrics):
        pivot = (df.pivot_table(index="station", columns="product", values=col)
                 .reindex(index=stations, columns=PRODUCTS))
        vals = pivot.values.astype(float)
        if center is not None:
            vmax = np.nanmax(np.abs(vals)) if np.isfinite(vals).any() else 1.0
            im = ax.imshow(vals, aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax)
        else:
            im = ax.imshow(vals, aspect="auto", cmap=cmap)
        ax.set_xticks(range(len(PRODUCTS)))
        ax.set_xticklabels(PRODUCTS)
        ax.set_yticks(range(n_s))
        ax.set_yticklabels(stations, fontsize=max(5, min(8, int(260 / max(1, n_s)))))
        ax.set_title(label, fontweight="bold")
        for i in range(n_s):
            for j in range(len(PRODUCTS)):
                v = vals[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                            color="white" if cmap in ("viridis", "cividis") else "black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("Per-station metric heatmaps (station \u00d7 product)",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return save_fig(fig, os.path.join(out_dir, "Fig8_Metric_Heatmaps.png"))


def plot_spatial_metric_maps(df: pd.DataFrame,
                             coords: Dict[str, Tuple[float, float]],
                             out_dir: str) -> Optional[str]:
    """Fig 9 - station markers coloured by trend slope, F_T and variance reduction.

    Each metric is averaged across products per station and plotted at the
    station location.  Uses Cartopy (coastlines/borders) when available,
    otherwise a clean lon/lat scatter.  Returns None if no usable coordinates.
    """
    usable = [s for s in df["station"].unique() if s in coords]
    if not usable:
        print("[INFO] No matching station coordinates; spatial maps skipped.")
        return None

    metrics = [("trend_slope", "Trend slope (mm/yr)", "coolwarm", True),
               ("trend_strength", "Trend strength F$_T$", "viridis", False),
               ("variance_reduction", "Variance reduction (%)", "cividis", False)]

    # Optional Cartopy.
    proj = None
    feat = None
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        proj, feat = ccrs.PlateCarree(), cfeature
    except Exception:
        proj = None

    lons = np.array([coords[s][1] for s in usable])
    lats = np.array([coords[s][0] for s in usable])
    pad = 2.0
    extent = [lons.min() - pad, lons.max() + pad, lats.min() - pad, lats.max() + pad]

    subplot_kw = {"projection": proj} if proj is not None else {}
    fig, axes = plt.subplots(1, len(metrics), figsize=(5.2 * len(metrics), 5.0),
                             subplot_kw=subplot_kw)
    if len(metrics) == 1:
        axes = [axes]

    for ax, (col, label, cmap, diverge) in zip(np.atleast_1d(axes), metrics):
        agg = df.groupby("station")[col].mean()
        vals = np.array([agg.get(s, np.nan) for s in usable], dtype=float)
        kw = {}
        if proj is not None:
            ax.set_extent(extent, crs=proj)
            ax.add_feature(feat.COASTLINE, linewidth=0.6)
            ax.add_feature(feat.BORDERS, linewidth=0.4, alpha=0.6)
            ax.add_feature(feat.LAND, facecolor="0.95")
            ax.add_feature(feat.OCEAN, facecolor="#eaf2f8")
            kw["transform"] = proj
        else:
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])
            ax.set_xlabel("Longitude", fontweight="bold")
            ax.set_ylabel("Latitude", fontweight="bold")
            ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
        if diverge and np.isfinite(vals).any():
            vmax = np.nanmax(np.abs(vals))
            sc = ax.scatter(lons, lats, c=vals, cmap=cmap, vmin=-vmax, vmax=vmax,
                            s=90, edgecolor="black", linewidth=0.6, zorder=5, **kw)
        else:
            sc = ax.scatter(lons, lats, c=vals, cmap=cmap, s=90, edgecolor="black",
                            linewidth=0.6, zorder=5, **kw)
        for s, lo, la in zip(usable, lons, lats):
            ax.annotate(s, (lo, la), xytext=(3, 3), textcoords="offset points",
                        fontsize=6, zorder=6,
                        **({"transform": None} if proj is not None else {}))
        ax.set_title(label, fontweight="bold")
        fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("Spatial distribution of trend metrics (mean across products)",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return save_fig(fig, os.path.join(out_dir, "Fig9_Spatial_Maps.png"))


# =============================================================================
# SECTION 13 - TABLES & STATISTICAL TESTS
# =============================================================================
def build_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    """Build the per-product summary table (used by CSV and Excel exports)."""
    rows = []
    for product in PRODUCTS:
        sub = df[df["product"] == product]
        n = len(sub)
        rows.append({
            "Product": product, "N_Stations": n,
            "Mean_Slope_mm_yr": sub["trend_slope"].mean(),
            "Significant_Trends_pct": (sub["trend_pvalue"] < ALPHA).sum() / n * 100 if n else np.nan,
            "Trend_Variance_pct": sub["trend_contribution"].mean(),
            "Seasonal_Variance_pct": sub["seasonal_contribution"].mean(),
            "Residual_Variance_pct": sub["resid_contribution"].mean(),
            "Orig_Stationary_N": int((sub["adf_orig"] < ALPHA).sum()),
            "Resid_Stationary_N": int((sub["adf_resid"] < ALPHA).sum()),
            "Mean_Delta_Sigma_pct": sub["delta_sigma_percent"].mean(),
            "Std_Delta_Sigma_pct": sub["delta_sigma_percent"].std(),
            "Mean_Variance_Reduction_pct": sub["variance_reduction"].mean(),
            "Mean_Trend_Strength_F_T": sub["trend_strength"].mean(),
            "Mean_Seasonal_Strength_F_S": sub["seasonal_strength"].mean(),
        })
    return pd.DataFrame(rows)


def build_anova_df(df: pd.DataFrame) -> pd.DataFrame:
    """Build the ANOVA / Kruskal-Wallis comparison table across products."""
    metrics = [("Trend Slopes", "trend_slope"),
               ("Trend Variance Contribution", "trend_contribution"),
               ("Delta Sigma Percent", "delta_sigma_percent"),
               ("Variance Reduction", "variance_reduction"),
               ("Trend Strength F_T", "trend_strength"),
               ("Seasonal Strength F_S", "seasonal_strength")]
    rows = []
    for label, col in metrics:
        groups = [df[df["product"] == p][col].dropna() for p in PRODUCTS]
        f_stat, p_anova = f_oneway(*groups)
        h_stat, p_kw = kruskal(*groups)
        rows.append({"Test": label, "ANOVA_F": f_stat, "ANOVA_p": p_anova,
                     "Kruskal_H": h_stat, "Kruskal_p": p_kw,
                     "Interpretation": ("No significant difference"
                                        if p_anova > ALPHA else "Significant difference")})
    return pd.DataFrame(rows)


def create_statistical_summary(df: pd.DataFrame, out_dir: str) -> str:
    """Write Table 1 (per-product summary) to CSV."""
    out = os.path.join(out_dir, "Table1_Statistical_Summary.csv")
    build_summary_df(df).to_csv(out, index=False, float_format="%.4f")
    return out


def perform_anova_tests(df: pd.DataFrame, out_dir: str) -> str:
    """Write Table 2 (ANOVA / Kruskal-Wallis) to CSV."""
    out = os.path.join(out_dir, "Table2_ANOVA_Tests.csv")
    build_anova_df(df).to_csv(out, index=False, float_format="%.6f")
    return out


# =============================================================================
# SECTION 14 - EXCEL WORKBOOK, MULTI-PANEL, AND REPORT
# =============================================================================
def write_excel_summary(df: pd.DataFrame, out_dir: str) -> Optional[str]:
    """Write a formatted multi-sheet Excel workbook of all result tables.

    Sheets: Detailed_Results, Per_Product_Summary, ANOVA_Tests, and pivot
    tables (station x product) for F_T, F_S, variance reduction and
    delta-sigma.  Stores computed values (not live formulas) so the workbook is
    static and free of formula errors; headers are bold on a dark fill, panes
    frozen, columns sized, and a consistent font applied.
    """
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except Exception as exc:
        print(f"[WARN] openpyxl unavailable; Excel workbook skipped ({exc})")
        return None

    out = os.path.join(out_dir, "STL_Summary_Workbook.xlsx")
    summary_df = build_summary_df(df)
    anova_df = build_anova_df(df)
    pivots = {
        "Pivot_Trend_Strength": df.pivot_table(index="station", columns="product",
                                                values="trend_strength"),
        "Pivot_Seasonal_Strength": df.pivot_table(index="station", columns="product",
                                                   values="seasonal_strength"),
        "Pivot_Variance_Reduction": df.pivot_table(index="station", columns="product",
                                                    values="variance_reduction"),
        "Pivot_Delta_Sigma": df.pivot_table(index="station", columns="product",
                                            values="delta_sigma_percent"),
    }

    # Write all sheets with pandas, then format with openpyxl.
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Detailed_Results", index=False)
        summary_df.to_excel(xw, sheet_name="Per_Product_Summary", index=False)
        anova_df.to_excel(xw, sheet_name="ANOVA_Tests", index=False)
        for name, piv in pivots.items():
            piv.reindex(columns=PRODUCTS).to_excel(xw, sheet_name=name[:31])

    wb = load_workbook(out)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF", name=EXCEL_FONT)
    body_font = Font(name=EXCEL_FONT)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for col_cells in ws.columns:
            longest = max((len(str(c.value)) if c.value is not None else 0)
                          for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(40, max(10, longest + 2))
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = body_font
                if isinstance(cell.value, float):
                    cell.number_format = "0.000"
    wb.save(out)
    return out


def create_summary_multipanel(fig_paths: List[str], out_dir: str) -> Optional[str]:
    """Tile the main cohort figures into a single publication-ready PNG."""
    valid = [p for p in fig_paths if p and os.path.exists(p)]
    if len(valid) < 2:
        return None
    images = [Image.open(p).convert("RGB") for p in valid[:6]]
    ncols = 3 if len(images) > 2 else 2
    nrows = (len(images) + ncols - 1) // ncols
    target_h = 1200
    resized = [img.resize((int(target_h * img.size[0] / img.size[1]), target_h),
                          Image.LANCZOS) for img in images]
    max_w = max(img.size[0] for img in resized)
    canvas = Image.new("RGB", (max_w * ncols, target_h * nrows), (255, 255, 255))
    for idx, img in enumerate(resized):
        r, c = divmod(idx, ncols)
        canvas.paste(img, (c * max_w + (max_w - img.size[0]) // 2, r * target_h))
    out = os.path.join(out_dir, "Figure_Multipanel_Summary.png")
    canvas.save(out, "PNG", optimize=True, dpi=(300, 300))
    return out


def create_key_findings_report(df: pd.DataFrame, out_dir: str) -> str:
    """Generate the plain-text narrative report summarising every metric."""
    R: List[str] = []
    add = R.append
    add("=" * 80)
    add("STL DETRENDING ANALYSIS - KEY FINDINGS FOR AGU MANUSCRIPT")
    add("=" * 80)
    add("")
    add("MEASURING STRENGTH OF TREND AND SEASONALITY")
    add("-" * 80)
    add("Using variance-based metrics (Wang, Smith, & Hyndman, 2006):")
    add("F_T = max(0, [Var(Y - S) - Var(R)] / Var(Y))  # Trend strength")
    add("F_S = max(0, [Var(Y - T) - Var(R)] / Var(Y))  # Seasonal strength")
    add("F_T/F_S ~ 0: weak; ~ 1: strong")
    add("")
    add("1. OVERALL DATASET CHARACTERISTICS")
    add("-" * 80)
    add(f" Total stations analyzed: {df['station'].nunique()}")
    add(f" Total series analyzed: {len(df)}")
    add(f" Products: {', '.join(PRODUCTS)}")
    add(f" Mean observation period: {df['n_obs'].mean():.0f} days "
        f"({df['n_obs'].mean()/365.25:.1f} years)")
    add("")
    add("2. TREND ANALYSIS")
    add("-" * 80)
    for product in PRODUCTS:
        s = df[df["product"] == product]
        sig = int((s["trend_pvalue"] < ALPHA).sum())
        mean_pwv = s["orig_mean"].mean()
        slope = s["trend_slope"].mean()
        per_decade = (slope * 10 / mean_pwv) * 100 if mean_pwv > 0 else 0
        add(f" {product}:")
        add(f"  Mean trend: {slope:.4f} \u00b1 {s['trend_slope'].std():.4f} mm/year")
        add(f"  Significant trends (p < {ALPHA}): {sig}/{len(s)} ({sig/len(s)*100:.1f}%)")
        add(f"  Trend magnitude: {per_decade:.3f}% per decade")
        add(f"  Trend strength F_T: {s['trend_strength'].mean():.3f} "
            f"(weak <0.2, moderate 0.2-0.5, strong >0.5)")
    add("")
    add("3. VARIANCE DECOMPOSITION")
    add("-" * 80)
    for product in PRODUCTS:
        s = df[df["product"] == product]
        add(f" {product}:")
        add(f"  Trend contribution: {s['trend_contribution'].mean():.2f}% "
            f"\u00b1 {s['trend_contribution'].std():.2f}%")
        add(f"  Seasonal contribution: {s['seasonal_contribution'].mean():.2f}% "
            f"\u00b1 {s['seasonal_contribution'].std():.2f}%")
        add(f"  Residual contribution: {s['resid_contribution'].mean():.2f}% "
            f"\u00b1 {s['resid_contribution'].std():.2f}%")
        add(f"  Seasonal strength F_S: {s['seasonal_strength'].mean():.3f} "
            f"(weak <0.2, moderate 0.2-0.5, strong >0.5)")
    add("")
    add("4. STATIONARITY ASSESSMENT (ADF TEST)")
    add("-" * 80)
    for product in PRODUCTS:
        s = df[df["product"] == product]
        o = int((s["adf_orig"] < ALPHA).sum())
        r = int((s["adf_resid"] < ALPHA).sum())
        add(f" {product}:")
        add(f"  Original series stationary: {o}/{len(s)} ({o/len(s)*100:.1f}%)")
        add(f"  Detrended series stationary: {r}/{len(s)} ({r/len(s)*100:.1f}%)")
        add(f"  Improvement: {r-o} stations ({(r-o)/len(s)*100:.1f}%)")
    add("")
    add("5. IMPACT ON SHORT-TERM VARIABILITY")
    add("-" * 80)
    for product in PRODUCTS:
        s = df[df["product"] == product]
        md = s["delta_sigma_percent"].mean()
        impact = ("NEGLIGIBLE (<1%)" if abs(md) < 1 else "MINIMAL (1-5%)" if abs(md) < 5
                  else "MODERATE (5-10%)" if abs(md) < 10 else "SUBSTANTIAL (>10%)")
        add(f" {product}:")
        add(f"  Mean \u0394\u03c3%: {md:.2f}% \u00b1 {s['delta_sigma_percent'].std():.2f}%")
        add(f"  Median \u0394\u03c3%: {s['delta_sigma_percent'].median():.2f}%")
        add(f"  Impact classification: {impact}")
    add("")
    add("6. VARIANCE REDUCTION AFTER DETRENDING")
    add("-" * 80)
    for product in PRODUCTS:
        s = df[df["product"] == product]
        add(f" {product}:")
        add(f"  Mean variance reduction: {s['variance_reduction'].mean():.2f}% "
            f"\u00b1 {s['variance_reduction'].std():.2f}%")
    add("")
    add("7. KEY CONCLUSION FOR MANUSCRIPT")
    add("-" * 80)
    overall_trend_var = df["trend_contribution"].mean()
    overall_delta = df["delta_sigma_percent"].mean()
    add(f" * Trend component accounts for only {overall_trend_var:.1f}% of total variance")
    add(f" * Detrending changes short-term variability by {abs(overall_delta):.2f}% on average")
    add(f" * Variance reduction from detrending is {df['variance_reduction'].mean():.2f}%")
    add(f" * Overall trend strength F_T: {df['trend_strength'].mean():.3f}")
    add(f" * Overall seasonal strength F_S: {df['seasonal_strength'].mean():.3f}")
    add("")
    if abs(overall_delta) < 2 and overall_trend_var < 15:
        add(" [+] RECOMMENDATION: Detrending is NOT necessary for 3CH/ETC analysis")
        add("     - Trends contribute minimally to total variance (<15%)")
        add("     - Impact on short-term variability is negligible (<2%)")
        add("     - 3CH and ETC focus on high-frequency variability")
        add("     - Detrending does not substantially alter residual characteristics")
    else:
        add(" [!] RECOMMENDATION: Consider detrending for 3CH/ETC analysis")
        add("     - Trends may influence short-term variability metrics")
    add("")
    add("=" * 80)
    out = os.path.join(out_dir, "Key_Findings_Report.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(R))
    return out


# =============================================================================
# SECTION 15 - PIPELINE ORCHESTRATION
# =============================================================================
def run_pipeline(overrides: Dict) -> None:
    """Execute the full analysis using the already-applied configuration."""
    print("=" * 80)
    print("OPTIMIZED STL DETRENDING ANALYSIS FOR AGU PUBLICATION (v3)")
    print("=" * 80)
    print("Per-station decomposition, variance, climatology & residual diagnostics")
    print("Cohort heatmaps + spatial maps | Excel workbook | vector export")
    print("Gap-aware plotting | parallel STL+figures | strength metrics F_T, F_S")
    print()

    # --- Resolve I/O and build the output directory tree ---
    in_dir, is_temp = prepare_input_dir(INPUT_PATH)
    out_dir = ensure_outdir(OUTPUT_ROOT)
    agg_dir = ensure_outdir(os.path.join(out_dir, SUBDIR_AGG))
    comp_dir = ensure_outdir(os.path.join(out_dir, SUBDIR_COMPONENTS))
    sfig_dir = ensure_outdir(os.path.join(out_dir, SUBDIR_STATION_FIGS))

    csvs = discover_csvs(in_dir)
    if not csvs:
        raise FileNotFoundError(f"No CSV files found in: {in_dir}")
    coords = load_station_coords(COORDS_CSV)

    print(f"Found {len(csvs)} station CSV files")
    print(f"Backend='{PARALLEL_BACKEND}', N_JOBS="
          f"{'all cores' if N_JOBS < 0 else N_JOBS} | "
          f"station figs={MAKE_STATION_FIGURES}, diagnostics={MAKE_DIAGNOSTICS}, "
          f"climatology={MAKE_CLIMATOLOGY}")
    print(f"Vector formats={VECTOR_FORMATS or 'PNG only'}, "
          f"Excel={EXCEL_SUMMARY}, coords={'yes' if coords else 'no'}")
    print()

    # --- Parallel per-station processing (STL + stats + CSV + figures) ---
    print("Processing stations...")
    all_results = Parallel(n_jobs=N_JOBS, backend=PARALLEL_BACKEND, verbose=10)(
        delayed(process_station)(csv, comp_dir, sfig_dir, overrides) for csv in csvs)

    results_flat = [r for sub in all_results for r in sub]
    if not results_flat:
        raise ValueError("No valid results generated. Check input data.")
    df = pd.DataFrame([vars(r) for r in results_flat])
    print(f"\nProcessed {len(df)} series from {df['station'].nunique()} stations\n")

    # --- Master CSV (kept intact in OUTPUT_ROOT) ---
    detailed_csv = os.path.join(out_dir, "STL_Detailed_Results.csv")
    df.to_csv(detailed_csv, index=False, float_format="%.6f")
    print(f"[ok] {os.path.basename(detailed_csv)}")

    # --- Tables ---
    print("\nGenerating statistical tables...")
    print(f"[ok] {os.path.basename(create_statistical_summary(df, out_dir))}")
    print(f"[ok] {os.path.basename(perform_anova_tests(df, out_dir))}")

    # --- Excel workbook ---
    if EXCEL_SUMMARY:
        xlsx = write_excel_summary(df, out_dir)
        if xlsx:
            print(f"[ok] {os.path.basename(xlsx)}")

    # --- Aggregate figures ---
    print("\nGenerating aggregate (cohort) figures...")
    fig1 = plot_variance_contributions(df, agg_dir)
    fig2 = plot_trend_slopes(df, agg_dir)
    fig3 = plot_stationarity_comparison(df, agg_dir)
    fig4 = plot_std_comparison(df, agg_dir)
    fig5 = plot_variance_reduction(df, agg_dir)
    fig6 = plot_aggregated_variance_reduction(df, agg_dir)
    fig7 = plot_strength_metrics(df, agg_dir)
    fig8 = plot_metric_heatmaps(df, agg_dir)
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        print(f"[ok] {os.path.basename(f)}")
    fig9 = plot_spatial_metric_maps(df, coords, agg_dir)
    if fig9:
        print(f"[ok] {os.path.basename(fig9)}")

    multipanel = create_summary_multipanel([fig1, fig2, fig3, fig4, fig5, fig6], agg_dir)
    if multipanel:
        print(f"[ok] {os.path.basename(multipanel)}")

    # --- Narrative report ---
    print("\nGenerating key-findings report...")
    print(f"[ok] {os.path.basename(create_key_findings_report(df, out_dir))}")

    if is_temp:
        shutil.rmtree(in_dir, ignore_errors=True)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"All outputs saved under: {out_dir}")
    print(f"  Tables/reports/workbook : OUTPUT_ROOT/")
    print(f"  Cohort figures          : {SUBDIR_AGG}/")
    print(f"  Per-station components   : {SUBDIR_COMPONENTS}/<station>_detrended.csv")
    print(f"  Per-station figures      : {SUBDIR_STATION_FIGS}/<station>/")
    print()


def main(argv: Optional[List[str]] = None) -> None:
    """Parse CLI/YAML, apply configuration, then run the pipeline."""
    args = parse_args(argv)
    overrides = resolve_config(args)
    apply_runtime_config(overrides)   # parent process
    run_pipeline(overrides)           # workers re-apply via process_station


# =============================================================================
# SECTION 16 - ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
