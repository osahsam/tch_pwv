from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]


# =============================================================================
# Load the uploaded Excel file to analyze the data
# =============================================================================
file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "STATISTICAL analysis (Africa)_OUTLIER_removal+detrended.xlsx"
data = pd.ExcelFile(file_path)

# Load the data from the first sheet
df = data.parse('Sheet1')

# Display the first few rows to understand the structure
print(df.head())

# =============================================================================
# **********************************BARPLOTS
# =============================================================================

# Select relevant columns for the bar graph
stations = df['STN']
rmse_3ch = df[['RMSEigs(3ch)', 'RMSEera5(3ch)', 'RMSEvmf3(3ch)']]
rmse_etc = df[['RMSEigs(etc)', 'RMSEera5(etc)', 'RMSEvmf3(etc)']]

# =============================================================================
# PLOT 3CH & ETC RMSEs on A SINGLE  SUBPLOTS
# =============================================================================
#(1.0).
# High-resolution bar graph with bold fonts, including y-axis tick values
fig, ax = plt.subplots(figsize=(24, 12), dpi=1000)

# Bar width and positions with space between stations
bar_width = 0.15
spacing = 0.5
x = [i * (1 + spacing) for i in range(len(stations))]

# Plot bars for each dataset and method side by side with bright colors and space between stations
ax.bar([pos - 1.5 * bar_width for pos in x], rmse_3ch['RMSEigs(3ch)'], bar_width, label='IGS (3CH)', color='#007acc')
ax.bar([pos - 0.5 * bar_width for pos in x], rmse_etc['RMSEigs(etc)'], bar_width, label='IGS (ETC)', color='#00bfff')

ax.bar([pos + 0.5 * bar_width for pos in x], rmse_3ch['RMSEera5(3ch)'], bar_width, label='ERA5 (3CH)', color='#ffa500')
ax.bar([pos + 1.5 * bar_width for pos in x], rmse_etc['RMSEera5(etc)'], bar_width, label='ERA5 (ETC)', color='#ffd700')

ax.bar([pos + 2.5 * bar_width for pos in x], rmse_3ch['RMSEvmf3(3ch)'], bar_width, label='VMF3 (3CH)', color='#32cd32')
ax.bar([pos + 3.5 * bar_width for pos in x], rmse_etc['RMSEvmf3(etc)'], bar_width, label='VMF3 (ETC)', color='#00ff00')

# Configure the plot for readability
#ax.set_title('Side-by-Side 3CH and ETC Analysis', fontsize=18, fontweight='bold')
ax.set_xlabel('Stations', fontsize=30, labelpad=22, fontweight='bold')
ax.set_ylabel('RMSE (mm)', fontsize=30, labelpad=20, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(stations, rotation=90, fontsize=20, fontweight='bold')
ax.tick_params(axis='y', labelsize=24)
for tick in ax.get_yticklabels():
    tick.set_fontweight('bold')
ax.legend(title='Dataset and Method', fontsize=20, title_fontsize=20, loc='upper right')


# =============================================================================
# Make the axes (horizontal and vertical) black and bold
# =============================================================================
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(3)
ax.spines["bottom"].set_linewidth(3)
ax.spines["left"].set_linewidth(3)
ax.spines["right"].set_linewidth(3)

plt.tight_layout()

# =============================================================================
# Save the graph to a high-resolution image file (300 dpi)
# =============================================================================
output_file = REPO_ROOT / "Figures" / "Barplot_rmse_3CH_ETC.png"

fig.savefig(output_file, dpi=1000, bbox_inches='tight')

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()

# =============================================================================
# (1.1)High-resolution bar graph with bold fonts, increased bar width, and more space between stations
# =============================================================================

fig, ax = plt.subplots(figsize=(24, 12), dpi=1000)

# Bar width and positions with extra space between stations
bar_width = 0.25  # Increased bar width
spacing = 1.0  # Increased spacing between stations
x = [i * (1 + spacing) for i in range(len(stations))]

# Plot bars for each dataset and method side by side with bright colors and space between stations
ax.bar([pos - 1.5 * bar_width for pos in x], rmse_3ch['RMSEigs(3ch)'], bar_width, label='IGS (3CH)', color='#007acc')
ax.bar([pos - 0.5 * bar_width for pos in x], rmse_etc['RMSEigs(etc)'], bar_width, label='IGS (ETC)', color='#00bfff')

ax.bar([pos + 0.5 * bar_width for pos in x], rmse_3ch['RMSEera5(3ch)'], bar_width, label='ERA5 (3CH)', color='#ffa500')
ax.bar([pos + 1.5 * bar_width for pos in x], rmse_etc['RMSEera5(etc)'], bar_width, label='ERA5 (ETC)', color='#ffd700')

ax.bar([pos + 2.5 * bar_width for pos in x], rmse_3ch['RMSEvmf3(3ch)'], bar_width, label='VMF3 (3CH)', color='#32cd32')
ax.bar([pos + 3.5 * bar_width for pos in x], rmse_etc['RMSEvmf3(etc)'], bar_width, label='VMF3 (ETC)', color='#00ff00')

# Configure the plot for readability
#ax.set_title('Side-by-Side 3CH and ETC Analysis with Extra Space Between Stations', fontsize=18, fontweight='bold')
ax.set_xlabel('Stations', fontsize=30, labelpad=22, fontweight='bold')
ax.set_ylabel('RMSE (mm)', fontsize=30, labelpad=20, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(stations, rotation=90, fontsize=20, fontweight='bold')
ax.tick_params(axis='y', labelsize=24)
for tick in ax.get_yticklabels():
    tick.set_fontweight('bold')
ax.legend(title='Dataset and Method', fontsize=20, title_fontsize=20, loc='upper right')

# =============================================================================
# Make the axes (horizontal and vertical) black and bold
# =============================================================================
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(3)
ax.spines["bottom"].set_linewidth(3)
ax.spines["left"].set_linewidth(3)
ax.spines["right"].set_linewidth(3)

plt.tight_layout()

# =============================================================================
# Save the graph to a high-resolution image file (300 dpi)
# =============================================================================
output_file = REPO_ROOT / "Figures" / "Barplot_rmse_3CH_ETC.png"

fig.savefig(output_file, dpi=1000, bbox_inches='tight')

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()

# =============================================================================
# (1.2): IMPROVEMENTS:
#     a) REVISION OF BAR COLOURS: Using a consistent, visually appealing color palette, 
#        such as a gradient or theme, to differentiate datasets clearly.
#     b) Adjust the y-axis range to focus more closely on the range of RMSE values, ensuring 
#        better utilization of graph space.
# =============================================================================
# High-resolution bar graph with enhanced colors and adjusted y-axis scale
fig, ax = plt.subplots(figsize=(24, 12), dpi=1000)

# Bar width and positions with space between stations
bar_width = 0.25  # Increased bar width
spacing = 2.0  # Maintain space between station groups
x = [i * spacing for i in range(len(stations))]

# Plot bars for each dataset and method side by side with enhanced color palette
ax.bar([pos - 1.5 * bar_width for pos in x], rmse_3ch['RMSEigs(3ch)'], bar_width, label='IGS (3CH)', color='#004c99')
ax.bar([pos - 0.5 * bar_width for pos in x], rmse_etc['RMSEigs(etc)'], bar_width, label='IGS (ETC)', color='#80bfff')

ax.bar([pos + 0.5 * bar_width for pos in x], rmse_3ch['RMSEera5(3ch)'], bar_width, label='ERA5 (3CH)', color='#cc6600')
ax.bar([pos + 1.5 * bar_width for pos in x], rmse_etc['RMSEera5(etc)'], bar_width, label='ERA5 (ETC)', color='#ffcc80')

ax.bar([pos + 2.5 * bar_width for pos in x], rmse_3ch['RMSEvmf3(3ch)'], bar_width, label='VMF3 (3CH)', color='#006600')
ax.bar([pos + 3.5 * bar_width for pos in x], rmse_etc['RMSEvmf3(etc)'], bar_width, label='VMF3 (ETC)', color='#99ff99')

# Configure the plot for readability
#ax.set_title('Side-by-Side 3CH and ETC Analysis with Enhanced Colors and Adjusted Y-Axis', fontsize=18, fontweight='bold')
ax.set_xlabel('Stations', fontsize=30, labelpad=22, fontweight='bold')
ax.set_ylabel('RMSE (mm)', fontsize=30, labelpad=20, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(stations, rotation=90, fontsize=20, fontweight='bold')

# Adjust the y-axis scale to better focus on the range of RMSE values
ax.set_ylim(0, max(df[['RMSEigs(3ch)', 'RMSEera5(3ch)', 'RMSEvmf3(3ch)', 'RMSEigs(etc)', 'RMSEera5(etc)', 'RMSEvmf3(etc)']].max()) + 0.5)

ax.tick_params(axis='y', labelsize=24)
for tick in ax.get_yticklabels():
    tick.set_fontweight('bold')
ax.legend(title='Dataset and Method', fontsize=20, title_fontsize=20, loc='upper right')

# =============================================================================
# Make the axes (horizontal and vertical) black and bold
# =============================================================================
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(3)
ax.spines["bottom"].set_linewidth(3)
ax.spines["left"].set_linewidth(3)
ax.spines["right"].set_linewidth(3)

plt.tight_layout()

# =============================================================================
# Save the graph to a high-resolution image file (300 dpi)
# =============================================================================
output_file = REPO_ROOT / "Figures" / "Barplot_rmse_3CH_ETC.png"

fig.savefig(output_file, dpi=1000, bbox_inches='tight')

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()

# =============================================================================
# (2.0)Computing the difference b/n the 3CH and ETC methods for each datasets and plotting 
# the difference to enhance comparison
# =============================================================================

# Calculate the differences between 3CH and ETC RMSE values for each dataset
df['Diff_IGS'] = df['RMSEigs(3ch)'] - df['RMSEigs(etc)']
df['Diff_ERA5'] = df['RMSEera5(3ch)'] - df['RMSEera5(etc)']
df['Diff_VMF3'] = df['RMSEvmf3(3ch)'] - df['RMSEvmf3(etc)']

# Prepare the data for plotting
stations = df['STN']
differences = df[['Diff_IGS', 'Diff_ERA5', 'Diff_VMF3']]

# Plotting the differences
fig, ax = plt.subplots(figsize=(24, 12), dpi=1000)

# Bar width and positions
bar_width = 0.25
x = range(len(stations))

# Plot differences for each dataset
ax.bar([pos - bar_width for pos in x], differences['Diff_IGS'], bar_width, label='IGS Difference', color='#1f77b4')
ax.bar(x, differences['Diff_ERA5'], bar_width, label='ERA5 Difference', color='#ff7f0e')
ax.bar([pos + bar_width for pos in x], differences['Diff_VMF3'], bar_width, label='VMF3 Difference', color='#2ca02c')

# Configure the plot
#ax.set_title('Difference Between 3CH and ETC RMSE Values for Each Dataset', fontsize=18, fontweight='bold')
ax.set_xlabel('Stations', fontsize=30, labelpad=22, fontweight='bold')
ax.set_ylabel('Difference (mm)', fontsize=30, labelpad=20, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(stations, rotation=90, fontsize=20, fontweight='bold')
ax.tick_params(axis='y', labelsize=24)
for tick in ax.get_yticklabels():
    tick.set_fontweight('bold')
ax.axhline(0, color='black', linewidth=2.5, linestyle='--')
ax.legend(title='Dataset', fontsize=20, title_fontsize=20, loc='upper right')

# =============================================================================
# Make the axes (horizontal and vertical) black and bold
# =============================================================================
ax.spines["top"].set_color("black")
ax.spines["bottom"].set_color("black")
ax.spines["left"].set_color("black")
ax.spines["right"].set_color("black")
ax.spines["top"].set_linewidth(3)
ax.spines["bottom"].set_linewidth(3)
ax.spines["left"].set_linewidth(3)
ax.spines["right"].set_linewidth(3)


plt.tight_layout()

# =============================================================================
# # Save the updated graph
# =============================================================================
output_file_diff_3ch_etc = REPO_ROOT / "Figures" / "Barplot_diff_3CH_ETC.png"
fig.savefig(output_file_diff_3ch_etc, dpi=1000, bbox_inches='tight')

# Display the figure 
plt.show()

# Close the figure after saving
plt.close()


