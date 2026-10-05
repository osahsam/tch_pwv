# =============================================================================
# Import Required Libraries
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]

# Load the uploaded Excel file to analyze the data
# file_path = 'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/DATA ANALYTICs/3CH analysis/STATISTICAL analysis (Africa) 2_2.xlsx'
file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"
data = pd.read_excel(file_path)
# Display the first few rows of the data to understand its structure
print(data.head())
# =============================================================================
# *****************REGIONAL ANALYSIS (FIVE REGIONS OF AFRICA)****************
# =============================================================================
# Load the station data and combine with statistical analysis data
stations_file_path = REPO_ROOT / "Data" / "IGS STATIONS-Africa_27sta.xlsx"
stations_data = pd.read_excel(stations_file_path)
# Combine the stations data with the statistical analysis data to group by region
merged_data = pd.merge(stations_data, data, left_on="SITE", right_on="STN")
# Compute overall mean analysis for 3CH, ETC, and DC metrics by African region
region_mean_analysis = merged_data.groupby('AFRICAN REGION')[[
    "RMSEigs(3ch)", "RMSEera5(3ch)", "RMSEvmf3(3ch)",
    "RMSEigs(etc)", "RMSEera5(etc)", "RMSEvmf3(etc)",
    "RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)",
    "R_igs(etc)", "R_era5(etc)", "R_vmf3(etc)",
    "R(IGSvsERA5)", "R(VMF3vsERA5)"
]].mean()
# Reset index for easier manipulation
region_mean_analysis.reset_index(inplace=True)
# Reorganize and rename African regions
region_order = [
    "Northern Africa", "Central Africa", "Southern Africa",
    "Eastern Africa", "Western Africa"
]
region_rename_mapping = {
    "Northern Africa": "North Africa",
    "Eastern Africa": "East Africa",
    "Western Africa": "West Africa"
}
region_mean_analysis['AFRICAN REGION'] = region_mean_analysis['AFRICAN REGION'].replace(region_rename_mapping)
region_mean_analysis['AFRICAN REGION'] = pd.Categorical(
    region_mean_analysis['AFRICAN REGION'],
    categories=[region_rename_mapping.get(region, region) for region in region_order],
    ordered=True
)
region_mean_analysis.sort_values('AFRICAN REGION', inplace=True)
# Round numerical columns to 4 decimal places
region_mean_analysis.iloc[:, 1:] = region_mean_analysis.iloc[:, 1:].round(4)
# =============================================================================
# ***************SAVE REGIONAL ANALYSIS TO A CSV FILE***********************
# =============================================================================
# Define the output file path for the CSV file
output_csv_file = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "region_mean_analysis_3CH_ETC_DC_OUTLIER_removal+detrended.csv"
# Save the DataFrame to a CSV file
region_mean_analysis.to_csv(output_csv_file, index=False)
print(f"Region mean analysis saved successfully to {output_csv_file}")
# =============================================================================
# *****************OVERALL CONTINENT STATISTICS******************************
# =============================================================================
overall_values = merged_data[[
    "RMSEigs(3ch)", "RMSEvmf3(3ch)", "RMSEera5(3ch)",
    "RMSEigs(etc)", "RMSEvmf3(etc)", "RMSEera5(etc)",
    "R_igs(etc)", "R_vmf3(etc)", "R_era5(etc)",
    "RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)",
    "R(IGSvsERA5)", "R(VMF3vsERA5)"
]].mean()
overall_table = pd.DataFrame({
    'Dataset': ['IGS', 'VMF3', 'ERA5'],
    '3CH RMSE (mm)': [overall_values['RMSEigs(3ch)'], overall_values['RMSEvmf3(3ch)'], overall_values['RMSEera5(3ch)']],
    'ETC RMSE (mm)': [overall_values['RMSEigs(etc)'], overall_values['RMSEvmf3(etc)'], overall_values['RMSEera5(etc)']],
    'ETC R': [overall_values['R_igs(etc)'], overall_values['R_vmf3(etc)'], overall_values['R_era5(etc)']],
    'DC RMSE (mm)': [overall_values['RMSE(IGSvsERA5)'], overall_values['RMSE(VMF3vsERA5)'], np.nan],
    'DC R': [overall_values['R(IGSvsERA5)'], overall_values['R(VMF3vsERA5)'], np.nan]
}).round(4)
overall_table = overall_table.replace({np.nan: '-'}).reset_index(drop=True)
print("\nOverall Continent Statistics:")
print(overall_table.to_string(index=False))
# Save overall statistics to CSV
overall_csv_file = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "overall_statistics_3CH_ETC_DC_OUTLIER_removal+detrended.csv"
overall_table.to_csv(overall_csv_file, index=False)
print(f"Overall statistics saved successfully to {overall_csv_file}")
# =============================================================================
# Create Subplots for Regional RMSE and Correlation Coefficient Plots
# =============================================================================
fig, axs = plt.subplots(2, 1, figsize=(26, 20), dpi=1000)

# Define color mapping to ensure consistency across panels
colors = {
    'IGS_3CH': '#1f77b4',      # dark blue
    'IGS_ETC': '#87CEEB',      # light blue
    'IGS_DC': '#2ca02c',       # green
    'VMF3_3CH': '#d62728',     # red
    'VMF3_ETC': '#ff7f0e',     # orange
    'VMF3_DC': '#9467bd',      # purple
    'ERA5_3CH': '#8c564b',     # brown
    'ERA5_ETC': '#e377c2'      # pink
}

# =============================================================================
# Regional RMSE Barplot (Top Subplot)
# =============================================================================
rmse_columns_grouped = [
    "RMSEigs(3ch)", "RMSEigs(etc)", "RMSE(IGSvsERA5)",
    "RMSEvmf3(3ch)", "RMSEvmf3(etc)", "RMSE(VMF3vsERA5)",
    "RMSEera5(3ch)", "RMSEera5(etc)"
]
colors_top = [
    colors['IGS_3CH'], colors['IGS_ETC'], colors['IGS_DC'],
    colors['VMF3_3CH'], colors['VMF3_ETC'], colors['VMF3_DC'],
    colors['ERA5_3CH'], colors['ERA5_ETC']
]
mean_rmse = region_mean_analysis.set_index('AFRICAN REGION')[rmse_columns_grouped]
ax_rmse = mean_rmse.plot(
    kind='bar', color=colors_top, edgecolor='black', ax=axs[0]
)
# Formatting & Configuring top subplot
axs[0].legend(
    labels=[
        "IGS (3CH)", "IGS (ETC)", "IGS (DC)",
        "VMF3 (3CH)", "VMF3 (ETC)", "VMF3 (DC)",
        "ERA5 (3CH)", "ERA5 (ETC)"
    ],
    title="Dataset and Method", fontsize=22, title_fontsize=24, loc='upper right', frameon=True, ncol=2
)
axs[0].set_xlabel('') # Remove x-axis label for top plot
axs[0].set_ylabel('Mean RMSE (mm)', fontsize=30, fontweight='bold')
axs[0].set_xticks(ax_rmse.get_xticks())
axs[0].tick_params(axis='x', labelbottom=False, length=20, color='black') # Ensure x-tick markers remain
axs[0].tick_params(axis='y', labelsize=24)
for label in axs[0].get_yticklabels():
    label.set_fontweight('bold')
axs[0].grid(axis='y', linestyle='--', alpha=0.7)
# =============================================================================
# Adjust axes to extend and contain data labels
# =============================================================================
axs[0].set_ylim(0, axs[0].get_ylim()[1] + 0.5)
# Make the axes (horizontal and vertical) black and bold
axs[0].spines["top"].set_color("black")
axs[0].spines["bottom"].set_color("black")
axs[0].spines["left"].set_color("black")
axs[0].spines["right"].set_color("black")
axs[0].spines["top"].set_linewidth(2)
axs[0].spines["bottom"].set_linewidth(2)
axs[0].spines["left"].set_linewidth(2)
axs[0].spines["right"].set_linewidth(2)

# Overlay data labels for RMSE
for container in ax_rmse.containers:
    for i, bar in enumerate(container):
        try:
            height = bar.get_height()
            if not pd.isna(height) and height > 0:
                axs[0].text(
                    bar.get_x() + bar.get_width() / 2, height + 0.05,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=26, weight='bold', rotation=90
                )
        except AttributeError:
            print(f"Skipping bar {i} due to AttributeError")
            continue
# =============================================================================
# Regional Correlation Coefficient Barplot (Bottom Subplot)
# =============================================================================
correlation_columns_grouped = [
    "R_igs(etc)", "R(IGSvsERA5)",
    "R_vmf3(etc)", "R(VMF3vsERA5)",
    "R_era5(etc)"
]
colors_bottom = [
    colors['IGS_ETC'], colors['IGS_DC'],
    colors['VMF3_ETC'], colors['VMF3_DC'],
    colors['ERA5_ETC']
]
mean_corr = region_mean_analysis.set_index('AFRICAN REGION')[correlation_columns_grouped]
ax_corr = mean_corr.plot(
    kind='bar', color=colors_bottom, edgecolor='black', ax=axs[1]
)
axs[1].legend(
    loc='lower right', # Set legend location to bottom right
    labels=[
        "IGS (ETC)", "IGS (DC)",
        "VMF3 (ETC)", "VMF3 (DC)",
        "ERA5 (ETC)"
    ],
    title="Dataset and Method", fontsize=22, title_fontsize=24, frameon=True, ncol=2
)
axs[1].set_xlabel('African Region', fontsize=34, labelpad=22, fontweight='bold')# Add padding to separate label from x-tick labels
axs[1].set_ylabel('Mean Correlation Coefficient (R)', fontsize=30, fontweight='bold')
axs[1].tick_params(axis='x', rotation=0, labelsize=34, length=20, color='black')
for label in axs[1].get_xticklabels():
    label.set_fontweight('bold')
axs[1].tick_params(axis='y', labelsize=24)
for label in axs[1].get_yticklabels():
    label.set_fontweight('bold')
axs[1].grid(axis='y', linestyle='--', alpha=0.7)
# =============================================================================
# Adjust axes to extend and contain data labels
# =============================================================================
axs[1].set_ylim(0.5, axs[1].get_ylim()[1] + 0.2)
# =============================================================================
# # Make the axes (horizontal and vertical) black and bold
# =============================================================================
axs[1].spines["top"].set_color("black")
axs[1].spines["bottom"].set_color("black")
axs[1].spines["left"].set_color("black")
axs[1].spines["right"].set_color("black")
axs[1].spines["top"].set_linewidth(3)
axs[1].spines["bottom"].set_linewidth(3)
axs[1].spines["left"].set_linewidth(3)
axs[1].spines["right"].set_linewidth(3)
# Overlay data labels for Correlation
for container in ax_corr.containers:
    for i, bar in enumerate(container):
        try:
            height = bar.get_height()
            if not pd.isna(height) and height > 0:
                axs[1].text(
                    bar.get_x() + bar.get_width() / 2, height + 0.01,
                    f'{height:.4f}', ha='center', va='bottom', fontsize=24, weight='bold', rotation=90
                )
        except AttributeError:
            print(f"Skipping bar {i} due to AttributeError")
            continue
# Tight layout for better spacing
plt.tight_layout()
# =============================================================================
# Save the plot as a high-resolution image file
# =============================================================================
# output_file_path= (
# 'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/'
# 'DATA ANALYTICs/3CH analysis/FIGs_3ch_etc_dc_summary/'
# 'BARplot_regional_rmse_cc_3CH_ETC_DC115.png'
# )
output_file_path = REPO_ROOT / "Figures" / "BARplot_regional_rmse_cc_3CH_ETC_DC_preprocessed.png"
plt.savefig(output_file_path, format='png', dpi=1000, bbox_inches='tight')
print(f"Plot saved successfully to {output_file_path}")
# Display the figure
plt.show()
# Close the figure after saving
plt.close()
