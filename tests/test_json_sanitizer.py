import json
from core.parsing.json_sanitizer import extract_first_json, sanitize_and_parse


def test_extract_fenced_json():
    text = "Here is the result:\n```json\n{\"title\": \"Hi\", \"content\": \"Body\"}\n```\nThanks"
    candidate = extract_first_json(text)
    assert candidate is not None
    parsed = json.loads(candidate)
    assert parsed["title"] == "Hi"


def test_sanitize_and_parse_malformed():
    text = "Response:\n{ title: 'Bad JSON', content: 'Oops' }"
    parsed, sanitized = sanitize_and_parse(text)
    assert parsed is not None
    assert isinstance(parsed, dict)
    assert parsed.get("title") == "Bad JSON"


def test_sanitize_coerce_lines():
    text = "title: Simple\ncontent: Short content\nsource: test"
    parsed, sanitized = sanitize_and_parse(text)
    assert parsed is not None
    assert parsed.get("title") == "Simple"


def test_partial_json_returns_none():
    text = "Some intro {\"incomplete\": true"
    parsed, sanitized = sanitize_and_parse(text)
    assert parsed is None
    assert sanitized is None
