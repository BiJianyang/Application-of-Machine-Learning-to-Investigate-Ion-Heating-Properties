import os
import glob
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

# ----------- I/O -----------
date_part, shot_number = input("Enter date and shot number (e.g. 250317,22): ").strip().split(',')

base_dir    = f"C:/Users/psaoz/Desktop/doppler content/{date_part}/asc/net"
file_pattern = f"shot{shot_number}-delay*_fit_result.xlsx"
file_list    = glob.glob(os.path.join(base_dir, file_pattern))
if not file_list:
    raise FileNotFoundError(f"File not found: {file_pattern}")
file_path = file_list[0]
print("File found:", file_path)

# ----------- extract delay -----------
m = re.search(r"delay(\d+)", os.path.basename(file_path))
delay_us = m.group(1) if m else "XXX"

# ----------- read data -----------
df = pd.read_excel(file_path)
z = pd.to_numeric(df.iloc[:, 3], errors='coerce')     # Z [mm]
r = pd.to_numeric(df.iloc[:, 4], errors='coerce')     # R [mm]
T = pd.to_numeric(df.iloc[:, 9], errors='coerce')     # Ti [eV]
mask = (~z.isna()) & (~r.isna()) & (~T.isna())
z, r, T = z[mask], r[mask], T[mask]

# ----------- interpolation grid (R=150–350 mm) -----------
zi = np.linspace(z.min(), z.max(), 300)
ri = np.linspace(150, 350, 300)
Z, R = np.meshgrid(zi, ri)
Ti_grid = griddata((z, r), T, (Z, R), method='cubic')

# ----------- plot: fixed 0–30 eV -----------
plt.figure(figsize=(8, 6))
levels = np.linspace(0, 30, 31)                    # 0‑30 by 1 eV
cf = plt.contourf(Z, R, Ti_grid, levels=levels,
                  cmap='jet', extend='both')       # clamp + full bar
cbar = plt.colorbar(cf)
cbar.set_label('Ion Temperature Ti [eV]')
cbar.set_ticks(np.linspace(0, 30, 7))              # 0,5,10,…,30

plt.xlabel('Z [mm]')
plt.ylabel('R [mm]')
plt.title(f'{date_part} shot {shot_number}  delay {delay_us} µs ')
plt.ylim(150, 350)
plt.gca().set_aspect('equal', 'box')
plt.tight_layout()

# ----------- save -----------
save_name = f"H_shot{shot_number}_delay{delay_us}_Ti.png"
plt.savefig(os.path.join(base_dir, save_name), dpi=300)
plt.show()

print("Image saved to:", save_name)
