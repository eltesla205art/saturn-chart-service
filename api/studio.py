"""
Chart Studio API — POST /api/studio

Body: see saturnstudio/web.py, plus
  "include": ["svg", "data", "report", "context", "reading"]   (default: svg, data)

Response: {"kind", "score", "source", "svg"?, "data"?, "report"?, "context"?, "reading"?}
"reading" is the built-in plain-language interpretation (no AI) with tarot correspondences.

Privacy: data is used in memory for one request; nothing is stored or logged.
License: AGPL-3.0. Source: SOURCE_URL.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")

from saturnstudio.web import KINDS, SOURCE_URL, JSONHandler, chart_from  # noqa: E402

INCLUDES = {"svg", "data", "report", "context", "reading"}


def build(body: dict) -> dict:
    _, result = chart_from(body)
    include = set(body.get("include") or ["svg", "data"]) & INCLUDES
    out: dict = {"kind": result.kind, "score": result.score, "source": SOURCE_URL}
    if "svg" in include:
        out["svg"] = result.svg
    if "data" in include:
        out["data"] = result.data
    if "report" in include:
        out["report"] = result.report()
    if "context" in include:
        out["context"] = result.context()
    if "reading" in include:
        out["reading"] = result.interpret()
    return out


class handler(JSONHandler):
    def info(self) -> dict:
        return {
            "service": "Where Is Saturn? Chart Studio API",
            "kinds": sorted(KINDS),
            "includes": sorted(INCLUDES),
            "built_on": "https://github.com/g-battaglia/kerykeion",
        }

    def handle_body(self, body: dict) -> dict:
        return build(body)
