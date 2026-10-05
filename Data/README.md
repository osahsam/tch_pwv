# Data directory

## Collocated PWV station archive

`Collocated_PWVs (unpreprocessed)/PWVdata_27 stations(unpreprocessed).zip` contains one daily CSV for each of the 27 retained stations. The files cover 2015–2022 subject to station availability and collocation completeness.

Required analysis columns include:

- `STN`, `DOY`, `YEAR`, `MONTH`, `DAY`
- `LAT`, `LON`, `H`
- `IGS_PWV`, `VMF3_PWV`, `ERA5_PWV`

An ancillary `NGL_PWV` field is present in the archived files but is not one of the three datasets forming the final 3CH/ETC triplet.

## Station metadata

`IGS STATIONS-Africa_27sta.csv` and `.xlsx` provide station name/location, country, African sub-region, latitude, longitude, and height.

## Multiple-comparison input

`MCT/MCTdata_RMSE-3CH_ETC_DC.csv` contains the prepared data used by the MATLAB multiple-comparison script `Code/mct.m`.

## External source datasets

The repository contains processed/collocated research data rather than a redistribution of all original external archives. Original IGS, VMF3, MERRA-2, and ERA5-derived products should be obtained from the public sources listed in the root `README.md` and `DATA_AVAILABILITY.md`.
