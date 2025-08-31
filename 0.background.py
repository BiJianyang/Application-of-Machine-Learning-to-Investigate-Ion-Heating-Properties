#要求输入日期，并已经将iccd转换为asc文件，已存在C:\Users\psaoz\Desktop\doppler content\日期\asc。
# 代码将目标文件-背景保存在asc下的子文件夹net。
import os
import re
import pandas as pd

def read_asc(path):

    try:
        return pd.read_csv(path, header=None, sep=r"\s+", dtype=float)
    except Exception:
        return pd.read_csv(path, header=None, delimiter=",", dtype=float, usecols=lambda x: True)

def main(date_str):

    asc_dir = rf"C:\Users\psaoz\Desktop\doppler content\{date_str}\asc\origin"
    if not os.path.isdir(asc_dir):
        raise FileNotFoundError(f"❌ 目录不存在: {asc_dir}")

    pattern = re.compile(r"shot(\d+).*?delay(\d{3,})", re.IGNORECASE)
    files = []
    for fname in os.listdir(asc_dir):
        if not fname.lower().endswith(".asc"):
            continue
        m = pattern.search(fname)
        if not m:
            continue
        shot = int(m.group(1))
        delay = m.group(2)
        is_bg = "bg" in fname.lower()
        files.append(dict(fn=fname, shot=shot, delay=delay, is_bg=is_bg))

    if not files:
        raise RuntimeError("❌ 没有找到任何 .asc 文件")

    files.sort(key=lambda x: x["shot"])


    last_bg = None
    pairs = []
    for f in files:
        if f["is_bg"]:
            last_bg = f
        else:
            if last_bg is None:
                print(f"⚠️ {f['fn']} 没有找到之前的背景，跳过")
            else:
                pairs.append((f, last_bg))

    net_dir = os.path.join(asc_dir, "net")
    os.makedirs(net_dir, exist_ok=True)

    for tgt, bg in pairs:
        tgt_path = os.path.join(asc_dir, tgt["fn"])
        bg_path = os.path.join(asc_dir, bg["fn"])

        try:
            tgt_df = read_asc(tgt_path)
            bg_df = read_asc(bg_path)
        except Exception as e:
            print(f"❌ 读取失败 {tgt['fn']} 或 {bg['fn']}：{e}")
            continue

        if tgt_df.shape != bg_df.shape:
            print(f"❌ 尺寸不一致 {tgt['fn']} vs {bg['fn']}，跳过")
            continue

        net_df = tgt_df - bg_df
        out_name = f"shot{tgt['shot']}-delay{tgt['delay']}.asc"
        out_path = os.path.join(net_dir, out_name)

        try:
            net_df.to_csv(out_path, index=False, header=False, float_format="%.0f")

            print(f"✅ 生成：{out_name}")
        except Exception as e:
            print(f"❌ 保存失败：{out_name}，原因：{e}")

    print("\n🎉 全部处理完成！结果保存在 net 文件夹中。")

if __name__ == "__main__":
    date_input = input("请输入日期 (如 250317): ").strip()
    main(date_input)

