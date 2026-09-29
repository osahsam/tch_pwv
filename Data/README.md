# Data directory

`legacy_collocated_PWVs/` preserves the processed station-level PWV files that were present in the original uploaded GitHub repository. They represent an earlier processing archive and are separated from the final revised-manuscript statistics to avoid mixing versions.

- `legacy_collocated_PWVs/retained_in_final_27/` contains station IDs retained after the final >=700-day screening.
- `legacy_collocated_PWVs/excluded_lt700_days/` contains CGGN, DJIG, NURK, and RCMN, which were excluded from the final analysis.
- `station_inclusion.csv` records the valid-day count and final inclusion status.

The **authoritative numerical source for the revised manuscript** is `Analysis/final_27_station/PWV_Statistics_Results_with_nRMSE.csv`. The exact final post-QC station time series that produced those revised statistics were not included in the uploaded repository ZIP; add them here before claiming complete end-to-end reproduction from daily PWV files.

The archived CSV files contain identifiers/coordinates and collocated PWV series. The principal triplet analysed in the manuscript is IGS/GNSS, ERA5, and VMF3. `NGL_PWV` is retained as an ancillary field but is not part of the final 3CH/ETC triplet.
