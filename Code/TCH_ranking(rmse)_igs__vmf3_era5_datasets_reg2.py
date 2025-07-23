# =============================================================================
# 1. Import Required Libraries
# =============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# 2. Load the Excel file and parse the first sheet
# =============================================================================

# Load the uploaded CSV file for analysis
file_path = 'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/DATA ANALYTICs/3CH analysis/FIGs_3ch_etc_dc_summary/region_mean_analysis_3CH_ETC_DC.csv'
data = pd.read_csv(file_path)

# Display the first few rows to understand its structure
print(data.head())

# Analyzing performance across the regions for ranking

# Calculate the mean RMSE for each dataset and method per region
ranked_data = data[[
    "AFRICAN REGION",
    "RMSEigs(3ch)", "RMSEera5(3ch)", "RMSEvmf3(3ch)",
    "RMSEigs(etc)", "RMSEera5(etc)", "RMSEvmf3(etc)",
    "RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)"
]]

# Calculate rank by region and method
ranked_data["3CH_rank"] = ranked_data[["RMSEigs(3ch)", "RMSEera5(3ch)", "RMSEvmf3(3ch)"]].rank(axis=1).idxmin(axis=1)
ranked_data["ETC_rank"] = ranked_data[["RMSEigs(etc)", "RMSEera5(etc)", "RMSEvmf3(etc)"]].rank(axis=1).idxmin(axis=1)
ranked_data["DC_rank"] = ranked_data[["RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)"]].rank(axis=1).idxmin(axis=1)

# Display the rankings for the regions
print(ranked_data)

# =============================================================================
# 4. Calculate weighted rankings
# =============================================================================
# Define weights for the methods
weights = {"3CH": 0.5, "ETC": 0.5}

# Extract RMSE columns for each method and compute weighted RMSE for each dataset
weighted_rmse = pd.DataFrame()
weighted_rmse["AFRICAN REGION"] = ranked_data["AFRICAN REGION"]

# Compute weighted RMSE for each dataset
datasets = {
    "GNSS": ["RMSEigs(3ch)", "RMSEigs(etc)"],
    "ERA5": ["RMSEera5(3ch)", "RMSEera5(etc)"],
    "VMF3": ["RMSEvmf3(3ch)", "RMSEvmf3(etc)"]
}

for dataset, cols in datasets.items():
    weighted_rmse[dataset] = (
        weights["3CH"] * ranked_data[cols[0]]
        + weights["ETC"] * ranked_data[cols[1]]
    )

# Rank datasets based on weighted RMSE
weighted_rmse["Best Dataset"] = weighted_rmse[["GNSS", "ERA5", "VMF3"]].idxmin(axis=1)

# Display the results
print(weighted_rmse)

# =============================================================================
# (5)*****************************PLOT RANKINGS****************************
# =============================================================================

# Remove rows with NaN values in the weighted_rmse DataFrame
filtered_weighted_rmse = weighted_rmse.dropna(subset=["Best Dataset", "GNSS", "ERA5", "VMF3"])

# Extract only the valid regions
regions = filtered_weighted_rmse["AFRICAN REGION"]
datasets = ["GNSS", "ERA5", "VMF3"]

# =============================================================================
# (5)*****************************PLOT RANKINGS****************************
# =============================================================================

fig, ax = plt.subplots(figsize=(14, 7), dpi=1000)
bar_width = 0.25
x = range(len(regions))

# Assign distinct colors for each dataset
# colors = {
#     "GNSS": "green",
#     "ERA5": "skyblue",
#     "VMF3": "orange"
# }

colors = {
    "GNSS": "#1f77b4",
    "ERA5": "#ff7f0e",
    "VMF3": "#2ca02c"
}

# Plot bars with data labels and highlight the best dataset with an edge color
for i, dataset in enumerate(datasets):
    bars = ax.bar(
        [pos + i * bar_width for pos in x],
        filtered_weighted_rmse[dataset],
        width=bar_width,
        label=dataset,
        color=colors[dataset]
    )
    # Add bold data labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.02,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=15,
            fontweight="bold"  # Bolden the displayed value
        )

# Highlight the best dataset for each region using an edge color
for i, region in enumerate(regions):
    best_dataset = filtered_weighted_rmse.loc[i, "Best Dataset"]
    best_index = datasets.index(best_dataset)
    best_x = i + best_index * bar_width
    ax.bar(
        best_x,
        filtered_weighted_rmse.loc[i, best_dataset],
        width=bar_width,
        color=colors[best_dataset],  # Keep the color
        edgecolor="blue",  # Add a black edge to highlight
        linewidth=3.0  # Thicker edge for emphasis
    )

# Add gridlines for better readability
ax.yaxis.grid(True, linestyle="--", alpha=0.7)

# Add labels and legend
ax.set_xlabel("African Region", fontsize=22,  labelpad=22, fontweight="bold")  # Bolden x-axis label
ax.set_ylabel("Weighted RMSE (mm)", fontsize=22,  labelpad=22, fontweight="bold")  # Bolden y-axis label


# Bolden x and y tick labels, center-align x-axis ticks, and add padding
ax.set_xticks([pos + bar_width for pos in x])  # Center x-ticks under grouped bars
ax.set_xticklabels(
    regions,
    rotation=0,  # Horizontal alignment
    ha="center",  # Center-align labels under ticks
    fontsize=18,
    fontweight="bold"
) 

ax.tick_params(axis="x", pad=10)  # Add padding between x-ticks and labels
ax.tick_params(axis="y", pad=10)  # Add padding between y-ticks and labels
plt.setp(ax.get_yticklabels(), fontsize=20, fontweight="bold")  # Bold y-ticks

# Add legend
ax.legend(title="Dataset", fontsize=16, title_fontsize=24)


# =============================================================================
# Adjust axes to extend and contain data labels
# =============================================================================
ax.set_ylim(0, ax.get_ylim()[1] + 0.1)

# Make the axes (horizontal and vertical) black and bold
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)
ax.spines["left"].set_linewidth(2)
ax.spines["right"].set_linewidth(2)

# Tight layout for better spacing
plt.tight_layout()

# =============================================================================
# Save the plot as a high-resolution image file
# =============================================================================
output_file_path= (
    'D:/DATA/ATMOSPHERE data/TROPOSPHERE data/'
    'DATA ANALYTICs/3CH analysis/FIGs_3ch_etc_dc_summary/'
    'Ranking_igs_vmf3_era5regional_rmse_3CH_ETC_6.png'
)

plt.savefig(output_file_path, format='png', dpi=1000, bbox_inches='tight')

print(f"Plot saved successfully to {output_file_path}")

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()                                 
