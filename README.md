# PyQGIS-scripts-and-stuff

This repository contains a personal collection of small, utility scripts and functions written using **PyQGIS** (the Python API for QGIS). These scripts are designed to automate common geospatial processing tasks, data cleaning operations, and map production workflows within the QGIS environment.
## Data Sources

The scripts work primarily with Swedish open geospatial data, divided into two main categories:

- **NGP\_*** – structured datasets from the *National Geodata Platform (NGP)*, such as detailed development plans following Boverket and Lantmäteriet specifications.  
- **HVD\_*** – *High Value Datasets (HVD)* published by Lantmäteriet, accessible through STAC catalogs and open APIs.

Together, these datasets cover both the new, semantically modelled data from NGP and the established open base data released under the EU’s High Value framework.


---

## Environment and Compatibility

| Component | Version |
| :--- | :--- |
| **QGIS Desktop** | 3.44.2-Solothurn (or latest stable release in 3.x series) |
| **Python version** | 3.12.11 |
| **Tested OS** | **Windows** (Testing on other platforms is not guaranteed.) |

---

## Repository Structure

The scripts are organized for clarity and ease of use:

* `scripts/`: Contains the main Python files (`.py`) for individual tools and functions.
* `data_examples/`: (If applicable) Small, non-sensitive sample data files used for testing the scripts.
* `LICENSE`: The full text of the **GNU General Public License, Version 2 or any later version (GPLv2+)** governing the use of this code.

---

## Running the Scripts

The scripts in the `scripts/` folder are executed directly within the QGIS Python Console. Feel free to enhance them as you please.

### Procedure

1.  Open **QGIS Desktop**.
2.  Open the **Python Console** (Plugins > Python Console).
3.  Click the **"Show Editor"** button (usually a small file icon or pencil icon) within the Python Console panel to open the script editor.
4.  Use the **"Open file"** icon within the editor to browse to and select the desired script (`.py`) file from your local repository.
5.  Press the **"Run script"** button (usually a green play button or similar icon) to execute the code.

---

## License

All code contained in this repository is released under the **GNU General Public License, Version 2 or any later version (GPLv2+)**.

---

## Contribution

This is primarily a personal repository, but feedback, improvements and suggestions are welcome.

All ideas, requirements, debugging/testing is my work.

Coding is done by ChatGPT, Gemini and Claude.
