"""
AI deep reading — POST /api/interpret

Same body as /api/studio (kind, first, second, transit, year, month, options). The chart is
recomputed here, and only anonymized positions, houses and aspects are sent to Claude
(no names, birth dates, times, places or coordinates). The reply is Markdown.

GET returns {"enabled": bool} so the site can show or hide the button.

Needs ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) in the environment.
Prompt design adapted from Asteria by Alamahant (AGPL-3.0).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")

from saturnstudio.ai import DEFAULT_MODEL, AIError, build_prompt, call_claude  # noqa: E402
from saturnstudio.web import HTTPError, JSONHandler, chart_from  # noqa: E402


def enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def interpret(body: dict, caller=call_claude) -> dict:
    if not enabled() and caller is call_claude:
        raise HTTPError(503, "AI readings are not switched on yet.")
    studio, result = chart_from(body)
    system, user = build_prompt(result.data, studio.language)
    try:
        out = caller(system, user)
    except AIError as e:
        raise HTTPError(502, str(e)) from None
    return {"kind": result.kind, "markdown": out["markdown"], "model": out.get("model"),
            "truncated": out.get("stop_reason") == "max_tokens"}


class handler(JSONHandler):
    require_origin = True

    def info(self) -> dict:
        return {"service": "Where Is Saturn? AI chart reading", "enabled": enabled(),
                "model": os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL, "provider": "Anthropic Claude"}

    def handle_body(self, body: dict) -> dict:
        return interpret(body)
