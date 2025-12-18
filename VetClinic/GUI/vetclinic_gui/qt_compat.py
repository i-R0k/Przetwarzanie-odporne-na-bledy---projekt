from __future__ import annotations

"""
Small compatibility layer to ease the transition from PyQt5 to PyQt6.

It exposes the PyQt6 QtCore/QtGui/QtWidgets/QtCharts modules and adds the
most common PyQt5 enum attribute names onto Qt so existing code using
Qt.AlignCenter, Qt.PointingHandCursor etc. keeps working.
"""

from PyQt6 import QtCore, QtGui, QtWidgets

try:
    # QtCharts is optional; import lazily to avoid hard failure when absent.
    from PyQt6 import QtCharts  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    QtCharts = None  # type: ignore

Qt = QtCore.Qt


def _patch_enum_aliases() -> None:
    alias_map = {
        # Alignment flags
        "AlignCenter": Qt.AlignmentFlag.AlignCenter,
        "AlignLeft": Qt.AlignmentFlag.AlignLeft,
        "AlignRight": Qt.AlignmentFlag.AlignRight,
        "AlignTop": Qt.AlignmentFlag.AlignTop,
        "AlignBottom": Qt.AlignmentFlag.AlignBottom,
        "AlignHCenter": Qt.AlignmentFlag.AlignHCenter,
        "AlignVCenter": Qt.AlignmentFlag.AlignVCenter,
        "AlignJustify": Qt.AlignmentFlag.AlignJustify,
        # Cursor shapes
        "PointingHandCursor": Qt.CursorShape.PointingHandCursor,
        "ArrowCursor": Qt.CursorShape.ArrowCursor,
        "OpenHandCursor": Qt.CursorShape.OpenHandCursor,
        "ClosedHandCursor": Qt.CursorShape.ClosedHandCursor,
        "WaitCursor": Qt.CursorShape.WaitCursor,
        # Orientation / focus
        "Horizontal": Qt.Orientation.Horizontal,
        "Vertical": Qt.Orientation.Vertical,
        "NoFocus": Qt.FocusPolicy.NoFocus,
        # Brush / pen styles
        "NoBrush": Qt.BrushStyle.NoBrush,
        "NoPen": Qt.PenStyle.NoPen,
        "RoundCap": Qt.PenCapStyle.RoundCap,
        "RoundJoin": Qt.PenJoinStyle.RoundJoin,
        # Mouse buttons
        "LeftButton": Qt.MouseButton.LeftButton,
        "RightButton": Qt.MouseButton.RightButton,
        "MiddleButton": Qt.MouseButton.MiddleButton,
        # Item / match flags
        "ItemIsEditable": Qt.ItemFlag.ItemIsEditable,
        "ItemIsEnabled": Qt.ItemFlag.ItemIsEnabled,
        "ItemIsSelectable": Qt.ItemFlag.ItemIsSelectable,
        "ItemIsUserCheckable": Qt.ItemFlag.ItemIsUserCheckable,
        "ItemIsDragEnabled": Qt.ItemFlag.ItemIsDragEnabled,
        "ItemIsDropEnabled": Qt.ItemFlag.ItemIsDropEnabled,
        "MatchContains": Qt.MatchFlag.MatchContains,
        "MatchStartsWith": Qt.MatchFlag.MatchStartsWith,
        # Data roles
        "ForegroundRole": Qt.ItemDataRole.ForegroundRole,
        # Case sensitivity
        "CaseInsensitive": Qt.CaseSensitivity.CaseInsensitive,
        "CaseSensitive": Qt.CaseSensitivity.CaseSensitive,
        # Date / time formats
        "ISODate": Qt.DateFormat.ISODate,
        # Aspect / transform
        "KeepAspectRatio": Qt.AspectRatioMode.KeepAspectRatio,
        "SmoothTransformation": Qt.TransformationMode.SmoothTransformation,
        # Day of week
        "Monday": Qt.DayOfWeek.Monday,
        # Child search
        "FindChildrenRecursively": Qt.FindChildOption.FindChildrenRecursively,
        # Key codes
        "Key_Enter": Qt.Key.Key_Enter,
        "Key_Return": Qt.Key.Key_Return,
        # Colors
        "transparent": Qt.GlobalColor.transparent,
    }

    for name, value in alias_map.items():
        if not hasattr(Qt, name):
            try:
                setattr(Qt, name, value)
            except Exception:
                # Some enum classes are immutable; ignore failures silently.
                pass


_patch_enum_aliases()

__all__ = ["Qt", "QtCore", "QtGui", "QtWidgets", "QtCharts"]
