# =============================================================================
# Import Required Libraries
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]

# import geopandas as gpd
# import matplotlib.pyplot as plt
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
# from mpl_toolkits.axes_grid1 import make_axes_locatable

# Load the uploaded Excel file to analyze the data
# file_path = 'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/DATA ANALYTICs/3CH analysis/STATISTICAL analysis (Africa) 2_2.xlsx'

file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"

# data = pd.read_excel(file_path)
# # Display the first few rows of the data to understand its structure
# print(data.head())

data = pd.ExcelFile(file_path)

# Display sheet names to understand the structure
print(data.sheet_names)

# Load the data from the first sheet
df = data.parse('Sheet1')

# Display the first few rows to understand the structure of the data
print(df.head())

# =============================================================================
# # Plotting a bar graph for the 3CH results & Display the RMSE values directly 
#   above the bars for easier interpretation (Vertical)
# =============================================================================

# Setting up the data for the bar graph
bar_width = 0.25
indices = range(len(df['STN']))

fig, ax = plt.subplots(figsize=(15, 8))

# Plotting each dataset
bars1 = ax.bar(
    [i - bar_width for i in indices],
    df['RMSEigs(3ch)'],
    bar_width,
    label='IGS',
    color='blue',
    edgecolor='black'
)
bars2 = ax.bar(
    indices,
    df['RMSEera5(3ch)'],
    bar_width,
    label='ERA5',
    color='green',
    edgecolor='black'
)
bars3 = ax.bar(
    [i + bar_width for i in indices],
    df['RMSEvmf3(3ch)'],
    bar_width,
    label='VMF3',
    color='orange',
    edgecolor='black'
)

# =============================================================================
# Overlay data labels for RMSE (vertically oriented labels closer to each bar)
# =============================================================================
# for bars in [bars1, bars2, bars3]:
#     for bar in bars:
#         height = bar.get_height()
#         ax.text(
#             bar.get_x() + bar.get_width() / 2.0, 
#             height + 0.05,  # Reduce the vertical offset for closer placement
#             f'{height:.2f}', 
#             ha='center', 
#             va='bottom', 
#             fontsize=10, 
#             fontweight='bold', 
#             rotation=90
#         )

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                height + 0.05,  # Reduce the vertical offset for closer placement
                f'{height:.2f}', ha='center', va='bottom', fontsize=12, weight='bold', rotation=90
            )
            
# =============================================================================
# Adjust axes to extend and contain data labels
# =============================================================================
ax.set_ylim(0, ax.get_ylim()[1] + 0.12)


# Make the axes (horizontal and vertical) black and bold
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)
ax.spines["left"].set_linewidth(2)
ax.spines["right"].set_linewidth(2)


# Adding labels and legend with increased font sizes and bold fonts
ax.set_xlabel('Stations', fontsize=24, labelpad=22, fontweight='bold')
ax.set_ylabel('RMSE (mm)', fontsize=24, labelpad=22, fontweight='bold')
#ax.set_title('3CH Uncertainty Analysis with Adjusted Vertical RMSE Labels', fontsize=20, fontweight='bold')
ax.set_xticks(indices)
ax.set_xticklabels(df['STN'], rotation=90, fontsize=18, fontweight='bold')
ax.legend(fontsize=14, loc='upper left')

# Adjust y-axis tick labels to bold and appropriate formatting
ax.tick_params(axis='y', labelsize=22)
for label in ax.get_yticklabels():
    label.set_fontweight('bold')

# Tight layout for better spacing
plt.tight_layout()

# =============================================================================
# Save the plot as a high-resolution image file
# =============================================================================
# output_file_path= (
#     'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/'
#     'DATA ANALYTICs/3CH analysis/FIGs_3ch/'
#     'BARplot_rmse_3CH_5.png'
# )

output_file_path = REPO_ROOT / "Figures" / "BARplot_rmse_3CH.png"

plt.savefig(output_file_path, format='png', dpi=1000, bbox_inches='tight')

print(f"Plot saved successfully to {output_file_path}")

# Display the figure 
plt.show()

# Close the figure after saving
plt.close(fig)                                 
