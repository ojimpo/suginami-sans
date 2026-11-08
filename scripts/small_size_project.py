"""Optical corrections derived from existing SVG curves, not image retracing."""
import pathops
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path


def contours(data):
    pen = RecordingPen()
    parse_path(data, pen)
    result, current = [], RecordingPen()
    for operation, points in pen.value:
        getattr(current, operation)(*points)
        if operation == 'closePath':
            result.append(current)
            current = RecordingPen()
    return result


def point_transform(point, cx, cy, factor):
    return cx + (point[0] - cx) * factor, cy + (point[1] - cy) * factor


def corrected_open_letter(glyph, plan):
    """Open the existing a/s terminals; keep extents and original curve structure."""
    source, result = RecordingPen(), RecordingPen()
    parse_path(glyph['paths'][0]['d'], source)
    if plan['letter'] == 'a':
        assert len(source.value) == 22 and source.value[15][0] == 'moveTo'
    else:
        assert plan['letter'] == 's' and len(source.value) == 16
    for index, (operation, points) in enumerate(source.value):
        if plan['letter'] == 'a':
            if index in [0, 12, 13]:
                points = tuple((x, y - plan['upper_terminal_lift'] if y == 60 else y) for x, y in points)
            elif index >= 15:
                points = tuple(point_transform(p, 123.5, 139.5, plan['counter_scale']) for p in points)
        else:
            if index in [0, 1, 14]:
                points = tuple((x, y - plan['upper_terminal_lift'] if y in [51, 59] else y) for x, y in points)
            elif index in [7, 8]:
                points = tuple((x, y + plan['lower_terminal_drop'] if y in [147, 138] else y) for x, y in points)
        getattr(result, operation)(*points)
    path = pathops.Path()
    result.replay(path.getPen())
    path.fillType = pathops.FillType.EVEN_ODD
    return pathops.simplify(path, clockwise=True)


def corrected_percent(glyph, plan):
    combined = pathops.Path()
    for index, item in enumerate(glyph['paths']):
        path = pathops.Path()
        if index == 0:
            parse_path(item['d'], path.getPen())  # Slash stays unchanged.
        else:
            cx, cy = (53, -19) if index == 1 else (207, 141)
            dx = plan['circle_separation_x'] * (-1 if index == 1 else 1)
            for ci, contour in enumerate(contours(item['d'])):
                sx, sy = plan['outer_scale'] if ci == 0 else plan['counter_scale']
                contour.replay(TransformPen(path.getPen(), Transform(
                    sx, 0, 0, sy, cx * (1 - sx) + dx, cy * (1 - sy))))
        path.fillType = pathops.FillType.WINDING
        combined = pathops.op(combined, path, pathops.PathOp.UNION, clockwise=True)
    return combined


def corrected_at(glyph, plan):
    source, result = RecordingPen(), RecordingPen()
    parse_path(glyph['paths'][0]['d'], source)
    # The plan is guarded by the complete canonical JSON SHA-256 in the caller.
    assert len(source.value) == 58
    assert source.value[37][0] == source.value[52][0] == 'moveTo'
    outer, core, counter = plan['outer_scale'], plan['core_scale'], plan['counter_scale']
    for index, (operation, points) in enumerate(source.value):
        if index >= 52:
            break  # Omit the delivered numerical sliver (<0.01 font-unit area).
        if index <= 15 or 32 <= index <= 35:
            points = tuple(point_transform(p, 153, 84, outer) for p in points)
        elif 16 <= index <= 30:
            points = tuple(point_transform(p, 155, 80, core) for p in points)
        elif 37 <= index <= 51:
            points = tuple(point_transform(p, 155, 80, counter) for p in points)
        elif index == 31:
            # Bridge the unchanged a body to the expanded spiral, preserving curves.
            points = (point_transform(points[0], 155, 80, core),
                      *(point_transform(p, 153, 84, outer) for p in points[1:]))
        getattr(result, operation)(*points)
    path = pathops.Path()
    result.replay(path.getPen())
    path.fillType = pathops.FillType.WINDING
    return pathops.simplify(path, clockwise=True)
