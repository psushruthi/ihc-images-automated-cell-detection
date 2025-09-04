# Automated IHC Cell Detection – KOOB Analysis

## About the Project
This repository contains an automated pipeline for immunohistochemistry (IHC) image analysis using Python on [IMARIS](https://imaris.oxinst.com/newrelease?gad_source=1&gad_campaignid=22096982345&gbraid=0AAAAAD_QDQzJMUcAVA_Vn4lUv4hVtZQJi&gclid=Cj0KCQjw8eTFBhCXARIsAIkiuOyltNKRt4QPaAzD1Ki8guO-PVR1OVz8P8dRk2IWxd-GxPcnvh-wnhsaAo2ZEALw_wcB), a 3D Imaging Software. 
It was developed as part of the [MODEL-AD](https://www.model-ad.org) (Model Organism Development for Late-Onset Alzheimer’s Disease) study at the [Stark Neurosciences Research Institute](https://medicine.iu.edu/research-centers/neurosciences), Indiana University.  

The project focuses on KOOB analysis of mouse brain sections, automating the detection of **GFAP**, **IBA1**, and **NeuN**-positive cells in hippocampus and cortex regions.

---

## Study Context
The KOOB analysis investigates astrocytic (GFAP), microglial (IBA1), and neuronal (NeuN) markers in Alzheimer’s disease models.  
Traditionally, these markers are quantified manually, which is time-consuming and inconsistent.  
This pipeline reduces subjectivity by automating the workflow within Imaris, while still allowing flexibility to adjust thresholds for individual images where staining differences occur.  

---

## Pipeline Development
I built this pipeline to streamline the IHC workflow directly inside **Imaris**:

1. **Input Dataset**  
   Load `.ims` images into Imaris. Each dataset contains multiple channels (DAPI, GFAP, IBA1, NeuN).

2. **Colocalization**  
   - The script [`koobanalysis.py`](https://github.com/psushruthi/ihc-images-automated-cell-detection/blob/main/Scripts/koobanalysis.py) creates binary **colocalized channels** (e.g., GFAP and DAPI, IBA1 and DAPI) for hippocampus and cortex.  
   - Thresholds are defined in the scripts and can be adjusted per image to reduce background noise.  
   - The new channels are added back into the Imaris scene for visualization.

3. **Surface Detection**  
   - Scripts ([`gfapsurfaces.py`](https://github.com/psushruthi/ihc-images-automated-cell-detection/blob/main/Scripts/gfapsurfaces.py), [`iba1surfaces.py`](https://github.com/psushruthi/ihc-images-automated-cell-detection/blob/main/Scripts/iba1surfaces.py), [`neunsurfaces.py`](https://github.com/psushruthi/ihc-images-automated-cell-detection/blob/main/Scripts/neunsurfaces.py)) run **surface detection** on the colocalized channels.  
   - Parameters for smoothing, seed points, and intensity are kept consistent across animals.  

4. **Execution**  
   - Scripts are launched inside the **Imaris XT Python terminal**:  
     ```python
     exec(open(r'PATH\TO\koobanalysis.py').read())
     ```  
   - Similar commands run the surface detection scripts.

5. **Results**  
   - Detected surfaces are exported in Imaris via the **Statistics → Export** function.  
   - All results are consolidated into the Excel file `KOOB Analysis.xlsx`.

---

## Results
- The file [`Results/KOOB Analysis.xlsx`](https://github.com/psushruthi/ihc-images-automated-cell-detection/blob/main/Results/KOOB%20Analysis.csv) contains surface counts and thresholds used for each animal.  
- This ensures transparency in parameter selection and reproducibility across runs.  
- The results can be directly compared across cohorts (sex, genotype, diet, etc.) to evaluate staining differences.  

---

## Reproducibility
- Channel indices are defined at the top of each script and can be updated if your dataset differs.  
- Thresholds are image-dependent, but the **pipeline logic stays identical**, ensuring reproducible workflows.  
- By keeping all scripts and outputs in one repository, the entire KOOB workflow can be reproduced or adapted by others using the same MODEL-AD datasets.  

---

## Acknowledgments
This work was conducted at the MODEL-AD Lab at the [Stark Neurosciences Research Institute](https://medicine.iu.edu/research-centers/neurosciences), Indiana University School of Medicine.  

Special thanks to collaborators who assisted with defining ROIs and validating results.  

---

## License

If you use or adapt this workflow, please cite:  
Panakanti, S. (2025). Automated IHC Cell Detection – KOOB Analysis.
MODEL-AD, Stark Neurosciences Research Institute.
GitHub: https://github.com/psushruthi/ihc-images-automated-cell-detection

---

## Contact

For questions or suggestions, please contact [Sushruthi Panakanti](https://github.com/psushruthi) at [spanakan@iu.edu](spanakan@iu.edu).    
Thank you.
