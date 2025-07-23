function [] = mct()
 
%Data file
file = 'RMSE-3CH_ETC_DC.csv';

%Import Data
Data = importdata(file);

%Get numeric part of data
data = Data.data;

%Get Data sources/models as column headers
models = Data.colheaders';

% models = Data.textdata;
% models=models(:,1)
% models=models(2:end)

%ANALYSIS OF VARIANNCE(ANOVA)
[p,t,stats] = anova1(data,models);
 
%MULTIPLE COMPARISON TEST(MCT)
figure
% [c,m,h,nms] = multcompare(stats,'alpha',0.05,'ctype','scheffe' or 'bonferroni' or 'dunnett' or 'tukey-kramer','dunn-sidak' )
[c,m,h,gnames] = multcompare(stats,'alpha',0.05,'ctype','scheffe');

%Display the multiple comparison results and the corresponding group names in a table
tbl = array2table(m,"RowNames",models, ...
    "VariableNames",["Mean","Standard Error"]);

tbl1 = array2table(c,"VariableNames", ...
    ["Group A","Group B","Lower Limit","A-B","Upper Limit","P-value"]);

title('Multiple Comparison of Means','fontweight','bold')
ylabel('Groups','fontweight','bold');

%BOXPLOT
% title('Comparison of VMF3 & IGS ZTD products','fontweight','bold')
% ylabel('ZTD in [m]','fontweight','bold');
% xlabel('Product','fontweight','bold')
 

%GRAPH SETTINGS
% title('Multiple Comparison of ZTD Means','fontweight','bold')
% ylabel('Prediction Models (Groups)','fontweight','bold');
% ylabel('ZTD Products (Groups)','fontweight','bold');
%xlabel('RMSE [cm]','fontweight','bold');
% xlabel('ZTD [m]','fontweight','bold');
% xlswrite('MCT_DLM_IGS.xls',c)

% xlabel('Mean ZTD [m]','fontweight','bold');