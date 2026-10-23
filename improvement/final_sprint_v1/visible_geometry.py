"""Image-domain intersection of persistent tracked subject quadrilaterals.

The intersection describes only the transported, originally observed extent.
It neither invents newly revealed subject pixels nor changes tracker memory.
"""
from __future__ import annotations

import math
from typing import Sequence


def _clip_axis(polygon: list[list[float]], axis: int, edge: float,
               keep_greater: bool) -> list[list[float]]:
    """Sutherland--Hodgman clipping against one closed image half-plane."""
    if not polygon:
        return []
    clipped = []
    start = polygon[-1]
    start_inside = start[axis] >= edge if keep_greater else start[axis] <= edge
    for end in polygon:
        end_inside = end[axis] >= edge if keep_greater else end[axis] <= edge
        if start_inside != end_inside:
            fraction = (edge - start[axis]) / (end[axis] - start[axis])
            crossing = [(1 - fraction) * start[i] + fraction * end[i] for i in (0, 1)]
            crossing[axis] = edge
            clipped.append(crossing)
        if end_inside:
            clipped.append(list(end))
        start, start_inside = end, end_inside
    return clipped


def visible_polygon(polygon: Sequence[Sequence[float]], width: int,
                    height: int) -> list[list[float]]:
    """Return the positive-area polygon/image intersection, or no support.

    A clipped axis-aligned bounding box alone is insufficient: a rotated
    polygon outside an image corner may have overlapping x/y projections.
    Boundary-only contact and degenerate polygons have no visible area.
    """
    if (type(width) is not int or type(height) is not int or min(width, height) <= 0
            or len(polygon) != 4
            or any(len(point) != 2 or any(type(v) not in (int, float) or not math.isfinite(v)
                                         for v in point) for point in polygon)):
        raise ValueError("Finite subject quadrilateral and native image dimensions required")
    clipped = [list(map(float, point)) for point in polygon]
    for axis, edge, keep_greater in ((0, 0., True), (0, float(width), False),
                                      (1, 0., True), (1, float(height), False)):
        clipped = _clip_axis(clipped, axis, edge, keep_greater)
    if len(clipped) < 3:
        return []
    # Translate before the shoelace sum to reduce cancellation. There is no
    # visibility threshold: every strictly positive geometric area is legal.
    x0, y0 = clipped[0]
    twice_area = math.fsum((a[0] - x0) * (b[1] - y0) - (b[0] - x0) * (a[1] - y0)
                          for a, b in zip(clipped, clipped[1:] + clipped[:1]))
    return clipped if abs(twice_area) > 0 else []


def polygon_bounds(polygon: Sequence[Sequence[float]]) -> list[float]:
    """Bound a nonempty polygon after its visibility has been established."""
    return [min(point[0] for point in polygon), min(point[1] for point in polygon),
            max(point[0] for point in polygon), max(point[1] for point in polygon)]
