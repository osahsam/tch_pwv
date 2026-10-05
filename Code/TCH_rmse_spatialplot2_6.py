"""
High-Quality Spatial Mapping Script for Atmospheric Data Visualization
========================================================================
This script creates publication-ready spatial maps of GNSS-derived precipitable
water vapor (PWV) uncertainties across Africa, comparing IGS, VMF3, and ERA5 datasets.
Key Features:
- High-resolution output (300 DPI) optimized for journal publication
- Multiple customizable colormaps for visual comparison
- Robust error handling and data validation
- Proper axis formatting with directional labels (N/S/E/W)
- Enhanced visual contrast and readability
Author: [Your Name]
Date: December 2025
"""
# =============================================================================
# Import Required Libraries
# =============================================================================
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import warnings
from scipy.spatial import distance_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]


# Suppress unnecessary warnings
warnings.filterwarnings('ignore', category=UserWarning)
# =============================================================================
# Configuration Parameters
# =============================================================================
class Config:
    """Configuration class for spatial mapping parameters."""
   
    # File paths
    FILE_PATH = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"
    BASE_FIG_DIR = REPO_ROOT / "Figures"
    FIG_OUTPUT_DIR = "3CHPLOTs(subplots)final"
   
    # Map extent [lon_min, lon_max, lat_min, lat_max]
    MAP_EXTENT = [-30, 65, -50, 40]
   
    # Figure parameters (optimized for high-quality output)
    FIGURE_WIDTH = 24
    FIGURE_HEIGHT = 14
    DPI = 300
    
    # Font sizes
    TITLE_FONTSIZE = 20
    LABEL_FONTSIZE = 14
    TICK_FONTSIZE = 12
    STATION_FONTSIZE = 8
    COLORBAR_LABEL_FONTSIZE = 13
    COLORBAR_TICK_FONTSIZE = 11
    STATS_BOX_FONTSIZE = 13    # For statistical summary boxes
    
    # Visual parameters
    MARKER_SIZE = 250
    MARKER_EDGEWIDTH = 2.0
    MARKER_ALPHA = 0.90
    SPINE_LINEWIDTH = 2.5
    TICK_LENGTH = 8
    GRID_ALPHA = 0.3  #(0.4)
    GRID_LINEWIDTH = 0.6       # Explicit control for consistency
   
    # Label  positioning/offset (degrees latitude)- to ensure no overlap with markers
    LABEL_OFFSET = 1.8  # Adjust this value if needed for your station distribution (2.2)
    MIN_LABEL_SPACING = 1.5    # Minimum distance between labels (degrees)
        
    # Colorbar parameters (enhanced)
    COLORBAR_FRACTION = 0.046  # 
    COLORBAR_PAD = 0.04        # More separation from plot
    COLORBAR_SHRINK = 0.85     # Better proportions
    COLORBAR_ASPECT = 25       # Taller, more elegant appearance
    COLORBAR_N_TICKS = 8       # Number of tick marks for precision

    # Color scale parameters
    USE_PERCENTILE_SCALING = True   # Remove outlier influence
    PERCENTILE_LOW = 2              # Lower percentile cutoff
    PERCENTILE_HIGH = 98            # Upper percentile cutoff
    ROUND_COLOR_SCALE = True        # Round to nice numbers

    # Geographic features
    ADD_LAND_SHADING = True         # Add subtle land/ocean distinction
    ADD_LAKES = True                # Show major lakes
    LAND_ALPHA = 0.15               # Transparency for land shading
    OCEAN_ALPHA = 0.15              # Transparency for ocean shading

    # Statistics box
    SHOW_STATS_BOX = True           # Display statistics on each subplot
    STATS_BOX_POSITION = (0.02, 0.02) # Position (x, y) in axes coordinates [(top-left: 0.02, 0.98), bottom-left:(0.02, 0.02)]

    # Data columns
    RMSE_COLUMNS = ['RMSEigs(3ch)', 'RMSEvmf3(3ch)', 'RMSEera5(3ch)']
    SUBPLOT_TITLES = ['(a) IGS', '(b) VMF3', '(c) ERA5']
       
# =============================================================================
# Custom Colormaps
# =============================================================================
class ColorMaps:
    """Perceptually uniform, colorblind-friendly colormaps for publication."""
    
    @staticmethod
    def get_colormap(name='default'):
        colormaps = {
            'default': LinearSegmentedColormap.from_list(
                "custom_blue_red",
                [(0, 0, 1), (0, 1, 1), (1, 1, 0), (1, 0, 0)],
                N=256
            ),
            'viridis_like': LinearSegmentedColormap.from_list(
                "custom_viridis",
                ['#440154', '#31688e', '#35b779', '#fde724'],
                N=256
            ),
            'temperature': LinearSegmentedColormap.from_list(
                "temperature",
                ['#2166ac', '#67a9cf', '#f7f7f7', '#ef8a62', '#b2182b'],
                N=256
            ),
            'ocean': LinearSegmentedColormap.from_list(
                "ocean",
                ['#f7fbff', '#deebf7', '#9ecae1', '#4292c6', '#08519c'],
                N=256
            ),
            'earth': LinearSegmentedColormap.from_list(
                "earth",
                ['#543005', '#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e'],
                N=256
            ),
            'rainbow': 'turbo',
        }
        return colormaps.get(name, colormaps['default'])
    
# =============================================================================
# Utility Functions
# =============================================================================
def create_incremented_folder(base_folder):
    base_path = Path(base_folder)
    folder = base_path
    counter = 1
    while folder.exists():
        folder = Path(f"{base_folder} {counter}")
        counter += 1
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def format_coordinate_label(value, is_latitude=True):
    abs_value = abs(value)
    direction = 'N' if is_latitude and value >= 0 else 'S' if is_latitude else 'E' if value >= 0 else 'W'
    return f"{abs_value:.0f}°{direction}"

def validate_dataframe(df, required_columns):
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    for col in required_columns:
        if df[col].isna().any():
            warnings.warn(f"Column '{col}' contains NaN values")
   
def get_smart_color_range(df, rmse_columns, config):
    """
    Calculate intelligent color scale range.
    
    Uses percentile-based scaling to remove outlier influence,
    then rounds to nice numbers for easier reading.
    """
    all_values = pd.concat([df[col] for col in rmse_columns])
    
    if config.USE_PERCENTILE_SCALING:
        vmin = all_values.quantile(config.PERCENTILE_LOW / 100.0)
        vmax = all_values.quantile(config.PERCENTILE_HIGH / 100.0)
    else:
        vmin = all_values.min()
        vmax = all_values.max()
    
    if config.ROUND_COLOR_SCALE:
        # Round to nice numbers
        vmin = np.floor(vmin * 2) / 2  # Round to nearest 0.5
        vmax = np.ceil(vmax * 2) / 2
    
    return vmin, vmax

def calculate_label_positions(df, config):
    """
    Calculate smart label positions to avoid overlaps.
    
    Adjusts vertical offset based on nearby station density.
    """
    positions = []
    
    for idx, row in df.iterrows():
        # Count nearby stations
        nearby = df[
            (abs(df['LAT'] - row['LAT']) < 3) & 
            (abs(df['LON'] - row['LON']) < 3)
        ]
        
        # Adjust offset based on density
        if len(nearby) > 4:
            offset = config.LABEL_OFFSET * 1.4  # Increase in crowded areas
        elif len(nearby) > 2:
            offset = config.LABEL_OFFSET * 1.2
        else:
            offset = config.LABEL_OFFSET
        
        positions.append({
            'lon': row['LON'],
            'lat': row['LAT'],
            'label': row['STN'],
            'offset': offset
        })
    
    return positions            

# =============================================================================
# Data Loading and Preparation
# =============================================================================
def load_and_validate_data(file_path, sheet_name='Sheet1'):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        required_cols = ['LON', 'LAT', 'STN'] + Config.RMSE_COLUMNS
        validate_dataframe(df, required_cols)
        
        print(f"✓ Data loaded successfully: {len(df)} stations")
        print(f"  Longitude range: [{df['LON'].min():.1f}, {df['LON'].max():.1f}]")
        print(f"  Latitude range: [{df['LAT'].min():.1f}, {df['LAT'].max():.1f}]")
        
        return df
    
    except FileNotFoundError:
        print(f"✗ Error: File not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading data: {str(e)}")
        sys.exit(1)
        
# =============================================================================
# Map Creation Functions
# =============================================================================
def setup_map_axis(ax, extent, config):
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    # Clean white background
    ax.set_facecolor('white')
   
    # Minimal geographic features for clean look
    ax.add_feature(cfeature.COASTLINE, linewidth=1.5, edgecolor='black', zorder=1)
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.8, edgecolor='gray', zorder=1)
    
    # Gridlines
    gl = ax.gridlines(draw_labels=False, linewidth=0.5, color='gray',
                      alpha=config.GRID_ALPHA, linestyle='--', zorder=2)
   
    # Ticks and labels
    lon_ticks = range(extent[0], extent[1] + 1, 10)
    lat_ticks = range(extent[2], extent[3] + 1, 10)
   
    ax.set_xticks(lon_ticks, crs=ccrs.PlateCarree())
    ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
   
    ax.set_xticklabels([format_coordinate_label(x, False) for x in lon_ticks],
                       fontsize=config.TICK_FONTSIZE, fontweight='bold')
    ax.set_yticklabels([format_coordinate_label(y, True) for y in lat_ticks],
                       fontsize=config.TICK_FONTSIZE, fontweight='bold')
   
    ax.tick_params(axis='both', length=config.TICK_LENGTH, width=1.5, color='black')
   
    ax.set_xlabel("Longitude", fontsize=config.LABEL_FONTSIZE, labelpad=10, fontweight='bold')
    ax.set_ylabel("Latitude", fontsize=config.LABEL_FONTSIZE, labelpad=10, fontweight='bold')
   
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(config.SPINE_LINEWIDTH)

# =============================================================================
# Map Creation Functions
# =============================================================================
def setup_map_axis(ax, extent, config):
    """Configure map axis with publication-quality settings."""
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    # Clean white background
    ax.set_facecolor('white')
   
    # Add subtle land/ocean distinction if enabled
    if config.ADD_LAND_SHADING:
        ax.add_feature(
            cfeature.LAND, 
            facecolor='#f5f5f5', 
            alpha=config.LAND_ALPHA,
            zorder=0
        )
        ax.add_feature(
            cfeature.OCEAN, 
            facecolor='#e6f3ff', 
            alpha=config.OCEAN_ALPHA,
            zorder=0
        )
    
    # Add lakes if enabled
    if config.ADD_LAKES:
        ax.add_feature(
            cfeature.LAKES, 
            alpha=0.3, 
            facecolor='#d4e7f5',
            zorder=0
        )
    
    # Primary geographic features
    ax.add_feature(
        cfeature.COASTLINE, 
        linewidth=1.5, 
        edgecolor='black', 
        zorder=1
    )
    ax.add_feature(
        cfeature.BORDERS, 
        linestyle='-', 
        linewidth=0.8, 
        edgecolor='#666666', #OR gray
        zorder=1
    )
    
    # Gridlines
    gl = ax.gridlines(
        draw_labels=False, 
        linewidth=config.GRID_LINEWIDTH, 
        color='gray',
        alpha=config.GRID_ALPHA, 
        linestyle='--', 
        zorder=2
    )
   
    # Ticks and labels with improved formatting
    lon_ticks = range(extent[0], extent[1] + 1, 10)
    lat_ticks = range(extent[2], extent[3] + 1, 10)
   
    ax.set_xticks(lon_ticks, crs=ccrs.PlateCarree())
    ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
   
    ax.set_xticklabels(
        [format_coordinate_label(x, False) for x in lon_ticks],
        fontsize=config.TICK_FONTSIZE, 
        fontweight='bold'
    )
    ax.set_yticklabels(
        [format_coordinate_label(y, True) for y in lat_ticks],
        fontsize=config.TICK_FONTSIZE, 
        fontweight='bold'
    )
   
    ax.tick_params(
        axis='both', 
        length=config.TICK_LENGTH, 
        width=1.5, 
        color='black'
    )
    
    # Axis labels with proper spacing
    ax.set_xlabel(
        "Longitude", 
        fontsize=config.LABEL_FONTSIZE, 
        labelpad=10, 
        fontweight='bold'
    )
    ax.set_ylabel(
        "Latitude", 
        fontsize=config.LABEL_FONTSIZE, 
        labelpad=10, 
        fontweight='bold'
    )
   
    # Spines
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(config.SPINE_LINEWIDTH)

def add_statistics_box(ax, data, column_name, config):
    """Add statistical summary box to subplot."""
    if not config.SHOW_STATS_BOX:
        return
    
    stats_text = (
        f"Mean: {data[column_name].mean():.2f} mm\n"
        f"Std: {data[column_name].std():.2f} mm\n"
        f"Min: {data[column_name].min():.2f} mm\n"
        f"Max: {data[column_name].max():.2f} mm"
    )
    
    ax.text(
        config.STATS_BOX_POSITION[0], 
        config.STATS_BOX_POSITION[1],
        stats_text,
        transform=ax.transAxes,
        fontsize=config.STATS_BOX_FONTSIZE,
        verticalalignment='bottom',
        horizontalalignment='left',
        fontweight='bold',
        bbox=dict(
            boxstyle='round,pad=0.5', 
            facecolor='white', 
            edgecolor='black',
            alpha=0.85,
            linewidth=1.5
        ),
        zorder=10
    )
    
def create_spatial_plot(df, config, colormap_name='default'):
    cmap = ColorMaps.get_colormap(colormap_name)
   
    fig, axes = plt.subplots(
        1, 3,
        figsize=(config.FIGURE_WIDTH, config.FIGURE_HEIGHT),
        subplot_kw={'projection': ccrs.PlateCarree()},
        dpi=config.DPI
    )
   
    # Calculate color range
    vmin = df[config.RMSE_COLUMNS].min().min()
    vmax = df[config.RMSE_COLUMNS].max().max()
    
    print(f"  Color scale range: [{vmin:.2f}, {vmax:.2f}] mm")
   
    # Calculate smart label positions
    label_positions = calculate_label_positions(df, config)
    
    for idx, (ax, title, rmse_col) in enumerate(zip(axes, config.SUBPLOT_TITLES, config.RMSE_COLUMNS)):
        
        # Setup map
        setup_map_axis(ax, config.MAP_EXTENT, config)
       
        # Plot data points
        sc = ax.scatter(
            df['LON'], df['LAT'],
            c=df[rmse_col],
            cmap=cmap,
            s=config.MARKER_SIZE,
            marker='o',
            edgecolor='black',
            linewidth=config.MARKER_EDGEWIDTH,
            alpha=config.MARKER_ALPHA,
            vmin=vmin, vmax=vmax,
            transform=ccrs.PlateCarree(),
            zorder=3
        )
       
        # Add station labels with smart positioning: bold black text, no halo/background, positioned clearly above markers
        for pos in label_positions:
            ax.text(
                pos['lon'],
                pos['lat'] + pos['offset'],
                pos['label'],
                fontsize=config.STATION_FONTSIZE,
                fontweight='bold',
                ha='center',
                va='bottom',
                color='black',
                transform=ccrs.PlateCarree(),
                zorder=5
            )
       
        # Add subplot title
        ax.set_title(title, fontsize=config.TITLE_FONTSIZE, weight='bold', pad=15)
       
        # Colorbar
        cbar = plt.colorbar(
            sc, ax=ax, 
            orientation='vertical',
            fraction=config.COLORBAR_FRACTION, 
            pad=config.COLORBAR_PAD, 
            shrink=config.COLORBAR_SHRINK, 
            aspect=config.COLORBAR_ASPECT,
            extend='both'  # Show arrows if data exceeds range
        )
                           
        cbar.set_label('Uncertainty (mm)', fontsize=config.COLORBAR_LABEL_FONTSIZE,
                       weight='bold', labelpad=15)
        cbar.ax.tick_params(labelsize=config.COLORBAR_TICK_FONTSIZE, width=1.5, length=6)
        
        # Set precise number of colorbar ticks
        cbar.locator = ticker.MaxNLocator(nbins=config.COLORBAR_N_TICKS)
        cbar.update_ticks()
        
        cbar.outline.set_linewidth(1.5)
        
        # Add statistics box
        add_statistics_box(ax, df, rmse_col, config)
   
    plt.tight_layout()
    return fig, axes

# =============================================================================
# Main Execution
# =============================================================================
def main():
    print("="*70)
    print("High-Quality Spatial Mapping for Atmospheric Data")
    print("="*70)
   
    config = Config()
   
    print("\n[1/4] Loading data...")
    df = load_and_validate_data(config.FILE_PATH)
   
    print("\n[2/4] Creating output directory...")
    output_dir = create_incremented_folder(Path(config.BASE_FIG_DIR) / config.FIG_OUTPUT_DIR)
    print(f"✓ Output directory: {output_dir}")
    
    # Generate Figure versions with alternative colormaps
   
    colormap_options = ['default', 'viridis_like', 'temperature', 'ocean', 'earth', 'rainbow']
   
    print(f"\n[3/4] Generating plots with {len(colormap_options)} colormaps...")
    print(f"  Figure dimensions: {config.FIGURE_WIDTH}\" × {config.FIGURE_HEIGHT}\"")
    print(f"  Resolution: {config.DPI} DPI")
    
    # Generate main figure
    for cmap_name in colormap_options:
        print(f" → Creating plot with '{cmap_name}' colormap...")
        
        fig, _ = create_spatial_plot(df, config, colormap_name=cmap_name)
        filename = f"Spatial_plot_3CH_pwv_{cmap_name}_high_quality.png"
        output_path = output_dir / filename
        fig.savefig(output_path, dpi=config.DPI, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        print(f" ✓ Saved: {filename}")
        
        plt.close(fig)
   
    print("\n[4/4] Creating high-resolution and vector versions...")
    fig_hires, _ = create_spatial_plot(df, config, colormap_name='default')
    hires_path = output_dir / "Spatial_plot_3CH_pwv_600dpi_final.png"
    fig_hires.savefig(hires_path, dpi=600, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved ultra-high-res PNG (600 DPI): {hires_path.name}")
    plt.close(fig_hires)
   
    fig_vector, _ = create_spatial_plot(df, config, colormap_name='default')
    pdf_path = output_dir / "Spatial_plot_3CH_pwv_vector.pdf"
    fig_vector.savefig(pdf_path, format='pdf', bbox_inches='tight')
    print(f"✓ Saved vector PDF: {pdf_path.name}")
   
    #EPS FORMAT
    eps_path = output_dir / "Spatial_plot_3CH_pwv_vector.eps"
    fig_vector.savefig(eps_path, format='eps', bbox_inches='tight')
    print(f"✓ Saved vector EPS: {eps_path.name}")
    plt.close(fig_vector)
    
    #SVG FORMAT
    svg_path = output_dir / "Spatial_plot_3CH_pwv_vector.svg"
    fig_vector.savefig(svg_path, format='svg', bbox_inches='tight')
    print(f"✓ Saved vector SVG: {svg_path.name}")
    plt.close(fig_vector)
   
    # Print summary
    print("\n" + "="*70)
    print("✓ All plots generated successfully!")
    print(f"✓ Output location: {output_dir}")
    print(f"\nFiles generated:")
    print(f"  • Main figures: 4 formats (PNG 300/600 DPI, PDF, EPS, SVG)")
    print(f"\nRecommended for submission:")
    print(f"  • Primary: PNG or SVG or EPS (vector format)")
    print(f"  • Backup: PNG at 600 DPI")
    print(f"  ✓ Statistical summary boxes")
    print("="*70)
    
if __name__ == "__main__":
    main()
