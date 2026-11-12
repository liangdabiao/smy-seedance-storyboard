#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seedance 提示词「对白护栏」检查脚本。

背景（2026-11-12 野猪林事故）：
剧本每集都有旁白和台词，但六集提示词的【声音】段全写成
"只生成音效，不要生成音乐，不要生成任何字幕"，一句台词都没有。
Seedance 只能照办：人闭嘴，只出环境音。6 条视频 540 积分白跑。

本脚本的作用：在花钱生成视频之前，把这类提示词拦下来。

用法：
    python scripts/check_prompts.py <prompts目录>
    python scripts/check_prompts.py <prompts目录> -p "E*.txt"
    python scripts/check_prompts.py <prompts目录> --quiet

退出码：
    0 = 全部通过（可能带警告）
    1 = 存在 FAIL，禁止开跑
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

# Windows 控制台可能是 GBK，强制 UTF-8 输出，避免中文报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- 规则阈值 ----------------------------------------------------------
MAX_TOTAL_CHARS = 60      # 全集合计台词字数上限（超了容易赶词）
FATAL_TOTAL_CHARS = 90    # 硬上限
MAX_LINE_CHARS = 20       # 单句台词字数上限
SOUND_SECTION = "【声音】"

# 这些串出现在【声音】段里 = 主动把对白掐死
FATAL_PHRASES = [
    "只生成音效",
    "只保留音效",
    "不要生成对白",
    "不要生成台词",
    "不含对白",
    "没有对白",
    "无人说话",
    "纯音效",
    "不需要对白",
]

# 判断"模型是否被告知要开口"
SPEAK_HINTS = ["开口说话", "开口", "说话", "对白", "台词", "同期声", "念白"]

# 时间码：0-3秒 / 0—3秒 / 第3秒
RE_TIME = re.compile(r"(\d+\s*[-—~至]\s*\d+\s*秒|第\s*\d+\s*秒)")
# 台词引号：中文直角引号优先，兼容弯引号与直引号
RE_QUOTE = re.compile(r"[「“\"]([^」”\"]{1,80})[」”\"]")
# 说话人：时间码之后、第一个括号或冒号之前
RE_SPEAKER = re.compile(r"\d+\s*[-—~至]\s*\d+\s*秒\s*([^\s（(：:]{1,10})")

CN_PUNCT = "，。、；：！？…—·「」“”‘’（）《》,.;:!?\"'() \n\t"


def cut_sound_section(text: str) -> str:
    """截取【声音】段：从【声音】到下一个【...】行或文末。"""
    idx = text.find(SOUND_SECTION)
    if idx < 0:
        return ""
    tail = text[idx:]
    # 找下一个段落标记（【参考】【画面】等）
    m = re.search(r"\n\s*【(?!声音)", tail)
    return tail[: m.start()] if m else tail


def count_chars(s: str) -> int:
    """台词净字数：去掉标点与空白。"""
    return sum(1 for ch in s if ch not in CN_PUNCT)


def check_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    fails: list[str] = []
    warns: list[str] = []

    sound = cut_sound_section(text)
    if not sound:
        fails.append("没有【声音】段（模型不会被要求生成对白）")
        sound = ""

    # 1) 致命串
    hits = [p for p in FATAL_PHRASES if p in sound]
    if hits:
        fails.append("【声音】段命中扼杀对白的写法：" + "、".join(f"「{h}」" for h in hits))

    # 2) 是否要求开口
    if sound and not any(h in sound for h in SPEAK_HINTS):
        warns.append("【声音】段没写「人物开口说话」，可能仍会闭嘴")

    # 3) 逐行抽台词
    dialogues = []
    for line_no, line in enumerate(sound.splitlines(), 1):
        if not RE_TIME.search(line):
            continue
        quotes = RE_QUOTE.findall(line)
        if not quotes:
            continue
        m = RE_SPEAKER.search(line)
        speaker = m.group(1) if m else "?"
        kind = "画外音" if "画外音" in line else ("同期声" if "同期声" in line else "未标注")
        for q in quotes:
            dialogues.append(
                {"line": line_no, "speaker": speaker, "quote": q, "kind": kind, "raw": line.strip()}
            )

    if not dialogues:
        fails.append("【声音】段里没有一条带时间码的台词")

    sync = [d for d in dialogues if d["kind"] == "同期声"]
    if dialogues and not sync:
        fails.append("没有人物同期对白（全是旁白 = 报幕员念稿）")

    unmarked = [d for d in dialogues if d["kind"] == "未标注"]
    if unmarked:
        warns.append(f"{len(unmarked)} 条台词没标声音属性（同期声 / 画外音）")

    # 4) 容量
    total = sum(count_chars(d["quote"]) for d in dialogues)
    if total > FATAL_TOTAL_CHARS:
        fails.append(f"台词总量 {total} 字，超过硬上限 {FATAL_TOTAL_CHARS} 字（必赶词）")
    elif total > MAX_TOTAL_CHARS:
        warns.append(f"台词总量 {total} 字，超过建议上限 {MAX_TOTAL_CHARS} 字")

    for d in dialogues:
        n = count_chars(d["quote"])
        if n > MAX_LINE_CHARS:
            warns.append(f"第{d['line']}行「{d['speaker']}」单句 {n} 字，超过 {MAX_LINE_CHARS} 字")

    return {
        "path": path,
        "name": os.path.basename(path),
        "fails": fails,
        "warns": warns,
        "dialogues": dialogues,
        "total": total,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Seedance 提示词对白护栏")
    ap.add_argument("prompt_dir", help="存放 E01.txt / E02.txt ... 的目录")
    ap.add_argument("-p", "--pattern", default="E*.txt", help="文件名通配，默认 E*.txt")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总")
    args = ap.parse_args()

    if not os.path.isdir(args.prompt_dir):
        print(f"目录不存在：{args.prompt_dir}")
        return 1

    files = sorted(glob.glob(os.path.join(args.prompt_dir, args.pattern)))
    if not files:
        print(f"没找到匹配 {args.pattern} 的文件：{args.prompt_dir}")
        return 1

    n_fail = 0
    for f in files:
        r = check_file(f)
        status = "FAIL" if r["fails"] else ("WARN" if r["warns"] else "PASS")
        if r["fails"]:
            n_fail += 1
        if not args.quiet:
            print(f"\n[{status}] {r['name']}   台词 {len(r['dialogues'])} 条 / {r['total']} 字")
            for d in r["dialogues"]:
                print(f"     · {d['speaker']}（{d['kind']}）「{d['quote']}」")
            for msg in r["fails"]:
                print(f"     ✗ {msg}")
            for msg in r["warns"]:
                print(f"     ! {msg}")

    print("\n" + "-" * 60)
    print(f"合计 {len(files)} 个文件：{len(files) - n_fail} 通过 / {n_fail} 失败")
    if n_fail:
        print("存在 FAIL —— 禁止开跑视频，先按 skill §5.1c 台词迁移表补齐【声音】段。")
        return 1
    print("全部通过，可以生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
