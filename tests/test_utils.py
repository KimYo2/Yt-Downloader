"""Unit tests for app/utils.py utility functions."""

import pytest

from app.utils import (
    apply_cookie_settings,
    has_cookie_opts,
    human_bytes,
    is_cookie_copy_error,
    is_youtube_bot_check_error,
    strip_cookie_settings,
)


# ---------------------------------------------------------------------------
# human_bytes
# ---------------------------------------------------------------------------

def test_human_bytes_bytes():
    assert "512.0 B" in human_bytes(512)


def test_human_bytes_kilobytes():
    assert "2.0 KB" in human_bytes(2048)


def test_human_bytes_megabytes():
    assert "1.4 MB" in human_bytes(1_500_000)


def test_human_bytes_gigabytes():
    assert "1.9 GB" in human_bytes(2_000_000_000)


# ---------------------------------------------------------------------------
# is_cookie_copy_error
# ---------------------------------------------------------------------------

def test_is_cookie_copy_error_true():
    assert is_cookie_copy_error(Exception("could not copy chrome cookie database")) is True


def test_is_cookie_copy_error_false():
    assert is_cookie_copy_error(Exception("network timeout")) is False


def test_is_cookie_copy_error_dpapi():
    assert is_cookie_copy_error(Exception("failed to decrypt with dpapi")) is True


# ---------------------------------------------------------------------------
# is_youtube_bot_check_error
# ---------------------------------------------------------------------------

def test_is_youtube_bot_check_true():
    assert is_youtube_bot_check_error(Exception("sign in to confirm you're not a bot")) is True


def test_is_youtube_bot_check_false():
    assert is_youtube_bot_check_error(Exception("video unavailable")) is False


# ---------------------------------------------------------------------------
# has_cookie_opts
# ---------------------------------------------------------------------------

def test_has_cookie_opts_with_cookiefile():
    assert has_cookie_opts({"cookiefile": "/path/cookies.txt"}) is True


def test_has_cookie_opts_with_browser():
    assert has_cookie_opts({"cookiesfrombrowser": ("chrome",)}) is True


def test_has_cookie_opts_empty():
    assert has_cookie_opts({}) is False


# ---------------------------------------------------------------------------
# strip_cookie_settings
# ---------------------------------------------------------------------------

def test_strip_cookie_settings_removes_both():
    opts = {"cookiefile": "x", "cookiesfrombrowser": ("chrome",), "quiet": True}
    strip_cookie_settings(opts)
    assert "cookiefile" not in opts
    assert "cookiesfrombrowser" not in opts
    assert opts == {"quiet": True}


# ---------------------------------------------------------------------------
# apply_cookie_settings
# ---------------------------------------------------------------------------

def test_apply_cookie_settings_with_browser():
    opts: dict = {}
    apply_cookie_settings(opts, {"cookies_from_browser": "chrome", "cookies_file": ""})
    assert opts.get("cookiesfrombrowser") == ("chrome",)


def test_apply_cookie_settings_with_none_browser():
    opts: dict = {}
    apply_cookie_settings(opts, {"cookies_from_browser": "none", "cookies_file": ""})
    assert "cookiesfrombrowser" not in opts
