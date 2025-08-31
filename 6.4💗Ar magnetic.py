import TS6_1 as ts6
import os
import glob
import re
import sys
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
delay_us = m.group(1) if m else "XXX"     # micro‑seconds as string

# ---------- read data ----------
df = pd.read_excel(file_path)
z = pd.to_numeric(df.iloc[:, 3], errors='coerce')
r = pd.to_numeric(df.iloc[:, 4], errors='coerce')
T = pd.to_numeric(df.iloc[:, 9], errors='coerce')

mask = (~z.isna()) & (~r.isna()) & (~T.isna())
z, r, T = z[mask], r[mask], T[mask]

# ---------- interpolation grid ----------
zi = np.linspace(z.min(), z.max(), 300)
ri = np.linspace(150, 350, 300)
Z, R = np.meshgrid(zi, ri)
Ti_grid = griddata((z, r), T, (Z, R), method='cubic')

# ---------- plotting ----------
fig, ax = plt.subplots(figsize=(8, 6))

# 温度图背景
levels = np.linspace(0, 100, 101)              # 0‑100 eV, 1 eV steps
cf = ax.contourf(Z, R, Ti_grid, levels=levels, cmap='jet', extend='both')    # force full color range

# 温度图 colorbar
cbar = fig.colorbar(cf, ax=ax)
cbar.set_label('Ion Temperature Ti [eV]')
cbar.set_ticks(np.linspace(0, 90, 11))         # 0,10,...,100

# ========== 加入磁场等高线 ==========
frame = int(delay_us)  # 延迟 µs 就是 frame
rlim = (150/1000, 350/1000)  # mm → m
zlim = (z.min()/1000, z.max()/1000)

# 获取 ψ
ψ_all = ts6.psi_at_t(date_part, int(shot_number), frame)
R_all, Z_all = ts6.RZ_mesh()
ψ_shape = ψ_all.shape
R_all, Z_all = R_all.T[:ψ_shape[0], :ψ_shape[1]], Z_all.T[:ψ_shape[0], :ψ_shape[1]]

# 单位换成 mm 以匹配温度图
R_all *= 1000
Z_all *= 1000

# 筛选感兴趣区域
mask = (R_all >= 150) & (R_all <= 350) & (Z_all >= z.min()) & (Z_all <= z.max())
ψ_roi = np.where(mask, ψ_all, np.nan)

# 设置磁场等高线 levels
finite_vals = ψ_roi[np.isfinite(ψ_roi)]
if finite_vals.size > 0:
    levels_psi = np.linspace(finite_vals.min(), finite_vals.max(), 40)
    ax.contour(Z_all, R_all, ψ_roi, levels=levels_psi, colors='k', linewidths=1)

# 图形信息
ax.set_xlabel('Z [mm]')
ax.set_ylabel('R [mm]')
ax.set_title(f' delay {delay_us} µs ')
ax.set_ylim(150, 350)
ax.set_xlim(-50, 50)
ax.set_aspect('equal', 'box')
plt.tight_layout()

# 保存
save_name = f"Ar_shot{shot_number}_delay{delay_us}_Ti_withBfield.png"
save_path = os.path.join(base_dir, save_name)
plt.savefig(save_path, dpi=300)
plt.show()

print("Image saved to:", save_path)
