import os
import pytest

from web.backend.vendor_quote_parser_lynn import parse_money

@pytest.mark.parametrize(
    "text,expected",
    [
        ("$12,345.67", 12345.67),
        ("USD 12,345.67", 12345.67),
        ("12.345,67", 12345.67),          # EU style
        ("1234567", 1234567.00),          # plain digits => integer dollars
        ("12.5k", 12500.00),              # K suffix
        ("1.2m", 1200000.00),             # M suffix
        ("(1,234.00)", -1234.00),         # parentheses negative
        ("  $  99.9  ", 99.90),
        ("$0.00", 0.0),
    ],
)
def test_parse_money_happy_paths(text, expected):
    val, reason = parse_money(text, cfg={})
    assert reason is None, f"unexpected drop reason={reason} for {text!r}"
    assert pytest.approx(val, rel=1e-6) == expected


def test_parse_money_caps_default():
    # Default cap is 10,000,000; values above should be dropped with 'gt-max-*'
    val, reason = parse_money("20000000", cfg={})
    assert val is None
    assert reason is not None and str(reason).startswith("gt-max"), f"reason={reason}"


def test_parse_money_caps_from_env(monkeypatch):
    # Override via env VENDOR_MAX_LINE is applied in model loader, but parser
    # uses vendor_map parsing config; still ensure large number under cap = ok if cap raised
    # Simulate by passing cfg with parsing.max_line_amount
    val, reason = parse_money("15000000", cfg={"parsing": {"max_line_amount": 20_000_000}})  # 15M under 20M cap
    assert reason is None
    assert val == 15000000.0


@pytest.mark.parametrize(
    "garbage",
    [
        "",
        "not a number",
        "USD",
        "amount due: n/a",
        ".,,",
    ],
)
def test_parse_money_no_match(garbage):
    val, reason = parse_money(garbage, cfg={})
    assert val is None
    assert reason in ("empty", "no-match", "parse-failed")
