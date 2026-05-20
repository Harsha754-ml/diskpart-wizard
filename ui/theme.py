# ui/theme.py - Design system tokens and CTk theme setup
# All colors, fonts, and spacing defined here.
# Import from here everywhere. Never hardcode colors elsewhere.

import json
import os
import tempfile
import ctypes
from typing import Optional
import tkinter.font as tkfont

import customtkinter as ctk

COLORS = {
    "bg_primary": "#0D0D0D",  # near-black canvas
    "bg_secondary": "#141414",  # card/panel bg
    "bg_tertiary": "#1C1C1C",  # input/hover bg
    "border": "#2A2A2A",  # subtle separators
    "accent": "#00E5FF",  # electric cyan - single accent color
    "accent_dim": "#007A8A",  # muted accent for secondary states
    "danger": "#FF3B3B",  # destructive actions only
    "warning": "#FFB300",  # warnings
    "success": "#00C853",  # success states
    "text_primary": "#F0F0F0",  # main text
    "text_secondary": "#8A8A8A",  # labels, metadata
    "text_muted": "#444444",  # disabled, placeholders
}

_JETBRAINS_FAMILY = "JetBrains Mono"
_jetbrains_loaded: Optional[bool] = None
_theme_path: Optional[str] = None


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _register_font(font_path: str) -> bool:
    if not os.path.exists(font_path):
        return False
    try:
        added = ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
        return added > 0
    except Exception:
        return False


def _load_jetbrains_fonts() -> bool:
    global _jetbrains_loaded
    if _jetbrains_loaded is not None:
        return _jetbrains_loaded

    fonts_dir = os.path.join(_project_root(), "assets", "fonts")
    regular = os.path.join(fonts_dir, "JetBrainsMono-Regular.ttf")
    bold = os.path.join(fonts_dir, "JetBrainsMono-Bold.ttf")

    loaded = _register_font(regular) or _register_font(bold)
    try:
        if _JETBRAINS_FAMILY in tkfont.families():
            loaded = True
    except Exception:
        pass

    _jetbrains_loaded = loaded
    return loaded


def FONT(size: int = 12, weight: str = "normal") -> tuple:
    """Returns font tuple for CTk widgets. Falls back to Courier if JetBrains not loaded."""
    family = _JETBRAINS_FAMILY if _jetbrains_loaded else "Courier New"
    return (family, size, weight)


def _build_theme_json() -> dict:
    return {
        "CTk": {
            "fg_color": [COLORS["bg_primary"], COLORS["bg_primary"]],
        },
        "CTkFrame": {
            "fg_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "border_width": 1,
        },
        "CTkLabel": {
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
        },
        "CTkButton": {
            "fg_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "hover_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "text_color_disabled": [COLORS["text_muted"], COLORS["text_muted"]],
        },
        "CTkEntry": {
            "fg_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "placeholder_text_color": [COLORS["text_muted"], COLORS["text_muted"]],
        },
        "CTkTextbox": {
            "fg_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "scrollbar_button_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "scrollbar_button_hover_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
        },
        "CTkProgressBar": {
            "fg_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "progress_color": [COLORS["accent"], COLORS["accent"]],
            "border_color": [COLORS["border"], COLORS["border"]],
        },
        "CTkOptionMenu": {
            "fg_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "button_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "button_hover_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "dropdown_fg_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "dropdown_hover_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
        },
        "CTkCheckBox": {
            "fg_color": [COLORS["accent"], COLORS["accent"]],
            "hover_color": [COLORS["accent_dim"], COLORS["accent_dim"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "checkmark_color": [COLORS["bg_primary"], COLORS["bg_primary"]],
        },
        "CTkSwitch": {
            "progress_color": [COLORS["accent"], COLORS["accent"]],
            "button_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "button_hover_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
        },
        "CTkScrollbar": {
            "fg_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "button_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "button_hover_color": [COLORS["border"], COLORS["border"]],
        },
        "CTkSlider": {
            "progress_color": [COLORS["accent"], COLORS["accent"]],
            "button_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "button_hover_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
        },
        "CTkComboBox": {
            "fg_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
            "border_color": [COLORS["border"], COLORS["border"]],
            "text_color": [COLORS["text_primary"], COLORS["text_primary"]],
            "dropdown_fg_color": [COLORS["bg_secondary"], COLORS["bg_secondary"]],
            "dropdown_hover_color": [COLORS["bg_tertiary"], COLORS["bg_tertiary"]],
        },
    }


def apply_theme():
    global _theme_path
    _load_jetbrains_fonts()
    ctk.set_appearance_mode("dark")

    if _theme_path is None:
        theme = _build_theme_json()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as theme_file:
            json.dump(theme, theme_file)
            _theme_path = theme_file.name

    ctk.set_default_color_theme(_theme_path)
    # Align CTk global background with our primary background color.
    ctk.ThemeManager.theme["CTk"]["fg_color"] = [
        COLORS["bg_primary"],
        COLORS["bg_primary"],
    ]
