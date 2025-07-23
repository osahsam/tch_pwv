# =============================================================================
# Import Required Libraries
# =============================================================================
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# =============================================================================
# Load the uploaded Excel file to analyze the data
# =============================================================================
file_path = 'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/DATA ANALYTICs/3CH analysis/STATISTICAL analysis (Africa) 2_2.xlsx'
data = pd.ExcelFile(file_path)

# Load the data from the first sheet
df = data.parse('Sheet1')

# =============================================================================
# Define path to Save Spatial Plots
# =============================================================================
BASE_figDIR = r"D:/DATA/ATMOSPHERE data/TROPOSPHERE data/DATA ANALYTICs/3CH analysis"
FIG_OUTPUT_DIR = os.path.join(BASE_figDIR, "3CHPLOTs(subplots)")

# Create incremented folders to avoid overwriting
def create_incremented_folder(base_folder):
    folder = base_folder
    counter = 1
    while os.path.exists(folder):
        folder = f"{base_folder} {counter}"
        counter += 1
    os.makedirs(folder, exist_ok=True)
    return folder

fig_output_dir = create_incremented_folder(FIG_OUTPUT_DIR)

# =============================================================================
# Helper function to format tick labels
# =============================================================================
def format_lat_lon_labels(value, is_latitude):
    """
    Formats latitude or longitude values with directional labels (N, S, W, E).
    """
    if is_latitude:
        return f"{abs(value)}°{'N' if value >= 0 else 'S'}"
    else:
        return f"{abs(value)}°{'E' if value >= 0 else 'W'}"

# =============================================================================
# Create subplots for IGS, VMF3, and ERA5 uncertainties (3 columns)
# =============================================================================

# Define a custom colormap
custom_colors = [
    (0, 0, 1),    # Blue
    (0, 1, 1),    # Cyan
    (1, 1, 0),    # Yellow
    (1, 0, 0)     # Red
]
custom_cmap = LinearSegmentedColormap.from_list("custom_colormap", custom_colors, N=256)

# Create the figure and subplots
fig, axes = plt.subplots(1, 3, figsize=(30, 50), subplot_kw={'projection': ccrs.PlateCarree()})
titles = ['(a) IGS', '(b) VMF3', '(c) ERA5']
rmse_columns = ['RMSEigs(3ch)', 'RMSEvmf3(3ch)', 'RMSEera5(3ch)']

# Iterate through each subplot and plot the uncertainties
for ax, title, rmse_column in zip(axes, titles, rmse_columns):
    # Map setup
    ax.set_extent([-30, 65, -50, 40], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.RIVERS)

    # Add ticks with formatted labels
    ax.set_xticks(range(-30, 66, 10), crs=ccrs.PlateCarree())
    ax.set_yticks(range(-50, 41, 10), crs=ccrs.PlateCarree())
    ax.set_xticklabels([format_lat_lon_labels(x, is_latitude=False) for x in range(-30, 66, 10)], fontsize=16, fontweight='bold')
    ax.set_yticklabels([format_lat_lon_labels(y, is_latitude=True) for y in range(-50, 41, 10)], fontsize=16, fontweight='bold')
    
    #Increase Grid tick Markers lengths
    ax.tick_params(axis='x', length=10, color='black')  #  x-tick markers 
    ax.tick_params(axis='y', length=10, color='black')  #  y-tick markers 
    
    #Label Axes (X-axis and Y-axis)
    ax.set_xlabel("Longitude", fontsize=26, labelpad=22, fontweight='bold')
    ax.set_ylabel("Latitude", fontsize=16, labelpad=8, fontweight='bold')
    
    
    # =============================================================================
    # # Make the axes (horizontal and vertical) black and bold
    # =============================================================================
    ax.spines["top"].set_color("black")
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_color("black")
    ax.spines["right"].set_color("black")
    ax.spines["top"].set_linewidth(3)
    ax.spines["bottom"].set_linewidth(3)
    ax.spines["left"].set_linewidth(3)
    ax.spines["right"].set_linewidth(3)
    
    # Scatter plot
    sc = ax.scatter(
        df['LON'],
        df['LAT'],
        c=df[rmse_column],
        cmap=custom_cmap,
        s=150,
        marker='o',  # Circle marker
        edgecolor='k',
        alpha=0.7,
        transform=ccrs.PlateCarree()
    )

    # Station labels
    for _, row in df.iterrows():
        ax.text(
            row['LON'], row['LAT'],
            row['STN'],
            fontsize=8,
            fontweight='bold',
            ha='center',
            va='bottom',
            color='black',
            transform=ccrs.PlateCarree()
        )

    # Title for the subplot
    ax.set_title(title, fontsize=30, weight='bold')

    # Colorbar
    cbar = plt.colorbar(sc, ax=ax, orientation='vertical', fraction=0.04, pad=0.02)
    cbar.set_label('Uncertainty (mm)', fontsize=16, weight='bold')
    cbar.ax.tick_params(labelsize=14)

# Adjust layout
plt.tight_layout()

# =============================================================================
# Save the figure to a high-resolution image file (300 dpi)
# =============================================================================
figname = "Subplots_Spatial_plot_pwv_igs_vmf3_era5_3columns_NSEW_ticks.png"
full_FIGoutput_path = os.path.join(fig_output_dir, figname)
plt.savefig(full_FIGoutput_path, dpi=1000, bbox_inches='tight')

# Show plot
plt.show()



