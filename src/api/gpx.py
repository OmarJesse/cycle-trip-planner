from __future__ import annotations

import re
from xml.sax.saxutils import escape

from src.tools.get_route import GetRouteOutput


GPX_MEDIA_TYPE = "application/gpx+xml"
GPX_CREATOR = "Cycling Trip Planner Agent"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def route_to_gpx(route: GetRouteOutput, *, creator: str = GPX_CREATOR) -> str:
    title = f"{route.origin} → {route.destination}"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<gpx version="1.1" creator="{escape(creator)}" xmlns="http://www.topografix.com/GPX/1/1">',
        "  <metadata>",
        f"    <name>{escape(title)}</name>",
        "  </metadata>",
        "  <rte>",
        f"    <name>{escape(title)}</name>",
    ]
    for wp in route.waypoints:
        lines.append(f'    <rtept lat="{wp.lat:.6f}" lon="{wp.lon:.6f}">')
        lines.append(f"      <name>{escape(wp.name)}</name>")
        lines.append("    </rtept>")
    lines.append("  </rte>")
    lines.append("</gpx>")
    return "\n".join(lines) + "\n"


def gpx_filename(route: GetRouteOutput) -> str:
    return f"{_slugify(route.origin)}-to-{_slugify(route.destination)}.gpx"


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.lower()).strip("-")
    return slug or "route"
