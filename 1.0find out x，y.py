import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import warnings, os

asc_path = input("请输入 ASC 文件路径：").strip('"')
cal_path = r"C:\Users\psaoz\Desktop\doppler content\cal_2_intensity.xlsx"
save_path = os.path.splitext(asc_path)[0] + "_fit_result.xlsx"

cal = pd.read_excel(cal_path, engine="openpyxl")
x0_list = pd.to_numeric(cal.iloc[:, 8], errors="coerce")  # I列
y0_list = pd.to_numeric(cal.iloc[:, 9], errors="coerce")  # J列

asc = np.genfromtxt(asc_path, delimiter=",", autostrip=True)
asc = np.nan_to_num(asc)[:, 1:]  # 去除第一列

def gauss(x, A, x0, s, C):
    return A * np.exp(-(x - x0)**2 / (2 * s**2)) + C

rows = []

for idx, (x0, y0) in enumerate(zip(x0_list, y0_list), 1):
    if np.isnan(x0) or np.isnan(y0):
        rows.append((idx, np.nan, np.nan))
        continue

    # -------- 偏移 +257 像素 --------
    x0 = int(round(x0 + 257))
    y0 = int(round(y0))

    # -----------------------
    # X方向 profile（纵向 ±5 列积分）
    # -----------------------
    x1, x2 = max(x0 - 20, 0), min(x0 + 21, asc.shape[0])
    y1, y2 = max(y0 - 5, 0), min(y0 + 6, asc.shape[1])

    x_profile = asc[x1:x2, y1:y2].sum(axis=1)
    x_axis = np.arange(x1, x2)

    if np.ptp(x_profile) == 0:
        rows.append((idx, np.nan, np.nan))
        continue

    try:
        popt_x, _ = curve_fit(gauss, x_axis, x_profile,
                              p0=[x_profile.max(), x_axis[np.argmax(x_profile)], 5, x_profile.min()],
                              maxfev=2000)
        x_fit = float(popt_x[1])
    except Exception:
        x_fit = np.nan

    # -----------------------
    # Y方向 profile（横向 ±20 行积分）
    # -----------------------
    if np.isnan(x_fit):
        rows.append((idx, np.nan, np.nan))
        continue

    x_fit_int = int(round(x_fit))
    x1_y, x2_y = max(x_fit_int - 20, 0), min(x_fit_int + 21, asc.shape[0])
    y1_y, y2_y = max(y0 - 5, 0), min(y0 + 6, asc.shape[1])

    y_profile = asc[x1_y:x2_y, y1_y:y2_y].sum(axis=0)
    y_axis = np.arange(y1_y, y2_y)

    if np.ptp(y_profile) == 0:
        rows.append((idx, x_fit, np.nan))
        continue

    try:
        popt_y, _ = curve_fit(gauss, y_axis, y_profile,
                              p0=[y_profile.max(), y_axis[np.argmax(y_profile)], 3, y_profile.min()],
                              maxfev=2000)
        y_fit = float(popt_y[1])
    except Exception:
        y_fit = np.nan

    rows.append((idx, x_fit, y_fit))

# -------- 保存 --------
df_out = pd.DataFrame(rows, columns=["channel", "x_center", "y_center"])
df_out.to_excel(save_path, index=False, engine="openpyxl")
print(f"✅ 拟合完成，结果已保存至: {save_path}")
