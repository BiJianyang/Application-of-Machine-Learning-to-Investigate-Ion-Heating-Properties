#此代码通过读取C:\Users\psaoz\Desktop\doppler content\250317\asc\net里的类似shot35-delay470_fit_result的中心坐标
#以每个channel中心x坐标左右各60像素做为波长空间，对每个波长上下共5像素求和作为该波长的L，新建文件夹并保存L。
#该代码还从校准文件导入4列参数到目标excel
import pandas as pd
import numpy as np
import os
from glob import glob

date_shot = input("请输入日期和 shot，例如 250317,22：").strip()
date, shot = date_shot.split(',')

base_dir = rf"C:\Users\psaoz\Desktop\doppler content\{date}\asc\net"
calib_path = r"C:\Users\psaoz\Desktop\doppler content\cal_2_intensity.xlsx"

excel_list = glob(os.path.join(base_dir, f"*shot{shot}*_fit_result.xlsx"))
if not excel_list:
    print(f"❌ 找不到 shot{shot} 的Excel文件！")
    exit()
fit_path = excel_list[0]
print(f"✅ 找到目标Excel: {fit_path}")

fit_df = pd.read_excel(fit_path, engine="openpyxl")
calib_df = pd.read_excel(calib_path, engine="openpyxl")

new_cols = ["Z", "p", "Intensity", "instrument"]
calib_cols = [5, 6, 13, 14]  # F,G,N,O

for i, (new_col, calib_col) in enumerate(zip(new_cols, calib_cols)):
    if new_col in fit_df.columns:
        fit_df[new_col] = calib_df.iloc[:, calib_col].values
    else:
        fit_df.insert(3 + i, new_col, calib_df.iloc[:, calib_col].values)


fit_df.to_excel(fit_path, index=False)
print("✅ 成功更新 D~G 四列：Z, p, Intensity, Extra")


asc_list = glob(os.path.join(base_dir, f"*shot{shot}*.asc"))
if not asc_list:
    print(f"❌ 找不到 shot{shot} 的ASC文件！")
    exit()
asc_path = asc_list[0]
asc_df = pd.read_csv(asc_path, header=None)
asc_data = asc_df.iloc[:, 1:].to_numpy()

L_by_z = {z: [] for z in sorted(fit_df['Z'].dropna().unique())}
L_calib_by_z = {z: [] for z in sorted(fit_df['Z'].dropna().unique())}
p_by_z = {z: [] for z in sorted(fit_df['Z'].dropna().unique())}
channel_by_z = {z: [] for z in sorted(fit_df['Z'].dropna().unique())}
pixel_axis = np.arange(-60, 61)  # 共121个点

for i, row in fit_df.iterrows():
    x_center = row.iloc[1]  # 第二列（B列）
    y_center = row.iloc[2]  # 第三列（C列）
    z_val = row['Z']
    p_val = row['p']
    intensity_corr = row['Intensity']
    channel_id = row['channel']

    if pd.isna(x_center) or pd.isna(y_center) or pd.isna(z_val):
        continue

    x = int(round(float(x_center)))
    y = int(round(float(y_center)))

    L = []
    L_calib = []
    for dx in pixel_axis:
        x_pos = x + dx
        if 0 <= x_pos < asc_data.shape[0]:
            y_min = max(0, y - 5)
            y_max = min(asc_data.shape[1], y + 6)
            value = np.sum(asc_data[x_pos, y_min:y_max])
        else:
            value = np.nan
        L.append(value)
        if intensity_corr and not pd.isna(intensity_corr):
            L_calib.append(value / intensity_corr * 1e8)
        else:
            L_calib.append(np.nan)

    L_by_z[z_val].append(L)
    L_calib_by_z[z_val].append(L_calib)
    p_by_z[z_val].append(p_val)
    channel_by_z[z_val].append(channel_id)

save_dir = os.path.join(base_dir, f"shot{shot}_L_output")
os.makedirs(save_dir, exist_ok=True)

for z_key in L_by_z:
    L_arr = np.array(L_by_z[z_key])
    L_calib_arr = np.array(L_calib_by_z[z_key])
    p_arr = np.array(p_by_z[z_key])
    ch_arr = np.array(channel_by_z[z_key])

    nan_row = np.full((1, L_arr.shape[1]), np.nan)
    df_raw = pd.DataFrame(L_arr, columns=[str(x) for x in pixel_axis])
    df_calib = pd.DataFrame(L_calib_arr, columns=[str(x) for x in pixel_axis])
    df_combined = pd.concat([df_raw, pd.DataFrame(nan_row, columns=df_raw.columns), df_calib], ignore_index=True)
    df_combined.insert(0, 'channel', list(ch_arr) + [np.nan] + list(ch_arr))
    df_combined['p'] = list(p_arr) + [np.nan] + list(p_arr)

    df_combined.to_csv(os.path.join(save_dir, f"Z{int(z_key)}_L.csv"), index=False)

print(f"✅ 每组Z的L谱线数据已保存到: {save_dir}")

