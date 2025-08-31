import os
import glob
import sys
import pandas as pd
import numpy as np


input_str = input("请输入日期和 shot 编号，例如 250317,22：")
date_part, shot_number = input_str.split(',')


confirm = input("您确定要运行温度计算吗？请输入 ok 继续，否则退出：")
if confirm.strip().lower() != 'ok':
    print("已取消温度计算。")
    sys.exit()


A = 1.008
lambda_0 = 486.1  # 单位 nm
factor = 2 * np.sqrt(2 * np.log(2))

base_dir = f"C:/Users/psaoz/Desktop/doppler content/{date_part}/asc/net"
file_pattern = f"shot{shot_number}-delay*_fit_result.xlsx"
file_list = glob.glob(os.path.join(base_dir, file_pattern))
if not file_list:
    raise FileNotFoundError(f"未找到匹配文件：{file_pattern}")
file_path = file_list[0]
print(f"找到文件：{file_path}")

df = pd.read_excel(file_path)


sigma_instr = df.iloc[:, 6] * 0.0038   # G列 = 第7列
sigma_exp   = df.iloc[:, 7]            # H列 = 第8列
sigma_sq    = sigma_exp**2 - sigma_instr**2
sigma_sq[sigma_sq < 0] = np.nan        # 避免 sqrt 负数报错
sigma_true  = np.sqrt(sigma_sq)

delta_lambda_half = factor * sigma_true
Ti = 1.69e8 * A * (delta_lambda_half / lambda_0)**2

df['σ_true']   = sigma_true
df['T_i [eV]'] = Ti


cols = df.columns.tolist()
for col in ['σ_true', 'T_i [eV]']:
    if col in cols:
        cols.remove(col)
cols.insert(8, 'σ_true')
cols.insert(9, 'T_i [eV]')
df = df[cols]

df.to_excel(file_path, index=False)
print("✅ 已计算并覆盖原 Excel 文件（含 σ_true 和 Ti）。")

