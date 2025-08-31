import pandas as pd
import numpy as np
import os
from glob import glob


date_shot = input("请输入日期和shot编号，例如 250317,22：").strip()
date, shot = date_shot.split(',')


base_dir = rf"C:\Users\psaoz\Desktop\doppler content\{date}\asc\net\shot{shot}_L_output"
csv_files = sorted(glob(os.path.join(base_dir, "Z*_L.csv")))

for file in csv_files:
    df = pd.read_csv(file, header=None)

    empty_row = df.isnull().all(axis=1)
    if not empty_row.any():
        print(f"⚠️ 文件 {file} 中未找到空行，跳过")
        continue
    split_idx = empty_row[empty_row].index[0]

 
    wavelength_row = df.iloc[0]
    wavelength = wavelength_row[1:-1].astype(float).values  # 去掉首尾
    center_index = np.argmin(np.abs(wavelength))  # 找到波长为0的位置（中心像素）

 
    L_block = df.iloc[split_idx+1:].reset_index(drop=True)
    L_values = L_block.iloc[:, 1:-1].astype(float).values
    channel_ids = L_block.iloc[:, 0].values
    p_vals = L_block.iloc[:, -1].values

    sorted_L = []
    for row in L_values:
        sorted_row = np.full_like(row, np.nan)
        sorted_vals = -np.sort(-row)  # 从大到小排序

        center = center_index
        left = center - 1
        right = center + 1
        sorted_row[center] = sorted_vals[0]

        for i in range(1, len(sorted_vals)):
            if i % 2 == 1:
                if left >= 0:
                    sorted_row[left] = sorted_vals[i]
                    left -= 1
            else:
                if right < len(row):
                    sorted_row[right] = sorted_vals[i]
                    right += 1
        sorted_L.append(sorted_row)

    sorted_L = np.array(sorted_L)

    new_block = pd.DataFrame(sorted_L)
    new_block.insert(0, 'channel', channel_ids)
    new_block[len(new_block.columns)] = p_vals  # 插入 p

    df.iloc[split_idx+1:] = new_block.values

    df.to_csv(file, index=False, header=False)
    print(f"✅ 已覆盖保存: {file}")

print("✅ 所有文件已对称重排并覆盖保存完毕。")

