#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生图前「资产护栏」：在花积分出图之前，把不合格的资产提示词拦下来。

背景（2026-11-12 镇关西事故，实测抽帧核对的结论）：
1. 场景三机位提示词全部写成 16:9，成片是 9:16 竖屏 —— 参考图画幅与成片不符；
2. 角色只给「正面全身」一张，模型锁不住脸，同一个鲁达在五集里有四张脸；
3. 道具只写「五两银子」，没写尺寸参照，生成出菜碗大的元宝；
4. 郑屠设定里没有纹身，但提示词没写「无纹身」，模型自己加了一身刺青；
5. 素材清单里的编号与 prompts/ 目录里的文件对不上，运行时靠手写映射，容易错位。

本脚本只做文本层能判定的检查；造型是否真的对了，必须按 §6.2 看图核对。

用法：
    python scripts/check_assets.py <项目目录>
    python scripts/check_assets.py <项目目录> --ratio 9:16
    python scripts/check_assets.py <项目目录> --quiet

退出码：
    0 = 通过（可能带警告）
    1 = 有 FAIL，禁止出图
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- 色盘 --------------------------------------------------------------
# 上美影风格指南 §2.3 的六主色
BASE_COLORS = ["青瓷绿", "朱砂红", "鎏金", "墨黑", "赭石", "月白"]
# 扩展色最多 2 个，超了就是跑色
MAX_EXTRA_COLORS = 2
# 常见跑色词（不在色盘里，且模型会照字面画）
KNOWN_OFF_PALETTE = [
    "绛紫", "酱紫", "紫红", "石青", "石绿", "藤黄", "翠绿", "粉红", "桃红",
    "金黄", "雪白", "乌黑", "深红", "暗红", "湖蓝", "天蓝", "草绿", "玫红",
]

# ---- 风格块 ------------------------------------------------------------
STYLE_TOKENS = ["手绘", "平涂", "笔触"]
BAN_STYLE = ["3D渲染", "写实", "体积光", "赛璐珞", "anime", "photorealistic"]

# ---- 角色 / 道具 --------------------------------------------------------
# 角色资产必须给出多角度特征，否则单张正面锁不住脸
ANGLE_TOKENS = ["正面", "侧面", "背面", "四分之三", "侧脸", "多角度", "三视图"]
MIN_ANGLE_TOKENS = 2
# 道具必须写尺寸参照，否则会长成臆想的形状
SIZE_TOKENS = ["约", "大小", "寸", "尺", "掌", "拳", "碗口", "指节", "厘米", "cm", "参照", "比例"]

RE_RATIO = re.compile(r"(9\s*:\s*16|16\s*:\s*9|3\s*:\s*4|4\s*:\s*3|1\s*:\s*1|2\s*:\s*3|3\s*:\s*2|21\s*:\s*9)")

# 角色设定图只要是竖版就行（3:4 更省，9:16 更贴成片）；场景/道具必须与成片同比例，
# 否则参考图会把构图带偏（2026-11-12 镇关西：10 张场景写成 16:9，成片是 9:16）
PORTRAIT_OK = {"3:4", "9:16", "2:3"}


def load(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def norm_ratio(s: str) -> str:
    return re.sub(r"\s+", "", s)


def check_asset(path: str, kind: str, ratio: str | None) -> dict:
    """kind: char / scene / prop"""
    text = load(path)
    name = os.path.basename(path)
    fails: list[str] = []
    warns: list[str] = []

    head = text.split("\n")[0] if text.strip() else ""

    # 1) 风格块
    miss = [t for t in STYLE_TOKENS if t not in head]
    if miss:
        fails.append(f"首行风格块缺关键词：{'、'.join(miss)}（首行必须逐字统一）")
    ban = [t for t in BAN_STYLE if t in text]
    if ban:
        fails.append(f"出现禁用风格词：{'、'.join(ban)}")

    # 2) 画幅
    found = RE_RATIO.findall(text)
    if not found:
        fails.append("没有声明画幅（如「9:16竖屏」），比例靠猜")
    elif kind == "char":
        norm = {norm_ratio(f) for f in found}
        if not (norm & PORTRAIT_OK):
            fails.append(f"角色设定图画幅 {sorted(norm)} 不是竖版，应为 3:4 或 9:16")
    elif ratio:
        norm = {norm_ratio(f) for f in found}
        if norm_ratio(ratio) not in norm:
            fails.append(
                f"画幅 {sorted(norm)} 与成片比例 {ratio} 不一致"
                f"（场景/道具必须与成片同比例，否则参考图带偏构图）"
            )

    # 3) 色盘
    off = [c for c in KNOWN_OFF_PALETTE if c in text]
    if off:
        fails.append(f"出现色盘外颜色：{'、'.join(off)}（只允许六主色 + 最多 2 个扩展色）")

    # 4) 角色多角度
    if kind == "char":
        hits = [t for t in ANGLE_TOKENS if t in text]
        if len(hits) < MIN_ANGLE_TOKENS:
            fails.append(
                f"角色只有 {len(hits)} 个视角特征（{hits or '无'}），"
                f"要求 ≥{MIN_ANGLE_TOKENS}（正面/侧面/背面），否则跨集会换脸"
            )
        # 明确「无纹身 / 无额外装饰」防止模型自由发挥
        if not re.search(r"无纹身|不加纹身|不要纹身|身上无任何刺青", text):
            warns.append("没写「无纹身/无额外装饰」，模型可能自行加刺青、戒指或伤疤")

    # 5) 道具尺寸
    if kind == "prop":
        if not any(t in text for t in SIZE_TOKENS):
            fails.append("道具没有尺寸参照（写「约拳头一半大」这类），会生成臆想比例")

    return {"name": name, "path": path, "fails": fails, "warns": warns}


def classify(name: str) -> str:
    base = os.path.basename(name)
    if re.match(r"^C\d", base):
        return "char"
    if re.match(r"^S\d", base):
        return "scene"
    if re.match(r"^P\d", base):
        return "prop"
    return "other"


def collect_ids(storyboard_dir: str) -> dict[str, set[str]]:
    """从分镜里抓「素材上传清单」的素材ID，确认每个ID都有提示词。"""
    used: dict[str, set[str]] = {}
    for f in glob.glob(os.path.join(storyboard_dir, "*分镜*.md")):
        text = load(f)
        ep = re.search(r"E\d{2}", os.path.basename(f))
        for m in re.finditer(r"\|\s*图片\d+\s*\|\s*([A-Z]\d{2}(?:-(?:正打|反打|侧面))?)\s*\|", text):
            used.setdefault(m.group(1), set()).add(ep.group(0) if ep else "?")
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description="生图前资产护栏")
    ap.add_argument("project_dir", help="项目根目录（含 prompts/ 与分镜 md）")
    ap.add_argument("--ratio", default="9:16", help="成片画幅，默认 9:16")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总")
    args = ap.parse_args()

    pdir = os.path.join(args.project_dir, "prompts")
    if not os.path.isdir(pdir):
        print(f"找不到 prompts 目录：{pdir}")
        return 1

    files = sorted(glob.glob(os.path.join(pdir, "*.txt")))
    if not files:
        print(f"prompts 目录是空的：{pdir}")
        return 1

    n_fail = 0
    n_char = n_scene = n_prop = 0
    for f in files:
        kind = classify(f)
        if kind == "char":
            n_char += 1
        elif kind == "scene":
            n_scene += 1
        elif kind == "prop":
            n_prop += 1
        if kind == "other":
            continue
        r = check_asset(f, kind, args.ratio)
        status = "FAIL" if r["fails"] else ("WARN" if r["warns"] else "PASS")
        if r["fails"]:
            n_fail += 1
        if not args.quiet:
            print(f"[{status}] {r['name']}  ({kind})")
            for msg in r["fails"]:
                print(f"     ✗ {msg}")
            for msg in r["warns"]:
                print(f"     ! {msg}")

    # 素材覆盖：分镜里引用到的 ID 必须有提示词
    stem = {os.path.splitext(os.path.basename(f))[0].replace("_", "-") for f in files}
    stem |= {os.path.splitext(os.path.basename(f))[0] for f in files}
    used = collect_ids(args.project_dir)
    missing = {k: v for k, v in used.items() if k not in stem}
    if missing:
        n_fail += 1
        if not args.quiet:
            print("\n[FAIL] 分镜引用了但没有提示词的素材：")
            for k, eps in sorted(missing.items()):
                print(f"     ✗ {k}  （被 {','.join(sorted(eps))} 引用）")

    print("\n" + "-" * 60)
    print(f"资产 {len(files)} 个：角色 {n_char} / 场景 {n_scene} / 道具 {n_prop}；失败 {n_fail}")
    if n_fail:
        print("存在 FAIL —— 禁止出图，先补齐提示词。")
        return 1
    print("通过。接着先出 3 张关键图（主角/主场景/关键道具），按 SKILL.md「关卡一之后：看图核对」逐张看过再放量。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
