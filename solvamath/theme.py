"""Color palettes shared by the app and page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    key: str
    label: str
    bg: str
    panel: str
    panel2: str
    text: str
    muted: str
    accent: str
    accent2: str
    gold: str
    success: str
    error: str


THEMES = {
    "greenit": Palette(
        "greenit", "Greenit", "#0C1F17", "#122A1F", "#193B2C",
        "#DEF4E5", "#9CB8A3", "#7BD88F", "#63C9A8", "#E0CD97", "#7BD88F", "#F07178",
    ),
    "bluney": Palette(
        "bluney", "Bluney", "#0E1B2E", "#122A46", "#193754",
        "#E3EFF9", "#9DB8D2", "#7DBBFF", "#8BD5FF", "#E0CD97", "#7DBBFF", "#F07178",
    ),
    "yellen": Palette(
        "yellen", "Yellen", "#171408", "#24200C", "#332B10",
        "#F3E8B8", "#A79765", "#F2D14E", "#E6C15A", "#E0CD97", "#A9B85A", "#C76A52",
    ),
    "nord": Palette(
        "nord", "Nord", "#2E3440", "#3B4252", "#434C5E",
        "#ECEFF4", "#9AA7B8", "#88C0D0", "#81A1C1", "#EBCB8B", "#A3BE8C", "#BF616A",
    ),
    "dracula": Palette(
        "dracula", "Dracula", "#282A36", "#343746", "#44475A",
        "#F8F8F2", "#A6ACCD", "#BD93F9", "#8BE9FD", "#F1FA8C", "#50FA7B", "#FF5555",
    ),
    "gruvbox": Palette(
        "gruvbox", "Gruvbox", "#282828", "#3C3836", "#504945",
        "#EBDBB2", "#A89984", "#FE8019", "#8EC07C", "#FABD2F", "#B8BB26", "#FB4934",
    ),
    "catppuccin": Palette(
        "catppuccin", "Catppuccin", "#1E1E2E", "#313244", "#45475A",
        "#CDD6F4", "#A6ADC8", "#CBA6F7", "#89B4FA", "#F9E2AF", "#A6E3A1", "#F38BA8",
    ),
    "tokyonight": Palette(
        "tokyonight", "Tokyo Night", "#1A1B26", "#292E42", "#3B4261",
        "#C0CAF5", "#A9B1D6", "#7AA2F7", "#BB9AF7", "#E0AF68", "#9ECE6A", "#F7768E",
    ),
    "mono": Palette(
        "mono", "Mono", "#0B0B0B", "#161616", "#222222",
        "#F0F0F0", "#999999", "#DDDDDD", "#FFFFFF", "#DDDDDD", "#EEEEEE", "#FF6B6B",
    ),
}
THEME_ORDER = ("greenit", "bluney", "yellen", "nord", "dracula", "gruvbox", "catppuccin", "tokyonight", "mono")


def get_palette(name: str) -> Palette:
    return THEMES.get(name, THEMES["greenit"])


def next_theme(name: str) -> str:
    try:
        index = THEME_ORDER.index(name)
    except ValueError:
        index = 0
    return THEME_ORDER[(index + 1) % len(THEME_ORDER)]
