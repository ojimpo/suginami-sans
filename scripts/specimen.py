"""Create an editorial specimen with original prose and actual font outlines."""
import html
import json
import shutil
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
from font_project import ROOT, sha256, write_json
from raster import render_text


def make_specimen(config, source):
    version = f'{config["version_major"]}.{config["version_minor"]:03d}'
    output = ROOT / 'proofs'
    template = ROOT / 'scripts/specimen'
    article = json.loads((template / 'text.json').read_text(encoding='utf-8'))
    font = ROOT / (config['output_stem'] + '.otf')
    paper, ink, muted, rule, accent = '#f5f3eb', '#171916', '#666a60', '#cfcec4', '#ad4929'
    image = Image.new('RGB', (1600, 2920), paper)
    draw = ImageDraw.Draw(image)
    label_font, small_font = ImageFont.load_default(size=21), ImageFont.load_default(size=17)
    placements = []

    def label(value, x, y, color=muted, small=False):
        draw.text((x, y), value, fill=color, font=small_font if small else label_font)

    def line(y):
        draw.line((72, y, 1528, y), fill=rule, width=2)

    def text(value, x, y, size, width=1456, alternate=False, kern=True, color=ink):
        mask = render_text(font, value, size, alternate, kern)
        while mask.width > width and size > 12:
            size -= 1
            mask = render_text(font, value, size, alternate, kern)
        assert mask.width <= width, value
        assert x + mask.width <= image.width - 40 and y + mask.height <= image.height - 30
        image.paste(color, (x, y), mask)
        placements.append({'text': value, 'size_px': size, 'ss01': alternate, 'kern': kern,
                           'rect': [x, y, mask.width, mask.height]})

    def paragraph(value, x, y, size, width, leading):
        words = value.split()
        rows, current = [], ''
        for word in words:
            trial = current + (' ' if current else '') + word
            if render_text(font, trial, size).width <= width:
                current = trial
            else:
                rows.append(current)
                current = word
        if current:
            rows.append(current)
        for row in rows:
            text(row, x, y, size, width)
            y += leading
        return y

    label('SUGINAMI SANS / TYPE SPECIMEN', 80, 45, accent)
    text('Suginami Sans', 72, 90, 135)
    label('EXTENDED BOLD', 80, 270, ink)
    label(f'STATIC {version}  /  99 GLYPHS  /  97 UNICODE', 865, 270)
    line(325)
    label('01 / A TEXT IN CONTEXT', 80, 355, accent)
    text('A quieter way', 72, 400, 95)
    text('through the city', 72, 520, 95)
    y = paragraph(article['deck'], 72, 670, 34, 1456, 54) + 25
    for value in article['paragraphs']:
        y = paragraph(value, 72, y, 26, 1456, 40) + 25
    assert y < 1360, f'Article overflows its panel: {y}'
    line(1400)
    label('02 / THE CHARACTER SET', 80, 1430, accent)
    text('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 72, 1475, 59)
    text('abcdefghijklmnopqrstuvwxyz', 72, 1570, 65)
    text('0123456789', 72, 1675, 85)
    text('! ? & @ # $ % + = / ( ) [ ] { }', 72, 1790, 47)
    line(1895)
    label('03 / TWO WAYS TO WRITE y', 80, 1925, accent)
    label('DEFAULT / U+0079', 80, 1980)
    label('ALTERNATE / ss01', 835, 1980)
    text('Type freely', 72, 2020, 60, width=685)
    text('Type freely', 827, 2020, 60, width=685, alternate=True)
    line(2145)
    label('04 / SPACING', 80, 2175, accent)
    label('KERNING ON', 80, 2225)
    label('KERNING OFF', 835, 2225)
    text('AVATAR WA To Ta', 72, 2265, 47, width=685)
    text('AVATAR WA To Ta', 827, 2265, 47, width=685, kern=False)
    line(2380)
    label('05 / SIZE & LEGIBILITY', 80, 2410, accent)
    for size, y in [(12, 2470), (16, 2515), (24, 2570), (48, 2635), (96, 2730)]:
        label(f'{size:02d} PX', 80, y + 5, small=True)
        text('Il1 O0 rn m vv w', 210, y, size, width=1310)
    label('SIL OPEN FONT LICENSE 1.1 / Copyright (c) 2026, Kouki Ojima', 80, 2878, small=True)
    image.save(output / 'specimen.png')

    cmap = {g['unicode']: name for name, g in source.items() if g['unicode'] is not None}
    groups = [('大文字', range(65, 91)), ('小文字', range(97, 123)), ('数字', range(48, 58)),
              ('記号', [cp for cp in range(33, 127) if not chr(cp).isalnum()] + [0x2013, 0x2014])]
    sections = []
    for title, codes in groups:
        cells = [f'<div class="glyph"><span class="face">{html.escape(chr(cp))}</span><small>U+{cp:04X}</small></div>' for cp in codes]
        sections.append(f'<h3>{title}</h3><div class="glyph-grid">{"".join(cells)}</div>')
    sections.append('<h3>代替字形</h3><div class="glyph-grid"><div class="glyph"><span class="face alternate">y</span><small>y.alt / ss01</small></div></div>')
    size_rows = ''.join(f'<div class="size-row"><small>{size}px</small><div class="scroll"><div class="face size-example" style="font-size:{size}px">Il1 O0 rn m vv w / u y g y</div><div class="face size-example alternate inverse" style="font-size:{size}px">Il1 O0 rn m vv w / u y g y</div></div></div>' for size in [12, 16, 24, 48, 96])
    shaping = {}
    for ext in ['otf', 'ttf']:
        face = hb.Font(hb.Face((ROOT / (config['output_stem'] + '.' + ext)).read_bytes()))
        face.scale = (1000, 1000)
        shaping[ext] = {}
        for key, value, alternate, kern in [('default', 'Type freely', False, True), ('alternate', 'Type freely', True, True),
                ('kern_on', 'AVATAR WA To Ta', False, True), ('kern_off', 'AVATAR WA To Ta', False, False)]:
            buffer = hb.Buffer(); buffer.add_str(value); buffer.guess_segment_properties()
            hb.shape(face, buffer, {'ss01': int(alternate), 'kern': int(kern)})
            shaping[ext][key] = sum(p.x_advance for p in buffer.glyph_positions) / 10
    data = {'version': version, 'encoded': sorted(cmap), 'article': article, 'expected_widths_100px': shaping}
    page = (template / 'index.html').read_text(encoding='utf-8')
    substitutions = {'__VERSION__': version, '__GLYPHS__': ''.join(sections), '__SIZES__': size_rows,
                     '__ARTICLE_TITLE__': html.escape(article['title']), '__ARTICLE_DECK__': html.escape(article['deck']),
                     '__PARAGRAPHS__': ''.join('<p>' + html.escape(p) + '</p>' for p in article['paragraphs']),
                     '__DATA__': json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')}
    for token, value in substitutions.items():
        page = page.replace(token, value)
    (output / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    for name in ['specimen.css', 'specimen.js']:
        shutil.copyfile(template / name, output / name)
    write_json('docs/SPECIMEN_BUILD.json', {'version': version, 'font_sha256': sha256(font),
        'raster_dimensions': list(image.size), 'raster_placements': placements,
        'article_words': len(' '.join(article['paragraphs']).split()), 'browser_widths_100px': shaping,
        'files': {name: sha256(output / name) for name in ['specimen.png', 'index.html', 'specimen.css', 'specimen.js']}})
