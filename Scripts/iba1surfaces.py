import ImarisLib
import Imaris
import sys

# Connect to Imaris
def GetImarisApp():
    vImarisLib = ImarisLib.ImarisLib()
    vApp = vImarisLib.GetApplication(0)
    return Imaris.IApplicationPrx.checkedCast(vApp)

imaris_app = GetImarisApp()

if not imaris_app:
    print("Failed to connect to Imaris.")
    sys.exit(1)

print("Connected to Imaris!")

# Get Dataset and Image Processing
dataset = imaris_app.GetDataSet()
image_processing = imaris_app.GetImageProcessing()

if not dataset:
    print("No dataset found.")
    sys.exit(1)

print("Dataset loaded.")
print("Image processing module ready.")

# --- Surface Detection Function ---
def detect_iba1_surfaces(channel_index, region_name, smooth_width=0.9, contrast_width=100.0, threshold=500.0):
    print(f"Detecting IBA1 surfaces for {region_name} (Channel {channel_index})...")
    try:
        surfaces = image_processing.DetectSurfaces(
            dataset,
            [],                 
            channel_index,
            smooth_width,
            contrast_width,
            True,              
            threshold,         
            ""                 
        )
        surfaces.SetName(f"{region_name} IBA1")
        surfaces.SetVisible(True)
        imaris_app.GetSurpassScene().AddChild(surfaces, -1)
        print(f"{region_name} IBA1 surfaces added to scene! ({surfaces.GetNumberOfSurfaces()} surfaces)")
    except Exception as e:
        print(f"Error detecting surfaces for {region_name}: {e}")

# Detect in Hippocampus
detect_iba1_surfaces(channel_index=12, region_name="Hippocampus")

# Detect in Cortex
detect_iba1_surfaces(channel_index=13, region_name="Cortex")

print("Surface detection complete.")
