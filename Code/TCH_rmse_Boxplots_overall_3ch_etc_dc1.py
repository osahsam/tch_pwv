# =============================================================================
# Import Required Libraries
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]


# Load the uploaded Excel file to analyze the data
file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"
data = pd.read_excel(file_path)

# Display the first few rows of the data to understand its structure
print(data.head())


# Compute summary statistics for RMSE and correlation coefficients
summary_stats = data.describe()

# Extract key columns for clarity in analysis
key_columns = [
    "RMSEigs(3ch)", "RMSEera5(3ch)", "RMSEvmf3(3ch)",
    "RMSEigs(etc)", "RMSEera5(etc)", "RMSEvmf3(etc)",
    "R_igs(etc)", "R_era5(etc)", "R_vmf3(etc)",
    "RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)",
    "R(IGSvsERA5)", "R(VMF3vsERA5)"
]

summary_stats_filtered = summary_stats[key_columns]

# Display the summary statistics to the user for detailed insight
print(summary_stats_filtered )

# =============================================================================
# *******************************************PLOTs
# =============================================================================

# =============================================================================
# ********************OVERALL ANALYSIS OVER AFRICA*************************
# =============================================================================

#            =================================
# ***********RMSE Boxplot with Grouped Methods***********
#           ==================================
output_path_rmse_grouped = REPO_ROOT / "Figures" / "RMSE_Boxplot_Grouped.png"
plt.figure(figsize=(16, 10), dpi=1000)

# Updated column order to group by dataset (IGS, VMF3, ERA5)
rmse_columns_grouped = [
    "RMSEigs(3ch)", "RMSEigs(etc)", "RMSE(IGSvsERA5)",
    "RMSEvmf3(3ch)", "RMSEvmf3(etc)", "RMSE(VMF3vsERA5)",
    "RMSEera5(3ch)", "RMSEera5(etc)"
]

# Mapping for renaming columns
column_name_mapping_grouped = {
    "RMSEigs(3ch)": "IGS (3CH)",
    "RMSEigs(etc)": "IGS (ETC)",
    "RMSE(IGSvsERA5)": "IGS (DC)",
    "RMSEvmf3(3ch)": "VMF3 (3CH)",
    "RMSEvmf3(etc)": "VMF3 (ETC)",
    "RMSE(VMF3vsERA5)": "VMF3 (DC)",
    "RMSEera5(3ch)": "ERA5 (3CH)",
    "RMSEera5(etc)": "ERA5 (ETC)"
}

# Grouped labels for x-axis
updated_columns_grouped = [column_name_mapping_grouped[col] for col in rmse_columns_grouped]

boxplot_rmse_grouped = data.boxplot(
    column=rmse_columns_grouped,
    patch_artist=True,
    boxprops=dict(facecolor="lightblue", linewidth=2),
    medianprops=dict(color="red", linewidth=2),
    whiskerprops=dict(linewidth=2),
    capprops=dict(linewidth=2),
    flierprops=dict(marker='o', color='black', alpha=0.5),
    return_type='dict'
)

# Add mean markers explicitly for RMSE
for i, col in enumerate(rmse_columns_grouped, start=1):
    mean_value = np.mean(data[col])
    plt.scatter(i, mean_value, color='blue', marker='D', s=100, label='Mean' if i == 1 else "")
    plt.text(i, mean_value, f'{mean_value:.2f}', fontsize=12, fontweight='bold', ha='center', va='bottom')

# Titles and labels for RMSE
plt.ylabel("RMSE (mm)", fontsize=30, labelpad=22, fontweight='bold')
plt.xticks(ticks=range(1, len(updated_columns_grouped) + 1), labels=updated_columns_grouped, rotation=45, fontsize=24, fontweight='bold')
plt.yticks(fontsize=24, fontweight='bold')
plt.grid(axis='y', linestyle='', alpha=0.7)#Remove y-axis grid lines
plt.grid(axis='x', linestyle='', alpha=0.7) #Remove x-axis grid lines

# =============================================================================
# Increase Grid tick lengths
# =============================================================================
ax = plt.gca()
ax.tick_params(axis='x', length=10, color='black')  # Ensure x-tick markers remain
ax.tick_params(axis='y', length=10, color='black')  # Ensure x-tick markers remain


# Annotate min and max values for RMSE
for i, col in enumerate(rmse_columns_grouped, start=1):
    min_value = data[col].min()
    max_value = data[col].max()
    plt.text(i, min_value, f'Min: {min_value:.2f}', fontsize=12, fontweight='bold', ha='center', va='top')
    plt.text(i, max_value, f'Max: {max_value:.2f}', fontsize=12, fontweight='bold', ha='center', va='bottom')

#plt.legend(fontsize=10, loc='upper right', frameon=False)


# =============================================================================
# # Make the axes (horizontal and vertical) black and bold
# =============================================================================
# Access the current axes and customize spines
ax = plt.gca()
for spine in ax.spines.values():
    spine.set_color("black")
    spine.set_linewidth(2)

# =============================================================================
# # Save the plot as a high-resolution image file
# =============================================================================
output_file_rmse = (
    REPO_ROOT / "Figures" / "BOXplot_rmse_cc_3CH_ETC_DC.png"
)

plt.savefig(output_file_rmse, dpi=1000, bbox_inches='tight')

print(f"Plot saved successfully to {output_file_rmse}")

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()
