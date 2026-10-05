"""
ENHANCED PWV QC / OUTLIER ANALYSIS PIPELINE WITH DETRENDING
============================================================
Improvements:
1. Multiple outlier detection methods (Hampel, IQR, Z-score)
2. Enhanced visualizations for manuscript quality
3. Comprehensive summary statistics
4. Sample size adequacy assessment
5. Method comparison analysis
6. LINEAR DETRENDING ANALYSIS (NEW)
References:
   Hampel, F. R. (1974). JASA 69(346), 383–393.
   Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley.
   Leys, C., et al. (2013). J. Exp. Soc. Psychol. 49, 764–766.
"""
from pathlib import Path
import os
import io
import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch, Rectangle
from scipy.stats import gaussian_kde, zscore, linregress
import seaborn as sns
import warnings

REPO_ROOT = Path(__file__).resolve().parents[1]

warnings.filterwarnings('ignore')
# ============================================================================
# USER CONFIGURATION SECTION - MODIFY THESE PATHS AND PARAMETERS
# ============================================================================
# INPUT/OUTPUT PATHS
INPUT_PATH = REPO_ROOT / "Data" / "Collocated_PWVs (unpreprocessed)" / "PWVdata_27 stations(unpreprocessed).zip"
OUTPUT_ROOT = REPO_ROOT / "Analysis" / "Results_Preprocessing" / "Results_Outlier detection & removal"

# OUTLIER DETECTION METHOD SELECTION
# =============================================================================
# # Options: 'Hampel', 'IQR', 'Zscore', 'ALL'
# #          - Use 'Hampel', 'IQR', or 'Zscore' to apply only that method
# #          - Use 'ALL' to compare all three methods and automatically select the best
# =============================================================================
OUTLIER_METHOD = 'All' # Change to 'Hampel', 'IQR', 'Zscore', or 'ALL'


# OPTIMAL METHOD SELECTION (used when OUTLIER_METHOD = 'ALL')
# =============================================================================
# # Options: 'CONSERVATIVE' or 'CONSENSUS'
# #           - 'CONSERVATIVE': Use method that detects fewest outliers (most conservative)
# #           - 'CONSENSUS': Use outliers flagged by at least 2 out of 3 methods (majority vote)
# =============================================================================
OPTIMAL_SELECTION = 'CONSERVATIVE' # Change to 'CONSERVATIVE' or 'CONSENSUS'

# HAMPEL FILTER PARAMETERS
HAMPEL_WINDOW = 7 # Rolling window length (days) - typically 7-14
HAMPEL_SIGMA = 3.0 # Sigma threshold for MAD - typically 2.5-3.5

# IQR METHOD PARAMETERS
IQR_MULTIPLIER = 1.5 # IQR multiplier (Tukey's rule) - typically 1.5

# Z-SCORE METHOD PARAMETERS
ZSCORE_THRESHOLD = 3.0 # Z-score threshold - typically 2.5-3.5

# PHYSICAL PLAUSIBILITY LIMITS
PWV_MIN_MM = 0.0 # Lower bound [mm] - cannot be negative
PWV_MAX_MM = 100.0 # Upper bound [mm] - max for tropical atmosphere

# SAMPLE SIZE QUALITY THRESHOLDS
MIN_VALID_DAYS = 700 # Excellent: recommended for 3CH/ETC analysis
MIN_ACCEPTABLE_DAYS = 365 # Acceptable: use with caution
MIN_WARNING_DAYS = 180 # Warning: limited reliability

# DETRENDING CONFIGURATION
DETRENDING_DEGREE = 2  # Polynomial degree for detrending (1=linear, 2=quadratic, 3=cubic, etc.)

# ============================================================================
# END OF USER CONFIGURATION
# ============================================================================
# Plot styling
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 300,
})
# -----------------------
# IO / UTILITIES
# -----------------------
def ensure_dir(path):
    """Ensure the directory at the given path exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)
    
def list_station_files(input_path):
    """Return list of (name, src, mode) for station CSVs.
   
    Supports both directory of CSV files and ZIP archives containing CSVs.
   
    Parameters:
    -----------
    input_path : str
        Path to directory or ZIP file.
   
    Returns:
    --------
    list
        List of tuples (filename, source, mode) where mode is 'disk' or 'zip'.
    """
    if os.path.isdir(input_path):
        out = []
        for fname in sorted(os.listdir(input_path)):
            if fname.lower().endswith(".csv"):
                full = os.path.join(input_path, fname)
                out.append((fname, full, "disk"))
        if not out:
            raise RuntimeError("Directory provided but no .csv files found.")
        return out
    elif os.path.isfile(input_path) and input_path.lower().endswith(".zip"):
        zf = zipfile.ZipFile(input_path, "r")
        members = sorted([n for n in zf.namelist() if n.lower().endswith(".csv")])
        if not members:
            raise RuntimeError("ZIP provided but no .csv files found inside.")
        return [(m, zf, "zip") for m in members]
    else:
        raise RuntimeError("INPUT_PATH must be a folder of CSVs or a .zip with CSVs.")
        
def read_station_df(entry):
    """Read one station CSV into a pandas DataFrame.
   
    Handles both disk files and ZIP members.
   
    Parameters:
    -----------
    entry : tuple
        (filename, source, mode) from list_station_files.
   
    Returns:
    --------
    pd.DataFrame
        DataFrame with stripped column names.
    """
    name, src, mode = entry
    if mode == "disk":
        df = pd.read_csv(src)
    else:
        with src.open(name) as f:
            raw = f.read()
        df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip() for c in df.columns]
    return df

def build_datetime(df):
    """Build daily datetime column from YEAR/MONTH/DAY or YEAR/DOY columns.
   
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with date columns.
   
    Returns:
    --------
    pd.Series
        Datetime series aligned with df index.
   
    Raises:
    -------
    ValueError
        If neither YMD nor DOY format is available.
    """
    have_ymd = all(c in df.columns for c in ["YEAR", "MONTH", "DAY"])
    have_doy = all(c in df.columns for c in ["YEAR", "DOY"])
   
    if have_ymd:
        dt = pd.to_datetime(
            dict(year=df["YEAR"], month=df["MONTH"], day=df["DAY"]),
            errors="coerce",
        )
    elif have_doy:
        base = pd.to_datetime(
            df["YEAR"].astype(int).astype(str) + "-01-01",
            errors="coerce",
        )
        dt = base + pd.to_timedelta(df["DOY"] - 1, unit="D")
    else:
        raise ValueError("Station file missing date info.")
    return dt

# -----------------------
# OPTIMAL METHOD SELECTION
# -----------------------
def select_optimal_outliers(outlier_masks, method_names, selection_strategy='CONSERVATIVE'):
    """
    Select optimal outliers from multiple detection methods.
   
    Parameters:
    -----------
    outlier_masks : dict
        Dictionary of {method_name: boolean_series} outlier masks
    method_names : list
        List of method names used
    selection_strategy : str
        'CONSERVATIVE': Use method with fewest outliers
        'CONSENSUS': Use majority vote (2+ methods agree)
   
    Returns:
    --------
    optimal_mask : pd.Series
        Boolean series of selected outliers
    selected_method : str
        Name of method or strategy used
    """
    if selection_strategy == 'CONSERVATIVE':
        # Find method with fewest outliers
        outlier_counts = {name: mask.sum() for name, mask in outlier_masks.items()}
        selected_method = min(outlier_counts, key=outlier_counts.get)
        optimal_mask = outlier_masks[selected_method]
       
    elif selection_strategy == 'CONSENSUS':
        # Majority vote: outlier if 2+ methods agree
        vote_sum = sum(mask.astype(int) for mask in outlier_masks.values())
        optimal_mask = vote_sum >= 2
        selected_method = 'Consensus'
       
    else:
        raise ValueError(f"Unknown selection strategy: {selection_strategy}")
   
    return optimal_mask, selected_method

def get_methods_to_apply():
    """
    Determine which methods to apply based on OUTLIER_METHOD setting.
   
    Returns:
    --------
    methods_config : list
        List of (method_name, method_func, method_params) tuples
    apply_all : bool
        True if comparing all methods, False if using single method
    """
    all_methods = [
        ('Hampel', hampel_filter, {'window_size': HAMPEL_WINDOW,
                                   'n_sigmas': HAMPEL_SIGMA}),
        ('IQR', iqr_filter, {'multiplier': IQR_MULTIPLIER}),
        ('Zscore', zscore_filter, {'threshold': ZSCORE_THRESHOLD})
    ]
   
    if OUTLIER_METHOD.upper() == 'ALL':
        return all_methods, True
    elif OUTLIER_METHOD.capitalize() == 'Hampel':
        return [all_methods[0]], False
    elif OUTLIER_METHOD.upper() == 'IQR':
        return [all_methods[1]], False
    elif OUTLIER_METHOD.capitalize() == 'Zscore':
        return [all_methods[2]], False
    else:
        raise ValueError(f"Invalid OUTLIER_METHOD: {OUTLIER_METHOD}. "
                        f"Use 'Hampel', 'IQR', 'Zscore', or 'ALL'")
        
def hampel_filter(series_mm, window_size=7, n_sigmas=3.0,
                  pwv_min=0.0, pwv_max=100.0):
    """Hampel filter (robust outlier detection).
   
    Uses median absolute deviation (MAD) for robust Z-scores over a rolling window.
   
    Parameters:
    -----------
    series_mm : pd.Series
        PWV time series in mm.
    window_size : int
        Rolling window length (days).
    n_sigmas : float
        Threshold for outlier detection.
    pwv_min, pwv_max : float
        Physical bounds for PWV.
   
    Returns:
    --------
    cleaned : pd.Series
        Cleaned series with outliers replaced and interpolated.
    outliers : pd.Series
        Boolean mask of detected outliers.
    """
    x = series_mm.astype(float).copy()
    phys_ok = (x >= pwv_min) & (x <= pwv_max)
    x[~phys_ok] = np.nan
   
    x_work = x.interpolate(limit_direction="both")
    med = x_work.rolling(window=window_size, center=True, min_periods=1).median()
    mad = (x_work - med).abs().rolling(window=window_size, center=True, min_periods=1).median()
   
    robust_std = 1.4826 * mad.replace(0, np.nan)
    zscore_vals = (x_work - med) / robust_std
    outliers = zscore_vals.abs() > n_sigmas
   
    cleaned = x.copy()
    cleaned[outliers] = med[outliers]
    cleaned = cleaned.interpolate(limit_direction="both")
   
    return cleaned, outliers.fillna(False)

def iqr_filter(series_mm, multiplier=1.5, pwv_min=0.0, pwv_max=100.0):
    """IQR-based outlier detection (Tukey's method).
   
    Detects outliers beyond Q1 - multiplier*IQR and Q3 + multiplier*IQR.
   
    Parameters:
    -----------
    series_mm : pd.Series
        PWV time series in mm.
    multiplier : float
        IQR multiplier threshold.
    pwv_min, pwv_max : float
        Physical bounds for PWV.
   
    Returns:
    --------
    cleaned : pd.Series
        Cleaned series with outliers replaced by median and interpolated.
    outliers : pd.Series
        Boolean mask of detected outliers.
    """
    x = series_mm.astype(float).copy()
    phys_ok = (x >= pwv_min) & (x <= pwv_max)
    x[~phys_ok] = np.nan
   
    q1 = x.quantile(0.25)
    q3 = x.quantile(0.75)
    iqr = q3 - q1
   
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
   
    outliers = (x < lower_bound) | (x > upper_bound)
    median_val = x.median()
   
    cleaned = x.copy()
    cleaned[outliers] = median_val
    cleaned = cleaned.interpolate(limit_direction="both")
   
    return cleaned, outliers.fillna(False)

def zscore_filter(series_mm, threshold=3.0, pwv_min=0.0, pwv_max=100.0):
    """Z-score based outlier detection.
   
    Uses mean and standard deviation for Z-scores.
   
    Parameters:
    -----------
    series_mm : pd.Series
        PWV time series in mm.
    threshold : float
        Z-score threshold for outliers.
    pwv_min, pwv_max : float
        Physical bounds for PWV.
   
    Returns:
    --------
    cleaned : pd.Series
        Cleaned series with outliers replaced by mean and interpolated.
    outliers : pd.Series
        Boolean mask of detected outliers.
    """
    x = series_mm.astype(float).copy()
    phys_ok = (x >= pwv_min) & (x <= pwv_max)
    x[~phys_ok] = np.nan
   
    mean_val = x.mean()
    std_val = x.std()
   
    if std_val == 0:
        return x, pd.Series([False] * len(x), index=x.index)
   
    z_scores = np.abs((x - mean_val) / std_val)
    outliers = z_scores > threshold
   
    cleaned = x.copy()
    cleaned[outliers] = mean_val
    cleaned = cleaned.interpolate(limit_direction="both")
   
    return cleaned, outliers.fillna(False)



# -----------------------
# DETRENDING ANALYSIS (COMPLETE MODULE)
# -----------------------

def calculate_polynomial_trend(time_series, dates, degree=2):
    """
    Calculate polynomial trend from time series.
    
    Parameters:
    -----------
    time_series : pd.Series or np.array
        PWV values in mm
    dates : pd.Series
        Datetime values
    degree : int
        Polynomial degree (1=linear, 2=quadratic, etc.)
    
    Returns:
    --------
    effective_slope : float
        Effective slope (derivative at mean time) in mm/year
    trend_line : np.array
        Fitted trend values
    """
    # Remove NaN values
    valid_mask = ~np.isnan(time_series)
    if valid_mask.sum() < degree + 1:
        return np.nan, np.full_like(time_series, np.nan)
    
    valid_dates = dates[valid_mask]
    valid_values = time_series[valid_mask]
    
    # Convert dates to decimal years for regression
    decimal_years = valid_dates.dt.year + (valid_dates.dt.dayofyear - 1) / 365.25
    
    # Perform polynomial regression
    coeffs = np.polyfit(decimal_years, valid_values, degree)
    
    # Create full trend line for all dates
    all_decimal_years = dates.dt.year + (dates.dt.dayofyear - 1) / 365.25
    trend_line = np.polyval(coeffs, all_decimal_years)
    
    # Effective slope: derivative evaluated at mean time
    mean_time = np.mean(all_decimal_years[~np.isnan(time_series)])
    derivative_coeffs = np.polyder(coeffs)
    effective_slope = np.polyval(derivative_coeffs, mean_time)
    
    return effective_slope, trend_line


def calculate_detrending_impact(time_series, dates, degree=2):
    """
    Calculate the impact of detrending on time series variability.
    
    Parameters:
    -----------
    time_series : pd.Series or np.array
        PWV values in mm (cleaned)
    dates : pd.Series
        Datetime values
    degree : int
        Polynomial degree for detrending
    
    Returns:
    --------
    results : dict
        Dictionary containing:
        - trend_slope: Effective slope in mm/year
        - std_original: Standard deviation of original series
        - std_detrended: Standard deviation of detrended series
        - delta_std_pct: Percentage change in std after detrending
        - detrended_series: The detrended time series
    """
    # Calculate polynomial trend
    slope, trend_line = calculate_polynomial_trend(time_series, dates, degree)
    
    # Calculate std of original series
    std_original = np.nanstd(time_series)
    
    # Create detrended series
    detrended_series = time_series - trend_line
    
    # Calculate std of detrended series
    std_detrended = np.nanstd(detrended_series)
    
    # Calculate percentage change
    if std_original > 0:
        delta_std_pct = ((std_detrended - std_original) / std_original) * 100
    else:
        delta_std_pct = np.nan
    
    return {
        'trend_slope': slope,
        'std_original': std_original,
        'std_detrended': std_detrended,
        'delta_std_pct': delta_std_pct,
        'detrended_series': detrended_series
    }


def perform_detrending_analysis(cleaned_data_dict, degree=2):
    """
    Perform detrending analysis on all stations and products.
    
    Parameters:
    -----------
    cleaned_data_dict : dict
        Dictionary with station names as keys, each containing:
        - 'dates': pd.Series of datetime values
        - 'IGS_clean': cleaned IGS PWV time series
        - 'VMF3_clean': cleaned VMF3 PWV time series
        - 'ERA5_clean': cleaned ERA5 PWV time series
    degree : int
        Polynomial degree for detrending
    
    Returns:
    --------
    detrending_results : pd.DataFrame
        DataFrame with columns:
        - Station
        - IGS_trend, IGS_delta_std_pct
        - VMF3_trend, VMF3_delta_std_pct
        - ERA5_trend, ERA5_delta_std_pct
    """
    results_list = []
    
    for station, data in cleaned_data_dict.items():
        dates = data['dates']
        
        result_row = {'Station': station}
        
        for product in ['IGS', 'VMF3', 'ERA5']:
            clean_key = f'{product}_clean'
            
            if clean_key in data:
                time_series = data[clean_key]
                analysis = calculate_detrending_impact(time_series, dates, degree)
                
                result_row[f'{product}_trend'] = analysis['trend_slope']
                result_row[f'{product}_delta_std_pct'] = analysis['delta_std_pct']
            else:
                result_row[f'{product}_trend'] = np.nan
                result_row[f'{product}_delta_std_pct'] = np.nan
        
        results_list.append(result_row)
    
    return pd.DataFrame(results_list)


def create_detrending_summary_figure(detrending_df, outdir, degree=2):
    """
    Create Figure: Detrending Analysis Summary (Enhanced for Publication)
    Panel (a): Polynomial PWV Trends by Station
    Panel (b): Impact of Polynomial Detrending on Variability
    Panel (c): Scatter plot showing trend vs variability change relationship
    Panel (d): Box plot comparison across products
    
    Parameters:
    -----------
    detrending_df : pd.DataFrame
        Results from perform_detrending_analysis
    outdir : str
        Output directory for figure
    degree : int
        Polynomial degree used for detrending
    
    Returns:
    --------
    str
        Path to saved figure
    """
    DETRENDING_DEGREE = degree
    fig = plt.figure(figsize=(18, 10))
    gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.3, height_ratios=[1, 1])
    
    stations = detrending_df['Station'].tolist()
    n_stations = len(stations)
    
    # Define bar positions
    x = np.arange(n_stations)
    width = 0.25
    
    # Define colors for products
    colors = {'IGS': '#1f77b4', 'VMF3': '#ff7f0e', 'ERA5': '#2ca02c'}
    
    # Panel (a): Polynomial Trends
    ax1 = fig.add_subplot(gs[0, 0])
    
    igs_trends = detrending_df['IGS_trend'].values
    vmf3_trends = detrending_df['VMF3_trend'].values
    era5_trends = detrending_df['ERA5_trend'].values
    
    ax1.bar(x - width, igs_trends, width, label='IGS', color=colors['IGS'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    ax1.bar(x, vmf3_trends, width, label='VMF3', color=colors['VMF3'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    ax1.bar(x + width, era5_trends, width, label='ERA5', color=colors['ERA5'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    
    ax1.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.7)
    ax1.set_xlabel('Station Code', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Effective Slope (mm/yr)', fontweight='bold', fontsize=11)
    ax1.set_title(f'(a) PWV Effective Slopes by Station', 
                  fontweight='bold', pad=10, fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(stations, rotation=90, fontsize=8)
    ax1.grid(axis='y', alpha=0.3, linewidth=0.5)
    
    # Calculate mean trends
    mean_igs = np.nanmean(igs_trends)
    mean_vmf3 = np.nanmean(vmf3_trends)
    mean_era5 = np.nanmean(era5_trends)
    
    # Add mean trend lines with custom legend entries
    line_igs = ax1.axhline(mean_igs, color=colors['IGS'], linestyle='--',
                           linewidth=1.5, alpha=0.6, label=f'IGS Mean: {mean_igs:.3f} mm/yr')
    line_vmf3 = ax1.axhline(mean_vmf3, color=colors['VMF3'], linestyle='--',
                            linewidth=1.5, alpha=0.6, label=f'VMF3 Mean: {mean_vmf3:.3f} mm/yr')
    line_era5 = ax1.axhline(mean_era5, color=colors['ERA5'], linestyle='--',
                            linewidth=1.5, alpha=0.6, label=f'ERA5 Mean: {mean_era5:.3f} mm/yr')
    
    # Create legend with both bars and dashed lines
    # =============================================================================
    #     valid value for loc; supported values are 'best', 'upper right', 'upper left',
    #     'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 
    #     'upper center', 'center'
    # =============================================================================
    handles1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(handles=handles1, labels=labels1, loc='lower left', 
               frameon=True, fontsize=8, ncol=2, columnspacing=0.5)
    
    # Adjust y-axis limits to show positive values if they exist
    y_min = min(np.nanmin(igs_trends), np.nanmin(vmf3_trends), np.nanmin(era5_trends))
    y_max = max(np.nanmax(igs_trends), np.nanmax(vmf3_trends), np.nanmax(era5_trends))
    y_range = y_max - y_min
    ax1.set_ylim([y_min - 0.1 * y_range, y_max + 0.1 * y_range])
    
    # Panel (b): Impact on Variability
    ax2 = fig.add_subplot(gs[0, 1])
    
    igs_delta = detrending_df['IGS_delta_std_pct'].values
    vmf3_delta = detrending_df['VMF3_delta_std_pct'].values
    era5_delta = detrending_df['ERA5_delta_std_pct'].values
    
    ax2.bar(x - width, igs_delta, width, label='IGS', color=colors['IGS'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    ax2.bar(x, vmf3_delta, width, label='VMF3', color=colors['VMF3'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    ax2.bar(x + width, era5_delta, width, label='ERA5', color=colors['ERA5'],
            edgecolor='black', linewidth=0.5, alpha=0.8)
    
    ax2.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.7)
    ax2.set_xlabel('Station Code', fontweight='bold', fontsize=11)
    ax2.set_ylabel('∆ Std After Detrending (%)', fontweight='bold', fontsize=11)
    ax2.set_title(f'(b) Impact of Detrending on Variability', 
                  fontweight='bold', pad=10, fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(stations, rotation=90, fontsize=8)
    ax2.grid(axis='y', alpha=0.3, linewidth=0.5)
    
    # Calculate mean deltas
    mean_delta_igs = np.nanmean(igs_delta)
    mean_delta_vmf3 = np.nanmean(vmf3_delta)
    mean_delta_era5 = np.nanmean(era5_delta)
    
    # Add mean delta lines with custom legend entries
    ax2.axhline(mean_delta_igs, color=colors['IGS'], linestyle='--',
                linewidth=1.5, alpha=0.6, label=f'IGS Mean: {mean_delta_igs:.2f}%')
    ax2.axhline(mean_delta_vmf3, color=colors['VMF3'], linestyle='--',
                linewidth=1.5, alpha=0.6, label=f'VMF3 Mean: {mean_delta_vmf3:.2f}%')
    ax2.axhline(mean_delta_era5, color=colors['ERA5'], linestyle='--',
                linewidth=1.5, alpha=0.6, label=f'ERA5 Mean: {mean_delta_era5:.2f}%')
    
    # Create legend with both bars and dashed lines
    # =============================================================================
    #     valid value for loc; supported values are 'best', 'upper right', 'upper left',
    #     'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 
    #     'upper center', 'center'
    # =============================================================================
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(handles=handles2, labels=labels2, loc='lower left', 
               frameon=True, fontsize=8, ncol=2, columnspacing=0.5)
    
    # Adjust y-axis limits for better visibility
    y_min2 = min(np.nanmin(igs_delta), np.nanmin(vmf3_delta), np.nanmin(era5_delta))
    y_max2 = max(np.nanmax(igs_delta), np.nanmax(vmf3_delta), np.nanmax(era5_delta))
    y_range2 = y_max2 - y_min2
    ax2.set_ylim([y_min2 - 0.1 * y_range2, y_max2 + 0.1 * y_range2])
    
    # Panel (c): Scatter plot - Trend vs Delta Std
    ax3 = fig.add_subplot(gs[1, 0])
    
    for product in ['IGS', 'VMF3', 'ERA5']:
        trend_col = f'{product}_trend'
        delta_col = f'{product}_delta_std_pct'
        
        x_data = detrending_df[trend_col].values
        y_data = detrending_df[delta_col].values
        
        # Remove NaN values
        valid_mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_valid = x_data[valid_mask]
        y_valid = y_data[valid_mask]
        
        ax3.scatter(x_valid, y_valid, s=100, alpha=0.7, color=colors[product],
                   label=product, edgecolor='black', linewidth=0.7)
        
        # Add trend line with R² annotation
        if len(x_valid) > 2:
            z = np.polyfit(x_valid, y_valid, 1)
            p = np.poly1d(z)
            x_line = np.linspace(x_valid.min(), x_valid.max(), 100)
            
            # Calculate R²
            y_pred = p(x_valid)
            ss_res = np.sum((y_valid - y_pred) ** 2)
            ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            ax3.plot(x_line, p(x_line), "--", color=colors[product],
                    linewidth=2, alpha=0.6, 
                    label=f'{product} fit (R²={r_squared:.3f})')
    
    ax3.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.axvline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
    ax3.set_xlabel('Effective Slope (mm/yr)', fontweight='bold', fontsize=11)
    ax3.set_ylabel('∆ Std After Detrending (%)', fontweight='bold', fontsize=11)
    ax3.set_title(f'(c) Relationship: Slope Magnitude vs Variability Reduction',
                 fontweight='bold', pad=10, fontsize=12)
    ax3.legend(loc='best', frameon=True, fontsize=8, ncol=1)
    ax3.grid(True, alpha=0.3, linewidth=0.5)
    
    # Panel (d): Box plot comparison of trends across products
    ax4 = fig.add_subplot(gs[1, 1])
    
    trend_data = [
        igs_trends[~np.isnan(igs_trends)],
        vmf3_trends[~np.isnan(vmf3_trends)],
        era5_trends[~np.isnan(era5_trends)]
    ]
    
    bp = ax4.boxplot(trend_data, labels=['IGS', 'VMF3', 'ERA5'],
                     patch_artist=True, showfliers=True,
                     boxprops=dict(linewidth=1.5),
                     medianprops=dict(color='darkred', linewidth=2.5),
                     whiskerprops=dict(linewidth=1.5),
                     capprops=dict(linewidth=1.5),
                     flierprops=dict(marker='o', markersize=6, alpha=0.6,
                                   markeredgecolor='black', markeredgewidth=0.5))
    
    # Color the boxes
    for patch, product in zip(bp['boxes'], ['IGS', 'VMF3', 'ERA5']):
        patch.set_facecolor(colors[product])
        patch.set_alpha(0.7)
        patch.set_edgecolor('black')
    
    ax4.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.7)
    ax4.set_ylabel('Effective Slope (mm/yr)', fontweight='bold', fontsize=11)
    ax4.set_xlabel('Product', fontweight='bold', fontsize=11)
    ax4.set_title(f'(d) Slope Distribution Comparison Across Products',
                 fontweight='bold', pad=10, fontsize=12)
    ax4.grid(axis='y', alpha=0.3, linewidth=0.5)
    
    # Add mean markers with legend
    mean_markers = []
    for i, data in enumerate(trend_data):
        mean_val = np.mean(data)
        marker = ax4.plot(i+1, mean_val, marker='D', markersize=10, 
                         color='darkred', markeredgecolor='black', 
                         markeredgewidth=1, zorder=5)
        if i == 0:
            mean_markers = marker
    
    # Add statistics annotations
    stats_text = []
    for i, (data, product) in enumerate(zip(trend_data, ['IGS', 'VMF3', 'ERA5'])):
        median_val = np.median(data)
        mean_val = np.mean(data)
        stats_text.append(f'{product}: μ={mean_val:.3f}, M={median_val:.3f}')
    
    # Add legend for mean marker
    ax4.legend([mean_markers[0]], ['Mean'], loc='upper left', 
               frameon=True, fontsize=9)
    
    # Add text box with statistics
    textstr = '\n'.join(stats_text)
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5, edgecolor='black')
    ax4.text(0.98, 0.02, textstr, transform=ax4.transAxes, fontsize=8,
            verticalalignment='bottom', horizontalalignment='right', bbox=props)
    
    plt.suptitle(f'Figure: Comprehensive Polynomial Detrending Analysis (Degree {DETRENDING_DEGREE})',
                 fontweight='bold', fontsize=14, y=0.995)
    
    outpath = os.path.join(outdir, f"Figure_Detrending_Analysis_Degree{DETRENDING_DEGREE}.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
    
    print(f"\n{'='*70}")
    print(f"DETRENDING ANALYSIS SUMMARY (Degree {DETRENDING_DEGREE})")
    print(f"{'='*70}")
    print(f"\nMean Effective Slopes:")
    print(f"  IGS:  {mean_igs:>7.4f} mm/yr")
    print(f"  VMF3: {mean_vmf3:>7.4f} mm/yr")
    print(f"  ERA5: {mean_era5:>7.4f} mm/yr")
    print(f"\nMean Variability Change (∆ Std):")
    print(f"  IGS:  {mean_delta_igs:>6.2f} %")
    print(f"  VMF3: {mean_delta_vmf3:>6.2f} %")
    print(f"  ERA5: {mean_delta_era5:>6.2f} %")
    print(f"\nFigure saved to: {outpath}")
    print(f"{'='*70}\n")
    
    return outpath

def create_example_detrending_timeseries(cleaned_data_dict, detrending_df, outdir, n_examples=6):
    """
    Create figure showing example time series with trend lines for selected stations.
   
    Parameters:
    -----------
    cleaned_data_dict : dict
        Dictionary with station data including dates and cleaned PWV
    detrending_df : pd.DataFrame
        Results from detrending analysis
    outdir : str
        Output directory for figure
    n_examples : int
        Number of example stations to show (default 6)
   
    Returns:
    --------
    str
        Path to saved figure
    """
    # Select diverse stations (highest trend, lowest trend, middle trends)
    sorted_by_trend = detrending_df.sort_values('IGS_trend', ascending=False)
   
    # Get indices for diverse selection
    n_total = len(sorted_by_trend)
    indices = [0, 1, n_total//3, n_total//2, 2*n_total//3, n_total-1]
    example_stations = [sorted_by_trend.iloc[i]['Station'] for i in indices[:n_examples]]
   
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(3, 2, hspace=0.4, wspace=0.3)
   
    colors_product = {'IGS': '#1f77b4', 'VMF3': '#ff7f0e', 'ERA5': '#2ca02c'}
   
    for idx, station in enumerate(example_stations):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
       
        if station not in cleaned_data_dict:
            continue
       
        station_data = cleaned_data_dict[station]
        dates = station_data['dates']
       
        # Convert dates to decimal years for plotting
        decimal_years = dates.dt.year + (dates.dt.dayofyear - 1) / 365.25
       
        for product in ['IGS', 'VMF3', 'ERA5']:
            clean_key = f'{product}_clean'
           
            if clean_key not in station_data:
                continue
           
            pwv_clean = station_data[clean_key]
           
            # Get trend from detrending_df
            station_row = detrending_df[detrending_df['Station'] == station]
            if len(station_row) == 0:
                continue
           
            trend_slope = station_row[f'{product}_trend'].values[0]
           
            # Calculate trend line
            _, trend_line = calculate_polynomial_trend(pwv_clean, dates, DETRENDING_DEGREE)
           
            # Plot original cleaned data (with transparency)
            ax.plot(dates, pwv_clean, alpha=0.3, linewidth=0.8,
                   color=colors_product[product])
           
            # Plot trend line
            ax.plot(dates, trend_line, linewidth=2.5, color=colors_product[product],
                   label=f'{product} (eff. slope: {trend_slope:.3f} mm/yr)')
       
        ax.set_xlabel('Year', fontweight='bold', fontsize=10)
        ax.set_ylabel('PWV (mm)', fontweight='bold', fontsize=10)
        ax.set_title(f'Station: {station}', fontweight='bold', fontsize=11)
        ax.legend(loc='best', frameon=True, fontsize=8)
        ax.grid(True, alpha=0.3, linewidth=0.5)
   
    plt.suptitle(f'Figure: Example Time Series with Degree {DETRENDING_DEGREE} Polynomial Trends',
                 fontweight='bold', fontsize=14, y=0.995)
   
    outpath = os.path.join(outdir, f"Figure_Example_Detrending_Timeseries_Degree{DETRENDING_DEGREE}.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
   
    return outpath

def create_heatmap_trends(detrending_df, outdir):
    """
    Create heatmap showing trends across all stations and products.
   
    Parameters:
    -----------
    detrending_df : pd.DataFrame
        Results from detrending analysis
    outdir : str
        Output directory for figure
   
    Returns:
    --------
    str
        Path to saved figure
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
   
    stations = detrending_df['Station'].tolist()
    products = ['IGS', 'VMF3', 'ERA5']
   
    # Prepare data for heatmaps
    trend_matrix = np.zeros((len(stations), len(products)))
    delta_matrix = np.zeros((len(stations), len(products)))
   
    for i, station in enumerate(stations):
        for j, product in enumerate(products):
            trend_matrix[i, j] = detrending_df.loc[detrending_df['Station'] == station,
                                                    f'{product}_trend'].values[0]
            delta_matrix[i, j] = detrending_df.loc[detrending_df['Station'] == station,
                                                   f'{product}_delta_std_pct'].values[0]
   
    # Heatmap 1: Trends
    im1 = axes[0].imshow(trend_matrix, aspect='auto', cmap='RdBu_r',
                         interpolation='nearest')
    axes[0].set_xticks(np.arange(len(products)))
    axes[0].set_yticks(np.arange(len(stations)))
    axes[0].set_xticklabels(products, fontsize=10, fontweight='bold')
    axes[0].set_yticklabels(stations, fontsize=8)
    axes[0].set_xlabel('Product', fontweight='bold', fontsize=11)
    axes[0].set_ylabel('Station', fontweight='bold', fontsize=11)
    axes[0].set_title(f'(a) Effective Slopes Heatmap (Degree {DETRENDING_DEGREE}, mm/yr)', fontweight='bold', fontsize=12)
   
    # Add colorbar
    cbar1 = plt.colorbar(im1, ax=axes[0])
    cbar1.set_label('Effective Slope (mm/yr)', fontweight='bold', fontsize=10)
   
    # Add text annotations
    for i in range(len(stations)):
        for j in range(len(products)):
            text = axes[0].text(j, i, f'{trend_matrix[i, j]:.2f}',
                              ha="center", va="center", color="black", fontsize=7)
   
    # Heatmap 2: Delta Std
    im2 = axes[1].imshow(delta_matrix, aspect='auto', cmap='RdYlGn_r',
                         interpolation='nearest')
    axes[1].set_xticks(np.arange(len(products)))
    axes[1].set_yticks(np.arange(len(stations)))
    axes[1].set_xticklabels(products, fontsize=10, fontweight='bold')
    axes[1].set_yticklabels(stations, fontsize=8)
    axes[1].set_xlabel('Product', fontweight='bold', fontsize=11)
    axes[1].set_ylabel('Station', fontweight='bold', fontsize=11)
    axes[1].set_title(f'(b) Variability Change Heatmap (∆ Std %, Degree {DETRENDING_DEGREE})', fontweight='bold', fontsize=12)
   
    # Add colorbar
    cbar2 = plt.colorbar(im2, ax=axes[1])
    cbar2.set_label('∆ Std (%)', fontweight='bold', fontsize=10)
   
    # Add text annotations
    for i in range(len(stations)):
        for j in range(len(products)):
            text = axes[1].text(j, i, f'{delta_matrix[i, j]:.1f}',
                              ha="center", va="center", color="black", fontsize=7)
   
    plt.suptitle(f'Figure: Polynomial Detrending Analysis Heatmaps (Degree {DETRENDING_DEGREE})',
                 fontweight='bold', fontsize=14, y=0.98)
    plt.tight_layout()
   
    outpath = os.path.join(outdir, f"Figure_Detrending_Heatmaps_Degree{DETRENDING_DEGREE}.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
   
    return outpath

# =============================================================================
# COMAPRISON OF LINEAR & NONLINEAR DETRENDING
# =============================================================================
def compare_linear_vs_quadratic(cleaned_data_dict, outdir):
    """
    Compare linear vs quadratic detrending fits for all stations and products.
    Performs statistical tests and exports detailed comparative analysis.
    
    Parameters:
    -----------
    cleaned_data_dict : dict
        Dictionary with station data including dates and cleaned PWV
    outdir : str
        Output directory for results files
    
    Returns:
    --------
    comparison_df : pd.DataFrame
        Detailed comparison results
    summary_stats : dict
        Summary statistics for manuscript
    """
    import scipy.stats as stats
    
    results = []
    
    for station, data in cleaned_data_dict.items():
        dates = data['dates']
        
        for product in ['IGS', 'VMF3', 'ERA5']:
            clean_key = f'{product}_clean'
            if clean_key not in data:
                continue
                
            time_series = data[clean_key]
            valid_mask = ~np.isnan(time_series)
            
            if valid_mask.sum() < 3:
                continue
            
            valid_dates = dates[valid_mask]
            valid_values = time_series[valid_mask]
            decimal_years = valid_dates.dt.year + (valid_dates.dt.dayofyear - 1) / 365.25
            
            n = len(valid_values)
            
            # ==========================================
            # LINEAR FIT (Degree 1)
            # ==========================================
            coeffs_linear = np.polyfit(decimal_years, valid_values, 1)
            trend_linear = np.polyval(coeffs_linear, decimal_years)
            residuals_linear = valid_values - trend_linear
            
            # Linear metrics
            rss_linear = np.sum(residuals_linear**2)
            rmse_linear = np.sqrt(rss_linear / n)
            mae_linear = np.mean(np.abs(residuals_linear))
            
            # R² for linear
            ss_total = np.sum((valid_values - np.mean(valid_values))**2)
            r2_linear = 1 - (rss_linear / ss_total) if ss_total > 0 else 0
            
            # Adjusted R² for linear
            adj_r2_linear = 1 - ((1 - r2_linear) * (n - 1) / (n - 2)) if n > 2 else 0
            
            # Linear slope and uncertainty
            linear_slope = coeffs_linear[0]
            
            # Standard error of slope
            x_mean = np.mean(decimal_years)
            sxx = np.sum((decimal_years - x_mean)**2)
            se_slope = np.sqrt(rss_linear / (n - 2) / sxx) if n > 2 and sxx > 0 else np.nan
            
            # ==========================================
            # QUADRATIC FIT (Degree 2)
            # ==========================================
            coeffs_quad = np.polyfit(decimal_years, valid_values, 2)
            trend_quad = np.polyval(coeffs_quad, decimal_years)
            residuals_quad = valid_values - trend_quad
            
            # Quadratic metrics
            rss_quad = np.sum(residuals_quad**2)
            rmse_quad = np.sqrt(rss_quad / n)
            mae_quad = np.mean(np.abs(residuals_quad))
            
            # R² for quadratic
            r2_quad = 1 - (rss_quad / ss_total) if ss_total > 0 else 0
            
            # Adjusted R² for quadratic
            adj_r2_quad = 1 - ((1 - r2_quad) * (n - 1) / (n - 3)) if n > 3 else 0
            
            # Effective slope at mean time (derivative)
            mean_time = np.mean(decimal_years)
            derivative_coeffs = np.polyder(coeffs_quad)
            effective_slope = np.polyval(derivative_coeffs, mean_time)
            
            # Quadratic coefficient
            quad_coeff = coeffs_quad[0]
            
            # ==========================================
            # STATISTICAL TESTS
            # ==========================================
            
            # F-test for additional quadratic term
            # H0: Quadratic term adds no explanatory power
            df1 = 1  # Additional parameter (quadratic term)
            df2 = n - 3  # Degrees of freedom for quadratic model
            
            if df2 > 0 and rss_quad > 0:
                f_stat = ((rss_linear - rss_quad) / df1) / (rss_quad / df2)
                # Critical F-value at α=0.05
                f_critical = stats.f.ppf(0.95, df1, df2)
                p_value_f = 1 - stats.f.cdf(f_stat, df1, df2)
                significant = f_stat > f_critical
            else:
                f_stat = np.nan
                f_critical = np.nan
                p_value_f = np.nan
                significant = False
            
            # ==========================================
            # IMPROVEMENT METRICS
            # ==========================================
            
            # RMSE improvement
            rmse_improvement_pct = ((rmse_linear - rmse_quad) / rmse_linear) * 100 if rmse_linear > 0 else 0
            
            # R² improvement
            delta_r2 = r2_quad - r2_linear
            delta_adj_r2 = adj_r2_quad - adj_r2_linear
            
            # MAE improvement
            mae_improvement_pct = ((mae_linear - mae_quad) / mae_linear) * 100 if mae_linear > 0 else 0
            
            # ==========================================
            # INFORMATION CRITERIA (for model selection)
            # ==========================================
            
            # Akaike Information Criterion (AIC)
            # AIC = n*ln(RSS/n) + 2*k, where k is number of parameters
            aic_linear = n * np.log(rss_linear / n) + 2 * 2 if rss_linear > 0 else np.nan
            aic_quad = n * np.log(rss_quad / n) + 2 * 3 if rss_quad > 0 else np.nan
            delta_aic = aic_quad - aic_linear
            
            # Bayesian Information Criterion (BIC)
            # BIC = n*ln(RSS/n) + k*ln(n)
            bic_linear = n * np.log(rss_linear / n) + 2 * np.log(n) if rss_linear > 0 else np.nan
            bic_quad = n * np.log(rss_quad / n) + 3 * np.log(n) if rss_quad > 0 else np.nan
            delta_bic = bic_quad - bic_linear
            
            # Time series characteristics
            time_span_years = (decimal_years.max() - decimal_years.min())
            
            # ==========================================
            # STORE RESULTS
            # ==========================================
            
            results.append({
                # Identification
                'Station': station,
                'Product': product,
                'N_obs': n,
                'Time_Span_Years': time_span_years,
                
                # Linear model
                'Linear_Slope_mm_yr': linear_slope,
                'Linear_Slope_SE': se_slope,
                'Linear_RMSE': rmse_linear,
                'Linear_MAE': mae_linear,
                'Linear_R2': r2_linear,
                'Linear_Adj_R2': adj_r2_linear,
                'Linear_AIC': aic_linear,
                'Linear_BIC': bic_linear,
                
                # Quadratic model
                'Quad_Coeff_a2': quad_coeff,
                'Quad_Effective_Slope_mm_yr': effective_slope,
                'Quad_RMSE': rmse_quad,
                'Quad_MAE': mae_quad,
                'Quad_R2': r2_quad,
                'Quad_Adj_R2': adj_r2_quad,
                'Quad_AIC': aic_quad,
                'Quad_BIC': bic_quad,
                
                # Comparison metrics
                'Delta_R2': delta_r2,
                'Delta_Adj_R2': delta_adj_r2,
                'RMSE_Improvement_pct': rmse_improvement_pct,
                'MAE_Improvement_pct': mae_improvement_pct,
                'Delta_AIC': delta_aic,
                'Delta_BIC': delta_bic,
                
                # Statistical tests
                'F_Statistic': f_stat,
                'F_Critical_0.05': f_critical,
                'F_Test_P_Value': p_value_f,
                'Quadratic_Significant': significant,
                
                # Decision criteria
                'Prefer_Quadratic_F': significant,
                'Prefer_Quadratic_AIC': delta_aic < -2,  # AIC improvement > 2
                'Prefer_Quadratic_BIC': delta_bic < 0,   # Any BIC improvement
            })
    
    comparison_df = pd.DataFrame(results)
    
    # ==========================================
    # SUMMARY STATISTICS
    # ==========================================
    
    summary_stats = {
        'Total_Comparisons': len(comparison_df),
        'Mean_N_obs': comparison_df['N_obs'].mean(),
        'Mean_Time_Span_Years': comparison_df['Time_Span_Years'].mean(),
        
        # Linear trends
        'Mean_Linear_Slope': comparison_df['Linear_Slope_mm_yr'].mean(),
        'Median_Linear_Slope': comparison_df['Linear_Slope_mm_yr'].median(),
        'Std_Linear_Slope': comparison_df['Linear_Slope_mm_yr'].std(),
        
        # Quadratic coefficients
        'Mean_Quad_Coeff': comparison_df['Quad_Coeff_a2'].mean(),
        'Median_Quad_Coeff': comparison_df['Quad_Coeff_a2'].median(),
        'Mean_Effective_Slope': comparison_df['Quad_Effective_Slope_mm_yr'].mean(),
        
        # Performance comparisons
        'Mean_RMSE_Improvement_pct': comparison_df['RMSE_Improvement_pct'].mean(),
        'Median_RMSE_Improvement_pct': comparison_df['RMSE_Improvement_pct'].median(),
        'Mean_Delta_R2': comparison_df['Delta_R2'].mean(),
        'Mean_Delta_Adj_R2': comparison_df['Delta_Adj_R2'].mean(),
        'Mean_Delta_AIC': comparison_df['Delta_AIC'].mean(),
        'Mean_Delta_BIC': comparison_df['Delta_BIC'].mean(),
        
        # Statistical significance
        'N_Significant_F_Test': comparison_df['Quadratic_Significant'].sum(),
        'Pct_Significant_F_Test': (comparison_df['Quadratic_Significant'].sum() / len(comparison_df)) * 100,
        'N_Prefer_Quad_AIC': comparison_df['Prefer_Quadratic_AIC'].sum(),
        'N_Prefer_Quad_BIC': comparison_df['Prefer_Quadratic_BIC'].sum(),
        
        # By product
        'IGS_Mean_Linear_Slope': comparison_df[comparison_df['Product']=='IGS']['Linear_Slope_mm_yr'].mean(),
        'VMF3_Mean_Linear_Slope': comparison_df[comparison_df['Product']=='VMF3']['Linear_Slope_mm_yr'].mean(),
        'ERA5_Mean_Linear_Slope': comparison_df[comparison_df['Product']=='ERA5']['Linear_Slope_mm_yr'].mean(),
        
        'IGS_Mean_RMSE_Improvement': comparison_df[comparison_df['Product']=='IGS']['RMSE_Improvement_pct'].mean(),
        'VMF3_Mean_RMSE_Improvement': comparison_df[comparison_df['Product']=='VMF3']['RMSE_Improvement_pct'].mean(),
        'ERA5_Mean_RMSE_Improvement': comparison_df[comparison_df['Product']=='ERA5']['RMSE_Improvement_pct'].mean(),
    }
    
    # ==========================================
    # EXPORT RESULTS
    # ==========================================
    
    # 1. Detailed comparison CSV
    csv_path = os.path.join(outdir, "Linear_vs_Quadratic_Detailed_Comparison.csv")
    comparison_df.to_csv(csv_path, index=False, float_format='%.6f')
    
    # 2. Summary statistics text file
    summary_path = os.path.join(outdir, "Linear_vs_Quadratic_Summary_Statistics.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("LINEAR vs QUADRATIC DETRENDING COMPARISON - SUMMARY STATISTICS\n")
        f.write("="*80 + "\n\n")
        
        f.write("DATASET CHARACTERISTICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Total station-product combinations: {summary_stats['Total_Comparisons']}\n")
        f.write(f"Mean observations per series: {summary_stats['Mean_N_obs']:.0f}\n")
        f.write(f"Mean time span: {summary_stats['Mean_Time_Span_Years']:.1f} years\n\n")
        
        f.write("TREND MAGNITUDES\n")
        f.write("-"*80 + "\n")
        f.write(f"Linear trends (mm/yr):\n")
        f.write(f"  Mean:   {summary_stats['Mean_Linear_Slope']:>8.4f}\n")
        f.write(f"  Median: {summary_stats['Median_Linear_Slope']:>8.4f}\n")
        f.write(f"  Std:    {summary_stats['Std_Linear_Slope']:>8.4f}\n\n")
        
        f.write(f"Quadratic effective slopes (mm/yr):\n")
        f.write(f"  Mean:   {summary_stats['Mean_Effective_Slope']:>8.4f}\n\n")
        
        f.write(f"Quadratic coefficient (a2):\n")
        f.write(f"  Mean:   {summary_stats['Mean_Quad_Coeff']:>10.6f}\n")
        f.write(f"  Median: {summary_stats['Median_Quad_Coeff']:>10.6f}\n\n")
        
        f.write("MODEL PERFORMANCE COMPARISON\n")
        f.write("-"*80 + "\n")
        f.write(f"RMSE improvement with quadratic:\n")
        f.write(f"  Mean:   {summary_stats['Mean_RMSE_Improvement_pct']:>6.3f}%\n")
        f.write(f"  Median: {summary_stats['Median_RMSE_Improvement_pct']:>6.3f}%\n\n")
        
        f.write(f"R-squared improvement:\n")
        f.write(f"  Delta-R2:     {summary_stats['Mean_Delta_R2']:>8.6f}\n")
        f.write(f"  Delta-Adj-R2: {summary_stats['Mean_Delta_Adj_R2']:>8.6f}\n\n")
        
        f.write(f"Information criteria:\n")
        f.write(f"  Delta-AIC:    {summary_stats['Mean_Delta_AIC']:>8.3f}\n")
        f.write(f"  Delta-BIC:    {summary_stats['Mean_Delta_BIC']:>8.3f}\n\n")
        
        f.write("STATISTICAL SIGNIFICANCE\n")
        f.write("-"*80 + "\n")
        f.write(f"F-test (α=0.05):\n")
        f.write(f"  Significant cases: {summary_stats['N_Significant_F_Test']}/{summary_stats['Total_Comparisons']}\n")
        f.write(f"  Percentage: {summary_stats['Pct_Significant_F_Test']:.1f}%\n\n")
        
        f.write(f"Model preference by information criteria:\n")
        f.write(f"  Prefer quadratic (AIC): {summary_stats['N_Prefer_Quad_AIC']}/{summary_stats['Total_Comparisons']}\n")
        f.write(f"  Prefer quadratic (BIC): {summary_stats['N_Prefer_Quad_BIC']}/{summary_stats['Total_Comparisons']}\n\n")
        
        f.write("PRODUCT-SPECIFIC TRENDS\n")
        f.write("-"*80 + "\n")
        f.write(f"Linear slopes (mm/yr):\n")
        f.write(f"  IGS:  {summary_stats['IGS_Mean_Linear_Slope']:>7.4f}\n")
        f.write(f"  VMF3: {summary_stats['VMF3_Mean_Linear_Slope']:>7.4f}\n")
        f.write(f"  ERA5: {summary_stats['ERA5_Mean_Linear_Slope']:>7.4f}\n\n")
        
        f.write(f"RMSE improvement (%):\n")
        f.write(f"  IGS:  {summary_stats['IGS_Mean_RMSE_Improvement']:>6.3f}\n")
        f.write(f"  VMF3: {summary_stats['VMF3_Mean_RMSE_Improvement']:>6.3f}\n")
        f.write(f"  ERA5: {summary_stats['ERA5_Mean_RMSE_Improvement']:>6.3f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("RECOMMENDATION\n")
        f.write("="*80 + "\n")
        
        # Decision logic
        if (summary_stats['Mean_Delta_R2'] < 0.001 and 
            summary_stats['Pct_Significant_F_Test'] < 10 and
            summary_stats['Mean_Delta_BIC'] > 0):
            recommendation = "LINEAR DETRENDING"
            reason = (
                "The quadratic model shows negligible improvement:\n"
                f"  - Delta-R2 < 0.001 (actual: {summary_stats['Mean_Delta_R2']:.6f})\n"
                f"  - F-test significance < 10% (actual: {summary_stats['Pct_Significant_F_Test']:.1f}%)\n"
                f"  - BIC penalizes additional parameter (Delta-BIC > 0)\n"
                "Linear detrending is preferred based on parsimony principle."
            )
        else:
            recommendation = "QUADRATIC DETRENDING"
            reason = (
                "The quadratic model shows statistically significant improvement:\n"
                f"  - Delta-R2 = {summary_stats['Mean_Delta_R2']:.6f}\n"
                f"  - F-test significance: {summary_stats['Pct_Significant_F_Test']:.1f}%\n"
                f"  - RMSE improvement: {summary_stats['Mean_RMSE_Improvement_pct']:.2f}%\n"
                "Quadratic detrending captures non-linear trends in the data."
            )
        
        f.write(f"\nRECOMMENDED MODEL: {recommendation}\n\n")
        f.write("JUSTIFICATION:\n")
        f.write(reason + "\n\n")
        f.write("="*80 + "\n")
    
    # 3. Product-specific summary CSV
    product_summary = comparison_df.groupby('Product').agg({
        'Linear_Slope_mm_yr': ['mean', 'median', 'std', 'min', 'max'],
        'Quad_Effective_Slope_mm_yr': ['mean', 'median'],
        'RMSE_Improvement_pct': ['mean', 'median', 'min', 'max'],
        'Delta_R2': ['mean', 'median'],
        'Quadratic_Significant': 'sum'
    }).round(6)
    
    product_summary_path = os.path.join(outdir, "Linear_vs_Quadratic_Product_Summary.csv")
    product_summary.to_csv(product_summary_path)
    
    # ==========================================
    # CONSOLE OUTPUT
    # ==========================================
    
    print("\n" + "="*80)
    print("LINEAR vs QUADRATIC DETRENDING COMPARISON")
    print("="*80)
    print(f"\nTotal comparisons: {summary_stats['Total_Comparisons']}")
    print(f"Mean time span: {summary_stats['Mean_Time_Span_Years']:.1f} years")
    print(f"\nMean RMSE improvement: {summary_stats['Mean_RMSE_Improvement_pct']:.3f}%")
    print(f"Mean Delta-R2: {summary_stats['Mean_Delta_R2']:.6f}")
    print(f"Quadratic significant (F-test): {summary_stats['N_Significant_F_Test']}/{summary_stats['Total_Comparisons']} ({summary_stats['Pct_Significant_F_Test']:.1f}%)")
    print(f"\nRecommendation: {recommendation}")
    print(f"\nResults exported to:")
    print(f"  - {csv_path}")
    print(f"  - {summary_path}")
    print(f"  - {product_summary_path}")
    print("="*80 + "\n")
    
    return comparison_df, summary_stats
# =============================================================================
# *************END OF COMPARISON OF LINEAR & NONLINEAR DETRENDING ANALYSIS
# =============================================================================

# -----------------------
# ENHANCED VISUALIZATIONS
# -----------------------
def create_figure_1_sample_size_assessment(summary_df, outdir):
    """
    Figure 1: Sample Size Assessment and Station Quality
    Panel (a): Bar chart with sample size categories
    Panel (b): Geographic/temporal coverage heatmap
   
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary statistics per station.
    outdir : str
        Output directory for figure.
   
    Returns:
    --------
    str
        Path to saved figure.
    """
    fig = plt.figure(figsize=(14, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1])
   
    # Panel (a): Sample size bar chart with color coding
    ax1 = fig.add_subplot(gs[0])
   
    stations = summary_df["STN"].tolist()
    days = summary_df["DAYS_total"].values
   
    # Color code by adequacy
    colors = []
    for d in days:
        if d >= MIN_VALID_DAYS:
            colors.append('#2ecc71') # Green: Excellent
        elif d >= MIN_ACCEPTABLE_DAYS:
            colors.append('#f39c12') # Orange: Acceptable
        elif d >= MIN_WARNING_DAYS:
            colors.append('#e74c3c') # Red: Warning
        else:
            colors.append('#95a5a6') # Gray: Insufficient
   
    bars = ax1.barh(stations, days, color=colors, edgecolor='black', linewidth=0.5)
   
    # Add threshold lines
    ax1.axvline(MIN_VALID_DAYS, color='green', linestyle='--',
                linewidth=1.5, label=f'Optimal (≥{MIN_VALID_DAYS}d)', alpha=0.7)
    ax1.axvline(MIN_ACCEPTABLE_DAYS, color='orange', linestyle='--',
                linewidth=1.5, label=f'Acceptable (≥{MIN_ACCEPTABLE_DAYS}d)', alpha=0.7)
    ax1.axvline(MIN_WARNING_DAYS, color='red', linestyle='--',
                linewidth=1.5, label=f'Warning (≥{MIN_WARNING_DAYS}d)', alpha=0.7)
   
    # Add value labels
    for i, (station, day) in enumerate(zip(stations, days)):
        ax1.text(day + 20, i, f'{day}', va='center', fontsize=7)
   
    ax1.set_xlabel('Sample Size (Days)', fontweight='bold')
    ax1.set_ylabel('Station Code', fontweight='bold')
    ax1.set_title('(a) Sample Size Assessment by Station', fontweight='bold', pad=10)
    ax1.legend(loc='lower right', frameon=True, fontsize=7)
    ax1.grid(axis='x', alpha=0.3, linewidth=0.5)
    ax1.invert_yaxis()
   
    # Panel (b): Sample size statistics
    ax2 = fig.add_subplot(gs[1])
    ax2.axis('off')
   
    # Calculate statistics
    excellent = np.sum(days >= MIN_VALID_DAYS)
    acceptable = np.sum((days >= MIN_ACCEPTABLE_DAYS) & (days < MIN_VALID_DAYS))
    warning = np.sum((days >= MIN_WARNING_DAYS) & (days < MIN_ACCEPTABLE_DAYS))
    insufficient = np.sum(days < MIN_WARNING_DAYS)
   
    stats_text = f"""
    Sample Size Summary Statistics
    {'='*45}
   
    Total Stations: {len(stations)}
   
    Sample Size Categories:
    ✓ Excellent (≥{MIN_VALID_DAYS}d): {excellent:2d} ({excellent/len(stations)*100:.1f}%)
    ○ Acceptable (≥{MIN_ACCEPTABLE_DAYS}d): {acceptable:2d} ({acceptable/len(stations)*100:.1f}%)
    ⚠ Warning (≥{MIN_WARNING_DAYS}d): {warning:2d} ({warning/len(stations)*100:.1f}%)
    ✗ Insufficient (<{MIN_WARNING_DAYS}d): {insufficient:2d} ({insufficient/len(stations)*100:.1f}%)
   
    Descriptive Statistics:
    Mean: {np.mean(days):.1f} days
    Median: {np.median(days):.1f} days
    Std Dev: {np.std(days):.1f} days
    Min: {np.min(days):.0f} days
    Max: {np.max(days):.0f} days
   
    Stations Suitable for Analysis:
    3CH/ETC Eligible: {excellent} stations
    Extended Analysis: {excellent + acceptable} stations
    """
   
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes,
             fontsize=8, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
   
    plt.tight_layout()
    outpath = os.path.join(outdir, "Figure_1_Sample_Size_Assessment.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
    return outpath

def create_figure_2_method_comparison(summary_df, outdir, methods_display):
    """
    Figure 2: Outlier Detection Method Comparison
    Shows outlier percentages for the applied methods across products.
    Adapts layout: 3x3 grid for all methods, 1x3 for single method.
   
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary statistics per station.
    outdir : str
        Output directory for figure.
    methods_display : list
        List of method names applied.
   
    Returns:
    --------
    str
        Path to saved figure.
    """
    products = ['IGS', 'VMF3', 'ERA5']
    n_methods = len(methods_display)
   
    if n_methods == 3:
        fig = plt.figure(figsize=(15, 10))
        gs = gridspec.GridSpec(3, 3, hspace=0.4, wspace=0.3)
        suptitle = 'Outlier Detection Method Comparison Across Products'
       
        for i, method in enumerate(methods_display):
            for j, product in enumerate(products):
                ax = fig.add_subplot(gs[i, j])
               
                col_name = f"{product}_{method}_outliers_pct"
                if col_name not in summary_df.columns:
                    continue
               
                stations = summary_df["STN"].tolist()
                values = summary_df[col_name].values
               
                # Color gradient based on outlier percentage
                colors_map = plt.cm.RdYlGn_r(values / np.max(values))
               
                bars = ax.bar(range(len(stations)), values, color=colors_map,
                             edgecolor='black', linewidth=0.4)
               
                ax.set_xticks(range(len(stations)))
                ax.set_xticklabels(stations, rotation=90, fontsize=7)
                ax.set_ylabel('Outliers (%)', fontsize=8)
                ax.set_title(f'{product} - {method}', fontweight='bold', fontsize=9)
                ax.grid(axis='y', alpha=0.3, linewidth=0.5)
                ax.set_ylim(0, max(10, np.max(values) * 1.1))
               
                # Add mean line
                mean_val = np.mean(values)
                ax.axhline(mean_val, color='red', linestyle='--',
                          linewidth=1, alpha=0.6, label=f'Mean: {mean_val:.2f}%')
                ax.legend(fontsize=6, loc='upper right')
       
    else: # Single method
        fig = plt.figure(figsize=(15, 5))
        gs = gridspec.GridSpec(1, 3, hspace=0.4, wspace=0.3)
        method = methods_display[0]
        suptitle = f'Outlier Percentages Using {method} Method Across Products'
       
        for j, product in enumerate(products):
            ax = fig.add_subplot(gs[0, j])
           
            col_name = f"{product}_{method}_outliers_pct"
            if col_name not in summary_df.columns:
                continue
           
            stations = summary_df["STN"].tolist()
            values = summary_df[col_name].values
           
            # Color gradient based on outlier percentage
            colors_map = plt.cm.RdYlGn_r(values / np.max(values))
           
            bars = ax.bar(range(len(stations)), values, color=colors_map,
                         edgecolor='black', linewidth=0.4)
           
            ax.set_xticks(range(len(stations)))
            ax.set_xticklabels(stations, rotation=90, fontsize=7)
            ax.set_ylabel('Outliers (%)', fontsize=8)
            ax.set_title(f'{product} - {method}', fontweight='bold', fontsize=9)
            ax.grid(axis='y', alpha=0.3, linewidth=0.5)
            ax.set_ylim(0, max(10, np.max(values) * 1.1))
           
            # Add mean line
            mean_val = np.mean(values)
            ax.axhline(mean_val, color='red', linestyle='--',
                      linewidth=1, alpha=0.6, label=f'Mean: {mean_val:.2f}%')
            ax.legend(fontsize=6, loc='upper right')
   
    plt.suptitle(f'Figure 2: {suptitle}',
                 fontweight='bold', fontsize=12, y=0.995)
   
    outpath = os.path.join(outdir, "Figure_2_Method_Comparison.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
    return outpath

def create_figure_3_enhanced_split_violin(pooled_distributions, outdir):
    """
    Figure 3: Enhanced Split-Violin Plot with Statistical Annotations
   
    Parameters:
    -----------
    pooled_distributions : dict
        Pooled original and cleaned PWV values by product and method.
    outdir : str
        Output directory for figure.
   
    Returns:
    --------
    str
        Path to saved figure.
    """
    fig = plt.figure(figsize=(14, 8))
    gs = gridspec.GridSpec(2, 3, height_ratios=[3, 1], hspace=0.3, wspace=0.3)
   
    products = ['IGS_PWV', 'VMF3_PWV', 'ERA5_PWV']
    product_labels = ['IGS', 'VMF3', 'ERA5']
    methods = ['Hampel', 'IQR', 'Zscore']
   
    left_color = '#bdbdbd'
    right_color = '#0052cc'
   
    for idx, (prod_key, prod_label) in enumerate(zip(products, product_labels)):
        ax_main = fig.add_subplot(gs[0, idx])
       
        # Combine all methods for this product
        orig_combined = []
        clean_combined = []
       
        for method in methods:
            key = f"{prod_key}_{method}"
            if key in pooled_distributions:
                orig_combined.extend(pooled_distributions[key]["orig"])
                clean_combined.extend(pooled_distributions[key]["clean"])
       
        orig_vals = np.array([v for v in orig_combined if np.isfinite(v)])
        clean_vals = np.array([v for v in clean_combined if np.isfinite(v)])
       
        if len(orig_vals) < 10 or len(clean_vals) < 10:
            continue
       
        # KDE
        kde_orig = gaussian_kde(orig_vals)
        kde_clean = gaussian_kde(clean_vals)
       
        y_min = min(orig_vals.min(), clean_vals.min())
        y_max = max(orig_vals.max(), clean_vals.max())
        ygrid = np.linspace(y_min, y_max, 300)
       
        dens_orig = kde_orig(ygrid)
        dens_clean = kde_clean(ygrid)
       
        max_d = max(dens_orig.max(), dens_clean.max())
        scale = 0.4 / max_d if max_d > 0 else 1
       
        # Left side (Original)
        left_x = np.concatenate([0.5 - dens_orig * scale, np.full_like(dens_orig, 0.5)[::-1]])
        left_y = np.concatenate([ygrid, ygrid[::-1]])
        poly_left = PolyCollection([np.column_stack([left_x, left_y])],
                                   facecolor=left_color, edgecolor='black',
                                   linewidth=0.6, alpha=0.7)
        ax_main.add_collection(poly_left)
       
        # Right side (Cleaned)
        right_x = np.concatenate([np.full_like(dens_clean, 0.5), 0.5 + dens_clean[::-1] * scale])
        right_y = np.concatenate([ygrid, ygrid[::-1]])
        poly_right = PolyCollection([np.column_stack([right_x, right_y])],
                                    facecolor=right_color, edgecolor='black',
                                    linewidth=0.6, alpha=0.7)
        ax_main.add_collection(poly_right)
       
        # Add box plot overlays
        bp_orig = ax_main.boxplot([orig_vals], positions=[0.3], widths=0.1,
                                  patch_artist=True, showfliers=False,
                                  boxprops=dict(facecolor='none', edgecolor='black', linewidth=1.5),
                                  medianprops=dict(color='red', linewidth=2),
                                  whiskerprops=dict(color='black', linewidth=1.5),
                                  capprops=dict(color='black', linewidth=1.5))
       
        bp_clean = ax_main.boxplot([clean_vals], positions=[0.7], widths=0.1,
                                   patch_artist=True, showfliers=False,
                                   boxprops=dict(facecolor='none', edgecolor='black', linewidth=1.5),
                                   medianprops=dict(color='red', linewidth=2),
                                   whiskerprops=dict(color='black', linewidth=1.5),
                                   capprops=dict(color='black', linewidth=1.5))
       
        # Add jittered strip plot points (uniform jitter as alternative to normal)
        jitter_width = 0.05 # Increased jitter width
        if len(orig_vals) > 0:
            jitter_x_orig = 0.3 + np.random.uniform(-jitter_width, jitter_width, len(orig_vals))
            ax_main.scatter(jitter_x_orig, orig_vals, s=3, color='gray', alpha=0.6, zorder=5)
       
        if len(clean_vals) > 0:
            jitter_x_clean = 0.7 + np.random.uniform(-jitter_width, jitter_width, len(clean_vals))
            ax_main.scatter(jitter_x_clean, clean_vals, s=3, color='darkblue', alpha=0.6, zorder=5)
       
        ax_main.set_xlim(0, 1)
        ax_main.set_ylim(y_min - 2, y_max + 2)
        ax_main.set_xticks([0.3, 0.7])
        ax_main.set_xticklabels(['Original', 'Cleaned'], fontsize=9)
        ax_main.set_ylabel('PWV (mm)', fontweight='bold')
        ax_main.set_title(f'{prod_label}', fontweight='bold', fontsize=11)
        ax_main.grid(axis='y', alpha=0.3, linewidth=0.5)
       
        # Statistical comparison panel
        ax_stats = fig.add_subplot(gs[1, idx])
        ax_stats.axis('off')
       
        # Calculate statistics
        orig_mean, orig_std = np.mean(orig_vals), np.std(orig_vals)
        clean_mean, clean_std = np.mean(clean_vals), np.std(clean_vals)
        orig_median, clean_median = np.median(orig_vals), np.median(clean_vals)
        reduction = ((orig_std - clean_std) / orig_std) * 100
       
        stats_text = f"""
        Original:
        Mean: {orig_mean:.2f} mm
        Median: {orig_median:.2f} mm
        Std: {orig_std:.2f} mm
       
        Cleaned:
        Mean: {clean_mean:.2f} mm
        Median: {clean_median:.2f} mm
        Std: {clean_std:.2f} mm
       
        Improvement:
        Std Reduction: {reduction:.1f}%
        """
       
        ax_stats.text(0.1, 0.9, stats_text, transform=ax_stats.transAxes,
                     fontsize=7, verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
   
    plt.suptitle('Figure 3: PWV Distribution Before and After Outlier Removal (Applied Methods Combined)',
                 fontweight='bold', fontsize=12, y=0.98)
   
    outpath = os.path.join(outdir, "Figure_3_Enhanced_Split_Violin.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
    return outpath

def create_figure_4_method_effectiveness(method_stats_df, outdir):
    """
    Figure 4: Method Effectiveness Comparison
    Shows which method works best for each product
   
    Parameters:
    -----------
    method_stats_df : pd.DataFrame
        Summary statistics per station (used as method_stats_df).
    outdir : str
        Output directory for figure.
   
    Returns:
    --------
    str
        Path to saved figure.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
   
    products = ['IGS', 'VMF3', 'ERA5']
    methods = ['Hampel', 'IQR', 'Zscore']
   
    for idx, (ax, product) in enumerate(zip(axes, products)):
        data_to_plot = []
        labels = []
       
        for method in methods:
            col_name = f"{product}_{method}_outliers_pct"
            if col_name in method_stats_df.columns:
                values = method_stats_df[col_name].dropna().values
                data_to_plot.append(values)
                labels.append(method)
       
        if data_to_plot:
            bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                           showfliers=True,
                           boxprops=dict(facecolor='lightblue', edgecolor='black', linewidth=1.5),
                           medianprops=dict(color='red', linewidth=2),
                           whiskerprops=dict(color='black', linewidth=1.5),
                           capprops=dict(color='black', linewidth=1.5),
                           flierprops=dict(marker='o', markerfacecolor='red',
                                         markersize=4, alpha=0.5))
           
            ax.set_ylabel('Outliers Detected (%)', fontweight='bold')
            ax.set_title(f'{product}', fontweight='bold', fontsize=11)
            ax.grid(axis='y', alpha=0.3, linewidth=0.5)
           
            # Add mean values as text
            for i, data in enumerate(data_to_plot):
                mean_val = np.mean(data)
                ax.text(i+1, ax.get_ylim()[1] * 0.95, f'μ={mean_val:.2f}%',
                       ha='center', fontsize=8, fontweight='bold')
   
    plt.suptitle('Figure 4: Outlier Detection Method Effectiveness Comparison',
                 fontweight='bold', fontsize=12)
    plt.tight_layout()
   
    outpath = os.path.join(outdir, "Figure_4_Method_Effectiveness.png")
    plt.savefig(outpath, dpi=600, bbox_inches='tight')
    plt.close()
    return outpath

# -----------------------
# MAIN PIPELINE
# -----------------------
def main():
    """
    Main pipeline for PWV outlier detection and quality control.
   
    Processes station data, applies selected outlier methods, generates summaries,
    figures, and reports.
    """
    # Setup directories
    cleaned_dir = os.path.join(OUTPUT_ROOT, "cleaned_per_station")
    fig_dir = os.path.join(OUTPUT_ROOT, "figures")
    ensure_dir(OUTPUT_ROOT)
    ensure_dir(cleaned_dir)
    ensure_dir(fig_dir)
   
    entries = list_station_files(INPUT_PATH)
   
    # Determine which methods to apply
    methods_config, apply_all_methods = get_methods_to_apply()
    methods_display = [m[0] for m in methods_config]
   
    # Print configuration
    print("\n" + "="*70)
    print("PWV QUALITY CONTROL CONFIGURATION")
    print("="*70)
    print(f"Outlier Detection Mode: {OUTLIER_METHOD}")
    if apply_all_methods:
        print(f"Optimal Selection Strategy: {OPTIMAL_SELECTION}")
        print(" Methods to compare: Hampel, IQR, Z-score")
        if OPTIMAL_SELECTION == 'CONSERVATIVE':
            print(" → Will use method with FEWEST outliers for cleaning")
        else:
            print(" → Will use CONSENSUS (majority vote) for cleaning")
    else:
        print(f" Single method: {methods_display[0]}")
    print(f"Detrending Polynomial Degree: {DETRENDING_DEGREE}")
    print("="*70 + "\n")
   
    summary_rows = []
    pooled_distributions = {}
    cleaned_data_dict = {} # NEW: Store cleaned data for detrending analysis
   
    # Initialize pooled distributions
    for product in ['IGS_PWV', 'VMF3_PWV', 'ERA5_PWV']:
        for method_name, _, _ in methods_config:
            key = f"{product}_{method_name}"
            pooled_distributions[key] = {"orig": [], "clean": []}
   
    print("Processing stations...")
    for entry in entries:
        df = read_station_df(entry)
       
        required_core = ["STN", "YEAR", "IGS_PWV", "VMF3_PWV", "ERA5_PWV", "LAT", "LON", "H"]
        for col in required_core:
            if col not in df.columns:
                raise ValueError(f"{entry[0]} missing required column '{col}'")
       
        stn = str(df["STN"].iloc[0]).strip()
        print(f" Processing {stn}...")
       
        df["DATE"] = build_datetime(df)
        df = (df.sort_values("DATE")
                .dropna(subset=["DATE"])
                .drop_duplicates(subset=["DATE"], keep="first")
                .reset_index(drop=True))
       
        # Convert to mm
        df["IGS_PWV_mm"] = df["IGS_PWV"].astype(float) * 1000.0
        df["VMF3_PWV_mm"] = df["VMF3_PWV"].astype(float) * 1000.0
        df["ERA5_PWV_mm"] = df["ERA5_PWV"].astype(float) * 1000.0
       
        record_len = len(df)
        station_counts = {
            "STN": stn,
            "DAYS_total": record_len,
        }
       
        cleaned_data = {}
       
        # NEW: Initialize station data storage for detrending
        cleaned_data_dict[stn] = {'dates': df["DATE"]}
       
        for var in ["IGS_PWV_mm", "VMF3_PWV_mm", "ERA5_PWV_mm"]:
            base = var.split("_")[0]
           
            for method_name, method_func, method_params in methods_config:
                cleaned, outmask = method_func(
                    df[var],
                    pwv_min=PWV_MIN_MM,
                    pwv_max=PWV_MAX_MM,
                    **method_params
                )
               
                cleaned_data[f"{base}_{method_name}_clean"] = cleaned
               
                n_out = int(outmask.sum())
                pct_out = 100.0 * n_out / record_len if record_len else np.nan
               
                station_counts[f"{base}_{method_name}_outliers_count"] = n_out
                station_counts[f"{base}_{method_name}_outliers_pct"] = pct_out
               
                # Pool for distributions
                pool_key = f"{base}_PWV_{method_name}"
                pooled_distributions[pool_key]["orig"].extend(
                    df[var].dropna().tolist()
                )
                pooled_distributions[pool_key]["clean"].extend(
                    cleaned.dropna().tolist()
                )
           
            # NEW: Store cleaned data for detrending (use first method or consensus)
            if apply_all_methods:
                # Use the first method's cleaned data for detrending analysis
                cleaned_data_dict[stn][f'{base}_clean'] = cleaned_data[f"{base}_{methods_display[0]}_clean"]
            else:
                cleaned_data_dict[stn][f'{base}_clean'] = cleaned_data[f"{base}_{methods_display[0]}_clean"]
       
        # Build cleaned dataframe with additional metadata columns
        df_clean = pd.DataFrame(index=df.index)
        df_clean["STN"] = df["STN"]
        df_clean["LAT"] = df["LAT"]
        df_clean["LON"] = df["LON"]
        df_clean["H"] = df["H"]
        df_clean["YEAR"] = df["YEAR"]
        df_clean["MONTH"] = df["MONTH"]
        df_clean["DAY"] = df["DAY"]
        if "DOY" in df.columns:
            df_clean["DOY"] = df["DOY"]
        else:
            df_clean["DOY"] = df["DATE"].dt.dayofyear
        df_clean["DATE"] = df["DATE"]
        # Add original PWV columns (in cm)
        df_clean["IGS_PWV"] = df["IGS_PWV"]
        df_clean["VMF3_PWV"] = df["VMF3_PWV"]
        df_clean["ERA5_PWV"] = df["ERA5_PWV"]
        # Add original PWV_mm columns
        df_clean["IGS_PWV_mm"] = df["IGS_PWV_mm"]
        df_clean["VMF3_PWV_mm"] = df["VMF3_PWV_mm"]
        df_clean["ERA5_PWV_mm"] = df["ERA5_PWV_mm"]
        for key, values in cleaned_data.items():
            df_clean[key] = values
       
        # Reorder columns: meta + originals (cm + mm) + cleans (sorted by product and method)
        meta_cols = ["STN", "LAT", "LON", "H", "YEAR", "MONTH", "DAY", "DOY", "DATE"]
        original_cols = ["IGS_PWV", "IGS_PWV_mm", "VMF3_PWV", "VMF3_PWV_mm", "ERA5_PWV", "ERA5_PWV_mm"]
        clean_cols = sorted([col for col in df_clean.columns if col.endswith('_clean')], 
                            key=lambda x: (x.split('_')[0], '_'.join(x.split('_')[1:-1])))
        df_clean = df_clean[meta_cols + original_cols + clean_cols]
       
        # Save per-station cleaned CSV
        method_suffix = 'allmethods' if apply_all_methods else OUTLIER_METHOD.lower()
        cleaned_path = os.path.join(cleaned_dir, f"{stn}_cleaned_{method_suffix}.csv")
        df_clean.to_csv(cleaned_path, index=False)
       
        # Sample size assessment
        if record_len >= MIN_VALID_DAYS:
            station_counts["sample_quality"] = "Excellent"
        elif record_len >= MIN_ACCEPTABLE_DAYS:
            station_counts["sample_quality"] = "Acceptable"
        elif record_len >= MIN_WARNING_DAYS:
            station_counts["sample_quality"] = "Warning"
        else:
            station_counts["sample_quality"] = "Insufficient"
       
        station_counts["eligible_for_3CH_ETC"] = (
            "YES" if record_len >= MIN_VALID_DAYS else "NO"
        )
       
        summary_rows.append(station_counts)
   
    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_rows)
    summary_csv_path = os.path.join(OUTPUT_ROOT, "PWV_outlier_summary_comprehensive.csv")
    summary_df.to_csv(summary_csv_path, index=False)
   
    print("\nGenerating figures...")
   
    # Generate all figures
    fig1 = create_figure_1_sample_size_assessment(summary_df, fig_dir)
    print(f" Created: {fig1}")
   
    fig2 = create_figure_2_method_comparison(summary_df, fig_dir, methods_display)
    print(f" Created: {fig2}")
   
    fig3 = create_figure_3_enhanced_split_violin(pooled_distributions, fig_dir)
    print(f" Created: {fig3}")
   
    if apply_all_methods:
        fig4 = create_figure_4_method_effectiveness(summary_df, fig_dir)
        print(f" Created: {fig4}")
           
       
        # Create method comparison summary
        create_method_comparison_table(summary_df, OUTPUT_ROOT)
        
        
    # NEW: DETRENDING ANALYSIS
    print("\nPerforming detrending analysis...")
    detrending_df = perform_detrending_analysis(cleaned_data_dict)
   
    # Save detrending results
    detrending_csv_path = os.path.join(OUTPUT_ROOT, f"Detrending_Analysis_Results_Degree{DETRENDING_DEGREE}.csv")
    detrending_df.to_csv(detrending_csv_path, index=False)
    print(f" Saved detrending results: {detrending_csv_path}")
   
    # Create detrending summary figure
    fig_detrend = create_detrending_summary_figure(detrending_df, fig_dir)
    print(f" Created: {fig_detrend}")
   
    # NEW: Create additional detrending figures
    fig_example = create_example_detrending_timeseries(cleaned_data_dict, detrending_df, fig_dir)
    print(f" Created: {fig_example}")
   
    fig_heatmap = create_heatmap_trends(detrending_df, fig_dir)
    print(f" Created: {fig_heatmap}")
    
# =============================================================================
#  COMPARE LINEAR (degree 1) AND NONLINEAR/QUADRATIC (degree 2) DETRENDING
# =============================================================================
    comparison_df, summary_stats = compare_linear_vs_quadratic(cleaned_data_dict, OUTPUT_ROOT)
    
    # Generate comprehensive report
    generate_comprehensive_report(summary_df, OUTPUT_ROOT, apply_all_methods)
   
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\nOutput Directory: {OUTPUT_ROOT}")
    print(f"\nGenerated Files:")
    print(f" 1. Summary table: PWV_outlier_summary_comprehensive.csv")
    print(f" 2. Detrending results: Detrending_Analysis_Results_Degree{DETRENDING_DEGREE}.csv")
    if apply_all_methods:
        print(f" 3. Method comparison: Method_Comparison_Summary.csv")
        print(f" 4. Comprehensive report: QC_Analysis_Report.txt")
    else:
        print(f" 3. Comprehensive report: QC_Analysis_Report.txt")
    print(f"\nGenerated Figures:")
    print(f" 1. Figure 1: Sample Size Assessment")
    print(f" 2. Figure 2: Outlier Detection Method Comparison")
    print(f" 3. Figure 3: Enhanced Split-Violin Plots")
    if apply_all_methods:
        print(f" 4. Figure 4: Method Effectiveness")
        print(f" 5. Figure: Detrending Analysis Summary (Degree {DETRENDING_DEGREE}) (NEW)")
        print(f" 6. Figure: Example Time Series with Trends (Degree {DETRENDING_DEGREE}) (NEW)")
        print(f" 7. Figure: Detrending Heatmaps (Degree {DETRENDING_DEGREE}) (NEW)")
    else:
        print(f" 4. Figure: Detrending Analysis Summary (Degree {DETRENDING_DEGREE}) (NEW)")
        print(f" 5. Figure: Example Time Series with Trends (Degree {DETRENDING_DEGREE}) (NEW)")
        print(f" 6. Figure: Detrending Heatmaps (Degree {DETRENDING_DEGREE}) (NEW)")
    print(f"\nCleaned data per station: {cleaned_dir}")
    if apply_all_methods:
        print("\nAll methods (Hampel, IQR, Z-score) applied to IGS, VMF3, ERA5")
    else:
        print(f"\n{methods_display[0]} method applied to IGS, VMF3, ERA5")
        
def create_method_comparison_table(summary_df, outdir):
    """Create a summary table comparing method effectiveness.
   
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary statistics per station.
    outdir : str
        Output directory.
   
    Returns:
    --------
    str
        Path to saved CSV.
    """
    products = ['IGS', 'VMF3', 'ERA5']
    methods = ['Hampel', 'IQR', 'Zscore']
   
    comparison_data = []
   
    for product in products:
        for method in methods:
            col_name = f"{product}_{method}_outliers_pct"
            if col_name in summary_df.columns:
                values = summary_df[col_name].dropna()
               
                comparison_data.append({
                    'Product': product,
                    'Method': method,
                    'Mean_Outliers_%': values.mean(),
                    'Median_Outliers_%': values.median(),
                    'Std_Outliers_%': values.std(),
                    'Min_Outliers_%': values.min(),
                    'Max_Outliers_%': values.max(),
                    'Stations_Processed': len(values)
                })
   
    comparison_df = pd.DataFrame(comparison_data)
    output_path = os.path.join(outdir, "Method_Comparison_Summary.csv")
    comparison_df.to_csv(output_path, index=False)
   
    return output_path

def generate_comprehensive_report(summary_df, outdir, apply_all_methods):
    """Generate a comprehensive text report for the manuscript.
   
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary statistics per station.
    outdir : str
        Output directory.
    apply_all_methods : bool
        Whether all methods were applied.
   
    Returns:
    --------
    str
        Path to saved report.
    """
    report_path = os.path.join(outdir, "QC_Analysis_Report.txt")
   
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("PWV QUALITY CONTROL AND OUTLIER ANALYSIS REPORT\n")
        f.write("="*70 + "\n\n")
       
        # Section 1: Sample Size Assessment
        f.write("1. SAMPLE SIZE ASSESSMENT\n")
        f.write("-"*70 + "\n")
        total_stations = len(summary_df)
        days = summary_df['DAYS_total'].values
       
        excellent = np.sum(days >= MIN_VALID_DAYS)
        acceptable = np.sum((days >= MIN_ACCEPTABLE_DAYS) & (days < MIN_VALID_DAYS))
        warning = np.sum((days >= MIN_WARNING_DAYS) & (days < MIN_ACCEPTABLE_DAYS))
        insufficient = np.sum(days < MIN_WARNING_DAYS)
       
        f.write(f"Total Stations Analyzed: {total_stations}\n\n")
        f.write(f"Sample Size Categories:\n")
        f.write(f" Excellent (>={MIN_VALID_DAYS} days): {excellent:2d} ({excellent/total_stations*100:5.1f}%)\n")
        f.write(f" Acceptable (>={MIN_ACCEPTABLE_DAYS} days): {acceptable:2d} ({acceptable/total_stations*100:5.1f}%)\n")
        f.write(f" Warning (>={MIN_WARNING_DAYS} days): {warning:2d} ({warning/total_stations*100:5.1f}%)\n")
        f.write(f" Insufficient (<{MIN_WARNING_DAYS} days): {insufficient:2d} ({insufficient/total_stations*100:5.1f}%)\n\n")
       
        f.write(f"Sample Size Statistics:\n")
        f.write(f" Mean: {np.mean(days):7.1f} days\n")
        f.write(f" Median: {np.median(days):7.1f} days\n")
        f.write(f" Std Dev: {np.std(days):7.1f} days\n")
        f.write(f" Range: {np.min(days):.0f} - {np.max(days):.0f} days\n\n")
       
        # List stations with insufficient data
        insufficient_stations = summary_df[summary_df['DAYS_total'] < MIN_WARNING_DAYS]['STN'].tolist()
        if insufficient_stations:
            f.write(f"Stations with Insufficient Data (<{MIN_WARNING_DAYS} days):\n")
            for stn in insufficient_stations:
                days_val = summary_df[summary_df['STN'] == stn]['DAYS_total'].values[0]
                f.write(f" - {stn}: {days_val} days\n")
            f.write("\n")
       
        # Section 2: Outlier Detection Summary
        f.write("\n2. OUTLIER DETECTION SUMMARY\n")
        f.write("-"*70 + "\n")
       
        products = ['IGS', 'VMF3', 'ERA5']
        methods = ['Hampel', 'IQR', 'Zscore']
       
        if apply_all_methods:
            f.write("Methods Applied:\n")
            f.write(f" 1. Hampel Filter (window={HAMPEL_WINDOW}, σ={HAMPEL_SIGMA})\n")
            f.write(f" 2. IQR Method (multiplier={IQR_MULTIPLIER})\n")
            f.write(f" 3. Z-score Method (threshold={ZSCORE_THRESHOLD})\n\n")
        else:
            method_name = OUTLIER_METHOD.capitalize()
            if method_name == 'Hampel':
                f.write(f"Method Applied: Hampel Filter (window={HAMPEL_WINDOW}, σ={HAMPEL_SIGMA})\n\n")
            elif method_name.upper() == 'IQR':
                f.write(f"Method Applied: IQR Method (multiplier={IQR_MULTIPLIER})\n\n")
            else:
                f.write(f"Method Applied: Z-score Method (threshold={ZSCORE_THRESHOLD})\n\n")
       
        f.write("Average Outlier Percentages by Product and Method:\n")
        f.write(f"{'Product':<10} {'Method':<10} {'Mean %':<10} {'Median %':<10} {'Std %':<10}\n")
        f.write("-"*70 + "\n")
       
        for product in products:
            for method in methods:
                col_name = f"{product}_{method}_outliers_pct"
                if col_name in summary_df.columns:
                    values = summary_df[col_name].dropna()
                    f.write(f"{product:<10} {method:<10} {values.mean():>8.2f} "
                           f"{values.median():>8.2f} {values.std():>8.2f}\n")
       
        # Section 3: Method Effectiveness Analysis
        if apply_all_methods:
            f.write("\n3. METHOD EFFECTIVENESS ANALYSIS\n")
            f.write("-"*70 + "\n")
           
            for product in products:
                f.write(f"\n{product} PWV:\n")
                method_means = {}
                for method in methods:
                    col_name = f"{product}_{method}_outliers_pct"
                    if col_name in summary_df.columns:
                        method_means[method] = summary_df[col_name].mean()
               
                if method_means:
                    best_method = min(method_means, key=method_means.get)
                    most_sensitive = max(method_means, key=method_means.get)
                   
                    f.write(f" Most Conservative (fewest outliers): {best_method} "
                           f"({method_means[best_method]:.2f}%)\n")
                    f.write(f" Most Sensitive (most outliers): {most_sensitive} "
                           f"({method_means[most_sensitive]:.2f}%)\n")
        else:
            f.write("\n3. METHOD EFFECTIVENESS ANALYSIS\n")
            f.write("-"*70 + "\n")
            f.write(f"Single method applied: {OUTLIER_METHOD}\n")
            for product in products:
                col_name = f"{product}_{OUTLIER_METHOD.capitalize()}_outliers_pct"
                if col_name in summary_df.columns:
                    mean_pct = summary_df[col_name].mean()
                    f.write(f"{product}: ~{mean_pct:.2f}% outliers detected\n")
       
        # Section 4: Recommendations
        f.write("\n4. RECOMMENDATIONS FOR 3CH/ETC ANALYSIS\n")
        f.write("-"*70 + "\n")
       
        f.write(f"\nStations Recommended for Analysis:\n")
        recommended = summary_df[summary_df['eligible_for_3CH_ETC'] == 'YES']
        f.write(f" Total: {len(recommended)} stations\n")
        f.write(f" Stations: {', '.join(recommended['STN'].tolist())}\n\n")
       
        f.write(f"Stations Requiring Caution:\n")
        caution = summary_df[(summary_df['DAYS_total'] >= MIN_WARNING_DAYS) &
                            (summary_df['DAYS_total'] < MIN_VALID_DAYS)]
        if len(caution) > 0:
            f.write(f" Total: {len(caution)} stations\n")
            f.write(f" Stations: {', '.join(caution['STN'].tolist())}\n")
            f.write(f" Recommendation: Use with extended uncertainty bounds\n\n")
       
        f.write(f"Stations Not Recommended:\n")
        not_recommended = summary_df[summary_df['DAYS_total'] < MIN_WARNING_DAYS]
        if len(not_recommended) > 0:
            f.write(f" Total: {len(not_recommended)} stations\n")
            f.write(f" Stations: {', '.join(not_recommended['STN'].tolist())}\n")
            f.write(f" Recommendation: Exclude from statistical analysis\n\n")
       
        # Section 5: Quality Control Impact
        f.write("\n5. QUALITY CONTROL IMPACT ASSESSMENT\n")
        f.write("-"*70 + "\n")
       
        f.write("\nOverall QC Effectiveness:\n")
        for product in products:
            f.write(f"\n{product} PWV:\n")
            for method in methods:
                col_name = f"{product}_{method}_outliers_pct"
                if col_name in summary_df.columns:
                    mean_outliers = summary_df[col_name].mean()
                    f.write(f" {method}: ~{mean_outliers:.2f}% of data flagged and cleaned\n")
       
        # Section 6: Data Preprocessing Summary
        f.write("\n6. DATA PREPROCESSING SUMMARY\n")
        f.write("-"*70 + "\n")
        f.write("Steps Applied:\n")
        f.write(" 1. Physical plausibility screening (0-100 mm)\n")
        f.write(" 2. Outlier detection using applied method(s)\n")
        f.write(" 3. Outlier replacement with robust statistics\n")
        f.write(" 4. Gap interpolation for continuity\n")
        f.write(" 5. Time matching and detrending (implicit in daily means)\n")
        f.write(f" 6. Polynomial detrending analysis (degree {DETRENDING_DEGREE}) (NEW)\n\n")
       
        f.write("Reference:\n")
        f.write(" - Hampel, F.R. (1974). JASA 69(346), 383-393.\n")
        f.write(" - Tukey, J.W. (1977). Exploratory Data Analysis. Addison-Wesley.\n")
        f.write(" - Leys, C., et al. (2013). J. Exp. Soc. Psychol. 49, 764-766.\n\n")
       
        f.write("="*70 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*70 + "\n")
   
    return report_path

if __name__ == "__main__":
    main()
