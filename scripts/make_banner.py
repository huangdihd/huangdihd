"""生成 GitHub 主页顶部横幅（深色 / 浅色两张 SVG）。

文字全部转成矢量路径（README 里的图片加载不了网页字体），
签名复用博客的「阿凛」手写笔画，按笔顺写出；背景两层细雪缓慢飘落，近处再落几片大雪。

准备：
  pip install fonttools
  字体：在 <fonts 目录> 里执行 npm pack @fontsource/noto-serif@5.1.1 @fontsource/jetbrains-mono@5.1.1，
        再把两个 tgz 分别解压到同名目录（fontsource-noto-serif-5.1.1/、fontsource-jetbrains-mono-5.1.1/）
  签名：博客仓库 docs/.vitepress/theme/signature.mjs 导出的 signature 对象，存成 JSON
用法：python scripts/make_banner.py <fonts 目录> <signature.json> assets
"""
import json
import random
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

fonts_dir, sig_path, out_dir = map(Path, sys.argv[1:4])
serif = fonts_dir / 'fontsource-noto-serif-5.1.1/package/files'
mono = fonts_dir / 'fontsource-jetbrains-mono-5.1.1/package/files'
FONTS = {
    'name': TTFont(serif / 'noto-serif-latin-900-normal.woff'),
    'motto': TTFont(serif / 'noto-serif-latin-400-italic.woff'),
    'mono': TTFont(mono / 'jetbrains-mono-latin-400-normal.woff'),
}

W, H = 1280, 420
LEFT = 88

THEMES = {
    'dark': dict(bg='#1C1D22', text='#EEEEF1', text2='#C6C8D0', muted='#9C9EA8', line='#34363D',
                 brand='#AAB9D6', warm='#E3B7B3', snow='238,238,241', snow_a=(0.16, 0.08), flake=0.55),
    'light': dict(bg='#F5F5F7', text='#1C1D22', text2='#4A4C55', muted='#6E707A', line='#DCDCE1',
                  brand='#42537A', warm='#B0645E', snow='28,29,34', snow_a=(0.10, 0.05), flake=0.30),
}


def text_path(font_key, text, size, x, y, tracking=0.0):
    """把一段文字排成路径，返回 (d, 结束 x)。"""
    font = FONTS[font_key]
    scale = size / font['head'].unitsPerEm
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    pen = SVGPathPen(glyphs, ntos=lambda n: f'{n:.1f}'.rstrip('0').rstrip('.'))
    cursor = x
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
        cursor += glyphs[name].width * scale + tracking
    return pen.getCommands(), cursor - tracking


def snow_flakes(seed=7, count=34):
    rng = random.Random(seed)
    flakes = []
    for _ in range(count):
        depth = rng.random()
        flakes.append(dict(
            x=round(rng.uniform(0, W), 1),
            r=round(0.8 + depth * 1.6, 2),
            a=round(0.35 + depth * 0.65, 2),
            dur=round(16 - depth * 7, 2),
            delay=round(-rng.uniform(0, 16), 2),
            sway=round(rng.uniform(4, 9), 2),
            sway_delay=round(-rng.uniform(0, 9), 2),
        ))
    return flakes


def build(theme_name):
    t = THEMES[theme_name]
    sig = json.loads(Path(sig_path).read_text())

    eyebrow, _ = text_path('mono', 'HUANGDIHD · BEIJING', 14, LEFT, 116, tracking=4.2)
    name, _ = text_path('name', 'Huangdihd', 104, LEFT - 4, 228, tracking=-1)
    m1, end = text_path('motto', 'All I need, knowledge and ', 30, LEFT, 288)
    m2, end = text_path('motto', 'love', 30, end, 288)
    m3, _ = text_path('motto', '.', 30, end, 288)
    site, _ = text_path('mono', 'huangdihd.shouldbe.top', 14, LEFT, 364, tracking=0.6)

    # 签名放在右侧，高 236
    box = sig['box']
    sig_h = 236
    k = sig_h / box['height']
    sig_w = box['width'] * k
    sx, sy = W - LEFT - sig_w, (H - sig_h) / 2 - 4
    ink_scale = 0.5  # 博客上签名很小，笔画加粗过；横幅里大很多，收细一些

    masks, inks = [], []
    for i, s in enumerate(sig['strokes']):
        delay = 0.9 + float(s['delay'])
        masks.append(
            f'<mask id="m{i}" maskUnits="userSpaceOnUse" x="{box["x"]}" y="{box["y"]}" '
            f'width="{box["width"]}" height="{box["height"]}">'
            f'<path class="reveal" d="{s["center"]}" stroke-width="{s["reveal"]}" pathLength="1" '
            f'style="animation-delay:{delay:.3f}s;animation-duration:{s["duration"]}s"/></mask>'
        )
        segs = ''.join(f'<path d="{seg["d"]}" stroke-width="{seg["width"] * ink_scale:.2f}"/>' for seg in s['ink'])
        inks.append(f'<g mask="url(#m{i})">{segs}</g>')

    flakes = ''.join(
        f'<g class="sway" style="animation-duration:{f["sway"]}s;animation-delay:{f["sway_delay"]}s">'
        f'<circle class="flake" cx="{f["x"]}" cy="-6" r="{f["r"]}" fill-opacity="{f["a"]}" '
        f'style="animation-duration:{f["dur"]}s;animation-delay:{f["delay"]}s"/></g>'
        for f in snow_flakes()
    )

    a1, a2 = t['snow_a']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Huangdihd — All I need, knowledge and love. 阿凛">
<style>
.s1 {{ animation: fall1 9s linear infinite; }}
.s2 {{ animation: fall2 13s linear infinite; }}
@keyframes fall1 {{ to {{ transform: translate(37px, 41px); }} }}
@keyframes fall2 {{ to {{ transform: translate(-23px, 29px); }} }}
.flake {{ fill: rgb({t['snow']}); animation-name: drop; animation-timing-function: linear; animation-iteration-count: infinite; }}
@keyframes drop {{ to {{ transform: translateY({H + 12}px); }} }}
.sway {{ animation-name: sway; animation-timing-function: ease-in-out; animation-iteration-count: infinite; animation-direction: alternate; }}
@keyframes sway {{ from {{ transform: translateX(-10px); }} to {{ transform: translateX(10px); }} }}
.ink path {{ fill: none; stroke: {t['brand']}; stroke-linecap: round; stroke-linejoin: round; }}
.reveal {{ fill: none; stroke: #fff; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1 2; stroke-dashoffset: 1.01; animation: write linear forwards; }}
@keyframes write {{ to {{ stroke-dashoffset: 0; }} }}
.rise {{ animation: rise 1s cubic-bezier(.2,.7,.2,1) both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} }}
@media (prefers-reduced-motion: reduce) {{
  .s1, .s2, .flake, .sway, .rise {{ animation: none; }}
  .reveal {{ animation: none; stroke-dashoffset: 0; }}
}}
</style>
<defs>
<pattern id="p1" width="37" height="41" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="rgb({t['snow']})" fill-opacity="{a1}"/></pattern>
<pattern id="p2" width="23" height="29" patternUnits="userSpaceOnUse"><circle cx="12.5" cy="8.5" r="1" fill="rgb({t['snow']})" fill-opacity="{a2}"/></pattern>
{''.join(masks)}
</defs>
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
<g class="s1"><rect x="-37" y="-41" width="{W + 74}" height="{H + 82}" fill="url(#p1)"/></g>
<g class="s2"><rect x="-23" y="-29" width="{W + 46}" height="{H + 58}" fill="url(#p2)"/></g>
<g>{flakes}</g>
<g class="rise"><path d="{eyebrow}" fill="{t['muted']}"/></g>
<g class="rise" style="animation-delay:.08s"><path d="{name}" fill="{t['text']}"/></g>
<g class="rise" style="animation-delay:.18s"><path d="{m1}" fill="{t['text2']}"/><path d="{m2}" fill="{t['warm']}"/><path d="{m3}" fill="{t['text2']}"/></g>
<g class="rise" style="animation-delay:.28s"><rect x="{LEFT}" y="318" width="48" height="1.5" fill="{t['brand']}"/><path d="{site}" fill="{t['muted']}"/></g>
<g class="ink" transform="translate({sx:.1f} {sy:.1f}) scale({k:.4f}) translate({-box['x']} {-box['y']})">{''.join(inks)}</g>
<rect y="{H - 1}" width="{W}" height="1" fill="{t['line']}"/>
</svg>
'''


out = Path(out_dir)
out.mkdir(parents=True, exist_ok=True)
for theme in THEMES:
    svg = build(theme)
    (out / f'banner-{theme}.svg').write_text(svg)
    print(theme, f'{len(svg) / 1024:.1f} KiB')
