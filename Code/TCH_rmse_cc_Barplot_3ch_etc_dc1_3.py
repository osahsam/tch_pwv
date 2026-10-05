# =============================================================================
# 1. Import Required Libraries
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]


# =============================================================================
# 2. Load the Excel file and parse the first sheet
# =============================================================================
file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"
df = pd.read_excel(file_path, sheet_name='Sheet1')

# Display the first few rows to confirm structure
print(df.head())

# =============================================================================
# 3. Extract necessary columns for plotting
# =============================================================================
stations = df['STN']

# Define a dictionary of (label -> (Series, color, x_offset))
rmse_colors = {
    'IGS (3CH)':  '#1f77b4', 
    'IGS (ETC)':  '#aec7e8',
    'IGS (DC)':   '#ff7f0e',
    'VMF3 (3CH)': '#2ca02c',
    'VMF3 (ETC)': '#98df8a',
    'VMF3 (DC)':  '#d62728',
    'ERA5 (3CH)': '#9467bd',
    'ERA5 (ETC)': '#c5b0d5'
}

rmse_data_dict = [
    ("IGS (3CH)",  df['RMSEigs(3ch)'],   rmse_colors['IGS (3CH)'],  -1.5),
    ("IGS (ETC)",  df['RMSEigs(etc)'],   rmse_colors['IGS (ETC)'],  -0.5),
    ("IGS (DC)",   df['RMSE(IGSvsERA5)'],rmse_colors['IGS (DC)'],    0.5),
    ("VMF3 (3CH)", df['RMSEvmf3(3ch)'],  rmse_colors['VMF3 (3CH)'],  1.5),
    ("VMF3 (ETC)", df['RMSEvmf3(etc)'],  rmse_colors['VMF3 (ETC)'],  2.5),
    ("VMF3 (DC)",  df['RMSE(VMF3vsERA5)'], rmse_colors['VMF3 (DC)'], 3.5),
    ("ERA5 (3CH)", df['RMSEera5(3ch)'],  rmse_colors['ERA5 (3CH)'],  4.5),
    ("ERA5 (ETC)", df['RMSEera5(etc)'],  rmse_colors['ERA5 (ETC)'],  5.5),
]

# Correlation coefficients
etc_igs = df['R_igs(etc)']
etc_era5 = df['R_era5(etc)']
etc_vmf3 = df['R_vmf3(etc)']
dc_igs_vs_era5 = df['R(IGSvsERA5)']
dc_vmf3_vs_era5 = df['R(VMF3vsERA5)']

# =============================================================================
# 4. Create Subplots for RMSE and Correlation Coefficient (R)
# =============================================================================
fig, axs = plt.subplots(2, 1, figsize=(24, 16), dpi=1000)

# =============================================================================
# 4.1 RMSE Plot (Top Subplot)
# =============================================================================

#Define Bar width and spacing
bar_width = 0.15
spacing = 0.5

# Positions for each station
x_positions = [i * (1 + spacing) for i in range(len(stations))]

# Define a dictionary of (label -> (Series, color, x_offset))
rmse_colors = {
    'IGS (3CH)':  '#1f77b4', 
    'IGS (ETC)':  '#aec7e8',
    'IGS (DC)':   '#ff7f0e',
    'VMF3 (3CH)': '#2ca02c',
    'VMF3 (ETC)': '#98df8a',
    'VMF3 (DC)':  '#d62728',
    'ERA5 (3CH)': '#9467bd',
    'ERA5 (ETC)': '#c5b0d5'
}

# Calculate average values for each dataset
avg_values = {
    label: data.mean() for (label, data, _, _) in 
    [(item[0], item[1], item[2], item[3]) for item in rmse_data_dict]
}


# Plot each bar group
for i, x_center in enumerate(x_positions):
    for idx, (label, series, color, offset) in enumerate(rmse_data_dict):
        # If the data is valid, plot it
        value = series.iloc[i]  # get the i-th station's value
        # If there's a chance of leftover NaN, handle it:
        if pd.notna(value):
            axs[0].bar(
                x_center + offset * bar_width,  # shift bar
                value,
                bar_width,
                color=color,
                label=label if i == 0 else ""  # label only once
            )

# Plot & Highlight average RMSE values with dashed lines
for label, avg_val in avg_values.items():
    axs[0].axhline(
        avg_val, linestyle='--', linewidth=2.5,
        label=f'Average {label}: {avg_val:.2f}',
        alpha=0.7, color=rmse_colors[label]
    )

# Formatting & Configuring top subplot
#axs[0].set_title('RMSE by Method', fontsize=16, fontweight='bold')
#axs[0].set_xlabel('Stations', fontsize=12, fontweight='bold')
axs[0].set_ylabel('RMSE (mm)', fontsize=26, labelpad=22, fontweight='bold')
axs[0].set_xticks(x_positions)
axs[0].set_xticklabels(stations, rotation=90, fontsize=24, fontweight='bold')
axs[0].tick_params(axis='x', labelbottom=False)  # Hide x-axis labels here
axs[0].tick_params(axis='y', labelsize=24)

for tick in axs[0].get_yticklabels():
    tick.set_fontweight('bold')

axs[0].legend(
    title='Dataset, Method, and Averages',
    fontsize=16, title_fontsize=20, loc='upper right'
)

# Make the axes (horizontal and vertical) black and bold
axs[0].spines["top"].set_color("black")
axs[0].spines["bottom"].set_color("black")
axs[0].spines["left"].set_color("black")
axs[0].spines["right"].set_color("black")
axs[0].spines["top"].set_linewidth(3)
axs[0].spines["bottom"].set_linewidth(3)
axs[0].spines["left"].set_linewidth(3)
axs[0].spines["right"].set_linewidth(3)


#axs[0].grid(axis='y', linestyle='--', alpha=0.7)


# =============================================================================
# 4.2 Correlation Coefficient (R) Plot (Bottom Subplot)
# =============================================================================
grouped_data = {
    'IGS (ETC)':         etc_igs,
    'IGS (DC)':    dc_igs_vs_era5,
    'VMF3 (ETC)':        etc_vmf3,
    'VMF3 (DC)':   dc_vmf3_vs_era5,
    'ERA5 (ETC)':        etc_era5,
}

# Separate color palette for correlations to avoid overwriting the RMSE palette
corr_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

# Create a range for the correlation bars
x_corr = range(len(stations))
width_corr = 0.15

# We start offset from the center so the bars don’t overlap
offset = -2
for (label, data), color in zip(grouped_data.items(), corr_colors):
    axs[1].bar(
        [i + offset * width_corr for i in x_corr],
        data,
        width_corr,
        label=label,
        color=color
    )
    offset += 1

# Configure bottom subplot
axs[1].set_xlabel('Stations', fontsize=30, labelpad=22, fontweight='bold')
axs[1].set_ylabel('Correlation Coefficient (R)', fontsize=26, labelpad=22, fontweight='bold')
axs[1].set_xticks(list(x_corr))
axs[1].set_xticklabels(stations, rotation=90, fontsize=24, fontweight='bold')
axs[1].tick_params(axis='y', labelsize=24, labelcolor='black', direction='in', grid_alpha=0.5)

for label in axs[1].get_yticklabels():
    label.set_fontweight('bold')

# Add a horizontal line at R=1 for perfect correlation
axs[1].axhline(
    y=1, color='red', linestyle='--', linewidth=2.5,
    label='Perfect Correlation (R=1)'
)

# Add a horizontal line at R=0.9 for strong correlation
axs[1].axhline(
    y=0.95, color='blue', linestyle='--', linewidth=2.5,
    label='Strong Correlation (R=0.95)'
)

# Add a horizontal line at R=0.9 for strong correlation
axs[1].axhline(
    y=0.9, color='green', linestyle='--', linewidth=2.5,
    label='Strong Correlation (R=0.9)'
)


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

# Add gridlines
#axs[1].grid(axis='y', linestyle='--', alpha=0.7)

# Correlation legend
axs[1].legend(
    fontsize=16, loc='upper right',
    title='Dataset and Method',
    title_fontsize=20
)

# =============================================================================
# 5. Layout, Show, and Save
# =============================================================================
plt.tight_layout()


output_file = REPO_ROOT / "Figures" / "Barplot_rmse_cc_3CH_ETC_DC.png"
fig.savefig(output_file, dpi=1000, bbox_inches='tight')

print(f"Plot saved successfully to {output_file}")

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()


