#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""擦除即梦 / Seedream 生成素材左上角的「AI生成」水印。

只在需要干净素材时调用，不属于制作流程的必经步骤。

三种模式
  image  ｜图片：裁掉顶部水印带，再按目标比例居中裁边（画幅不变，构图略紧）
  video  ｜视频：默认 delogo 抹掉水印区；--method crop 改为切顶+居中裁边
  probe  ｜只报告按当前参数会处理的位置，不改任何文件

图片一律用裁剪：平涂画面补一块上去比切掉更显眼。
视频两种都行：delogo 不损失画面，但压在纹样、砖墙这类细节上会留下一块糊痕；
画面顶部是留白、天空、纯色墙时，用 --method crop 更干净（损失约 9% 高、少量宽）。

用法
  # 图片：保持 9:16
  python strip_watermark.py image assets/*.png --aspect 9:16

  # 图片：保持 3:4，写到另一个目录
  python strip_watermark.py image assets/C0*.png --aspect 3:4 --outdir clean

  # 图片：只裁水印带，不重新配比
  python strip_watermark.py image a.png --aspect keep

  # 视频
  python strip_watermark.py video videos/E01.mp4 -o videos/E01_clean.mp4

  # 视频：顶部是天空/留白时，改用裁剪
  python strip_watermark.py video videos/E01.mp4 -o out.mp4 --method crop --aspect 9:16

  # 先看会动哪里
  python strip_watermark.py probe assets/S01.png

依赖
  image / probe：Pillow
  video：ffmpeg（命令行）
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

# 水印在左上角，位置随分辨率按比例缩放。
# 图片：即梦出图是「AI生成」圆角胶囊，比视频上的字更宽。
IMAGE_BOX = (0.020, 0.014, 0.180, 0.056)   # x, y, w, h（相对宽高的比例）
VIDEO_BOX = (0.015, 0.009, 0.155, 0.045)   # 720x1280 实测约 (11, 12, 112, 58)


def _parse_aspect(text: str) -> tuple[int, int] | None:
    """'9:16' -> (9, 16)；'keep' -> None"""
    if text.lower() in ("keep", "none", "off"):
        return None
    try:
        a, b = text.replace("：", ":").split(":")
        w, h = int(a), int(b)
    except Exception:
        raise SystemExit(f"画幅写法不对：{text}，应形如 9:16 / 3:4 / keep")
    if w <= 0 or h <= 0:
        raise SystemExit(f"画幅写法不对：{text}")
    return w, h


def _box_px(size: tuple[int, int], rel: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    w, h = size
    rx, ry, rw, rh = rel
    return (int(w * rx), int(h * ry), int(w * rw), int(h * rh))


def process_image(path: str, out_path: str, aspect: tuple[int, int] | None) -> None:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    src_size = im.size
    box = _box_px(src_size, IMAGE_BOX)

    # 1) 裁掉水印带：顶部切到水印下缘再多留一点余量
    cut = min(src_size[1] - 1, box[1] + box[3] + int(src_size[1] * 0.02))
    im = im.crop((0, cut, src_size[0], src_size[1]))

    # 2) 按目标画幅居中裁边（只裁边，不变形）
    if aspect is not None:
        w, h = im.size
        want = aspect[0] / aspect[1]
        if w / h > want:
            nw = int(h * want)
            x = (w - nw) // 2
            im = im.crop((x, 0, x + nw, h))
        elif w / h < want:
            nh = int(w / want)
            y = (h - nh) // 2
            im = im.crop((0, y, w, y + nh))

    im.save(out_path)
    print(f"{path} {src_size[0]}x{src_size[1]} (切顶 {cut}px) -> {out_path} {im.size[0]}x{im.size[1]}")


def _probe_size(path: str) -> tuple[int, int] | None:
    probe_bin = shutil.which("ffprobe")
    if not probe_bin:
        return None
    r = subprocess.run(
        [probe_bin, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or "," not in r.stdout:
        return None
    w, h = r.stdout.strip().splitlines()[0].split(",")[:2]
    return (int(w), int(h))


def process_video(path: str, out_path: str, method: str = "delogo",
                  aspect: tuple[int, int] | None = (9, 16)) -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("没有找到 ffmpeg，请先安装或把它加进 PATH")

    size = _probe_size(path)
    if size is None:
        raise SystemExit("读不到视频分辨率（需要 ffprobe），请确认文件是有效视频")

    if method == "crop":
        x, y, bw, bh = _box_px(size, VIDEO_BOX)
        cut = y + bh + int(size[1] * 0.02)
        cut -= cut % 2          # libx264 要偶数
        h2 = size[1] - cut
        w2 = size[0]
        if aspect is not None:
            want = aspect[0] / aspect[1]
            if w2 / h2 > want:
                w2 = int(h2 * want) // 2 * 2
            else:
                h2 = int(w2 / want) // 2 * 2
        x_off = (size[0] - w2) // 2 // 2 * 2
        filt = f"crop={w2}:{h2}:{x_off}:{cut}"
        note = f"裁剪 -> {w2}x{h2}"
    else:
        x, y, bw, bh = _box_px(size, VIDEO_BOX)
        # delogo 的区域必须完全落在画面内，且四边各留 1px
        x, y = max(1, x), max(1, y)
        bw = min(bw, size[0] - x - 1)
        bh = min(bh, size[1] - y - 1)
        filt = f"delogo=x={x}:y={y}:w={bw}:h={bh}:show=0"
        note = f"去水印区 ({x},{y},{bw},{bh})"

    cmd = ["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", filt,
           "-c:v", "libx264", "-crf", "18", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "copy", out_path]
    subprocess.run(cmd, check=True)
    print(f"{path} {size[0]}x{size[1]} {note} -> {out_path}")


def probe(path: str) -> None:
    from PIL import Image

    if os.path.splitext(path)[1].lower() in (".mp4", ".mov", ".webm", ".mkv"):
        sys.exit("probe 只用于图片；视频会按 720p 实测的 (11,12,112,58) 等比换算")
    size = Image.open(path).size
    box = _box_px(size, IMAGE_BOX)
    cut = box[1] + box[3] + int(size[1] * 0.02)
    print(f"{path} {size[0]}x{size[1]}")
    print(f"  水印估计区 (x={box[0]} y={box[1]} w={box[2]} h={box[3]})")
    print(f"  image 模式会切掉顶部 {cut}px（占高 {cut / size[1]:.1%}）")


def main() -> None:
    p = argparse.ArgumentParser(
        description="擦除即梦素材左上角「AI生成」水印",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="mode", required=True)

    pi = sub.add_parser("image", help="处理图片（裁剪法）")
    pi.add_argument("files", nargs="+")
    pi.add_argument("--aspect", default="keep", help="目标画幅，如 9:16 / 3:4 / keep（默认 keep）")
    pi.add_argument("--outdir", default=None, help="输出目录，默认原地覆盖")
    pi.add_argument("--suffix", default="", help="输出文件名后缀，如 _clean")

    pv = sub.add_parser("video", help="处理视频（delogo 或裁剪）")
    pv.add_argument("file")
    pv.add_argument("-o", "--out", required=True)
    pv.add_argument("--method", choices=["delogo", "crop"], default="delogo",
                    help="delogo=抹掉（默认）；crop=切顶+居中裁边")
    pv.add_argument("--aspect", default="9:16", help="crop 时的目标画幅，默认 9:16")

    pp = sub.add_parser("probe", help="只报告水印位置，不改文件")
    pp.add_argument("file")

    args = p.parse_args()

    if args.mode == "probe":
        probe(args.file)
        return

    if args.mode == "video":
        process_video(args.file, args.out, args.method, _parse_aspect(args.aspect))
        return

    aspect = _parse_aspect(args.aspect)
    for f in args.files:
        if args.outdir:
            os.makedirs(args.outdir, exist_ok=True)
            stem, ext = os.path.splitext(os.path.basename(f))
            out = os.path.join(args.outdir, f"{stem}{args.suffix}{ext}")
        elif args.suffix:
            stem, ext = os.path.splitext(f)
            out = f"{stem}{args.suffix}{ext}"
        else:
            out = f
        process_image(f, out, aspect)


if __name__ == "__main__":
    main()
