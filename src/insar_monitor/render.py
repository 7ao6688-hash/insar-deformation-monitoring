from __future__ import annotations

import html
from pathlib import Path

from .analysis import Observation


def _colour(value: float, scale: float) -> str:
    ratio = max(-1.0, min(1.0, value / scale))
    if ratio < 0:
        t = ratio + 1
        return f"rgb({int(38 + 217*t)},{int(90 + 165*t)},{int(164 + 91*t)})"
    return f"rgb(255,{int(255 - 190*ratio)},{int(255 - 207*ratio)})"


def render_svg(items: list[Observation], path: str | Path, title: str) -> None:
    width, height = 1100, 720
    left, right, top, bottom = 92, 80, 72, 88
    xs = [x.longitude for x in items]
    ys = [x.latitude for x in items]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    scale = max(abs(x.los_displacement_cm) for x in items) or 1

    def px(x):
        return left + (x - min_x) / (max_x - min_x) * (width - left - right)

    def py(y):
        return height - bottom - (y - min_y) / (max_y - min_y) * (height - top - bottom)

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="35" font-family="Arial" font-size="26" font-weight="700" fill="#17212b">{html.escape(title)}</text>',
        f'<text x="{left}" y="58" font-family="Arial" font-size="14" fill="#5a6570">Synthetic demonstration data - not an observed earthquake product</text>',
        f'<rect x="{left}" y="{top}" width="{width-left-right}" height="{height-top-bottom}" fill="#f5f7f9" stroke="#c8d0d8"/>',
    ]
    for item in sorted(items, key=lambda x: abs(x.los_displacement_cm)):
        radius = 4.1 + 2.2 * item.coherence
        elements.append(
            f'<circle cx="{px(item.longitude):.1f}" cy="{py(item.latitude):.1f}" r="{radius:.1f}" '
            f'fill="{_colour(item.los_displacement_cm, scale)}" fill-opacity="0.88"/>'
        )
    # Simplified synthetic fault trace for orientation.
    x1, x2 = px(36.86 + (min_y - 37.4) * 0.32), px(36.86 + (max_y - 37.4) * 0.32)
    elements.append(f'<line x1="{x1:.1f}" y1="{py(min_y):.1f}" x2="{x2:.1f}" y2="{py(max_y):.1f}" stroke="#222" stroke-width="3" stroke-dasharray="8 6"/>')
    elements.append(f'<text x="{x2+8:.1f}" y="{py(max_y)+18:.1f}" font-family="Arial" font-size="13" fill="#222">synthetic fault trace</text>')

    for i in range(6):
        x = left + i * (width - left - right) / 5
        label = min_x + i * (max_x - min_x) / 5
        elements.append(f'<text x="{x:.1f}" y="{height-bottom+25}" text-anchor="middle" font-family="Arial" font-size="13">{label:.2f}°E</text>')
    for i in range(5):
        y = height - bottom - i * (height - top - bottom) / 4
        label = min_y + i * (max_y - min_y) / 4
        elements.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" font-family="Arial" font-size="13">{label:.2f}°N</text>')

    legend_x, legend_y, legend_w = 720, 675, 270
    for i in range(101):
        value = -scale + 2 * scale * i / 100
        elements.append(f'<rect x="{legend_x+i*legend_w/101:.2f}" y="{legend_y}" width="{legend_w/101+0.5:.2f}" height="14" fill="{_colour(value, scale)}"/>')
    elements.extend([
        f'<text x="{legend_x}" y="{legend_y-7}" font-family="Arial" font-size="13" fill="#17212b">LOS displacement (cm)</text>',
        f'<text x="{legend_x}" y="{legend_y+32}" font-family="Arial" font-size="12" text-anchor="middle">{-scale:.1f}</text>',
        f'<text x="{legend_x+legend_w/2}" y="{legend_y+32}" font-family="Arial" font-size="12" text-anchor="middle">0</text>',
        f'<text x="{legend_x+legend_w}" y="{legend_y+32}" font-family="Arial" font-size="12" text-anchor="middle">{scale:.1f}</text>',
        '</svg>',
    ])
    Path(path).write_text("\n".join(elements), encoding="utf-8")

