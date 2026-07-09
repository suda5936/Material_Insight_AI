import pytest

from app.services.llm.json_repair import LLMJsonParseError, parse_llm_json


def test_parse_plain_json() -> None:
    assert parse_llm_json('{"a": 1}') == {"a": 1}


def test_parse_json_with_code_fence() -> None:
    text = '```json\n{"a": 1}\n```'
    assert parse_llm_json(text) == {"a": 1}


def test_parse_json_with_plain_code_fence() -> None:
    text = '```\n{"a": 1}\n```'
    assert parse_llm_json(text) == {"a": 1}


def test_parse_json_with_surrounding_text() -> None:
    text = 'Here is the result:\n{"a": 1, "b": [1, 2]}\nThanks.'
    assert parse_llm_json(text) == {"a": 1, "b": [1, 2]}


def test_parse_nested_braces_in_string_values() -> None:
    text = '{"note": "value with { brace }", "n": 2}'
    assert parse_llm_json(text) == {"note": "value with { brace }", "n": 2}


def test_parse_unparsable_raises() -> None:
    with pytest.raises(LLMJsonParseError):
        parse_llm_json("not json at all")
