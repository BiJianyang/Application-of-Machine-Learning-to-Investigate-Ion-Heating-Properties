#该code通过输入的asc路径和校准文件的i列+140（H）+257（Ar）像素（目测目标文件比校准文件大140或257像素）+-20，y+-6范围内拟合。
#找出中心，创建excel并保存在asc\net
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import warnings, os


asc_path = input("请输入 ASC 文件路径：").strip('"')
cal_path = r"C:\Users\psaoz\Desktop\doppler content\cal_2_intensity.xlsx"#校准文件
save_path = os.path.splitext(asc_path)[0] + "_fit_result.xlsx"


cal = pd.read_excel(cal_path, engine="openpyxl")
x0_list = pd.to_numeric(cal.iloc[:, 8], errors="coerce")  # I列：x中心（校准）
y0_list = pd.to_numeric(cal.iloc[:, 9], errors="coerce")  # J列：y中心


asc = np.genfromtxt(asc_path, delimiter=",", autostrip=True)
asc = np.nan_to_num(asc)[:, 1:]  # 去除第一列


def gauss(x, A, x0, s, C):
    return A * np.exp(-(x - x0)**2 / (2 * s**2)) + C

rows = []


for idx, (x0, y0) in enumerate(zip(x0_list, y0_list), 1):
    if np.isnan(x0) or np.isnan(y0):
        rows.append((idx, np.nan, np.nan))
        continue

    x0 = int(round(x0 + 140))  # 加上140的校正偏移
    y0 = int(round(y0))

    x1, x2 = max(x0 - 30, 0), min(x0 + 31, asc.shape[0])
    y1, y2 = max(y0 - 6, 0), min(y0 + 7,  asc.shape[1])

    profile = asc[x1:x2, y1:y2].sum(axis=1)  # 沿 y 方向积分
    x_axis = np.arange(x1, x2)

    if np.ptp(profile) == 0:
        rows.append((idx, np.nan, y0))
        continue

    p0 = [profile.max() - profile.min(), x_axis[profile.argmax()], 5.0, profile.min()]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            popt, _ = curve_fit(gauss, x_axis, profile, p0=p0, maxfev=2000)
            x_fit = float(popt[1])
        except Exception:
            x_fit = np.nan

    rows.append((idx, x_fit, y0))


df_out = pd.DataFrame(rows, columns=["channel", "x_center", "y_center"])
df_out.to_excel(save_path, index=False, engine="openpyxl")
print(f"✅ 已完成，结果已保存至: {save_path}")
