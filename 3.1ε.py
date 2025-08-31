import numpy as np
import pandas as pd
import os
from glob import glob


date_shot = input("请输入日期和shot编号，例如 250317,22：").strip()
date, shot = date_shot.split(',')

base_dir = rf"C:\Users\psaoz\Desktop\doppler content\{date}\asc\net\shot{shot}_L_output"
excel_files = sorted(glob(os.path.join(base_dir, "Z*_L.csv")))
inverse_dispersion = 0.0038  # 每像素对应的波长差 [nm/pixel]

for file in excel_files:
    df = pd.read_csv(file, header=None)


    empty_row_indices = df[df.isnull().all(axis=1)].index.tolist()
    if not empty_row_indices:
        print(f"⚠️ 未找到空行，跳过：{file}")
        continue
    split_idx = empty_row_indices[0]


    wavelength_pixels = df.iloc[0, 1:-1].astype(float).values
    wavelengths_nm = np.round(wavelength_pixels * inverse_dispersion, 4)


    L_block = df.iloc[split_idx+1:].reset_index(drop=True)
    channel_ids = L_block.iloc[:, 0].values
    p_vals = L_block.iloc[:, -1].values.astype(float)
    L_vals = L_block.iloc[:, 1:-1].values.astype(float)

    sort_idx = np.argsort(p_vals)
    p_sorted = p_vals[sort_idx]
    L_sorted = L_vals[sort_idx]
    channel_sorted = channel_ids[sort_idx]

    M, K = L_sorted.shape
    epsilon = np.zeros((M, K))

    for n in range(M):
        rn = p_sorted[n]
        for k in range(K):
            integral = 0
            for m in range(n+1, M):
                pm = p_sorted[m]
                if pm == rn:
                    continue
                dL = (L_sorted[m, k] - L_sorted[m - 1, k]) / (p_sorted[m] - p_sorted[m - 1])
                kernel = dL / np.sqrt(pm**2 - rn**2)
                integral += kernel * (p_sorted[m] - p_sorted[m - 1])
            epsilon[n, k] = -1 / np.pi * integral


    df_eps = pd.DataFrame(epsilon, columns=wavelengths_nm)
    df_eps.insert(0, "p", p_sorted)
    df_eps.insert(0, "channel", channel_sorted)

    base_filename = os.path.basename(file)
    z_name = base_filename.split('_')[0]  # e.g., Z30
    save_path = os.path.join(base_dir, f"{z_name}_ε.csv")
    df_eps.to_csv(save_path, index=False)
    print(f"✅ 保存: {save_path}")


print("✅ 所有 Z 平面的 epsilon 计算完成。")
