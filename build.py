#!/usr/bin/env python3
"""Render index.html from content.json.

    python3 build.py                 # content.json -> index.html
    python3 build.py -o preview.html # ghi ra file khác

Sửa nội dung trong content.json, chạy lại lệnh trên. Không sửa index.html
trực tiếp — nó sẽ bị ghi đè.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# inline markup:  **bold**  *italic*  @@accent@@  ##green##  `mono`  ^{sup}
# LaTeX ($...$, $$...$$) được bảo vệ, không bị đụng tới.
# --------------------------------------------------------------------------
MATH_RE = re.compile(r'(\$\$.+?\$\$|\$[^$]+?\$)', re.S)


def _sup(text):
    return re.sub(r'\^\{(.+?)\}', r'<sup>\1</sup>', text)


def inline(text, t=None):
    """Chuyển cú pháp inline rút gọn thành HTML."""
    if text is None:
        return ''
    t = t or THEME
    parts = MATH_RE.split(str(text))
    out = []
    for i, part in enumerate(parts):
        if i % 2:                       # đoạn LaTeX -> giữ nguyên
            out.append(part)
            continue
        p = part
        p = re.sub(r'`(.+?)`',
                   lambda m: "<span style=\"font-family: 'JetBrains Mono', monospace; "
                             f"font-size: 14px; color: {t['accent']};\">{_sup(m.group(1))}</span>", p)
        p = re.sub(r'@@(.+?)@@', lambda m: f"<strong style=\"color: {t['accent']};\">{m.group(1)}</strong>", p)
        p = re.sub(r'##(.+?)##', lambda m: f"<span style=\"color: {t['green']}; font-weight: 600;\">{m.group(1)}</span>", p)
        p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)
        p = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', p)
        p = _sup(p)
        out.append(p)
    return ''.join(out)


# --------------------------------------------------------------------------
# blocks
# --------------------------------------------------------------------------
PARAGRAPH_VARIANTS = {
    # variant      -> (font-size, color, line-height, margin-bottom mặc định)
    'body':     ('18px', '#2b303c', '1.72', 16),
    'card':     ('16px', '#4a5060', '1.7', 14),
    'caption':  ('14.5px', '#6b7180', '1.6', 18),
    'note':     ('14.5px', '#5b6170', '1.65', 40),
    'footnote': ('12.5px', '#9aa1b1', None, 12),
    'small':    ('15px', '#5b6170', '1.65', 0),
    'boxed':    ('15.5px', '#2b303c', '1.65', 12),
    'guarantee':('16px', '#3a4150', '1.7', 6),
}


def p_block(b, default_variant='card'):
    variant = b.get('variant', default_variant)
    size, color, lh, mb = PARAGRAPH_VARIANTS[variant]
    if b.get('last'):
        mb = 0
    mb = b.get('margin_bottom', mb)
    margin = '0' if mb == 0 else f'0 0 {mb}px'
    style = f'font-size: {size}; color: {color}; margin: {margin};'
    if variant == 'small':
        style = f'font-size: {size}; color: {color}; margin: 6px 0 0;'
    if lh:
        style += f' line-height: {lh};'
    return f'      <p style="{style}">{inline(b["text"])}</p>'


def heading_block(b):
    size = b.get('size', 22)
    mb = b.get('margin_bottom', 6)
    return ('      <h3 style="font-family: \'Newsreader\', serif; font-size: %dpx; font-weight: 600; '
            'margin: 0 0 %dpx; color: %s;">%s</h3>' % (size, mb, THEME['ink'], inline(b['text'])))


def list_block(b):
    mb = b.get('margin_bottom', 0)
    color = b.get('color', '#4a5060')
    items = b['items']
    lis = []
    for i, it in enumerate(items):
        s = ' style="margin-bottom: 8px;"' if i < len(items) - 1 else ''
        lis.append(f'        <li{s}>{inline(it)}</li>')
    margin = '0' if mb == 0 else '0 0 %dpx' % mb
    return ('      <ul style="font-size: 15px; color: %s; margin: %s; padding-left: 20px; '
            'line-height: 1.7;">\n%s\n      </ul>' % (color, margin, '\n'.join(lis)))


def math_block(b):
    return f'        $${b["tex"]}$$'


def defs_block(b):
    cells = []
    for it in b['items']:
        cells.append(
            '          <div style="background: #f7f9fc; border-radius: 10px; padding: 14px 16px;">\n'
            "            <div style=\"font-family: 'JetBrains Mono', monospace; font-size: 14px; "
            'color: %s; font-weight: 500; margin-bottom: 2px;">%s</div>\n'
            '            <div style="font-size: 14px; color: #5b6170;">%s</div>\n'
            '          </div>' % (THEME['accent'], _sup(it['term']), inline(it['desc'])))
    return ('        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; '
            'margin-bottom: 14px;">\n%s\n        </div>' % '\n'.join(cells))


def callout_block(b):
    inner = '\n'.join(render_block(x, default_variant='boxed') for x in b['blocks'])
    return ('        <div style="background: #f7f9fc; border: 1px solid #e7ebf2; border-left: 3px solid %s; '
            'border-radius: 10px; padding: 16px 20px; margin-bottom: 14px;">\n%s\n        </div>'
            % (THEME['accent'], inner))


def card_block(b):
    head = (
        '        <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">\n'
        f'          <span style="font-size: 22px;">{b["icon"]}</span>\n'
        "          <h3 style=\"font-family: 'Newsreader', serif; font-size: 23px; font-weight: 600; "
        f'margin: 0; color: {THEME["ink"]};">{inline(b["title"])}</h3>\n'
        f'          <span style="font-size: 14px; color: #8a909e;">{inline(b["subtitle"])}</span>\n'
        '        </div>')
    inner = '\n'.join(render_block(x, default_variant='card') for x in b['blocks'])
    return ('      <div style="border: 1px solid %s; border-radius: 16px; padding: 28px 30px; margin-bottom: 20px;">\n'
            '%s\n%s\n      </div>' % (THEME['line'], head, inner))


def highlight_box_block(b):
    inner = '\n'.join(render_block(x, default_variant='guarantee') for x in b['blocks'])
    return ('      <div style="background: linear-gradient(180deg, #f4f8ff, %s); border: 1px solid #d8e5fb; '
            'border-radius: 16px; padding: 26px 30px;">\n'
            "        <h3 style=\"font-family: 'Newsreader', serif; font-size: 21px; font-weight: 600; "
            'margin: 0 0 10px; color: %s;">%s</h3>\n%s\n      </div>'
            % (THEME['accent_bg'], THEME['ink'], inline(b['title']), inner))


def details_block(b):
    inner = '\n'.join(render_block(x, default_variant='boxed') for x in b['blocks'])
    return (
        '      <details style="border: 1px solid #d8e5fb; border-radius: 16px; '
        'background: #fbfdff; margin-top: 18px; overflow: hidden;">\n'
        '        <summary style="cursor: pointer; padding: 18px 22px; font-size: 16px; '
        f'font-weight: 600; color: {THEME["ink"]}; background: {THEME["accent_bg"]}; '
        'list-style-position: inside;">'
        f'{inline(b["summary"])}</summary>\n'
        '        <div style="padding: 22px 26px 24px;">\n'
        f'{inner}\n'
        '        </div>\n'
        '      </details>')


def figure_pdf_block(b):
    max_width = b.get('max_width')
    figure_style = ('margin: 0 auto 48px; max-width: %dpx;' % max_width
                    if max_width else 'margin: 0 0 36px;')
    return (
        f'      <figure style="{figure_style}">\n'
        f'        <object data="{b["src"]}#toolbar=0&navpanes=0&scrollbar=0&view=FitH" type="application/pdf" '
        f'style="width: 100%; aspect-ratio: {b["aspect_ratio"]}; border-radius: 16px; border: 1px solid #e4e8f0; display: block;">\n'
        f'          <p style="text-align: center; color: #9aa1b1; padding: 40px;">Unable to display PDF. '
        f'<a href="{b["src"]}">Download PDF</a></p>\n'
        '        </object>\n'
        f'        <figcaption style="text-align: center; font-size: 14px; color: #7b8294; margin-top: 14px;">'
        f'{caption(b["caption"])}</figcaption>\n'
        '      </figure>')


def caption(text):
    """Caption: **Figure 2.** ở đầu được tô màu #4a5060 như bản gốc."""
    html = inline(text)
    return html.replace('<strong>', '<strong style="color: #4a5060;">', 1)


# ---- bảng ---------------------------------------------------------------
def table_block(b):
    pad = b.get('padding', 10)
    cols = b['columns']
    ths = []
    for i, c in enumerate(cols):
        align = c.get('align', 'center')
        last = i == len(cols) - 1
        px = 12 if (i == 0 or last or pad == 11) else 8
        weight = 700 if c.get('emphasis') else 600
        ths.append(f'              <th style="text-align: {align}; padding: 10px {px}px; '
                   f'font-weight: {weight}; color: {THEME["ink"]};">{inline(c["label"])}</th>')

    trs = []
    for row in b['rows']:
        hl, total = row.get('highlight'), row.get('total')
        if total:
            tr = f'            <tr style="border-bottom: 2px solid {THEME["accent"]}; background: {THEME["accent_bg"]};">'
        elif hl:
            tr = f'            <tr style="border-bottom: 1px solid {THEME["line"]}; background: {THEME["accent_bg"]};">'
        else:
            tr = f'            <tr style="border-bottom: 1px solid {THEME["line"]}; background: transparent;">'
        tds = [tr]
        for i, c in enumerate(cols):
            cell = row['cells'].get(c['key'], '')
            bold = muted = False
            if isinstance(cell, dict):
                bold = cell.get('bold', False)
                muted = cell.get('muted', False)
                cell = cell.get('text', '')
            align = c.get('align', 'center')
            last = i == len(cols) - 1
            px = 12 if (i == 0 or last or pad == 11) else 8
            style = ('' if i == 0 and align == 'left' else f'text-align: {align}; ')
            style += f'padding: {pad}px {px}px; '
            if i == 0:                                  # cột tên
                style += (f'color: {THEME["ink"]}; font-weight: 700;' if (hl or total)
                          else 'color: #4a5060; font-weight: 400;')
            elif c.get('style') == 'muted-small':
                style += 'color: #8a909e; font-size: 13px;'
            elif c.get('color') == 'accent':
                style += f'color: {THEME["accent"]}; font-weight: {700 if total else c.get("weight", 600)};'
            elif c.get('color') == 'green':
                col = '#9aa1b1' if muted else THEME['green']
                style += f'color: {col}; font-weight: {700 if (total or bold) else c.get("weight", 500)};'
            elif hl or total:
                style += f'color: {THEME["accent"] if hl else "#6b7180"}; font-weight: 700;' if hl else 'color: #6b7180;'
            elif c.get('emphasis'):
                style += 'color: #4a5060; font-weight: 700;'
            elif c.get('weight'):
                style += f'color: #6b7180; font-weight: {c["weight"]};'
            else:
                style += 'color: #6b7180;' + ('' if pad == 11 else ' font-weight: 400;')
            tds.append(f'              <td style="{style.strip()}">{inline(cell)}</td>')
        tds.append('            </tr>')
        trs.append('\n'.join(tds))

    return (
        '      <div style="overflow-x: auto; margin-bottom: 14px;">\n'
        f'        <table style="width: 100%; border-collapse: collapse; font-size: 14.5px; min-width: {b["min_width"]}px;">\n'
        '          <thead>\n'
        f'            <tr style="border-bottom: 2px solid {THEME["body"]};">\n'
        + '\n'.join(ths) + '\n'
        '            </tr>\n'
        '          </thead>\n'
        '          <tbody style="font-variant-numeric: tabular-nums;">\n'
        + '\n'.join(trs) + '\n'
        '          </tbody>\n'
        '        </table>\n'
        '      </div>')


# ---- gallery ảnh & video -------------------------------------------------
def gallery_item(it):
    n = len(it['images'])
    imgs = '\n'.join(
        f'              <img src="{im["src"]}" alt="{im["alt"]}" '
        'style="width: 100%; aspect-ratio: 1; object-fit: cover; display: block;">'
        for im in it['images'])
    return (
        '          <div>\n'
        f'            <div style="display: grid; grid-template-columns: {" ".join(["1fr"] * n)}; gap: 4px; '
        'border-radius: 12px; overflow: hidden;">\n'
        f'{imgs}\n'
        '            </div>\n'
        '            <div style="margin-top: 10px; display: flex; align-items: center; justify-content: space-between;">\n'
        f'              <div style="font-size: 15px; font-weight: 600; color: {THEME["ink"]};">{inline(it["title"])}</div>\n'
        f'              <div style="font-size: 13px; color: #6b7180;"><span style="color: {THEME["accent"]}; '
        f'font-weight: 600;">{it["ours"]}</span> vs. {it["baseline"]}</div>\n'
        '            </div>\n'
        '          </div>')


def task_gallery_block(b):
    rows = []
    for i, row in enumerate(b['rows']):
        last = i == len(b['rows']) - 1
        mb = '' if last else ' margin-bottom: 20px;'
        items = '\n'.join(gallery_item(it) for it in row['items'])
        rows.append(f'        <div style="display: grid; grid-template-columns: '
                    f'{" ".join(["1fr"] * row["columns"])}; gap: 20px;{mb}">\n{items}\n        </div>')
    return ('      <figure style="margin: 0 0 36px;">\n' + '\n'.join(rows) + '\n'
            '        <figcaption style="text-align: center; font-size: 14px; color: #7b8294; margin-top: 18px;">'
            f'{caption(b["caption"])}</figcaption>\n'
            '      </figure>')


def video_grid_block(b):
    vids = '\n'.join(
        f'          <video controls muted style="width: 100%; border-radius: 10px; display: block; '
        f'background: #0a0b0d;"><source src="{src}" type="video/mp4"></video>'
        for src in b['videos'])
    return (
        f'      <div style="margin-bottom: {b.get("margin_bottom", 32)}px;">\n'
        f'        <div style="font-size: 15px; font-weight: 600; color: {THEME["ink"]}; margin-bottom: 12px;">'
        f'{inline(b["title"])}</div>\n'
        f'        <div style="display: grid; grid-template-columns: repeat({b["columns"]}, 1fr); gap: 8px;">\n'
        f'{vids}\n'
        '        </div>\n'
        '      </div>')


BLOCKS = {
    'paragraph': p_block,
    'heading': lambda b: heading_block(b),
    'list': list_block,
    'math': math_block,
    'defs': defs_block,
    'callout': callout_block,
    'card': card_block,
    'highlight_box': highlight_box_block,
    'details': details_block,
    'figure_pdf': figure_pdf_block,
    'table': table_block,
    'task_gallery': task_gallery_block,
    'video_grid': video_grid_block,
}


def render_block(b, default_variant='card'):
    kind = b.get('type')
    if kind not in BLOCKS:
        sys.exit(f'build.py: block type không hợp lệ: {kind!r}')
    if kind == 'paragraph':
        return p_block(b, default_variant)
    return BLOCKS[kind](b)


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------
def section_heading(text):
    return ("      <h2 style=\"font-family: 'Newsreader', serif; font-size: 13px; font-weight: 600; "
            f'letter-spacing: 0.12em; text-transform: uppercase; color: {THEME["accent"]}; '
            f'margin: 0 0 18px;">{inline(text)}</h2>')


def hero_button(btn):
    label = f'{btn["icon"]} {inline(btn["label"])}'
    primary = btn.get('variant') == 'primary'
    base = 'display: inline-flex; align-items: center; gap: 8px; padding: 11px 20px; border-radius: 10px;'
    skin = ('background: #15171d; color: #fff;' if primary
            else 'background: #fff; border: 1px solid #d9dce3; color: #2b2f3a;')
    skin += ' font-size: 14.5px; font-weight: 500;'
    if btn.get('href'):
        note = (f' <span style="font-size: 11px; font-weight: 600; opacity: 0.8;">{btn["note"]}</span>'
                if btn.get('note') else '')
        return (f'        <a href="{btn["href"]}" style="{base} {skin} text-decoration: none;">{label}{note}</a>')
    note_style = ('font-size: 11px; font-weight: 600; opacity: 0.8;' if primary
                  else 'font-size: 11px; font-weight: 600; color: #8a909e;')
    note = f' <span style="{note_style}">{btn["note"]}</span>' if btn.get('note') else ''
    opacity = '0.5' if primary else '0.55'
    return f'        <span style="{base} {skin} opacity: {opacity}; cursor: not-allowed;">{label}{note}</span>'


def stat_card(s):
    return (
        f'      <div style="text-align: center; padding: 24px 16px; border: 1px solid {THEME["line"]}; '
        'border-radius: 14px; background: #fafbfc;">\n'
        f"        <div style=\"font-family: 'Newsreader', serif; font-size: 38px; font-weight: 600; "
        f'color: {THEME["accent"]}; line-height: 1;">{s["value"]}</div>\n'
        f'        <div style="font-size: 13px; color: #6b7180; margin-top: 8px;">{inline(s["caption"])}</div>\n'
        '      </div>')


def build(data):
    global THEME
    THEME = data['theme']
    nav, hero, foot = data['nav'], data['hero'], data['footer']

    nav_links = '\n'.join(
        f'      <a href="{l["href"]}" style="color: #5b6170; text-decoration: none;">{inline(l["label"])}</a>'
        for l in nav['links'])

    abstract = data['abstract']
    teaser = data.get('teaser')
    teaser_html = figure_pdf_block(teaser) if teaser else ''
    abstract_ps = []
    for i, text in enumerate(abstract['paragraphs']):
        last = i == len(abstract['paragraphs']) - 1
        abstract_ps.append(p_block({'text': text, 'variant': 'body',
                                    'margin_bottom': 0 if last else 16}))

    method = data['method']
    results = data['results']
    vid = data['video_section']

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{ margin: 0; }}
  ::selection {{ background: #cfe0fb; }}
  mjx-container {{ font-size: 1.02em !important; }}
</style>
<script>
  window.MathJax = {{
    tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] }},
    svg: {{ fontCache: 'global' }},
    startup: {{ typeset: true }}
  }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" id="MathJax-script" async></script>
</head>
<body>
<!-- ĐỪNG SỬA FILE NÀY — nó được sinh ra từ content.json bởi build.py -->
<div style="font-family: 'Inter', system-ui, sans-serif; color: {THEME['body']}; background: #ffffff; line-height: 1.65; -webkit-font-smoothing: antialiased;">

  <nav style="position: sticky; top: 0; z-index: 50; display: flex; align-items: center; justify-content: space-between; padding: 14px 32px; background: rgba(255,255,255,0.82); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid {THEME['line']};">
    <a href="#top" style="font-family: 'Newsreader', serif; font-weight: 600; font-size: 19px; letter-spacing: -0.01em; color: {THEME['body']}; text-decoration: none;">{nav['brand']['prefix']}<span style="color: {THEME['accent']};">{nav['brand']['accent']}</span></a>
    <div style="display: flex; align-items: center; gap: 28px; font-size: 14px; font-weight: 500;">
{nav_links}
    </div>
  </nav>

  <div id="top" style="max-width: 900px; margin: 0 auto; padding: 0 28px;">

    <!-- HERO -->
    <header style="text-align: center; padding: 76px 0 40px;">
      <div style="display: inline-block; font-size: 12.5px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: {THEME['accent']}; background: {THEME['accent_bg']}; padding: 6px 14px; border-radius: 999px; margin-bottom: 26px;">{inline(hero['badge'])}</div>
      <h1 style="font-family: 'Newsreader', serif; font-weight: 600; font-size: 47px; line-height: 1.14; letter-spacing: -0.02em; margin: 0 0 14px; color: {THEME['ink']}; text-wrap: balance;">{inline(hero['title'])}</h1>
      <p style="font-family: 'Newsreader', serif; font-style: italic; font-size: 23px; color: #565c6b; margin: 0 auto 30px; max-width: 620px; line-height: 1.4;">{inline(hero['tagline'])}</p>

      <div style="font-size: 17px; color: #2b2f3a; margin-bottom: 4px;">{inline(hero['authors'])}</div>
      <div style="font-size: 14.5px; color: #8a909e; margin-bottom: 30px;">{inline(hero['venue'])}</div>

      <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;">
{chr(10).join(hero_button(b) for b in hero['buttons'])}
      </div>
    </header>

    <!-- TEASER -->
{teaser_html}

    <!-- STAT CARDS -->
    <section style="display: grid; grid-template-columns: repeat({len(data['stats'])}, 1fr); gap: 16px; margin: 8px 0 56px;">
{chr(10).join(stat_card(s) for s in data['stats'])}
    </section>

    <!-- ABSTRACT -->
    <section id="{abstract['id']}" style="margin-bottom: 64px; scroll-margin-top: 80px;">
{section_heading(abstract['heading'])}
{chr(10).join(abstract_ps)}
    </section>

    <!-- METHOD -->
    <section id="{method['id']}" style="margin-bottom: 64px; scroll-margin-top: 80px;">
{section_heading(method['heading'])}
{chr(10).join(render_block(b, 'body') for b in method['blocks'])}
    </section>

    <!-- RESULTS -->
    <section id="{results['id']}" style="margin-bottom: 56px; scroll-margin-top: 80px;">
      <h2 style="font-family: 'Newsreader', serif; font-size: 13px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: {THEME['accent']}; margin: 0 0 26px;">{inline(results['heading'])}</h2>
{chr(10).join(render_block(b, 'body') for b in results['blocks'])}
    </section>

    <!-- VIDEO -->
    <section id="{vid['id']}" style="margin-bottom: 64px; scroll-margin-top: 80px;">
{section_heading(vid['heading'])}
      <figure style="margin: 0;">
        <video controls style="width: 100%; border-radius: 16px; border: 1px solid #e4e8f0; display: block; background: #0a0b0d;">
          <source src="{vid['src']}" type="video/mp4">
        </video>
        <figcaption style="text-align: center; font-size: 14px; color: #7b8294; margin-top: 14px;">{caption(vid['caption'])}</figcaption>
      </figure>
    </section>

    <footer style="border-top: 1px solid {THEME['line']}; padding: 36px 0 64px; text-align: center;">
      <p style="font-family: 'Newsreader', serif; font-size: 18px; color: #4a5060; margin: 0 0 6px;">{foot['brand']['prefix']}<span style="color: {THEME['accent']};">{foot['brand']['accent']}</span></p>
      <p style="font-size: 13.5px; color: #9aa1b1; margin: 0;">{inline(foot['text'])}</p>
    </footer>

  </div>
</div>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-c', '--content', default=ROOT / 'content.json')
    ap.add_argument('-o', '--out', default=ROOT / 'index.html')
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.content).read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        sys.exit(f'build.py: content.json lỗi cú pháp JSON — dòng {e.lineno}, cột {e.colno}: {e.msg}')

    html = build(data)
    Path(args.out).write_text(html, encoding='utf-8')
    print(f'✓ {args.out} ({len(html):,} bytes) ← {args.content}')


if __name__ == '__main__':
    main()
