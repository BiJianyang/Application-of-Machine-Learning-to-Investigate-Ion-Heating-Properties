import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from glob import glob
from scipy.optimize import curve_fit


date_shot = input("请输入日期和shot编号，例如 250317,22：").strip()
date, shot = date_shot.split(',')

base_dir = rf"C:\Users\psaoz\Desktop\doppler content\{date}\asc\net"
eps_dir = os.path.join(base_dir, f"shot{shot}_L_output")
csv_files = sorted(glob(os.path.join(eps_dir, "Z*_ε.csv")))


def gaussian(x, A, mu, sigma):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


for csv_file in csv_files:
    df = pd.read_csv(csv_file)

    wavelength_nm = df.columns[2:].astype(float)
    r_values = df.iloc[:, 1].values  # 第二列是 p

    n_channels = len(df)
    n_cols = 6
    n_rows_plot = (n_channels + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows_plot, n_cols, figsize=(4 * n_cols, 3 * n_rows_plot), dpi=120)
    axes = axes.flatten()

    for idx in range(n_channels):
        p = r_values[idx]
        y = df.iloc[idx, 2:].values.astype(float)  # C列开始是 ε 值
        x = wavelength_nm

        ax = axes[idx]
        ax.plot(x, y, label='ε vs λ', color='blue')

        try:
            popt, _ = curve_fit(gaussian, x, y, p0=[y.max(), x[np.argmax(y)], 0.1])
            A, mu, sigma = popt
            delta_lambda_half = 2 * sigma * np.sqrt(2 * np.log(2))
            ax.plot(x, gaussian(x, *popt), 'r--', label='fit')
            ax.set_title(f"Ch#{df.iloc[idx, 0]}\np={p:.1f}\nσ={sigma:.4f}, Δλ1/2={delta_lambda_half:.4f}")
        except:
            ax.set_title(f"Ch#{df.iloc[idx, 0]}\np={p:.1f}\nFit error")

        ax.set_xlabel("λ [nm]")
        ax.set_ylabel("ε")
        ax.grid(True)

    # 删除多余子图
    for j in range(n_channels, len(axes)):
        fig.delaxes(axes[j])

    z_str = os.path.basename(csv_file).split('_')[0]
    fig.tight_layout()
    plt.suptitle(f"ε(λ) at {z_str}", fontsize=16, y=1.02)
    plt.subplots_adjust(top=0.90)
    plt.savefig(os.path.join(eps_dir, f"{z_str}_ε.png"))
    plt.close()

    fit_result_list = glob(os.path.join(base_dir, f"*shot{shot}*_fit_result.xlsx"))
    if not fit_result_list:
        print(f"❌ 找不到对应的 _fit_result.xlsx 文件用于写入 σ：{z_str}")
        continue
    fit_result_path = fit_result_list[0]
    fit_df = pd.read_excel(fit_result_path, engine='openpyxl')


    sigma_list = []
    for idx in range(n_channels):
        y = df.iloc[idx, 2:].values.astype(float)
        x = wavelength_nm
        try:
            popt, _ = curve_fit(gaussian, x, y, p0=[y.max(), x[np.argmax(y)], 0.1])
            sigma_list.append(popt[2])  # σ
        except:
            sigma_list.append(np.nan)

    if 'channel' not in df.columns or 'channel' not in fit_df.columns:
        print(f"⚠️ 无法匹配通道编号写入 σ：{z_str}")
        continue

    channel_map = df['channel'].values
    for ch, sigma_val in zip(channel_map, sigma_list):
        mask = fit_df['channel'] == ch
        fit_df.loc[mask, 'σ_exp'] = sigma_val

    fit_df.to_excel(fit_result_path, index=False)
    print(f"✅ 已将 σ 写入 {os.path.basename(fit_result_path)} 的 H 列")

