# A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa

**Authors:**  
S. Osah¹*, A. A. Acheampong¹, S. A. Andam-Akorful¹, C. Gameti¹, R. M. Thundathil², C. Kelly³, B. Dadson¹, O. M. Abukari⁴, Y. Poku-Gyamfi⁵, T. B. Botchwey¹, J. Kojo¹, J. A. Quaye-Ballard¹, C. Fosu¹, I. Dadzie¹

¹ Department of Geomatic Engineering, Kwame Nkrumah University of Science and Technology (KNUST), Kumasi, Ghana  
² GFZ German Research Centre for Geosciences, Potsdam, Germany  
³ Hangzhou International Innovation Institute of Beihang University, Hangzhou, China  
⁴ Survey and Mapping Division, Lands Commission, Accra, Ghana  
⁵ Council for Scientific and Industrial Research (CSIR) College of Science and Technology, Kumasi, Ghana

*Corresponding author:* Samuel Osah — osahsamuel@knust.edu.gh

## Repository purpose

This repository supports the manuscript **“A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa.”** It contains processed station data, uncertainty-analysis code, summary products, and manuscript figures used to compare GNSS/IGS-, ERA5-, and VMF3-derived precipitable water vapour (PWV) over Africa during 2015–2022.

The revised manuscript uses **27 IGS stations** that satisfy a final data-completeness threshold of **at least 700 valid collocated days**. Four stations from the earlier analysis (CGGN, DJIG, NURK, and RCMN) are retained separately for transparency but are excluded from the final 27-station statistics.

## Methods represented

- **Three-Cornered Hat (3CH):** reference-independent uncertainty estimation.
- **Extended Triple Collocation (ETC):** uncertainty and correlation with respect to a latent common signal.
- **Direct Comparison (DC):** pairwise comparison using ERA5 as the reference dataset.
- **Normalised RMSE (nRMSE):** ETC-derived RMSE scaled by station mean ERA5 PWV to contextualise relative uncertainty across different moisture regimes.

## Data sources

| Product | Role | Public source |
|---|---|---|
| IGS ZTD | GNSS tropospheric input | [NASA CDDIS](https://cddis.nasa.gov/archive/gnss/products/troposphere/zpd/) |
| VMF3_OP | Model-based tropospheric product | [TU Wien VMF3 products](https://vmf.geo.tuwien.ac.at/trop_products/GNSS/VMF3/VMF3_OP/daily/) |
| MERRA-2 M2I1NXASM v5.12.4 | Surface meteorological parameters used in GNSS-PWV retrieval | [NASA GES DISC](https://disc.gsfc.nasa.gov/datasets/M2I1NXASM_5.12.4/summary), DOI: [10.5067/3Z173KIE2TPD](https://doi.org/10.5067/3Z173KIE2TPD) |
| ERA5-based site product | Comparison PWV product | [Wuhan University NWM service](http://gmet.users.sgg.whu.edu.cn/en/customized/NWMs-based-site/submit/) |

The original processed/collocated station files supplied in the uploaded repository are preserved under `Data/legacy_collocated_PWVs/`. They document the earlier processing archive and include an ancillary `NGL_PWV` field that is not one of the three products forming the final 3CH/ETC triplet. The **validated 27-station statistics in `Analysis/final_27_station/` are the authoritative numerical source for the revised manuscript**.

## Repository structure

```text
tch_pwv/
├── Analysis/
│   ├── final_27_station/       # Statistics and summaries used in the revised manuscript
│   └── legacy_31_station/      # Earlier outputs retained for provenance only
├── Code/
│   ├── final_manuscript/       # Portable scripts for the revised 27-station summaries
│   └── *.m / *.py              # Original analysis/plotting scripts retained for provenance
├── Data/
│   ├── legacy_collocated_PWVs/ # Original processed station series from the uploaded repository
│   │   ├── retained_in_final_27/
│   │   └── excluded_lt700_days/
│   ├── MCT/                    # Multiple-comparison input
│   ├── station_inclusion.csv   # Completeness screening record
│   └── IGS STATIONS-Africa.xlsx
├── Figures/
│   ├── final_27_station/       # Current nRMSE/ETC figures
│   └── legacy_31_station/      # Earlier figures retained for provenance only
├── CITATION.cff
├── requirements.txt
├── REPRODUCIBILITY.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Quick start

### Python environment

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

To reproduce the revised regional, continental, and network-wide ETC/nRMSE summaries:

```bash
python Code/final_manuscript/nrmse_summary_analysis.py
```

Generated CSV summaries are written to `Analysis/final_27_station/`.

### MATLAB core analysis

`Code/PWV_Analysis_TCH_ETC_DC.m` contains the original implementations of 3CH, ETC, and DC and is retained for methodological transparency. The original station time series supplied with the repository represent an earlier processing archive; therefore the validated final station-level statistics in `Analysis/final_27_station/` should be used for reproducing the revised manuscript summaries.

> **Important:** several historical Python plotting scripts in `Code/` retain local Windows paths from the original analysis environment. They are preserved for provenance. The portable script in `Code/final_manuscript/` is the recommended entry point for the revised manuscript summaries.

## Reproducibility note

The original GitHub ZIP contained 31-station analysis outputs and processed station files from an earlier workflow. The revised manuscript uses a 27-station post-screening analysis and updated validated statistics. Because the exact final post-QC/collocation station time series were not present in the uploaded ZIP, the repository separates the earlier materials as **legacy** and provides the validated final 27-station statistics and derived summaries as the authoritative source for the revised manuscript. For full end-to-end reproduction from daily PWV time series, the exact final post-QC station files should be added when available.

## Final 27-station analysis products

`Analysis/final_27_station/PWV_Statistics_Results_with_nRMSE.csv` is the validated station-level statistics table used for the revised manuscript. It includes 3CH and ETC RMSE, ETC correlation coefficients, DC metrics, mean ERA5 PWV, and normalised RMSE.

The accompanying summary files provide:

- `regional_ETC_summary.csv` — regional mean ETC RMSE, nRMSE, and ETC correlation;
- `continental_ETC_summary.csv` — continental-scale means across the 27 retained stations;
- `network_correlation_summary.csv` — network-wide Pearson correlations of mean PWV with absolute RMSE, nRMSE, and `R_ETC`;
- `regional_IGS_pwv_correlations.csv` — regional Pearson relationships between mean PWV and IGS absolute/nRMSE metrics where at least two stations are available;
- `pooled_metric_relationships.csv` — pooled ETC RMSE/nRMSE/`R_ETC` relationships used in the SNR discussion.

## Data-completeness screening

The final revision applies a minimum threshold of **700 valid collocated days**. `Data/station_inclusion.csv` records the number of valid observations in the archived station files and the final inclusion/exclusion status. The four excluded stations (CGGN, DJIG, NURK, and RCMN) are preserved under `Data/legacy_collocated_PWVs/excluded_lt700_days/` for transparency.

## Citation

If you use this repository, please cite the associated manuscript and this repository. A machine-readable citation record is provided in [`CITATION.cff`](./CITATION.cff).

Repository: https://github.com/osahsam/tch_pwv

## Licence

This repository is distributed under the [Apache License 2.0](./LICENSE).

## Contact

**Samuel Osah**  
Department of Geomatic Engineering, KNUST, Kumasi, Ghana  
osahsamuel@knust.edu.gh
