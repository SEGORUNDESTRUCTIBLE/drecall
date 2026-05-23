"""Utilities to sanitize and extract JSON from provider outputs.

This module focuses on non-destructive cleaning: removing markdown fences,
stripping leading/trailing prose, and extracting the first balanced JSON
object/array for deterministic parsing attempts.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

FENCE_RE = re.compile(r"```(?:[\s\S]*?)```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _strip_fences(text: str) -> str:
    """Remove triple-backtick fences and common fenced blocks."""
    if not text:
        return text
    return FENCE_RE.sub(lambda m: m.group(0).replace("```", ""), text)


def _strip_inline_code(text: str) -> str:
    """Remove inline backticks while preserving inner content."""
    return INLINE_CODE_RE.sub(lambda m: m.group(1), text)


def _find_first_json_by_braces(text: str) -> Optional[str]:
    """Find the first balanced JSON object/array by scanning braces.

    This attempts to locate a starting '[' or '{' then find its matching
    closing bracket while respecting string quoting.
    """
    if not text:
        return None

    start = None
    for i, ch in enumerate(text):
        if ch in "[{":
            start = i
            break
    if start is None:
        return None

    open_ch = text[start]
    close_ch = "]" if open_ch == "[" else "}"

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                # return the slice including start..i
                return text[start : i + 1]
    return None


def extract_first_json(text: str) -> Optional[str]:
    """Try multiple strategies to extract the first JSON candidate string.

    Returns the JSON substring if found, otherwise None.
    """
    if not text:
        return None

    # Quick heuristic: remove common fences, inline code backticks
    cleaned = _strip_fences(text)
    cleaned = _strip_inline_code(cleaned)

    # Try to find a balanced JSON by braces
    candidate = _find_first_json_by_braces(cleaned)
    if candidate:
        return candidate.strip()

    # Fallback: look for the first {...} or [...] via regex (less precise)
    regex = re.compile(r"(\{[\s\S]*?\}|\[[\s\S]*?\])", re.MULTILINE)
    for match in regex.finditer(cleaned):
        cand = match.group(1).strip()
        # quick validation: try load
        try:
            json.loads(cand)
            return cand
        except Exception:
            continue

    return None


def sanitize_and_parse(text: str) -> Tuple[Optional[object], Optional[str]]:
    """Sanitize provider output and attempt to parse into JSON.

    Returns a tuple of (parsed_object or None, sanitized_string or None).
    The sanitized_string is the JSON substring that was parsed (or None).
    """
    if not isinstance(text, str):
        return None, None

    preview = text[:400].replace('\n', ' ') if text else ''
    logger.debug("[json_sanitizer] raw preview=%s", preview)

    # 1) Try direct parse
    try:
        parsed = json.loads(text)
        return parsed, json.dumps(parsed)
    except Exception as exc:
        logger.debug("[json_sanitizer] direct json.loads failed: %s", exc)

    # 2) Strip fences and inline code then extract first balanced JSON
    candidate = extract_first_json(text)
    if candidate:
        try:
            parsed = json.loads(candidate)
            logger.debug("[json_sanitizer] extracted candidate success")
            return parsed, candidate
        except Exception as exc:
            logger.debug("[json_sanitizer] extracted candidate parse failed: %s", exc)

    # 3) As a last resort, attempt to coerce simple key: value lines into dict
    # but only if output appears to be a short structured listing.
    lines = [l.strip() for l in text.splitlines() if ":" in l and len(l.split(":", 1)) == 2]
    if lines and len(lines) <= 20:
        out = {}
        for l in lines:
            k, v = l.split(":", 1)
            out[k.strip()] = v.strip()
        try:
            logger.debug("[json_sanitizer] coerced key:value lines into dict")
            return out, json.dumps(out)
        except Exception:
            logger.debug("[json_sanitizer] coercion to dict failed")

    return None, None