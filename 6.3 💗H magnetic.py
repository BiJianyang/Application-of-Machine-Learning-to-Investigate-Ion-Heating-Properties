import TS6_1 as ts6
import os
import glob
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

# ---------- I/O ----------
input_str = input("Enter date and shot number (e.g. 250317,22): ").strip()
date_part, shot_number = input_str.split(',')

base_dir = f"C:/Users/psaoz/Desktop/doppler content/{date_part}/asc/net"
file_pattern = f"shot{shot_number}-delay*_fit_result.xlsx"
file_list = glob.glob(os.path.join(base_dir, file_pattern))
if not file_list:
    raise FileNotFoundError(f"File not found: {file_pattern}")
file_path = file_list[0]
print("File found:", file_path)

# ---------- extract delay from filename ----------
m = re.search(r"delay(\d+)", os.path.basename(file_path))
delay_us = m.group(1) if m else "XXX"

# ---------- read data ----------
df = pd.read_excel(file_path)
z = pd.to_numeric(df.iloc[:, 3], errors='coerce')     # Z [mm]
r = pd.to_numeric(df.iloc[:, 4], errors='coerce')     # R [mm]
T = pd.to_numeric(df.iloc[:, 9], errors='coerce')     # Ti [eV]
mask = (~z.isna()) & (~r.isna()) & (~T.isna())
z, r, T = z[mask], r[mask], T[mask]

# ---------- interpolation grid ----------
zi = np.linspace(z.min(), z.max(), 300)
ri = np.linspace(150, 350, 300)
Z, R = np.meshgrid(zi, ri)
Ti_grid = griddata((z, r), T, (Z, R), method='cubic')

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(8, 6))

# Ti 背景图：氢气用 0–30 eV
levels = np.linspace(0, 20, 21)
cf = ax.contourf(Z, R, Ti_grid, levels=levels, cmap='jet', extend='both')
cbar = fig.colorbar(cf, ax=ax)
cbar.set_label('Ion Temperature Ti [eV]')
cbar.set_ticks(np.linspace(0, 20, 7))  # 0,5,...,30

# ========= 加上磁场线 =========
frame = int(delay_us)
rlim = (150/1000, 350/1000)
zlim = (z.min()/1000, z.max()/1000)

ψ = ts6.psi_at_t(date_part, int(shot_number), frame)
Rψ, Zψ = ts6.RZ_mesh()
Rψ, Zψ = Rψ.T[:ψ.shape[0], :ψ.shape[1]], Zψ.T[:ψ.shape[0], :ψ.shape[1]]

# mm 单位
Rψ *= 1000
Zψ *= 1000

# 区域限制
mask = (Rψ >= 150) & (Rψ <= 350) & (Zψ >= z.min()) & (Zψ <= z.max())
ψ_roi = np.where(mask, ψ, np.nan)

# 绘制磁场线
finite_vals = ψ_roi[np.isfinite(ψ_roi)]
if finite_vals.size > 0:
    levels_psi = np.linspace(finite_vals.min(), finite_vals.max(), 40)
    ax.contour(Zψ, Rψ, ψ_roi, levels=levels_psi, colors='k', linewidths=1)

# 标注
ax.set_xlabel('Z [mm]')
ax.set_ylabel('R [mm]')
ax.set_title(f' delay {delay_us} µs ')
ax.set_ylim(150, 350)
ax.set_xlim(-50, 50)
ax.set_aspect('equal', 'box')
plt.tight_layout()

# 保存
save_name = f"H_shot{shot_number}_delay{delay_us}_Ti_withBfield.png"
save_path = os.path.join(base_dir, save_name)
plt.savefig(save_path, dpi=300)
plt.show()

print("Image saved to:", save_path)
