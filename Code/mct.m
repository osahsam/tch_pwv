%MCT - Multiple Comparison Test with ANOVA
%   ------------------------------
% DESCRIPTION:
%   ------------------------------
%   This function performs a one-way Analysis of Variance (ANOVA) followed by
%   multiple comparison tests to determine which groups have significantly
%   different means. It reads data from a CSV file, conducts statistical
%   analysis, and generates visualizations.
%
%   ------------------------------
% SYNTAX:
%   ------------------------------
%When running /called from command window as a function
%   mct()                           % Uses default settings
%   mct('filename', 'data.csv')     % Specify custom filename
%   mct('alpha', 0.01)              % Set significance level
%   mct('method', 'bonferroni')     % Set comparison method
%   results = mct(...)              % Return results structure 
%   results = mct('export', true);  % Export results automatically during analysis
%                                   Uses default filename 'MCT_Results.xlsx'
%   results = mct('export', true, 'exportfile', 'my_analysis.xlsx'); specify custom filename
%   Comprehensive analysis with automatic export
%   results = mct('filename', 'RMSE-3CH_ETC_DC.csv', ...
%                 'method', 'scheffe', ...
%                 'alpha', 0.05, ...
%                 'showplot', true, ...
%                 'showboxplot', true, ...
%                 'title', 'Model Performance Comparison', ...
%                 'xlabel', 'RMSE [cm]', ...
%                 'export', true, ...
%                 'exportfile', 'model_comparison_results.xlsx');
%
%   ------------------------------
% INPUT PARAMETERS (Name-Value Pairs):
%   ------------------------------
%   'filename'  - String: CSV filename (default: 'RMSE-3CH_ETC_DC.csv')
%   'alpha'     - Double: Significance level (default: 0.05)
%   'method'    - String: Multiple comparison method (default: 'scheffe')
%                 Options: 'scheffe', 'bonferroni', 'dunnett', 'tukey-kramer', 'dunn-sidak'
%   'showplot'  - Logical: Display comparison plot (default: true)
%   'showboxplot' - Logical: Display boxplot (default: false)
%   'title'     - String: Custom title for plots
%   'xlabel'    - String: Custom x-axis label
%   'ylabel'    - String: Custom y-axis label
%   'export'    - Logical: Export results to Excel file (default: false)
%   'exportfile'- String: Excel filename for export (default: 'MCT_Results.xlsx')
%
% OUTPUT:
%   ------------------------------
%   results - Structure containing:
%   ------------------------------
%     .anova_p      : ANOVA p-value
%     .anova_table  : ANOVA table
%     .anova_stats  : ANOVA statistics
%     .comparison   : Multiple comparison results matrix
%     .means        : Group means and standard errors
%     .group_names  : Names of the groups
%     .settings     : Analysis settings used
%   ------------------------------
%   Export result to MS Excel file
%   ------------------------------
%   **The Excel file will contain 3 sheets:
%     - Sheet1: Group_Means - Mean values and standard errors for each group
%     - Sheet2: Pairwise_Comparisons - All pairwise comparison results with p-values
%     - Sheet3: ANOVA_Table - The complete ANOVA results table
%   ------------------------------
%   PLOTS 
%   ------------------------------
%   1. Multiple Comparison Test (MCT) plot of group means
%   2.  Boxplot of group mean
%
%   ------------------------------
% EXAMPLE:
%   ------------------------------
%   % Basic usage with default settings
%   results = mct();
%   
%   % Custom analysis with Bonferroni correction
%   results = mct('filename', 'mydata.csv', 'method', 'bonferroni', 'alpha', 0.01);
%   results = mct('filename', 'RMSE-3CH_ETC_DC.csv', ...
%                 'method', 'scheffe', ...
%                 'alpha', 0.05, ...
%                 'showplot', true, ...
%                 'showboxplot', true, ...
%                 'title', 'Model Performance Comparison', ...
%                 'xlabel', 'RMSE [cm]', ...
%                 'export', true, ...
%                 'exportfile', 'model_comparison_results.xlsx');
%------
%NOTE: In Script Mode, When you click "Run" button 
%------
%      - No inputs are required
%      - Uses default parameters
%      - No export of results
%      - Results displayed in command window
%      - Plots are displayed
%   ------------------------------
% REQUIREMENTS:
%   ------------------------------
%1. SOFTWARE:
%             - MATLAB R2018b or later (tested up to R2024b)
%2. DATA FORMAT:
%                - CSV file with numeric data and column headers
%                - First row should contain group/model names
%
%   ------------------------------
% AUTHOR:
%   ------------------------------
%        Dr. Samuel Osah
%        Department of Geomatic Engineering, KNUST, Kumasi, Ghana
%        Email: osahsamuel@knust.edu.gh / osahsamuel@yahoo.ca
%        Date: March 2021
% ========================================================================
% ========================================================================
% ========================================================================

function [results] = mct(varargin)


%% Input Validation and Parameter Parsing
    % Set default parameters
    p = inputParser;
    addParameter(p, 'filename', 'MCTdata_RMSE-3CH_ETC_DC.csv', @ischar);
    addParameter(p, 'alpha', 0.05, @(x) isnumeric(x) && x > 0 && x < 1);
    addParameter(p, 'method', 'scheffe', @(x) ismember(x, {'scheffe', 'bonferroni', 'dunnett', 'tukey-kramer', 'dunn-sidak'}));
    addParameter(p, 'showplot', true, @islogical);
    addParameter(p, 'showboxplot', true, @islogical);
    addParameter(p, 'title', 'Model Performance Comparison', @ischar);
    addParameter(p, 'xlabel', 'RMSE [mm]', @ischar);
    addParameter(p, 'ylabel', 'Groups', @ischar);
    addParameter(p, 'export', false, @islogical);
    addParameter(p, 'exportfile', 'MCT_Results.xlsx', @ischar);
    
    parse(p, varargin{:});
    
    % Extract parameters
    filename = p.Results.filename;
    alpha_level = p.Results.alpha;
    comparison_method = p.Results.method;
    show_plot = p.Results.showplot;
    show_boxplot = p.Results.showboxplot;
    plot_title = p.Results.title;
    x_label = p.Results.xlabel;
    y_label = p.Results.ylabel;
    export_results_flag = p.Results.export;
    export_filename = p.Results.exportfile;

%% Data Import and Validation
    try
        fprintf('Reading data from: %s\n', filename);
        
        % Check if file exists
        if ~exist(filename, 'file')
            error('MCT:FileNotFound', 'File "%s" not found in current directory.', filename);
        end
        
        % Import data
        Data = importdata(filename);
        
        % Validate data structure
        if ~isstruct(Data) || ~isfield(Data, 'data') || ~isfield(Data, 'colheaders')
            error('MCT:InvalidData', 'Invalid data format. Expected CSV with headers and numeric data.');
        end
        
        % Extract numeric data and model names
        data = Data.data;
        models = Data.colheaders';
        
        % Validate data dimensions
        if isempty(data) || size(data, 2) ~= length(models)
            error('MCT:DataMismatch', 'Data dimensions do not match number of headers.');
        end
        
        fprintf('Successfully loaded data: %d observations, %d groups\n', size(data, 1), size(data, 2));
        
    catch ME
        fprintf('Error reading data: %s\n', ME.message);
        if nargout > 0
            results = [];
        end
        return;
    end

%% Data Summary
    fprintf('\nData Summary:\n');
    fprintf('Groups: %s\n', strjoin(models, ', '));
    fprintf('Sample sizes: ');
    for i = 1:length(models)
        valid_data = ~isnan(data(:, i));
        fprintf('%s: %d  ', models{i}, sum(valid_data));
    end
    fprintf('\n\n');

%% Analysis of Variance (ANOVA)
    try
        fprintf('Performing one-way ANOVA...\n');
        [anova_p, anova_table, anova_stats] = anova1(data, models, 'off'); % 'off' suppresses default plot
        
        fprintf('ANOVA Results:\n');
        fprintf('F-statistic: %.4f\n', anova_table{2,5});
        fprintf('p-value: %.6f\n', anova_p);
        
        if anova_p < alpha_level
            fprintf('Result: Significant differences detected between groups (p < %.3f)\n\n', alpha_level);
        else
            fprintf('Result: No significant differences detected between groups (p >= %.3f)\n', alpha_level);
            fprintf('Multiple comparison test may not be meaningful.\n\n');
        end
        
    catch ME
        error('MCT:ANOVAError', 'Error in ANOVA analysis: %s', ME.message);
    end

%% Multiple Comparison Test
    try
        fprintf('Performing multiple comparison test using %s method...\n', comparison_method);
        
        if show_plot
            figure('Name', 'Multiple Comparison Test', 'NumberTitle', 'off');
        end
        
        % Perform multiple comparison
        if show_plot
            display_option = 'on';
        else
            display_option = 'off';
        end
        
        [comparison_results, means_table, ~, group_names] = multcompare(anova_stats, ...
            'alpha', alpha_level, ...
            'ctype', comparison_method, ...
            'display', display_option);
        
        % Create results tables
        means_tbl = array2table(means_table, ...
            "RowNames", models, ...
            "VariableNames", ["Mean", "Standard_Error"]);
        
        comparison_tbl = array2table(comparison_results, ...
            "VariableNames", ["Group_A", "Group_B", "Lower_Limit", "Difference_A_B", "Upper_Limit", "P_value"]);
        
        % Add group names to comparison table for clarity
        group_A_names = models(comparison_results(:,1));
        group_B_names = models(comparison_results(:,2));
        comparison_tbl.Group_A_Name = group_A_names;
        comparison_tbl.Group_B_Name = group_B_names;
        
        % Reorder columns for better readability
        comparison_tbl = comparison_tbl(:, [7, 8, 1, 2, 3, 4, 5, 6]);
        
        % Customize plot if shown
        if show_plot
            if ~isempty(plot_title)
                title(plot_title, 'FontWeight', 'bold', 'FontSize', 12);
            else
                title('Multiple Comparison of Means', 'FontWeight', 'bold', 'FontSize', 12);
            end
            
            ylabel(y_label, 'FontWeight', 'bold', 'FontSize', 11);
            
            if ~isempty(x_label)
                xlabel(x_label, 'FontWeight', 'bold', 'FontSize', 11);
            end
            
            grid on;
            grid minor;
        end
        
    catch ME
        error('MCT:ComparisonError', 'Error in multiple comparison test: %s', ME.message);
    end

%% Optional Boxplot
    if show_boxplot
        figure('Name', 'Boxplot Comparison', 'NumberTitle', 'off');
        boxplot(data, 'Labels', models);
        
        if ~isempty(plot_title)
            title([plot_title, ' - Boxplot'], 'FontWeight', 'bold', 'FontSize', 12);
        else
            title('Data Distribution by Group', 'FontWeight', 'bold', 'FontSize', 12);
        end
        
        xlabel('Groups', 'FontWeight', 'bold', 'FontSize', 11);
        if ~isempty(x_label)
            ylabel(x_label, 'FontWeight', 'bold', 'FontSize', 11);
        else
            ylabel('Values', 'FontWeight', 'bold', 'FontSize', 11);
        end
        
        grid on;
        xtickangle(45); % Rotate labels if they're long
    end

%% Display Results
    fprintf('\n=== MULTIPLE COMPARISON RESULTS ===\n');
    fprintf('Method: %s\n', upper(comparison_method));
    fprintf('Significance level: %.3f\n\n', alpha_level);
    
    fprintf('Group Means and Standard Errors:\n');
    disp(means_tbl);
    
    fprintf('\nPairwise Comparisons:\n');
    fprintf('(Significant differences marked with p < %.3f)\n\n', alpha_level);
    disp(comparison_tbl);
    
    % Highlight significant comparisons
    significant_pairs = comparison_results(:, 6) < alpha_level;
    if any(significant_pairs)
        fprintf('Significant pairwise differences found:\n');
        sig_comparisons = comparison_tbl(significant_pairs, :);
        disp(sig_comparisons);
    else
        fprintf('No significant pairwise differences found at α = %.3f level.\n', alpha_level);
    end

%% Prepare Output Structure
    if nargout > 0
        results.anova_p = anova_p;
        results.anova_table = anova_table;
        results.anova_stats = anova_stats;
        results.comparison = comparison_results;
        results.comparison_table = comparison_tbl;
        results.means = means_table;
        results.means_table = means_tbl;
        results.group_names = models;
        results.settings.filename = filename;
        results.settings.alpha = alpha_level;
        results.settings.method = comparison_method;
        results.settings.significant_pairs = sum(significant_pairs);
        results.settings.total_comparisons = size(comparison_results, 1);
    end
   
    fprintf('\nAnalysis completed successfully!\n');
    
    %% Export Results (if requested)
   
    if export_results_flag
        export_results(results, export_filename);
    end
    
end

%% Additional Helper Functions (Optional)
function export_results(results, export_filename)
   
    %EXPORT_RESULTS Export analysis results to Excel file
    %
    % SYNTAX:
    %   export_results(results, 'output.xlsx')
    
    if nargin < 2
        export_filename = 'MCT_Results.xlsx';
    end
    
    try
        % Export means table
        writetable(results.means_table, export_filename, 'Sheet', 'Group_Means', 'WriteRowNames', true);
        
        % Export comparison results
        writetable(results.comparison_table, export_filename, 'Sheet', 'Pairwise_Comparisons');
        
        % Export ANOVA table
        anova_tbl = cell2table(results.anova_table(2:end,:), 'VariableNames', results.anova_table(1,:));
        writetable(anova_tbl, export_filename, 'Sheet', 'ANOVA_Table');
        
        fprintf('Results exported to: %s\n', export_filename);
        
    catch ME
        warning('Could not export results: %s', ME.message);
    end
end
