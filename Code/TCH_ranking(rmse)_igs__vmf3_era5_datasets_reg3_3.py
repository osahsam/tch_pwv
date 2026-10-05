# =============================================================================
# Enhanced Regional PWV Dataset Ranking Analysis
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# =============================================================================
# 1. Load and Prepare Data
# =============================================================================
from scipy.stats import wilcoxon

REPO_ROOT = Path(__file__).resolve().parents[1]


file_path = REPO_ROOT / "Analysis" / "Results_3CH, ETC & DC" / "region_mean_analysis_3CH_ETC_DC_OUTLIER_removal+detrended.csv"

data = pd.read_csv(file_path)
print("Dataset Overview:")
print(data.head())
print("\n" + "="*80 + "\n")

# =============================================================================
# 2. Improved Weighted Ranking Method with Sensitivity Analysis
# =============================================================================
"""
RANKING METHODOLOGY:
--------------------
This analysis uses a composite scoring approach combining two independent 
PWV retrieval methods (3CH and ETC) to evaluate three datasets (GNSS, ERA5, VMF3).

Weighting Scheme:
- 3CH method: 50% (weight = 0.5)
- ETC method: 50% (weight = 0.5)

The composite RMSE for each dataset is calculated as:
    Composite_RMSE = w₁ × RMSE_3CH + w₂ × RMSE_ETC
    where w₁ = w₂ = 0.5

Normalization (optional): To account for different scales, normalized RMSE can be used:
    Normalized_RMSE = (RMSE - min_RMSE) / (max_RMSE - min_RMSE)

Lower composite RMSE indicates better performance across both methods.
The dataset with minimum composite RMSE is ranked as "Best" for each region.
"""

# Define weights with clear documentation
weights = {
    "3CH": 0.5,   # Three-Channel method weight
    "ETC": 0.5    # Effective Temperature Constant method weight
}

# Option to use normalized scoring (set to False for absolute RMSE)
USE_NORMALIZED_SCORES = False

print("WEIGHTED RANKING METHODOLOGY")
print("="*80)
print(f"Method Weights: 3CH = {weights['3CH']}, ETC = {weights['ETC']}")
print(f"Formula: Composite_RMSE = {weights['3CH']}×RMSE_3CH + {weights['ETC']}×RMSE_ETC")
print(f"Normalization: {'Enabled' if USE_NORMALIZED_SCORES else 'Disabled (using absolute RMSE values)'}")
print("\n" + "="*80 + "\n")

# Extract relevant columns
ranking_data = data[[
    "AFRICAN REGION",
    "RMSEigs(3ch)", "RMSEera5(3ch)", "RMSEvmf3(3ch)",
    "RMSEigs(etc)", "RMSEera5(etc)", "RMSEvmf3(etc)",
    "RMSE(IGSvsERA5)", "RMSE(VMF3vsERA5)"
]].copy()

# =============================================================================
# 3. Calculate Composite RMSE Scores with Optional Normalization
# =============================================================================
datasets_mapping = {
    "GNSS": ["RMSEigs(3ch)", "RMSEigs(etc)"],
    "ERA5": ["RMSEera5(3ch)", "RMSEera5(etc)"],
    "VMF3": ["RMSEvmf3(3ch)", "RMSEvmf3(etc)"]
}

composite_scores = pd.DataFrame()
composite_scores["Region"] = ranking_data["AFRICAN REGION"]

# Helper function for normalization
def normalize_column(series):
    """Min-max normalization to [0, 1] range"""
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series(0, index=series.index)
    return (series - min_val) / (max_val - min_val)

# Calculate composite RMSE for each dataset
for dataset, [col_3ch, col_etc] in datasets_mapping.items():
    if USE_NORMALIZED_SCORES:
        # Normalize each method separately
        norm_3ch = normalize_column(ranking_data[col_3ch])
        norm_etc = normalize_column(ranking_data[col_etc])
        composite_scores[f"{dataset}_Composite"] = (
            weights["3CH"] * norm_3ch + weights["ETC"] * norm_etc
        )
    else:
        # Use absolute RMSE values
        composite_scores[f"{dataset}_Composite"] = (
            weights["3CH"] * ranking_data[col_3ch] + 
            weights["ETC"] * ranking_data[col_etc]
        )
    
    # Store individual method contributions
    composite_scores[f"{dataset}_3CH"] = ranking_data[col_3ch]
    composite_scores[f"{dataset}_ETC"] = ranking_data[col_etc]

# Determine best dataset per region
composite_scores["Best_Dataset"] = composite_scores[
    ["GNSS_Composite", "ERA5_Composite", "VMF3_Composite"]
].idxmin(axis=1).str.replace("_Composite", "")

# Calculate ranking (1 = best, 3 = worst)
for dataset in ["GNSS", "ERA5", "VMF3"]:
    composite_scores[f"{dataset}_Rank"] = composite_scores[
        ["GNSS_Composite", "ERA5_Composite", "VMF3_Composite"]
    ].rank(axis=1)[f"{dataset}_Composite"]

# Calculate performance margins (difference from best)
for idx in composite_scores.index:
    best_score = composite_scores.loc[idx, ["GNSS_Composite", "ERA5_Composite", "VMF3_Composite"]].min()
    for dataset in ["GNSS", "ERA5", "VMF3"]:
        composite_scores.loc[idx, f"{dataset}_Margin"] = composite_scores.loc[idx, f"{dataset}_Composite"] - best_score

# =============================================================================
# 4. Statistical Summary and Significance Testing
# =============================================================================
print("COMPOSITE RMSE SCORES BY REGION")
print("="*80)
display_cols = ["Region", "GNSS_Composite", "ERA5_Composite", "VMF3_Composite", 
                "Best_Dataset"]
print(composite_scores[display_cols].to_string(index=False))
print("\n" + "="*80 + "\n")

# Overall statistics
print("OVERALL PERFORMANCE STATISTICS")
print("="*80)
overall_stats = {}
for dataset in ["GNSS", "ERA5", "VMF3"]:
    scores = composite_scores[f"{dataset}_Composite"].dropna()
    overall_stats[dataset] = {
        'mean': scores.mean(),
        'std': scores.std(),
        'min': scores.min(),
        'max': scores.max(),
        'median': scores.median(),
        'wins': (composite_scores['Best_Dataset'] == dataset).sum()
    }
    print(f"\n{dataset}:")
    print(f"  Mean RMSE:   {overall_stats[dataset]['mean']:.3f} mm")
    print(f"  Median RMSE: {overall_stats[dataset]['median']:.3f} mm")
    print(f"  Std Dev:     {overall_stats[dataset]['std']:.3f} mm")
    print(f"  Min RMSE:    {overall_stats[dataset]['min']:.3f} mm")
    print(f"  Max RMSE:    {overall_stats[dataset]['max']:.3f} mm")
    print(f"  Wins:        {overall_stats[dataset]['wins']} regions ({overall_stats[dataset]['wins']/len(composite_scores.dropna())*100:.1f}%)")

# Pairwise statistical tests (Wilcoxon signed-rank test for paired samples)
print("\n" + "="*80)
print("PAIRWISE STATISTICAL SIGNIFICANCE (Wilcoxon Signed-Rank Test)")
print("="*80)

pairs = [("GNSS", "ERA5"), ("GNSS", "VMF3"), ("ERA5", "VMF3")]
for d1, d2 in pairs:
    data1 = composite_scores[f"{d1}_Composite"].dropna()
    data2 = composite_scores[f"{d2}_Composite"].dropna()
    
    # Ensure same length for paired test
    common_idx = data1.index.intersection(data2.index)
    if len(common_idx) > 0:
        stat, p_value = wilcoxon(data1[common_idx], data2[common_idx])
        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
        print(f"{d1} vs {d2}: p-value = {p_value:.4f} {significance}")
        print(f"  Mean difference: {data1[common_idx].mean() - data2[common_idx].mean():.3f} mm")

print("\nSignificance levels: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
print("\n" + "="*80 + "\n")

# Ranking consistency analysis
print("RANKING CONSISTENCY ANALYSIS")
print("="*80)
for dataset in ["GNSS", "ERA5", "VMF3"]:
    ranks = composite_scores[f"{dataset}_Rank"].dropna()
    print(f"\n{dataset} Ranking Distribution:")
    print(f"  1st place: {(ranks == 1).sum()} times ({(ranks == 1).sum()/len(ranks)*100:.1f}%)")
    print(f"  2nd place: {(ranks == 2).sum()} times ({(ranks == 2).sum()/len(ranks)*100:.1f}%)")
    print(f"  3rd place: {(ranks == 3).sum()} times ({(ranks == 3).sum()/len(ranks)*100:.1f}%)")
    print(f"  Average rank: {ranks.mean():.2f}")

print("\n" + "="*80 + "\n")

# =============================================================================
# 5. Enhanced Visualization with Multiple Panels
# =============================================================================
# Remove rows with missing data
plot_data = composite_scores.dropna(
    subset=["Best_Dataset", "GNSS_Composite", "ERA5_Composite", "VMF3_Composite"]
)

regions = plot_data["Region"].values
datasets = ["GNSS", "ERA5", "VMF3"]

# Enhanced color scheme with better contrast
colors = {
    "GNSS": "#2E86AB",    # Deep blue
    "ERA5": "#E63946",    # Red
    "VMF3": "#06A77D"     # Green
}

colors = {
"GNSS": "#1f77b4", # shade of blue
"ERA5": "#ff7f0e", # shade of orange
"VMF3": "#2ca02c" # shade of green
}

# Create figure with three panels
fig = plt.figure(figsize=(18, 14), dpi=300)
gs = fig.add_gridspec(3, 2, height_ratios=[3, 1.2, 1.2], width_ratios=[3, 1], 
                      hspace=0.35, wspace=0.3)

ax1 = fig.add_subplot(gs[0, :])  # Main plot (top, full width)
ax2 = fig.add_subplot(gs[1, 0])  # Regional wins (bottom left)
ax3 = fig.add_subplot(gs[1, 1])  # Overall ranking distribution (bottom right)
ax4 = fig.add_subplot(gs[2, :])  # Performance margins (bottom, full width)

# =============================================================================
# Panel 1: Main Composite RMSE Comparison
# =============================================================================
bar_width = 0.25
x = np.arange(len(regions))

# Plot bars with enhanced styling
bars_dict = {}
for i, dataset in enumerate(datasets):
    values = plot_data[f"{dataset}_Composite"].values
    bars = ax1.bar(
        x + i * bar_width,
        values,
        width=bar_width,
        label=dataset,
        color=colors[dataset],
        alpha=0.85,
        edgecolor='black',
        linewidth=0.5
    )
    bars_dict[dataset] = bars
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.05,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

# Highlight best dataset with star marker
for idx, region in enumerate(regions):
    best = plot_data.iloc[idx]["Best_Dataset"]
    best_idx = datasets.index(best)
    best_value = plot_data.iloc[idx][f"{best}_Composite"]
    
    ax1.plot(
        idx + best_idx * bar_width,
        best_value + 0.15,
        marker='*',
        markersize=18,
        color='gold',
        markeredgecolor='black',
        markeredgewidth=1.5,
        zorder=5
    )

# Styling for main plot
ax1.set_ylabel("Composite RMSE (mm)", fontsize=15, fontweight="bold", labelpad=12)
ax1.set_xticks(x + bar_width)
ax1.set_xticklabels(regions, fontsize=12, fontweight="bold", rotation=0, ha="center")
ax1.tick_params(axis='both', labelsize=12, width=2, length=6)
ax1.yaxis.grid(True, linestyle="--", alpha=0.4, linewidth=0.8)

ax1.set_axisbelow(True)
ax1.set_title("Regional Composite RMSE Comparison", fontsize=16, fontweight="bold", pad=15)

legend = ax1.legend(
    title="Dataset",
    fontsize=12,
    title_fontsize=14,
    loc='lower left',
    framealpha=0.95,
    edgecolor='black',
    fancybox=True
)
legend.get_frame().set_linewidth(1.5)

ax1.text(
    0.98, 0.97,
    "★ = Best performing dataset",
    transform=ax1.transAxes,
    fontsize=10,
    verticalalignment='top',
    horizontalalignment='right',
    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, edgecolor='black')
)

for spine in ax1.spines.values():
    spine.set_linewidth(2)
    spine.set_color('black')

ax1.set_ylim(0, ax1.get_ylim()[1] * 1.12)

# =============================================================================
# Panel 2: Regional Wins Summary
# =============================================================================
win_counts = plot_data["Best_Dataset"].value_counts().reindex(datasets, fill_value=0)

bars_summary = ax2.bar(
    datasets,
    win_counts.values,
    color=[colors[d] for d in datasets],
    alpha=0.85,
    edgecolor='black',
    linewidth=1.5
)

for bar in bars_summary:
    height = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        height + 0.15,
        f"{int(height)}\n({int(height)/len(regions)*100:.0f}%)",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold"
    )

ax2.set_ylabel("Regions Won", fontsize=13, fontweight="bold", labelpad=10)
ax2.set_xlabel("Dataset", fontsize=13, fontweight="bold", labelpad=10)
ax2.set_ylim(0, max(win_counts.values) * 1.25)
ax2.tick_params(axis='both', labelsize=11, width=2, length=6)
ax2.yaxis.grid(True, linestyle="--", alpha=0.4)
ax2.set_axisbelow(True)
ax2.set_title("Overall Winners", fontsize=14, fontweight="bold", pad=10)

for spine in ax2.spines.values():
    spine.set_linewidth(2)
    spine.set_color('black')

# =============================================================================
# Panel 3: Ranking Distribution (Box Plot)
# =============================================================================
rank_data = [plot_data[f"{dataset}_Rank"].values for dataset in datasets]

bp = ax3.boxplot(
    rank_data,
    labels=datasets,
    patch_artist=True,
    widths=0.6,
    boxprops=dict(linewidth=1.5),
    medianprops=dict(color='red', linewidth=2),
    whiskerprops=dict(linewidth=1.5),
    capprops=dict(linewidth=1.5)
)

for patch, dataset in zip(bp['boxes'], datasets):
    patch.set_facecolor(colors[dataset])
    patch.set_alpha(0.7)

ax3.set_ylabel("Rank Position", fontsize=13, fontweight="bold", labelpad=10)
ax3.set_xlabel("Dataset", fontsize=13, fontweight="bold", labelpad=10)
ax3.set_ylim(0.5, 3.5)
ax3.set_yticks([1, 2, 3])
ax3.set_yticklabels(['1st', '2nd', '3rd'], fontsize=11, fontweight="bold")
ax3.tick_params(axis='x', labelsize=11, width=2, length=6)
ax3.yaxis.grid(True, linestyle="--", alpha=0.4)
ax3.invert_yaxis()  # Lower is better
ax3.set_axisbelow(True)
ax3.set_title("Rank Distribution", fontsize=14, fontweight="bold", pad=10)

for spine in ax3.spines.values():
    spine.set_linewidth(2)
    spine.set_color('black')

# =============================================================================
# Panel 4: Performance Margins (Difference from Best)
# =============================================================================
x_margin = np.arange(len(regions))
bar_width_margin = 0.25

for i, dataset in enumerate(datasets):
    margins = plot_data[f"{dataset}_Margin"].values
    bars = ax4.bar(
        x_margin + i * bar_width_margin,
        margins,
        width=bar_width_margin,
        label=dataset,
        color=colors[dataset],
        alpha=0.85,
        edgecolor='black',
        linewidth=0.5
    )

ax4.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
ax4.set_ylabel("RMSE Difference from Best (mm)", fontsize=13, fontweight="bold", labelpad=10)
ax4.set_xlabel("Region", fontsize=13, fontweight="bold", labelpad=10)
ax4.set_xticks(x_margin + bar_width_margin)
ax4.set_xticklabels(regions, fontsize=11, fontweight="bold", rotation=0, ha="center")
ax4.tick_params(axis='both', labelsize=10, width=2, length=6)
ax4.yaxis.grid(True, linestyle="--", alpha=0.4, linewidth=0.8)
ax4.set_axisbelow(True)
ax4.set_title("Performance Gap Analysis (Lower is Better)", fontsize=14, fontweight="bold", pad=10)

ax4.legend(fontsize=11, loc='upper left', framealpha=0.95, edgecolor='black')

for spine in ax4.spines.values():
    spine.set_linewidth(2)
    spine.set_color('black')

# Overall title
fig.suptitle(
    "Comprehensive PWV Dataset Performance Analysis: 3CH + ETC Methods",
    fontsize=17,
    fontweight="bold",
    y=0.995
)

# =============================================================================
# 6. Save Output and Export All Results
# =============================================================================
output_file = REPO_ROOT / "Figures" / "Ranking_Regional_RMSE_Analysis.png"

plt.savefig(output_file, format='png', dpi=300, bbox_inches='tight')
print(f"\nPlot saved successfully to:\n{output_file}")

# =============================================================================
# Export 1: Detailed Composite Scores
# =============================================================================
output_csv = output_file.replace('.png', '_Detailed_Results.csv')
composite_scores.to_csv(output_csv, index=False)
print(f"\nDetailed composite scores exported to:\n{output_csv}")

# =============================================================================
# Export 2: Summary Statistics Table
# =============================================================================
summary_stats_file = output_file.replace('.png', '_Summary_Statistics.csv')

summary_data = []
for dataset in ["GNSS", "ERA5", "VMF3"]:
    scores = composite_scores[f"{dataset}_Composite"].dropna()
    ranks = composite_scores[f"{dataset}_Rank"].dropna()
    wins = (composite_scores['Best_Dataset'] == dataset).sum()
    
    summary_data.append({
        'Dataset': dataset,
        'Mean_Composite_RMSE_mm': f"{scores.mean():.3f}",
        'Median_Composite_RMSE_mm': f"{scores.median():.3f}",
        'Std_Dev_mm': f"{scores.std():.3f}",
        'Min_RMSE_mm': f"{scores.min():.3f}",
        'Max_RMSE_mm': f"{scores.max():.3f}",
        'Regions_Won': wins,
        'Win_Percentage': f"{wins/len(composite_scores.dropna())*100:.1f}%",
        'Average_Rank': f"{ranks.mean():.2f}",
        'Rank_1st_Count': (ranks == 1).sum(),
        'Rank_2nd_Count': (ranks == 2).sum(),
        'Rank_3rd_Count': (ranks == 3).sum()
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(summary_stats_file, index=False)
print(f"Summary statistics exported to:\n{summary_stats_file}")

# =============================================================================
# Export 3: Statistical Significance Testing Results
# =============================================================================
significance_file = output_file.replace('.png', '_Statistical_Significance.csv')

significance_results = []
pairs = [("GNSS", "ERA5"), ("GNSS", "VMF3"), ("ERA5", "VMF3")]

for d1, d2 in pairs:
    data1 = composite_scores[f"{d1}_Composite"].dropna()
    data2 = composite_scores[f"{d2}_Composite"].dropna()
    
    # Ensure same length for paired test
    common_idx = data1.index.intersection(data2.index)
    
    if len(common_idx) > 0:
        stat, p_value = wilcoxon(data1[common_idx], data2[common_idx])
        mean_diff = data1[common_idx].mean() - data2[common_idx].mean()
        
        # Determine significance level
        if p_value < 0.001:
            significance = "***"
            interpretation = "Highly significant"
        elif p_value < 0.01:
            significance = "**"
            interpretation = "Very significant"
        elif p_value < 0.05:
            significance = "*"
            interpretation = "Significant"
        else:
            significance = "ns"
            interpretation = "Not significant"
        
        # Determine which dataset is better
        if mean_diff < 0:
            better_dataset = d1
            worse_dataset = d2
        else:
            better_dataset = d2
            worse_dataset = d1
        
        significance_results.append({
            'Comparison': f"{d1} vs {d2}",
            'Test_Statistic': f"{stat:.4f}",
            'P_Value': f"{p_value:.6f}",
            'Significance_Level': significance,
            'Interpretation': interpretation,
            'Mean_Difference_mm': f"{abs(mean_diff):.3f}",
            'Better_Dataset': better_dataset,
            'Worse_Dataset': worse_dataset,
            'Sample_Size': len(common_idx)
        })

significance_df = pd.DataFrame(significance_results)
significance_df.to_csv(significance_file, index=False)
print(f"Statistical significance results exported to:\n{significance_file}")

# =============================================================================
# Export 4: Ranking Consistency Analysis
# =============================================================================
consistency_file = output_file.replace('.png', '_Ranking_Consistency.csv')

consistency_data = []
for dataset in ["GNSS", "ERA5", "VMF3"]:
    ranks = composite_scores[f"{dataset}_Rank"].dropna()
    
    consistency_data.append({
        'Dataset': dataset,
        'Average_Rank': f"{ranks.mean():.2f}",
        'Rank_Std_Dev': f"{ranks.std():.2f}",
        'Median_Rank': f"{ranks.median():.1f}",
        'Best_Rank': int(ranks.min()),
        'Worst_Rank': int(ranks.max()),
        'Times_Ranked_1st': (ranks == 1).sum(),
        'Times_Ranked_2nd': (ranks == 2).sum(),
        'Times_Ranked_3rd': (ranks == 3).sum(),
        'Percentage_1st': f"{(ranks == 1).sum()/len(ranks)*100:.1f}%",
        'Percentage_2nd': f"{(ranks == 2).sum()/len(ranks)*100:.1f}%",
        'Percentage_3rd': f"{(ranks == 3).sum()/len(ranks)*100:.1f}%"
    })

consistency_df = pd.DataFrame(consistency_data)
consistency_df.to_csv(consistency_file, index=False)
print(f"Ranking consistency analysis exported to:\n{consistency_file}")

# =============================================================================
# Export 5: Performance Margins Analysis
# =============================================================================
margins_file = output_file.replace('.png', '_Performance_Margins.csv')

margins_export = composite_scores[[
    'Region', 
    'GNSS_Composite', 'ERA5_Composite', 'VMF3_Composite',
    'GNSS_Margin', 'ERA5_Margin', 'VMF3_Margin',
    'Best_Dataset',
    'GNSS_Rank', 'ERA5_Rank', 'VMF3_Rank'
]].copy()

# Round for readability
for col in margins_export.columns:
    if col != 'Region' and col != 'Best_Dataset':
        margins_export[col] = margins_export[col].round(3)

margins_export.to_csv(margins_file, index=False)
print(f"Performance margins exported to:\n{margins_file}")

# =============================================================================
# Export 6: Method-Specific Contributions
# =============================================================================
methods_file = output_file.replace('.png', '_Method_Contributions.csv')

methods_export = composite_scores[[
    'Region',
    'GNSS_3CH', 'GNSS_ETC', 'GNSS_Composite',
    'ERA5_3CH', 'ERA5_ETC', 'ERA5_Composite',
    'VMF3_3CH', 'VMF3_ETC', 'VMF3_Composite',
    'Best_Dataset'
]].copy()

# Round for readability
for col in methods_export.columns:
    if col not in ['Region', 'Best_Dataset']:
        methods_export[col] = methods_export[col].round(3)

methods_export.to_csv(methods_file, index=False)
print(f"Method-specific contributions exported to:\n{methods_file}")

# =============================================================================
# Export 7: Comprehensive Report (Text File)
# =============================================================================
report_file = output_file.replace('.png', '_Analysis_Report.txt')

with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("PWV DATASET RANKING ANALYSIS - COMPREHENSIVE REPORT\n")
    f.write("="*80 + "\n\n")
    
    f.write("METHODOLOGY\n")
    f.write("-" * 80 + "\n")
    f.write("Composite RMSE Ranking Approach:\n")
    f.write(f"  - 3CH Method Weight: {weights['3CH']}\n")
    f.write(f"  - ETC Method Weight: {weights['ETC']}\n")
    f.write("  - Formula: Composite_RMSE = w1×RMSE_3CH + w2×RMSE_ETC\n")
    f.write(f"  - Normalization: {'Enabled' if USE_NORMALIZED_SCORES else 'Disabled'}\n")
    f.write("  - Statistical Test: Wilcoxon Signed-Rank Test\n")
    f.write("  - Significance Level: p < 0.05\n\n")
    
    f.write("OVERALL PERFORMANCE STATISTICS\n")
    f.write("-" * 80 + "\n")
    for dataset in ["GNSS", "ERA5", "VMF3"]:
        scores = composite_scores[f"{dataset}_Composite"].dropna()
        ranks = composite_scores[f"{dataset}_Rank"].dropna()
        wins = (composite_scores['Best_Dataset'] == dataset).sum()
        
        f.write(f"\n{dataset}:\n")
        f.write(f"  Mean Composite RMSE:   {scores.mean():.3f} mm\n")
        f.write(f"  Median Composite RMSE: {scores.median():.3f} mm\n")
        f.write(f"  Standard Deviation:    {scores.std():.3f} mm\n")
        f.write(f"  Min RMSE:              {scores.min():.3f} mm\n")
        f.write(f"  Max RMSE:              {scores.max():.3f} mm\n")
        f.write(f"  Regions Won:           {wins} ({wins/len(composite_scores.dropna())*100:.1f}%)\n")
        f.write(f"  Average Rank:          {ranks.mean():.2f}\n")
        f.write(f"  1st Place Count:       {(ranks == 1).sum()}\n")
        f.write(f"  2nd Place Count:       {(ranks == 2).sum()}\n")
        f.write(f"  3rd Place Count:       {(ranks == 3).sum()}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("PAIRWISE STATISTICAL SIGNIFICANCE (Wilcoxon Signed-Rank Test)\n")
    f.write("="*80 + "\n\n")
    
    for result in significance_results:
        f.write(f"{result['Comparison']}:\n")
        f.write(f"  Test Statistic:  {result['Test_Statistic']}\n")
        f.write(f"  P-value:         {result['P_Value']} {result['Significance_Level']}\n")
        f.write(f"  Interpretation:  {result['Interpretation']}\n")
        f.write(f"  Mean Difference: {result['Mean_Difference_mm']} mm\n")
        f.write(f"  Better Dataset:  {result['Better_Dataset']}\n")
        f.write(f"  Sample Size:     {result['Sample_Size']}\n\n")
    
    f.write("Significance levels: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant\n\n")
    
    f.write("="*80 + "\n")
    f.write("REGIONAL RESULTS\n")
    f.write("="*80 + "\n\n")
    
    for idx, row in plot_data.iterrows():
        f.write(f"{row['Region']}:\n")
        f.write(f"  GNSS: {row['GNSS_Composite']:.3f} mm (Rank {int(row['GNSS_Rank'])}, Margin: {row['GNSS_Margin']:.3f} mm)\n")
        f.write(f"  ERA5: {row['ERA5_Composite']:.3f} mm (Rank {int(row['ERA5_Rank'])}, Margin: {row['ERA5_Margin']:.3f} mm)\n")
        f.write(f"  VMF3: {row['VMF3_Composite']:.3f} mm (Rank {int(row['VMF3_Rank'])}, Margin: {row['VMF3_Margin']:.3f} mm)\n")
        f.write(f"  * BEST: {row['Best_Dataset']}\n\n")
    
    f.write("="*80 + "\n")
    f.write("ANALYSIS COMPLETE\n")
    f.write("="*80 + "\n")

print(f"Comprehensive analysis report exported to:\n{report_file}")

# =============================================================================
# Summary of Exported Files
# =============================================================================
print("\n" + "="*80)
print("EXPORT SUMMARY - 7 FILES CREATED:")
print("="*80)
print(f"1. PNG Figure:                {output_file}")
print(f"2. Detailed Results CSV:      {output_csv}")
print(f"3. Summary Statistics CSV:    {summary_stats_file}")
print(f"4. Statistical Significance:  {significance_file}")
print(f"5. Ranking Consistency CSV:   {consistency_file}")
print(f"6. Performance Margins CSV:   {margins_file}")
print(f"7. Method Contributions CSV:  {methods_file}")
print(f"8. Comprehensive Report TXT:  {report_file}")
print("="*80)

plt.show()
plt.close()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
