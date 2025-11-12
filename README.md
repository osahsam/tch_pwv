# A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa

**Authors:**  
S. Osah¹*, A. A. Acheampong¹, S. A. Andam-Akorful¹, C. Gameti¹, R. M. Thundathil², C. Kelly³, B. Dadson¹, O. M. Abukari⁴, Y. Poku-Gyamfi⁵, T. B. Botchwey¹, J. Kojo¹, J. A. Quaye-Ballard¹, C. Fosu¹, I. Dadzie¹  

¹ Department of Geomatic Engineering, Kwame Nkrumah University of Science and Technology (KNUST), Kumasi, Ghana  
² GFZ German Research Centre for Geosciences, 14473 Potsdam, Germany  
³ Hangzhou International Innovation Institute of Beihang University, Hangzhou, China  
⁴ Survey and Mapping Division, Lands Commission, Accra, Ghana  
⁵ Council for Scientific and Industrial Research (CSIR) College of Science and Technology, Kumasi, Ghana  

*Corresponding author:* Samuel Osah (osahsamuel@knust.edu.gh)

---

## 🧭 Repository Purpose

This repository contains scripts and resources used in the research titled:  
**“A Three-Cornered Hat-Based Comparison of GNSS, VMF3, and ERA5 Precipitable Water Vapour Datasets over Africa.”**

The study evaluates the uncertainty and reliability of three precipitable water vapour (PWV) datasets — **GNSS**, **VMF3**, and **ERA5** — across 27 African GNSS stations (2015–2022).  
Three complementary methods were implemented to quantify uncertainty:
- **Three-Cornered Hat (3CH)**
- **Extended Triple Collocation (ETC)**
- **Direct Comparison (DC)**  

This repository serves as an open reference for future research in **atmospheric water vapour estimation**, **GNSS meteorology**, and **climate monitoring**.

---

## ⚙️ Tools Used

- **MATLAB** – core statistical and uncertainty analysis computations  
- **Python** – data processing, visualization, and spatial analysis  
- **Microsoft Excel** – data validation, tabular formatting, and summary statistics  
- **QGIS** – spatial mapping and visual representation of results  

---

## 📦 Dependencies (Python)

The Python scripts rely on the following libraries:

```python
pandas
numpy
matplotlib
geopandas
cartopy
mpl_toolkits
```

---

## 🗂️ Directory Structure

Below is the structure and purpose of each folder in the repository:

```
project_root/
│
├── Analysis/                  # Contains output datasets
│
├── Code/
│   ├── matlab/               # MATLAB scripts for core uncertainty analysis (3CH, ETC, DC)
│   └── python/               # Python scripts for visualization, data preprocessing, and mapping
│
├── Data/                     # Contains input Dataset used in the research
│
├── Figures/                  # Generated plots and maps (e.g., spatial uncertainty maps, time series)
│
└── README.md                 # Project documentation (this file)
```

---

## 🎯 Target Audience

This repository is intended for:
- Researchers and graduate students in **remote sensing**, **geodesy**, or **atmospheric sciences**.  
- Professionals in **climate and GNSS meteorology** exploring uncertainty estimation methods.  
- Academics seeking reproducible workflows for **multi-source PWV dataset comparison**.  

---

## ⚖️ License

This project is licensed under the **Apache License 2.0**.  
You are free to use, modify, and distribute this work, provided that:
- Appropriate credit is given to the original authors.
- A copy of the license is included in all derivative works.
- Any modifications are clearly stated.

For the full license text, see the [`LICENSE`](./LICENSE) file or visit:  
[https://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0)

---

## 📫 Contact

For questions, collaborations, or data access requests, please contact:  
**Samuel Osah** – osahsamuel@knust.edu.gh  
Department of Geomatic Engineering, KNUST, Kumasi, Ghana.

---

*© 2025. Department of Geomatic Engineering, KNUST. All Rights Reserved.*
