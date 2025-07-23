%% PWV_ANALYSIS_MAIN.m
% ========================================================================
% PRECIPITABLE WATER VAPOR (PWV) STATISTICAL ANALYSIS TOOL
% ========================================================================
%
% DESCRIPTION:
% This script performs comprehensive statistical analysis of Precipitable 
% Water Vapor (PWV) measurements from three different sources:
%
% ------------
% DATA SOURCES:
% ------------
% - IGS/GNSS derived PWV
% - ERA5 reanalysis PWV  
% - VMF3 model PWV
%
% ------------
% ANALYSIS METHODS IMPLEMENTED:
% ------------
%   1. Three-Cornered Hat (3CH) Method
%      - Estimates uncertainties without a priori knowledge of true values
%      - Provides independent uncertainty estimates for each data source
%      - Particularly useful when no absolute reference is available
%
%   2. Extended Triple Collocation (ETC) Method  
%      - Estimates error variance and correlation coefficients
%      - Determines correlation with respect to unknown true value
%      - Provides both uncertainty and quality metrics
%
%   3. Direct Comparison (DC) Approach
%      - Uses ERA5 as reference for traditional validation
%      - Computes RMSE and correlation coefficients
%      - Provides straightforward comparison metrics
%
% ------------
% REQUIREMENTS:
% ------------
%1. SOFTWARE:
%            - MATLAB R2016b or later (tested up to R2024b)
%2. DATA FORMAT:
%               - CSV files containing PWV data with the following columns:
%                 STN (Station ID), DOY (Day of Year), YEAR, MONTH, DAY,
%                 LAT (Latitude), LON (Longitude), H (Height),
%                 IGS_PWV, VMF3_PWV, ERA5_PWV
%               - All PWV values must be in meters (automatically converted to mm)
%               - Missing values should be properly handled or removed beforehand
%
%INPUT:
%      - User selects folder containing CSV files via GUI dialog
%      - Each CSV file should represent data from one station
%      - Handles unlimited number of files 
% OUTPUT:
%        - Creates 'STATs' folder (or STATs1, STATs2, etc. if folder exists)
%        - Generates comprehensive statistical results in CSV format
%        - Automatically opens results file upon completion
%
% STATISTICAL OUTPUTS:
%   For each station, the following metrics are computed:
%   - 3CH uncertainties: RMSEigs(3ch), RMSEera5(3ch), RMSEvmf3(3ch)
%   - ETC uncertainties: RMSEigs(etc), RMSEera5(etc), RMSEvmf3(etc)  
%   - ETC correlations: Rigs(etc), Rera5(etc), Rvmf3(etc)
%   - Direct comparisons: RMSE(IGSvsERA5), RMSE(VMF3vsERA5)
%   - Direct correlations: R(IGSvsERA5), R(VMF3vsERA5)
%
% TROUBLESHOOTING:
%  -Common Issues:
%   1. "Folder selection canceled" - Ensure you select a valid folder
%   2. "No CSV files found" - Check file extensions and folder contents
%   3. "Missing required columns" - Verify CSV headers match requirements
%   4. "Numerical instability" - Check for NaN values or insufficient data
%   5. Complex results in 3CH method
%      - May indicate assumption violations
%      - Check for outliers in data 
%      - Ensure sufficient data variance
%   6. Negative error variances in ETC
%      - May indicate correlated errors between systems
%      - Consider data quality and temporal matching
%      - Check for systematic biases
%
% ERROR HANDLING:
%   - Validates input data format and completeness
%   - Handles missing or corrupted files gracefully
%   - Provides informative error messages and warnings
%   - Checks for numerical stability in statistical computations
% USAGE:
%   1. Prepare CSV files with required PWV data columns
%   2. Run the script in MATLAB
%   3. Select the folder containing CSV files when prompted via GUI dialog
%      - Each CSV file should represent data from one station
%   4. View results in the generated STATs.csv file
%
% REFERENCES:
%   [1] Ferreira, V.G., et al. (2016). Uncertainties of the GRACE time-variable
%       gravity-field solutions based on three-cornered hat method. 
%       J. Appl. Remote Sens., 10, 015015.
%   [2] McColl, K.A., et al. (2014). Extended triple collocation: Estimating 
%       errors and correlation coefficients with respect to an unknown target.
%       Geophys. Res. Lett., 41, 6229-6236.
%   [3] Xu, T., et al. (2019). Evaluation of twelve evapotranspiration products
%       from machine learning, remote sensing and land surface models.
%       J. Hydrology, 578, 124105.
%
% AUTHOR:
%        Dr. Samuel Osah
%        Department of Geomatic Engineering, KNUST, Kumasi, Ghana
%        Email: osahsamuel@knust.edu.gh / osahsamuel@yahoo.ca
%        Date: July 2024
% ========================================================================
% ========================================================================
% ========================================================================

function PWV_Analysis_Main()
    % Main function to orchestrate the PWV analysis
    
    try
        % Initialize analysis
        fprintf('\n=== PWV Statistical Analysis Tool ===\n');
        fprintf('Initializing analysis...\n');
        
        % Get input folder and validate
        [folderPath, fileList] = getInputFolder();
        if isempty(folderPath)
            return;
        end
        
        % Create output folder
        outputFolder = createOutputFolder(folderPath);
        
        % Define expected columns
        expectedColumns = {'STN', 'DOY', 'YEAR', 'MONTH', 'DAY', 'LAT', 'LON', 'H', ...
                          'IGS_PWV', 'VMF3_PWV', 'ERA5_PWV'};
        
        % Process all CSV files
        [statistics, stationInfo] = processCSVFiles(fileList, expectedColumns);
        
        % Create and save results table
        saveResults(statistics, stationInfo, outputFolder);
        
        fprintf('Analysis completed successfully!\n');
        
    catch ME
        fprintf('Error during analysis: %s\n', ME.message);
        fprintf('Stack trace:\n');
        for i = 1:length(ME.stack)
            fprintf('  %s (line %d)\n', ME.stack(i).name, ME.stack(i).line);
        end
    end
end

function [folderPath, fileList] = getInputFolder()
    
    % Get input folder and validate CSV files exist
    folderPath = uigetdir('', 'Select the folder containing CSV files');
    
    if folderPath == 0
        fprintf('Folder selection canceled.\n');
        folderPath = [];
        fileList = [];
        return;
    end
    
    % List all CSV files in the selected folder
    fileList = dir(fullfile(folderPath, '*.csv'));
    
    try
        if isempty(fileList)
            error('No CSV files found in the selected folder: %s', folderPath);
        end 
    
        fprintf('Found %d CSV files to process.\n', length(fileList));

    catch
          numFiles = numel(fileList);

          if numFiles == 0
             error('No CSV files found in selected directory: %s', folderPath);
          end 

          fprintf('Found %d CSV files to process.\n', length(fileList));
    end
end

function outputFolder = createOutputFolder(parentFolder)
    % Create unique output folder with incremental naming
    
    subfolderName = 'STATs';
    outputFolder = fullfile(parentFolder, subfolderName);
    index = 1;
    
    % Create unique folder name if folder exists
    while exist(outputFolder, 'dir')
        subfolderName = sprintf('STATs%d', index);
        outputFolder = fullfile(parentFolder, subfolderName);
        index = index + 1;
    end
    
    % Create the folder
    mkdir(outputFolder);
    fprintf('Created output folder: %s\n', outputFolder);
end

function [statistics, stationInfo] = processCSVFiles(fileList, expectedColumns)

    % Process all CSV files and compute statistics
    numFiles = length(fileList);
    
    % Initialize storage arrays
    statistics = zeros(numFiles, 13);
    stationInfo = cell(numFiles, 4);
    
    fprintf('Processing CSV files:\n');
    
    % Process each file
    for i = 1:numFiles
        fprintf('  [%d/%d] %s\n', i, numFiles, fileList(i).name);
        
        try
            % Load and validate data
            [data, pwvData] = loadAndValidateCSV(fileList(i), expectedColumns);
            
            % Compute statistics for this file
            [fileStats, fileStationInfo] = computeFileStatistics(data, pwvData);
            
            % Store results
            statistics(i, :) = fileStats;
            stationInfo(i, :) = fileStationInfo;
            
        catch ME
            fprintf('    Warning: Skipping file due to error: %s\n', ME.message);
            % Fill with NaN values for failed files
            statistics(i, :) = NaN(1, 13);
            stationInfo(i, :) = {NaN, NaN, NaN, NaN};
        end
    end
    
    fprintf('File processing completed.\n');
end

function [data, pwvData] = loadAndValidateCSV(fileInfo, expectedColumns)
    % Load CSV file and validate required columns exist
    
    filePath = fullfile(fileInfo.folder, fileInfo.name);
    
    % Set import options to preserve variable names
    opts = detectImportOptions(filePath);
    opts.VariableNamingRule = 'preserve';
    
    % Read the data
    data = readtable(filePath, opts);
    
    % Validate required columns exist
    missingCols = setdiff(expectedColumns, data.Properties.VariableNames);
    if ~isempty(missingCols)
        error('Missing required columns: %s', strjoin(missingCols, ', '));
    end
    
    % Validate data is not empty
    if height(data) == 0
        error('File contains no data rows');
    end
    
    % Extract and convert PWV data from meters to millimeters
    pwvData.igs = data{:, 'IGS_PWV'} * 1000;
    pwvData.era5 = data{:, 'ERA5_PWV'} * 1000;
    pwvData.vmf3 = data{:, 'VMF3_PWV'} * 1000;

    % Validate PWV data
    validatePWVData(pwvData);
    
end

function validatePWVData(pwvData)
    % Validate PWV data for analysis
    
    fields = {'igs', 'era5', 'vmf3'};
    
    for i = 1:length(fields)
        field = fields{i};
        values = pwvData.(field);
        
        % Check for NaN or infinite values
        if any(~isfinite(values))
            error('PWV data contains NaN or infinite values in %s', upper(field));
        end
        
        % Check for reasonable PWV range (0-100 mm)
        if any(values < 0) || any(values > 100)
            warning('PWV values outside expected range (0-100 mm) in %s', upper(field));
        end
        
        % Check for sufficient data variance
        if var(values) < 1e-6
            warning('Very low variance in %s PWV data', upper(field));
        end
    end
end


function [fileStats, fileStationInfo] = computeFileStatistics(data, pwvData)
    % Compute all statistics for a single file
    
    %Extract PWV arrays for convenience
    igsData = pwvData.igs;
    era5Data = pwvData.era5;
    vmf3Data = pwvData.vmf3;
    
    % 1. Three-Cornered Hat (3CH) Analysis
    U_3ch= computeThreeCorneredHat([igsData, era5Data, vmf3Data]);
    
    Uigs_3ch  = U_3ch(1);
    Uera5_3ch = U_3ch(2);
    Uvmf3_3ch = U_3ch(3);

    % 2. Extended Triple Collocation (ETC) Analysis
    [Uigs_etc, Uera5_etc, Uvmf3_etc, Rigs_etc, Rera5_etc, Rvmf3_etc] = ...
        computeExtendedTripleCollocation([igsData, era5Data, vmf3Data]);
    
    % 3. Direct Comparison (DC) Analysis using ERA5 as reference
    [rmse_igs_era5, rmse_vmf3_era5, r_igs_era5, r_vmf3_era5] = ...
        computeDirectComparison(igsData, era5Data, vmf3Data);
    
    % Compile statistics array
    fileStats = [
        roundn(Uigs_3ch, -2),      % 1: IGS uncertainty (3CH)
        roundn(Uera5_3ch, -2),     % 2: ERA5 uncertainty (3CH)
        roundn(Uvmf3_3ch, -2),     % 3: VMF3 uncertainty (3CH)
        roundn(Uigs_etc, -2),      % 4: IGS uncertainty (ETC)
        roundn(Uera5_etc, -2),     % 5: ERA5 uncertainty (ETC)
        roundn(Uvmf3_etc, -2),     % 6: VMF3 uncertainty (ETC)
        roundn(Rigs_etc, -4),      % 7: IGS correlation (ETC)
        roundn(Rera5_etc, -4),     % 8: ERA5 correlation (ETC)
        roundn(Rvmf3_etc, -4),     % 9: VMF3 correlation (ETC)
        rmse_igs_era5,             % 10: RMSE IGS vs ERA5
        rmse_vmf3_era5,            % 11: RMSE VMF3 vs ERA5
        r_igs_era5,                % 12: Correlation IGS vs ERA5
        r_vmf3_era5                % 13: Correlation VMF3 vs ERA5
    ];
    
    % Extract station information
    fileStationInfo = {
        extractStationValue(data, 'STN'),
        data{1, 'LAT'},
        data{1, 'LON'},
        data{1, 'H'}
    };
end

function stationValue = extractStationValue(data, columnName)
    % Safely extract station value handling both cell and numeric formats
    
    value = data{1, columnName};
    
    if iscell(value)
        stationValue = cell2mat(value);
    else
        stationValue = value;
    end
end

function [rmse_igs, rmse_vmf3, r_igs, r_vmf3] = computeDirectComparison(igsData, era5Data, vmf3Data)
    % Compute direct comparison statistics using ERA5 as reference
    
    % Calculate RMSE values
    rmse_igs = roundn(sqrt(mean((igsData - era5Data).^2)), -2);
    rmse_vmf3 = roundn(sqrt(mean((vmf3Data - era5Data).^2)), -2);
    
    % Calculate correlation coefficients
    r_igs = roundn(corr(igsData, era5Data), -4);
    r_vmf3 = roundn(corr(vmf3Data, era5Data), -4);
end

function saveResults(statistics, stationInfo, outputFolder)
    % Create and save the results table
   
    % Convert station info to proper format
    % stationData = cell2mat(stationInfo);
    
    % Create comprehensive results table
    statsTable = table(cell2mat(stationInfo(:,1)), cell2mat(stationInfo(:,2)), ...
                       cell2mat(stationInfo(:,3)), cell2mat(stationInfo(:,4)), ...
                       statistics(:,1), statistics(:,2), statistics(:,3), ...
                       statistics(:,4), statistics(:,5), statistics(:,6), ...
                       statistics(:,7), statistics(:,8), statistics(:,9), ...
                       statistics(:,10), statistics(:,11), statistics(:,12), statistics(:,13), ...
                       'VariableNames', {
                          'STN', 'LAT', 'LON', 'H', ...
                          'RMSE_IGS_3CH', 'RMSE_ERA5_3CH', 'RMSE_VMF3_3CH', ...
                          'RMSE_IGS_ETC', 'RMSE_ERA5_ETC', 'RMSE_VMF3_ETC', ...
                          'R_IGS_ETC', 'R_ERA5_ETC', 'R_VMF3_ETC', ...
                          'RMSE_IGS_vs_ERA5', 'RMSE_VMF3_vs_ERA5', ...
                          'R_IGS_vs_ERA5', 'R_VMF3_vs_ERA5'
                      });
    
    % Define output file
    outputFileName = fullfile(outputFolder, 'PWV_Statistics_Results.csv');
    
    % Write results to CSV
    writetable(statsTable, outputFileName);
    
    % Open the results file
    winopen(outputFileName);
    
    fprintf('Results saved to: %s\n', outputFileName);
    
    % Display summary statistics
    displaySummary(statsTable);
end

function displaySummary(statsTable)
    % Display summary of analysis results
    
    fprintf('\n=== ANALYSIS SUMMARY ===\n');
    fprintf('Number of stations processed: %d\n', height(statsTable));
    fprintf('Mean IGS RMSE (3CH): %.2f mm\n', mean(statsTable.RMSE_IGS_3CH, 'omitnan'));
    fprintf('Mean ERA5 RMSE (3CH): %.2f mm\n', mean(statsTable.RMSE_ERA5_3CH, 'omitnan'));
    fprintf('Mean VMF3 RMSE (3CH): %.2f mm\n', mean(statsTable.RMSE_VMF3_3CH, 'omitnan'));
    fprintf('Mean IGS RMSE (ETC): %.2f mm\n', mean(statsTable.RMSE_IGS_ETC, 'omitnan'));
    fprintf('Mean ERA5 RMSE (ETC): %.2f mm\n', mean(statsTable.RMSE_ERA5_ETC, 'omitnan'));
    fprintf('Mean VMF3 RMSE (ETC): %.2f mm\n', mean(statsTable.RMSE_VMF3_ETC, 'omitnan'));
    fprintf('Mean IGS RMSE (DC): %.2f mm\n', mean(statsTable.RMSE_IGS_vs_ERA5, 'omitnan'));
    fprintf('Mean VMF3 RMSE (DC): %.2f mm\n', mean(statsTable.RMSE_VMF3_vs_ERA5, 'omitnan'));
    fprintf('Mean IGS-ERA5 correlation: %.4f\n', mean(statsTable.R_IGS_vs_ERA5, 'omitnan'));
    fprintf('Mean VMF3-ERA5 correlation: %.4f\n', mean(statsTable.R_VMF3_vs_ERA5, 'omitnan'));
    fprintf('Mean IGS correlation (ETC): %.4f\n', mean(statsTable.R_IGS_ETC, 'omitnan'));
    fprintf('Mean ERA5 correlation (ETC): %.4f\n', mean(statsTable.R_ERA5_ETC, 'omitnan'));
    fprintf('Mean VMF3 correlation (ETC): %.4f\n', mean(statsTable.R_VMF3_ETC, 'omitnan'));
end

%% STATISTICAL METHOD IMPLEMENTATIONS

%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%1)********SUB-ROUTINEs TO IMPLEMENT THE THREE-CORNERED HAT (3CH) method 
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
function std_dev = computeThreeCorneredHat(data_matrix)
%-----------
%DESCRIPTION:
%-----------
% computeThreeCorneredHat Implements the Three-Cornered Hat (TCH) method for 
% uncertainty estimation. The three‐cornered hat (TCH) method is used to estimate 
% the uncertainties or error variances (standard deviations) of Three independent 
% measurement systems or datasets when no true reference is available or 
% without any a priori knowledge OR with respect to (w.r.t) the unknown true 
% value of the variable being measured. The method is particularly useful for 
% evaluating evapotranspiration products or other environmental datasets.
% -------------------------------------------------------------------------
% USAGE:
%       std_dev = computeThreeCorneredHat(data_matrix)
%
%1. INPUTS:
%          data_matrix: A matrix with N rows (time samples) and ...
%                         M columns (different measurement systems/products)
%                         e.g., data_matrix = [x1 x2 x3 x4];
%          NB: N must be the same for each measurement system & All NaNs 
%              must be removed
%
%2. OUTPUTS:
%           std_dev: A vector containing the estimated uncertainties or ...
%                    standard deviations (1 x M) of each measurement system   
%                    or dataset.The ith column corresponds to the measurement 
%                    system with observations in the ith column of data_matrix).
%
%REFERENCE:
%--------
%       [1] Xu, T., et al. (2019). Evaluation of twelve evapotranspiration 
%           products from machine learning, remote sensing and land surface 
%           models over conterminous United States. Journal of Hydrology, 
%           578, 124105. https://doi.org/10.1016/j.jhydrol.2019.124105
%       [2] He, X., et al. (2020). A Bayesian Three-Cornered Hat (BTCH) Method: 
%           Improving the Terrestrial Evapotranspiration Estimation. Remote 
%           Sensing, 12(5), 878. https://doi.org/10.3390/rs12050878
%       [3] Ferreira, V.G., Montecino, H.D.C., Yakubu, C.I., Heck, B., 2016. 
%           Uncertainties of the Gravity Recovery and Climate Experiment time-variable 
%           gravity-field solutions based on three-cornered hat method. J. Appl. 
%           Remote Sens 10, 015015. https://doi.org/10.1117/1.JRS.10.015015
%NOTE:
%   Original code by: Tongren Xu (xutr@bnu.edu.cn) and Xinlei He (hxlbsd@mail.bnu.edu.cn)
%   Available at: https://github.com/xutr-bnu/TCH_method
%   Modified by: Samuel Osah
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    
 try
    [~, num_products] = size(data_matrix);
    reference_idx = num_products;  % Last column is treated as reference
    
    % Calculate differences between each product and the reference
    diff_matrix = data_matrix(:, 1:end-1) - data_matrix(:, reference_idx);
    
    % Compute covariance matrix of the differences
    cov_matrix = cov(diff_matrix);
    
    % Initialize variables for optimization
    num_diff_products = num_products - 1;
    u = ones(1, num_diff_products);  % Unit vector
    
    % Initialize the result matrix
    R = zeros(num_products, num_products);
    
    % Set initial conditions for optimization
    R(end, end) = (2 * u / cov_matrix * u')^-1;  % Inverse of quadratic form
    initial_guess = zeros(num_products, 1);
    initial_guess(end) = R(end, end);
    
    % Optimization options
    opts = optimset('Algorithm', 'active-set', ...
                   'TolX', 2e-10, ...
                   'TolCon', 2e-10, ...
                   'Display', 'off');
    
    % Solve the constrained optimization problem
    optimal_r = fmincon(@(r) objective_function(r, cov_matrix), ...
                       initial_guess, ...
                       [], [], [], [], [], [], ...
                       @(r) constraints(r, cov_matrix), ...
                       opts);
    
    % Build the complete R matrix
    R(:, end) = optimal_r;
    
    % Fill in the upper triangular part of R
    for i = 1:num_diff_products
        for j = i:num_diff_products
            R(i, j) = cov_matrix(i, j) - R(end, end) + R(i, end) + R(j, end);
        end
    end
    
    % Symmetrize the matrix
    R = triu(R) + triu(R, 1)';
    
    % Extract standard deviations from the diagonal
    std_dev = sqrt(diag(R))'; 
        
catch ME
        warning('Error in 3CH calculation: %s', ME.message);
        std_dev = {NaN; NaN; NaN};
end 

end

%% Helper Functions

%1.OBJECTIVE_FUNCTION for the optimization problem
function F = objective_function(r, S)
%DESCRIPTION:
%-----------
%   This function computes the objective to be minimized in the TCH method,
%   which is based on the covariance structure of the differences between
%   measurement systems. The function corresponds to the equation   (8)
%   of Ferreira et al. (2016)

%REFERENCE:
%          Ferreira, V.G., Montecino, H.D.C., Yakubu, C.I., Heck, B., 2016. 
%          Uncertainties of the Gravity Recovery and Climate Experiment time-variable 
%          gravity-field solutions based on three-cornered hat method. J. Appl. 
%          Remote Sens 10, 015015. https://doi.org/10.1117/1.JRS.10.015015
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    num_vars = length(S);
    f = 0;
    
    % Sum of squared elements
    for j = 1:num_vars
        f = f + r(j)^2;
        for k = j+1:num_vars  % Only upper triangular part
            f = f + (S(j, k) - r(end) + r(j) + r(k))^2;
        end
    end
    
    % Normalize by the determinant of S
    F = f / (det(S))^(2/num_vars);
end

%=============================================END OF objective_function.m

%2. CONSTRAINTS function: Nonlinear constraints for the optimization problem
function [c, ceq] = constraints(r, S)
%DESCRIPTION:
%-----------
%   This function defines the constraints for the TCH optimization problem,
%   ensuring the solution maintains proper covariance relationships.
%   The function "constraints" corresponds to the equation (9) of 
%   Ferreira et al. (2016)
%REFERENCE:
%          Ferreira, V.G., Montecino, H.D.C., Yakubu, C.I., Heck, B., 2016. 
%          Uncertainties of the Gravity Recovery and Climate Experiment time-variable 
%          gravity-field solutions based on three-cornered hat method. J. Appl. 
%          Remote Sens 10, 015015. https://doi.org/10.1117/1.JRS.10.015015
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    num_vars = length(S);
    u = ones(1, num_vars);  % Unit vector
    
    % Extract variables for the constraint
    r_vector = r(1:num_vars)';
    r_last = r(end);
    
    % Compute the constraint value
    quadratic_form = (r_vector - r_last * u) / S * (r_vector - r_last * u)';
    c = -(r_last - quadratic_form) / (det(S))^(1/num_vars);
    
    % No equality constraints
    ceq = [];
end

%=============================================END OF constraints.m
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%********END OF THREE-CORNERED HAT (3CH) method subroutines
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%2)**SUB-ROUTINE TO IMPLEMENT THE EXTENDED TRIPLE COLLOCATION (ETC) method 
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
function [U1,U2,U3, R1,R2,R3] = computeExtendedTripleCollocation(observations)
%-----------
%DESCRIPTION
%-----------
%   Extended Triple Collocation (ETC) is a statistical method for estimating
%   the uncertainty (error variance) and correlation coefficients of three
%   measurement systems with respect to the unknown true value of the
%   variable being measured (e.g., soil moisture, wind speed). This
%   function "computeExtendedTripleCollocation" implements the ETC method 
%   by analyzing the covariance structure of the three collocated measurement
%   systems and estimating their respective uncertainties (U) and correlation 
%   coefficients (R) 
%
%USAGE:
%      [U1, U2, U3, R1, R2, R3] = computeExtendedTripleCollocation(observations) 

%1. INPUT:
%       observations - An N x 3 matrix of collocated observations from three
%                     measurement systems. Each column represents a different
%                     system, and rows represent simultaneous observations.
%                     Data must be complete (no NaNs) and have variability.
%                     N is the sample size.
%
%2. OUTPUTs:
%           U1, U2, U3 - Uncertainty estimates (standard deviation)
%                        for each measurement system
%           R1, R2, R3 - Correlation coefficients with respect to
%                         the unknown true value for each system
%
%   Example:
%           %Generate synthetic data for three measurement systems
%           N = 1000;
%           true_values = randn(N,1);
%           observations = [true_values + 0.1*randn(N,1), ...  % System 1
%                           true_values + 0.2*randn(N,1), ...   % System 2
%                            true_values + 0.3*randn(N,1)];       % System 3
%           [U1, U2, U3, R1, R2, R3] = computeExtendedTripleCollocation(observations);

%REFERENCE:
%       McColl, K.A., Vogelzang, J., Konings, A.G., Entekhabi, D., Piles, M.,
%       Stoffelen, A. (2014). Extended Triple Collocation: Estimating errors
%       and correlation coefficients with respect to an unknown target.
%       Geophysical Research Letters, 41, 6229-6236.
%       https://doi.org/10.1002/2014GL061322
%
%   Original code by: Kaighin McColl (original)
%   Date: September 14, 2014
%   Modified by: Samuel Osah
%   Last updated: [July 2024]
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

try
    %Input validation 0533327089
    if size(observations,2) ~= 3
        error('ETC:InputDimension', ...
             'Input data must be an N x 3 matrix with three measurement systems');
    end
    
    if any(isnan(observations(:)))
       error('ETC:MissingData', ...
             'Input data must not contain any missing values (NaNs)');
    end
    
    sample_sizes = arrayfun(@(col) length(unique(observations(:, col))), 1:3); 
    if any(sample_sizes == 1)
        error('ETC:NoVariability', ...
               ['Each measurement system must have variability. ', ...
                'Check for constant values or increase sample size.']);
    end
    
    % Estimate covariance matrix of the three measurement systems
    Q_hat = cov(observations); %covariance matrix

    % Calculate error variances
    errVar1 = Q_hat(1,1) - Q_hat(1,2)*Q_hat(1,3)/Q_hat(2,3); 
    errVar2 = Q_hat(2,2) - Q_hat(1,2)*Q_hat(2,3)/Q_hat(1,3); 
    errVar3 = Q_hat(3,3) - Q_hat(1,3)*Q_hat(2,3)/Q_hat(1,2);

    % Convert to uncertainties (standard deviations/RMSE)
    U1 = sqrt(errVar1);
    U2 = sqrt(errVar2);
    U3 = sqrt(errVar3);

    % Calculate correlation coefficients (R) with respect to the hypothetical true value
    R1 = sqrt(Q_hat(1,2)*Q_hat(1,3)/Q_hat(1,1)/Q_hat(2,3)); 
    R2 = sign(Q_hat(1,3)*Q_hat(2,3))*sqrt(Q_hat(1,2)*Q_hat(2,3)/Q_hat(2,2)/Q_hat(1,3)); 
    R3 = sign(Q_hat(1,2)*Q_hat(2,3))*sqrt(Q_hat(1,3)*Q_hat(2,3)/Q_hat(3,3)/Q_hat(1,2));

    %Compute squared correlation coefficients
    R1sqd = R1^2;
    R2sqd = R2^2;
    R3sqd = R3^2;

    %Check for potential issues with the estimates
    if any([errVar1, errVar2, errVar3] < 0)
        warning('ETC:NegativeVariance', ...
               ['Negative variance estimate detected. Possible causes:\n', ...
                '1. Small sample size\n', ...
                '2. Violation of ETC assumptions\n', ...
                '3. Poor quality measurements']);
    end

    % If squared correlation coefficients are negative, display a warning. 
    if any([R1^2, R2^2, R3^2] < 0)
        warning('Warning: at least one calculated squared correlation coefficient is negative. This can happen if the sample size is too small, or if one of the assumptions of ETC is violated.');
    end

    % Display summary if no output arguments are requested
    if nargout == 0
        fprintf('\nExtended Triple Collocation Results:\n');
        fprintf('--------------------------------\n');
        fprintf('System 1: Uncertainty = %.4f, Correlation = %.4f\n', U1, R1);
        fprintf('System 2: Uncertainty = %.4f, Correlation = %.4f\n', U2, R2);
        fprintf('System 3: Uncertainty = %.4f, Correlation = %.4f\n', U3, R3);
        fprintf('--------------------------------\n');
        fprintf('Note: Correlation is with respect to unknown true value\n\n');
    end

catch ME
        warning('Error in ETC calculation: %s', ME.message);
        U1 = NaN; U2 = NaN; U3 = NaN;
        R1 = NaN; R2 = NaN; R3 = NaN;
end 
      
end

%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
%********END OF TEXTENDED TRIPLE COLLOCATION (ETC) method subroutine
%=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

%% MAIN EXECUTION
% Execute the main function when script is run
if ~exist('OCTAVE_VERSION', 'builtin')
    % MATLAB execution
    PWV_Analysis_Main();
else
    % GNU Octave compatibility
    fprintf('Note: This script is optimized for MATLAB. Some features may not work in Octave.\n');
    PWV_Analysis_Main();
end