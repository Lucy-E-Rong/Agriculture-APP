#!/usr/bin/env python3
"""Offline lettuce-centred crops and image QC. No API or symptom labels."""
import argparse
import csv
import io
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from pillow_heif import register_heif_opener
from tqdm import tqdm

register_heif_opener()
ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['source', 'position', 'status', 'reasons', 'bbox_xyxy',
          'estimated_visible_fraction', 'subject_score', 'output', 'width', 'height',
          'bytes', 'sharpness', 'dark_fraction', 'bright_fraction']


def reading_order(boxes):
    """Group approximate rows before sorting left to right."""
    rows = []
    for box in sorted(boxes, key=lambda b: (b[1] + b[3]) / 2):
        cy = (box[1] + box[3]) / 2
        for row in rows:
            anchor = row[0]
            if abs(cy - (anchor[1] + anchor[3]) / 2) < min(
                    box[3] - box[1], anchor[3] - anchor[1]) * .45:
                row.append(box)
                break
        else:
            rows.append([box])
    return [box for row in rows for box in sorted(row, key=lambda b: b[0])]


def detect(image, args):
    small = image.copy()
    small.thumbnail((1200, 1200))
    rgb = np.array(small)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    # Broad foliage seed mask. Centres, rather than exact leaf outlines, drive crops.
    r, g, b = (rgb[:, :, j].astype(float) for j in range(3))
    green = (h >= 24) & (h <= 95) & (s > 55) & (v > 30) & (2*g-r-b > 25)
    purple = ((h >= 135) | (h <= 8)) & (s > 55) & (v > 25) & (b > g*.8) & (r > g*1.12)
    mask = ((green | purple).astype(np.uint8) * 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    sh, sw = mask.shape
    short = min(sw, sh)
    # Smooth over individual leaves. A local maximum approximates one lettuce heart.
    sigma = max(12.0, short * .045)
    density = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), sigma)
    peak_window = max(31, int(short * .15) | 1)
    maxima = (density == cv2.dilate(density, np.ones((peak_window, peak_window), np.uint8)))
    maxima &= density >= args.min_subject_score
    peak_count, peak_labels, peak_stats, peak_centers = cv2.connectedComponentsWithStats(maxima.astype(np.uint8))
    peaks = []
    for i in range(1, peak_count):
        x, y = peak_centers[i]
        score = float(density[min(sh-1, round(y)), min(sw-1, round(x))])
        peaks.append((x, y, score))
    # Highest score wins where one plant produces multiple nearby peaks.
    min_distance = short * .16
    centres = []
    for peak in sorted(peaks, key=lambda p: p[2], reverse=True):
        if all(np.hypot(peak[0]-p[0], peak[1]-p[1]) >= min_distance for p in centres):
            centres.append(peak)
    if not centres:
        return []
    nearest_values = []
    for i, centre in enumerate(centres):
        distances = [np.hypot(centre[0]-other[0], centre[1]-other[1])
                     for j, other in enumerate(centres) if i != j]
        if distances:
            nearest_values.append(min(distances))
    typical_spacing = float(np.median(nearest_values)) if nearest_values else short * .30
    boxes = []
    for i, (cx, cy, score) in enumerate(centres):
        distances = [np.hypot(cx-other[0], cy-other[1])
                     for j, other in enumerate(centres) if i != j]
        spacing = min(distances) if distances else typical_spacing
        # About 120% of a canopy whose natural diameter is close to plant spacing.
        crop_side = float(np.clip(spacing * 1.08, short * .20, short * .42))
        half = crop_side / 2
        intended = (cx-half, cy-half, cx+half, cy+half)
        xa, ya = max(0, intended[0]), max(0, intended[1])
        xb, yb = min(sw, intended[2]), min(sh, intended[3])
        visible_fraction = max(0.0, (xb-xa)*(yb-ya)/(crop_side*crop_side))
        reasons = []
        if visible_fraction < args.min_visible_fraction:
            reasons.append('estimated_visible_below_threshold')
        if score < args.review_subject_score:
            reasons.append('weak_subject_centre')
        sx, sy = image.width / sw, image.height / sh
        boxes.append((round(xa*sx), round(ya*sy), round(xb*sx), round(yb*sy),
                      reasons, round(visible_fraction, 3), round(score, 3)))
    return reading_order(boxes)


def quality(crop, min_side, blur_threshold):
    small = crop.copy()
    small.thumbnail((512, 512))
    gray = cv2.cvtColor(np.array(small), cv2.COLOR_RGB2GRAY)
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    dark, bright = float((gray < 12).mean()), float((gray > 248).mean())
    reasons = []
    if min(crop.size) < min_side:
        reasons.append('too_small')
    if sharp < blur_threshold:
        reasons.append('possibly_blurred')
    if dark > .45 or bright > .45:
        reasons.append('extreme_exposure')
    return reasons, [round(sharp, 2), round(dark, 4), round(bright, 4)]


def jpeg_bytes(crop):
    crop = crop.copy()
    crop.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    while True:
        for quality_value in (90, 85, 80, 75, 70):
            buffer = io.BytesIO()
            crop.save(buffer, format='JPEG', quality=quality_value, optimize=True)
            if buffer.tell() < 2_000_000:
                return buffer.getvalue(), crop.size
        crop.thumbnail((int(crop.width * .85), int(crop.height * .85)), Image.Resampling.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description='本地单株候选裁切与质检；不调用 AI API。')
    parser.add_argument('--input', type=Path, default=ROOT / 'Photos/Photos')
    parser.add_argument('--output', type=Path, default=ROOT / 'dataset')
    parser.add_argument('--limit', type=int, default=0, help='只处理前 N 张；0 为全部')
    parser.add_argument('--min-side', type=int, default=300)
    parser.add_argument('--blur-threshold', type=float, default=35)
    parser.add_argument('--min-visible-fraction', type=float, default=.70)
    parser.add_argument('--min-subject-score', type=float, default=.115)
    parser.add_argument('--review-subject-score', type=float, default=.16)
    args = parser.parse_args()
    if (args.limit < 0 or args.min_side < 1 or args.blur_threshold < 0
            or not 0 < args.min_visible_fraction <= 1
            or not 0 < args.min_subject_score <= args.review_subject_score <= 1):
        parser.error('参数范围无效')
    source = args.input.resolve()
    if not source.is_dir():
        parser.error(f'输入文件夹不存在：{source}')
    if args.output.resolve().is_relative_to(source):
        parser.error('输出目录不能在输入目录内部')
    files = sorted(p for p in source.rglob('*') if p.is_file()
                   and p.suffix.lower() in {'.heic', '.heif', '.jpg', '.jpeg', '.png'}
                   and not p.name.startswith('._'))
    if args.limit:
        files = files[:args.limit]
    if not files:
        parser.error('没有找到图片')
    names = [(str(p.relative_to(source).parent), p.stem.casefold()) for p in files]
    if len(set(names)) != len(names):
        parser.error('同一文件夹存在同名不同格式图片；请先区分文件名，防止裁片覆盖')
    run = args.output / datetime.now().strftime('run_%Y%m%d_%H%M%S_%f')
    run.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    totals = {'sources': len(files), 'processed': 0, 'candidate': 0, 'review': 0,
              'rejected': 0, 'errors': 0, 'no_detection': 0}
    with (run / 'manifest.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        progress = tqdm(files, desc='裁切与质检', unit='张', dynamic_ncols=True)
        try:
            for path in progress:
                rel = path.relative_to(source)
                try:
                    with Image.open(path) as raw:
                        image = ImageOps.exif_transpose(raw).convert('RGB')
                    boxes = detect(image, args)
                    overview = image.copy()
                    overview.thumbnail((1200, 1200))
                    draw = ImageDraw.Draw(overview)
                    scale = overview.width / image.width
                    if not boxes:
                        totals['no_detection'] += 1
                        writer.writerow({'source': str(rel), 'status': 'no_detection',
                                         'reasons': 'manual_check_required'})
                    for position, (x1, y1, x2, y2, detected_reasons,
                                   visible_fraction, subject_score) in enumerate(boxes, 1):
                        crop = image.crop((x1, y1, x2, y2))
                        qc_reasons, metrics = quality(crop, args.min_side, args.blur_threshold)
                        reasons = detected_reasons + qc_reasons
                        status = ('rejected' if 'estimated_visible_below_threshold' in reasons else
                                  'review' if reasons else 'candidate')
                        totals[status] += 1
                        output, size, length = '', ('', ''), ''
                        # Review crops remain visible in previews but only clean candidates are saved.
                        if status == 'candidate':
                            dest = run / 'images' / rel.parent / f'{path.stem}_{position:02d}.jpg'
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            data, size = jpeg_bytes(crop)
                            dest.write_bytes(data)
                            output, length = str(dest.relative_to(run)), len(data)
                        writer.writerow(dict(zip(FIELDS, [str(rel), position, status,
                            ';'.join(reasons), json.dumps([x1,y1,x2,y2]), visible_fraction,
                            subject_score, output, *size, length, *metrics])))
                        color = {'candidate':'lime', 'review':'orange', 'rejected':'red'}[status]
                        coords = tuple(round(v*scale) for v in (x1,y1,x2,y2))
                        draw.rectangle(coords, outline=color, width=3)
                        draw.text((coords[0]+3, coords[1]+3), f'{position:02d} {status}', fill='black',
                                  stroke_width=1, stroke_fill='white')
                    preview = run / 'previews' / rel.parent / f'{path.stem}_{path.suffix[1:]}.jpg'
                    preview.parent.mkdir(parents=True, exist_ok=True)
                    overview.save(preview, quality=80)
                    totals['processed'] += 1
                except Exception as exc:
                    totals['errors'] += 1
                    writer.writerow({'source': str(rel), 'status': 'error',
                                     'reasons': f'{type(exc).__name__}: {exc}'})
                    tqdm.write(f'读取/处理失败：{rel} ({type(exc).__name__})')
                f.flush()
                progress.set_postfix(saved=totals['candidate'], review=totals['review'],
                                     skipped=totals['rejected'], errors=totals['errors'])
        except KeyboardInterrupt:
            tqdm.write('已停止；已经完成的图片与清单保留。重新运行会创建新批次。')
        finally:
            totals['elapsed_seconds'] = round(time.monotonic() - start, 2)
            summary = {'totals': totals, 'parameters': {k: str(v) if isinstance(v, Path) else v
                       for k,v in vars(args).items()}, 'note':
                       'Heuristic candidates only. Inspect previews before accepting completeness. No symptom labels.'}
            (run / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'输出：{run.resolve()}\n统计：{totals}')
    return 1 if totals['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
