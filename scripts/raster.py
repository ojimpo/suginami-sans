"""Render real binaries with HarfBuzz + FreeType and prepare local browser proofs."""
import html
import math
import json

import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.ttLib import TTFont

from font_project import ROOT, read_json, read_ufo, recording_bounds, sha256, write_json
from glyph_source import load_source

PROOFS = ROOT / 'proofs/static'


def render_text(path, text, size, alternate=False, kern=True, phase_x=0.0, phase_y=0.0, allow_notdef=False):
    font = hb.Font(hb.Face(path.read_bytes()))
    font.scale = (size * 64, size * 64)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, {'ss01': int(alternate), 'kern': int(kern)})
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, size)
    advance = sum(p.x_advance for p in buffer.glyph_positions) / 64
    pad = 8
    baseline = pad + math.ceil(size * 0.85)
    mask = Image.new('L', (math.ceil(advance) + pad * 2, math.ceil(size * 1.1) + pad * 2))
    cursor = 0
    for glyph, position in zip(buffer.glyph_infos, buffer.glyph_positions):
        assert glyph.codepoint != 0 or allow_notdef, f'Unsupported proof character in {text!r}'
        origin = (cursor + position.x_offset) / 64 + phase_x
        left = math.floor(origin)
        face.set_transform(freetype.Matrix(65536, 0, 0, 65536),
                           freetype.Vector(round((origin - left) * 64), position.y_offset + round(phase_y * 64)))
        face.load_glyph(glyph.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        bitmap = face.glyph.bitmap
        if bitmap.width and bitmap.rows:
            pixels = bytes(bitmap.buffer)
            glyphmask = Image.frombytes('L', (bitmap.width, bitmap.rows), pixels, 'raw', 'L', abs(bitmap.pitch))
            x = pad + left + face.glyph.bitmap_left
            y = baseline - face.glyph.bitmap_top
            if x < 0 or y < 0 or x + bitmap.width > mask.width or y + bitmap.rows > mask.height:
                raise AssertionError(f'Clipped raster: {text}, {size}px')
            layer = Image.new('L', mask.size)
            layer.paste(glyphmask, (x, y))
            from PIL import ImageChops
            mask = ImageChops.lighter(mask, layer)
        cursor += position.x_advance
    return mask
