#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生视频前「提示词护栏」：花钱之前把不合格的 Seedance 提示词拦下来。

两批规则都来自实测事故，不是凭想象定的。

A. 对白规则（2026-11-12 野猪林事故）
   六集提示词的【声音】段全写成"只生成音效"，一句台词都没有，
   Seedance 照办让人闭嘴，540 积分白跑。→ 必须含同期对白。

B. 节奏与可拍性规则（2026-11-12 镇关西事故）
   五集成片逐秒抽帧核对，发现 75 秒里有 28 秒是静止重复画面（37%）：
   E01 眼睛特写停 5 秒、E03 切肉停 6 秒、E05 城楼俯视停 6 秒。
   根因是往 15 秒里塞了 5 个时间拍、每拍 3-4 个动作、40 多字台词，
   模型一个拍只能完成一个动作，剩下的时间就把同一姿势拖着不动。
   → 限制拍数、每拍动作数、台词总量，并要求相邻拍必须换景别。

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

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- A. 对白规则 -------------------------------------------------------
MAX_TOTAL_CHARS = 35      # 15 秒全集台词建议上限（实测 38-45 字必赶词）
FATAL_TOTAL_CHARS = 45    # 硬上限
MAX_LINE_CHARS = 15       # 单句上限
MAX_BEAT_CHARS = 12       # 单个时间拍的台词上限（3 秒约 12 字）
SOUND_SECTION = "【声音】"

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

SPEAK_HINTS = ["开口说话", "开口", "说话", "对白", "台词", "同期声", "念白"]

# ---- B. 节奏规则 -------------------------------------------------------
MAX_BEATS = 4             # 15 秒最多 4 个时间拍（5 拍 → 每拍 3 秒，做不完）
MAX_BEAT_CHARS_DESC = 70  # 单个时间拍的画面描述字数上限
MAX_ACTIONS_PER_BEAT = 2  # 单拍最多 2 个主要动作
SHOTS = ["大特写", "特写", "近景", "中景", "全景", "远景", "空镜", "中近景", "中全景"]

# 这些词描述的是"模型做不出来的抽象效果"，必须改写成可拍的具体画面
ABSTRACT_EFFECTS = [
    "色块炸开", "色块迸开", "色块绽开", "色块荡开", "色彩炸开", "颜色炸开",
    "同心纹荡", "光圈荡开", "波纹荡开", "抽象化", "具象化为",
]

# 动作动词：用来估算单拍塞了几个动作
ACTION_VERBS = [
    "抓", "掼", "摔", "磕", "抄", "扑", "攥", "拧", "推", "按", "抬", "转",
    "跪", "磕头", "切", "剁", "递", "接", "掏", "点", "指", "扬", "卷",
    "走", "跑", "倒", "探", "翻", "竖", "端", "呷", "踢", "踹", "拔",
    "挥", "拍", "扔", "抛", "拉", "扯", "跨", "蹲", "起身", "回头",
]

RE_TIME = re.compile(r"(\d+\s*[-—~至]\s*\d+\s*秒|第\s*\d+\s*秒)")
RE_QUOTE = re.compile(r"[「“\"]([^」”\"]{1,80})[」”\"]")
RE_SPEAKER = re.compile(r"\d+\s*[-—~至]\s*\d+\s*秒\s*([^\s（(：:]{1,10})")
# 时间轴行：0-3秒：描述
RE_BEAT = re.compile(r"^\s*(\d+)\s*[-—~至]\s*(\d+)\s*秒[：:]\s*(.+)$")

CN_PUNCT = "，。、；：！？…—·「」“”‘’（）《》,.;:!?\"'() \n\t"


def cut_sound_section(text: str) -> str:
    idx = text.find(SOUND_SECTION)
    if idx < 0:
        return ""
    tail = text[idx:]
    m = re.search(r"\n\s*【(?!声音)", tail)
    return tail[: m.start()] if m else tail


def count_chars(s: str) -> int:
    return sum(1 for ch in s if ch not in CN_PUNCT)


def parse_beats(text: str) -> list[dict]:
    """抽出时间轴拍，含起止秒、描述、景别、动作数。"""
    beats = []
    body = text.split(SOUND_SECTION)[0]
    for line in body.splitlines():
        m = RE_BEAT.match(line.strip())
        if not m:
            continue
        start, end, desc = int(m.group(1)), int(m.group(2)), m.group(3)
        shot = next((s for s in SHOTS if s in desc), None)
        acts = [v for v in ACTION_VERBS if v in desc]
        beats.append(
            {
                "range": f"{start}-{end}秒",
                "span": max(end - start, 1),
                "desc": desc,
                "shot": shot,
                "actions": acts,
                "chars": count_chars(desc),
            }
        )
    return beats


def check_beat(beat: dict) -> tuple[list[str], list[str]]:
    fails, warns = [], []
    tag = beat["range"]

    if beat["span"] < 2:
        warns.append(f"{tag} 只有 {beat['span']} 秒，太短，模型来不及完成一个动作")

    if beat["chars"] > MAX_BEAT_CHARS_DESC:
        fails.append(
            f"{tag} 画面描述 {beat['chars']} 字，超过 {MAX_BEAT_CHARS_DESC} 字"
            f"（模型只能挑一部分做，其余会变成定格）"
        )

    if len(beat["actions"]) > MAX_ACTIONS_PER_BEAT:
        fails.append(
            f"{tag} 有 {len(beat['actions'])} 个动作（{'、'.join(beat['actions'])}），"
            f"超过 {MAX_ACTIONS_PER_BEAT} 个，做不完会变成跳帧"
        )

    if not beat["shot"]:
        warns.append(f"{tag} 没写景别（近景/中景/全景/特写），分镜容易变成同一机位")

    return fails, warns


def check_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    fails: list[str] = []
    warns: list[str] = []

    # ================= A. 对白 =================
    sound = cut_sound_section(text)
    if not sound:
        fails.append("没有【声音】段（模型不会被要求生成对白）")
        sound = ""

    hits = [p for p in FATAL_PHRASES if p in sound]
    if hits:
        fails.append("【声音】段命中扼杀对白的写法：" + "、".join(f"「{h}」" for h in hits))

    if sound and not any(h in sound for h in SPEAK_HINTS):
        warns.append("【声音】段没写「人物开口说话」，可能仍会闭嘴")

    dialogues = []
    line_quotes: dict[int, list[str]] = {}
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
        line_quotes[line_no] = line_quotes.get(line_no, []) + quotes

    if not dialogues:
        fails.append("【声音】段里没有一条带时间码的台词")

    sync = [d for d in dialogues if d["kind"] == "同期声"]
    if dialogues and not sync:
        fails.append("没有人物同期对白（全是旁白 = 报幕员念稿）")

    unmarked = [d for d in dialogues if d["kind"] == "未标注"]
    if unmarked:
        warns.append(f"{len(unmarked)} 条台词没标声音属性（同期声 / 画外音）")

    total = sum(count_chars(d["quote"]) for d in dialogues)
    if total > FATAL_TOTAL_CHARS:
        fails.append(f"台词总量 {total} 字，超过硬上限 {FATAL_TOTAL_CHARS} 字（必赶词）")
    elif total > MAX_TOTAL_CHARS:
        warns.append(f"台词总量 {total} 字，超过建议上限 {MAX_TOTAL_CHARS} 字")

    for d in dialogues:
        n = count_chars(d["quote"])
        if n > MAX_LINE_CHARS:
            fails.append(f"第{d['line']}行「{d['speaker']}」单句 {n} 字，超过 {MAX_LINE_CHARS} 字")

    for line_no, quotes in line_quotes.items():
        n = sum(count_chars(q) for q in quotes)
        if n > MAX_BEAT_CHARS:
            warns.append(f"第{line_no}行台词合计 {n} 字，超过单拍 {MAX_BEAT_CHARS} 字")

    # ================= B. 节奏与可拍性 =================
    beats = parse_beats(text)
    if not beats:
        fails.append("没有解析到时间轴（需要「0-3秒：描述」这种行）")
    elif len(beats) > MAX_BEATS:
        fails.append(
            f"{len(beats)} 个时间拍，超过 {MAX_BEATS} 个上限"
            f"（15 秒切成 {len(beats)} 拍 = 每拍不到 {15 // len(beats)} 秒）"
        )

    prev_shot = None
    for b in beats:
        f2, w2 = check_beat(b)
        fails += f2
        warns += w2
        if prev_shot and b["shot"] and b["shot"] == prev_shot:
            warns.append(f"{b['range']} 与上一拍同为「{b['shot']}」，连续同机位容易变成定格")
        if b["shot"]:
            prev_shot = b["shot"]

    ab = [w for w in ABSTRACT_EFFECTS if w in text]
    if ab:
        fails.append(
            "写了模型做不出来的抽象效果：" + "、".join(f"「{w}」" for w in ab)
            + "（要改写成可拍的具体画面，如「赭色血点溅在青石板上，占画面上三分之一」）"
        )

    span_sum = sum(b["span"] for b in beats)
    if beats and not (13 <= span_sum <= 16):
        warns.append(f"时间轴合计 {span_sum} 秒，与 15 秒不符")

    return {
        "path": path,
        "name": os.path.basename(path),
        "fails": fails,
        "warns": warns,
        "dialogues": dialogues,
        "total": total,
        "beats": beats,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Seedance 提示词护栏（对白 + 节奏）")
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
            shots = "→".join((b["shot"] or "?") for b in r["beats"])
            print(
                f"\n[{status}] {r['name']}   "
                f"{len(r['beats'])} 拍 / 台词 {len(r['dialogues'])} 条 {r['total']} 字"
            )
            print(f"     景别顺序：{shots}")
            for d in r["dialogues"]:
                print(f"     · {d['speaker']}（{d['kind']}）「{d['quote']}」")
            for msg in r["fails"]:
                print(f"     ✗ {msg}")
            for msg in r["warns"]:
                print(f"     ! {msg}")

    print("\n" + "-" * 60)
    print(f"合计 {len(files)} 个文件：{len(files) - n_fail} 通过 / {n_fail} 失败")
    if n_fail:
        print("存在 FAIL —— 禁止开跑视频。先按 SKILL.md §5.1c 台词迁移表与 §5.2 节奏预算表改。")
        return 1
    print("通过，可以生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
