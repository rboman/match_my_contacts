from __future__ import annotations

from match_my_contacts_gui.app import _detect_qt_startup_issue


def test_detect_qt_startup_issue_for_missing_xcb_cursor(monkeypatch: object) -> None:
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setattr("match_my_contacts_gui.app.sys.platform", "linux")
    monkeypatch.setattr("match_my_contacts_gui.app.ctypes.util.find_library", lambda name: None)

    message = _detect_qt_startup_issue()

    assert message is not None
    assert "libxcb-cursor0" in message


def test_detect_qt_startup_issue_skips_when_platform_is_explicit(monkeypatch: object) -> None:
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("match_my_contacts_gui.app.sys.platform", "linux")

    message = _detect_qt_startup_issue()

    assert message is None
