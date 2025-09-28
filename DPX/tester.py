# Waterfall viewer for dBm spectrogram CSVs with interactive colorbar (vmin/vmax) sliders.
#
# How to use:
# 1) Set `csv_path` to your CSV file path (whitespace- or comma-separated). Example:
#       csv_path = r"C:\path\to\your\spectrogram.csv"
# 2) Run this cell. A figure will appear.
# 3) Use the sliders to set colorbar Min/Max. Click "Autoscale" to reset to data range.
#
# Notes:
# - Each row is treated as one time slice; columns are frequency bins.
# - If your file is very large, loading can take a moment.
# - This uses matplotlib (no seaborn) and one plot per figure, per instructions.

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib

# --------- 1) Set your CSV path here ---------
csv_path = r"C:\Users\kuma-\Downloads\RSA_API-master\RSA_API-master\Utilities\RSA_API Apps V3.11\Apps\x64\920_all.txt"  # <-- PUT YOUR CSV FILE PATH HERE (e.g., r"C:\Users\you\spectrogram.csv")

# ---------------------------------------------

def load_spectrogram(path: str) -> np.ndarray:
    """Load entire CSV into a full-resolution 2D float array (no trimming/decimation)."""
    if not path or not os.path.exists(path):
        # Tiny dummy so the UI renders before a real path is set.
        return np.array([[-100, -101, -102], [-104, -105, -106], [-108, -109, -110]], dtype=float)
    # Try robust parsing: whitespace or commas. genfromtxt tolerates ragged spaces.
    try:
        data = np.genfromtxt(path, dtype=float, delimiter=None)
    except Exception:
        data = np.genfromtxt(path, dtype=float, delimiter=",")
    # Ensure 2D
    if data.ndim == 1:
        data = data[None, :]
    return np.array(data, dtype=float, copy=False)

# Initial load
Z = load_spectrogram(csv_path)

plt.close("all")
fig = plt.figure(figsize=(10, 5))
gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[12, 1, 1], hspace=0.35)

ax_img = fig.add_subplot(gs[0, 0])
ax_vmin = fig.add_subplot(gs[1, 0])
ax_vmax = fig.add_subplot(gs[2, 0])

# FULL DATA PLOT: each sample as a pixel (nearest, no resampling)
img = ax_img.imshow(
    Z,
    aspect="auto",
    origin="lower",
    interpolation="nearest",
    resample=False,  # <- ensure no internal downsampling
)
cbar = fig.colorbar(img, ax=ax_img)
cbar.set_label("Power [dBm]")
ax_img.set_xlabel("Frequency bin (index)")
ax_img.set_ylabel("Time (row index)")
title_base = "Waterfall (dBm) — plotting ALL samples"
ax_img.set_title(title_base)

# Sliders range
zmin = float(np.nanmin(Z))
zmax = float(np.nanmax(Z))
rng = max(1.0, (zmax - zmin))
pad = rng * 0.2
sl_min = zmin - pad
sl_max = zmax + pad
vmin_slider = Slider(ax=ax_vmin, label="Colorbar Min (dBm)", valmin=sl_min, valmax=sl_max, valinit=zmin)
vmax_slider = Slider(ax=ax_vmax, label="Colorbar Max (dBm)", valmin=sl_min, valmax=sl_max, valinit=zmax)

def apply_clim(_=None):
    vmin = float(vmin_slider.val)
    vmax = float(vmax_slider.val)
    if vmin >= vmax:
        vmax = vmin + 1e-6
        vmax_slider.set_val(vmax)
    img.set_clim(vmin=vmin, vmax=vmax)
    fig.canvas.draw_idle()

vmin_slider.on_changed(apply_clim)
vmax_slider.on_changed(apply_clim)

# Buttons: Autoscale & Reload
btn_ax_autoscale = fig.add_axes([0.83, 0.86, 0.13, 0.06])
btn_autoscale = Button(btn_ax_autoscale, "Autoscale")

btn_ax_reload = fig.add_axes([0.83, 0.78, 0.13, 0.06])
btn_reload = Button(btn_ax_reload, "Reload CSV")

def on_autoscale(event):
    data = img.get_array()
    zmin = float(np.nanmin(data))
    zmax = float(np.nanmax(data))
    vmin_slider.set_val(zmin)
    vmax_slider.set_val(zmax)

def on_reload(event):
    global Z
    Z = load_spectrogram(csv_path)
    img.set_data(Z)  # still full data, no decimation
    ax_img.set_xlim(left=-0.5, right=Z.shape[1]-0.5)
    ax_img.set_ylim(bottom=-0.5, top=Z.shape[0]-0.5)
    # refresh slider ranges
    zmin = float(np.nanmin(Z))
    zmax = float(np.nanmax(Z))
    rng = max(1.0, (zmax - zmin))
    pad = rng * 0.2
    vmin_slider.ax.set_xlim(zmin - pad, zmax + pad)
    vmax_slider.ax.set_xlim(zmin - pad, zmax + pad)
    vmin_slider.set_val(zmin)
    vmax_slider.set_val(zmax)
    ax_img.set_title(f"{title_base} — reloaded: {os.path.basename(csv_path) or '(no file set)'}")
    fig.canvas.draw_idle()

btn_autoscale.on_clicked(on_autoscale)
btn_reload.on_clicked(on_reload)

plt.show()

print("✅ Ready.")
print("1) Set csv_path near the top of this cell to your file path.")
print("2) Click 'Reload CSV'.")
print("3) Adjust colorbar Min/Max with the sliders.")
