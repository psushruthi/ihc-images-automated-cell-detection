# -*- coding: utf-8 -*-
"""
koobanalysis.py

- Build coloc channels (GFAP+DAPI, IBA1+DAPI) for Hippo and Cortex
- Color GFAP colocs green; IBA1 colocs red
- Then run IBA1 and GFAP surface scripts

Binary AND mask logic (UInt16):
  out[x] = 65535 if (A[x] >= THR_A and DAPI[x] >= THR_DAPI) else 0
"""

import ImarisLib, array, sys, os

# -------- CONFIG: channel indices (API, 0-based) --------
CH_DAPI       = 0
CH_GFAP_HIP   = 4
CH_IBA1_HIP   = 5
CH_NEUN_HIP   = 6  # (unused here, just documented)
CH_GFAP_CTX   = 7
CH_IBA1_CTX   = 8
CH_NEUN_CTX   = 9  # (unused here, just documented)

# -------- THRESHOLDS --------
# GFAP colocalization
THR_DAPI_GFAP = 0.0
THR_GFAP      = 6000.0

# IBA1 colocalization
THR_DAPI_IBA1 = 0.0
THR_IBA1      = 600.0

# -------- Output channel names & colors --------
OUT_G_HIP_NAME = "Hippo GFAP DAPI"
OUT_G_CTX_NAME = "Ctx GFAP DAPI"
OUT_I_HIP_NAME = "Hippo IBA1 DAPI"
OUT_I_CTX_NAME = "Ctx IBA1 DAPI"

COLOR_GREEN = 0x00FF00FF  # RGBA
COLOR_RED   = 0xFF0000FF  # RGBA

# -------- Paths to surface scripts --------
PATH_IBA1_SURFACES = "/Volumes/Sushruthi/Automation/KOOBStaining/Scripts/iba1surfaces.py"
PATH_GFAP_SURFACES = "/Volumes/Sushruthi/Automation/KOOBStaining/Scripts/gfapsurfaces.py"

# =======================================

def _clone_same_C(app, ds):
    """Clone dataset with same XYZCT and copy all channels (names/colors/data)."""
    Imaris = ImarisLib.Imaris
    sx, sy, sz = ds.GetSizeX(), ds.GetSizeY(), ds.GetSizeZ()
    sc, st     = ds.GetSizeC(), ds.GetSizeT()
    print(f"[clone] Create new dataset XYZCT=({sx},{sy},{sz},{sc},{st})")
    factory = app.GetFactory()
    new_ds = factory.CreateDataSet()
    # Use the type from tType; your data is UInt16
    new_ds.Create(Imaris.tType.eTypeUInt16, sx, sy, sz, sc, st)

    # Spatial extents (guard each)
    for axis in ("X","Y","Z"):
        try:
            getattr(new_ds, f"SetExtendMin{axis}")(getattr(ds, f"GetExtendMin{axis}")())
            getattr(new_ds, f"SetExtendMax{axis}")(getattr(ds, f"GetExtendMax{axis}")())
            print(f"[ext] SetExtend*{axis} ok")
        except Exception as e:
            print(f"[ext] SetExtend*{axis} skipped:", e)

    print(f"[clone] copying {sc} channels …")
    for c in range(sc):
        try: new_ds.SetChannelName(c, ds.GetChannelName(c))
        except Exception: pass
        try: new_ds.SetChannelColorRGBA(c, ds.GetChannelColorRGBA(c))
        except Exception: pass
        for t in range(st):
            for z in range(sz):
                plane = ds.GetDataSubVolumeAs1DArrayFloats(0,0,z,c,t,sx,sy,1)
                new_ds.SetDataSubVolumeAs1DArrayFloats(plane,0,0,z,c,t,sx,sy,1)
        nm = ds.GetChannelName(c) if hasattr(ds,"GetChannelName") else f"ch{c}"
        print(f"[clone] copied ch{c} ({nm})")
    return new_ds

def _ensure_extra_channels(app, ds, extra):
    """Ensure 'extra' new channels exist; if SetSizeC doesn't actually grow, create target‑C clone."""
    sc = ds.GetSizeC()
    target_c = sc + extra
    grew = False
    try:
        ds.SetSizeC(target_c)
        grew = (ds.GetSizeC() == target_c)
        print(f"[grow] attempted in‑place to {target_c}; GetSizeC() -> {ds.GetSizeC()}")
    except Exception as e:
        print("[grow] in‑place SetSizeC raised:", e)
        grew = False
    if grew:
        return ds, sc

    # Fallback: build target‑C dataset and copy old channels
    print(f"[grow] fallback: creating target‑C dataset C={target_c}")
    Imaris = ImarisLib.Imaris
    sx, sy, sz, st = ds.GetSizeX(), ds.GetSizeY(), ds.GetSizeZ(), ds.GetSizeT()
    aux = app.GetFactory().CreateDataSet()
    aux.Create(Imaris.tType.eTypeUInt16, sx, sy, sz, target_c, st)

    for axis in ("X","Y","Z"):
        try:
            getattr(aux, f"SetExtendMin{axis}")(getattr(ds, f"GetExtendMin{axis}")())
            getattr(aux, f"SetExtendMax{axis}")(getattr(ds, f"GetExtendMax{axis}")())
        except Exception:
            pass

    for c in range(sc):
        try: aux.SetChannelName(c, ds.GetChannelName(c))
        except Exception: pass
        try: aux.SetChannelColorRGBA(c, ds.GetChannelColorRGBA(c))
        except Exception: pass
        for t in range(st):
            for z in range(sz):
                plane = ds.GetDataSubVolumeAs1DArrayFloats(0,0,z,c,t,sx,sy,1)
                aux.SetDataSubVolumeAs1DArrayFloats(plane,0,0,z,c,t,sx,sy,1)

    app.SetDataSet(aux)
    print(f"[grow] switched to target‑C dataset; C={aux.GetSizeC()}")
    return aux, sc

def _write_and_mask_U16(ds, ch_a, thr_a, ch_b, thr_b, out_index, out_name, out_color):
    """Binary AND mask → UInt16 channel: 65535 if (a>=thr_a and b>=thr_b) else 0."""
    sx, sy, sz, st = ds.GetSizeX(), ds.GetSizeY(), ds.GetSizeZ(), ds.GetSizeT()
    plane = sx * sy
    named = False
    total_true = 0

    for t in range(st):
        for z in range(sz):
            a = ds.GetDataSubVolumeAs1DArrayFloats(0,0,z,ch_a,t,sx,sy,1)
            b = ds.GetDataSubVolumeAs1DArrayFloats(0,0,z,ch_b,t,sx,sy,1)
            out = array.array('H', [0]*plane)
            cnt = 0
            # fast inline AND
            for i in range(plane):
                if a[i] >= thr_a and b[i] >= thr_b:
                    out[i] = 65535
                    cnt += 1
            total_true += cnt
            ds.SetDataSubVolumeAs1DArrayShorts(out, 0,0,z, out_index, t, sx, sy, 1)

            if not named:
                try: ds.SetChannelName(out_index, out_name)
                except Exception: pass
                try: ds.SetChannelColorRGBA(out_index, out_color)
                except Exception: pass
                named = True

    frac = total_true / float(plane * max(st,1) * max(sz,1))
    print(f"[coloc] {out_name} -> ch{out_index}, true voxels={total_true}, frac={frac:.6f}")

def _run_script(label, path):
    """Exec another python file (surface builders)."""
    try:
        with open(path, "r") as fh:
            code = fh.read()
    except Exception as e:
        print(f"[surfaces] {label}: could not read file: {e}")
        return
    try:
        exec(compile(code, path, "exec"), globals(), globals())
        print(f"[surfaces] executed: {label}")
    except Exception as e:
        print(f"[surfaces] {label}: execution error: {e}")

# ==================== main ====================

def XT_Koob_Analysis(aImarisApplicationID=0):
    # connect
    lib = ImarisLib.ImarisLib()
    app = lib.GetApplication(aImarisApplicationID)
    if app is None: raise RuntimeError("Could not connect to Imaris.")
    ds = app.GetDataSet()
    if ds is None: raise RuntimeError("No dataset open in Imaris.")

    print("[info] starting Koob Analysis")
    print(f"[info] src XYZCT=({ds.GetSizeX()},{ds.GetSizeY()},{ds.GetSizeZ()},{ds.GetSizeC()},{ds.GetSizeT()})")
    print(f"[info] GFAP thresholds: DAPI>={THR_DAPI_GFAP}, GFAP>={THR_GFAP}")
    print(f"[info] IBA1 thresholds: DAPI>={THR_DAPI_IBA1}, IBA1>={THR_IBA1}")

    # 1) clone and switch
    work = _clone_same_C(app, ds)
    app.SetDataSet(work)
    print(f"[info] switched to clone; C={work.GetSizeC()}")

    # 2) ensure +4 channels and record output indices
    work, start = _ensure_extra_channels(app, work, extra=4)
    out_g_hip = start + 0
    out_g_ctx = start + 1
    out_i_hip = start + 2
    out_i_ctx = start + 3
    print(f"[info] output indices -> {OUT_G_HIP_NAME}:{out_g_hip}, {OUT_G_CTX_NAME}:{out_g_ctx}, {OUT_I_HIP_NAME}:{out_i_hip}, {OUT_I_CTX_NAME}:{out_i_ctx}")

    # 3) write coloc masks
    # GFAP (green)
    _write_and_mask_U16(work, CH_GFAP_HIP, THR_GFAP, CH_DAPI, THR_DAPI_GFAP, out_g_hip, OUT_G_HIP_NAME, COLOR_GREEN)
    _write_and_mask_U16(work, CH_GFAP_CTX, THR_GFAP, CH_DAPI, THR_DAPI_GFAP, out_g_ctx, OUT_G_CTX_NAME, COLOR_GREEN)

    # IBA1 (red)
    _write_and_mask_U16(work, CH_IBA1_HIP, THR_IBA1, CH_DAPI, THR_DAPI_IBA1, out_i_hip, OUT_I_HIP_NAME, COLOR_RED)
    _write_and_mask_U16(work, CH_IBA1_CTX, THR_IBA1, CH_DAPI, THR_DAPI_IBA1, out_i_ctx, OUT_I_CTX_NAME, COLOR_RED)

    # 4) run surface scripts (assumes they operate on the current Imaris dataset/context)
    print("[info] running surface scripts…")
    _run_script("IBA1 surfaces", PATH_IBA1_SURFACES)
    _run_script("GFAP surfaces", PATH_GFAP_SURFACES)

    print("[done] Koob Analysis complete.")

# allow run via exec(...)
if __name__ == "__main__":
    XT_Koob_Analysis(0)
