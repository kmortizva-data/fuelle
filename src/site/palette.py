"""The course palette, computed rather than picked by eye.

Every module gets an accent. Picking 35 hex codes by hand gives an arc that
drifts: some steps too bright, some pairs indistinguishable, some failing
contrast on one of the two themes.

So the arc is generated in OKLCH, where lightness and chroma mean what they say,
and every colour is then measured for WCAG contrast against BOTH backgrounds
before it is allowed into temario.json.

The brief for this course is "looks like an engineer, not loud", so chroma is
held deliberately low: these are instrument colours, not neon.

Run:  .venv\\Scripts\\python.exe src\\site\\palette.py
Writes: results/palette.json
"""

from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT / "results" / "palette.json"

# The two grounds the course runs on.
BG_DARK = "#14181B"   # graphite, not pure black: pure black buzzes on OLED
BG_LIGHT = "#F7F5F1"  # paper, so the light theme is not an afterthought

# The two fixed colours of the whole course: what was measured, what was simulated.
#
# These two appear together on the same chart, so picking them by hue alone is a
# trap: the first attempt (#8FA9B4 against #C08A4E) measured 1.22 between them,
# which means anyone colour blind, or looking at a print, sees one line.
# So they are defined in OKLCH and pulled APART IN LIGHTNESS, per theme, and the
# separation is measured below. Colour is still never the only cue: the twin is
# always drawn dashed and the sensor solid. See SHAPE_RULE.
MEASURED_HUE, MEASURED_CHROMA = 232.0, 0.030    # cool grey blue, the sensor
SIMULATED_HUE, SIMULATED_CHROMA = 58.0, 0.105   # muted amber, the model

# Lightness per theme: on graphite the sensor is the bright one; on paper the
# order flips, because on paper "darker" is what reads as foreground.
MEASURED_L = {"dark": 0.90, "light": 0.42}
SIMULATED_L = {"dark": 0.68, "light": 0.62}

MIN_SERIES_SEPARATION = 1.8   # between the two lines, within one theme
MIN_GRAPHIC_CONTRAST = 3.0    # WCAG AA for non-text (lines, marks) vs background
SHAPE_RULE = "measured = solid line; simulated = dashed. Colour is never the only cue."

# The arc: cool instrument cyan at the raw data, warm terracotta at the leak.
# Hue in OKLCH degrees. Chroma stays low on purpose.
HUE_START, HUE_END = 205.0, 40.0
CHROMA_MIN, CHROMA_MAX = 0.055, 0.085
LIGHTNESS_DARK = 0.78   # accents sit on graphite, so they must be light
MIN_CONTRAST = 4.5      # WCAG AA for normal text


def _srgb_gamma(x: float) -> float:
    return 1.055 * (x ** (1 / 2.4)) - 0.055 if x > 0.0031308 else 12.92 * x


def _srgb_linear(x: float) -> float:
    return ((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92


def oklch_to_hex(lightness: float, chroma: float, hue_deg: float) -> str:
    """OKLCH to sRGB hex, clamped. Ottosson's matrices."""
    hue = math.radians(hue_deg)
    a, b = chroma * math.cos(hue), chroma * math.sin(hue)

    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3

    rgb = (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )
    out = []
    for channel in rgb:
        value = _srgb_gamma(max(0.0, min(1.0, channel)))
        out.append(round(max(0.0, min(1.0, value)) * 255))
    return "#{:02X}{:02X}{:02X}".format(*out)


def relative_luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (
        0.2126 * _srgb_linear(r)
        + 0.7152 * _srgb_linear(g)
        + 0.0722 * _srgb_linear(b)
    )


def contrast(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def darken_for_light_theme(lightness: float, chroma: float, hue: float) -> str:
    """The same hue, dropped in lightness until it clears AA on paper."""
    step = lightness
    while step > 0.20:
        candidate = oklch_to_hex(step, chroma, hue)
        if contrast(candidate, BG_LIGHT) >= MIN_CONTRAST:
            return candidate
        step -= 0.01
    return oklch_to_hex(0.20, chroma, hue)


def build_arc(n_modules: int) -> list[dict]:
    """One accent per module, walking the hue arc, measured on both themes."""
    accents = []
    for i in range(n_modules):
        t = i / (n_modules - 1) if n_modules > 1 else 0.0
        hue = HUE_START + (HUE_END - HUE_START) * t
        # Chroma swells in the middle so the ends stay quiet.
        chroma = CHROMA_MIN + (CHROMA_MAX - CHROMA_MIN) * math.sin(math.pi * t)

        on_dark = oklch_to_hex(LIGHTNESS_DARK, chroma, hue)
        on_light = darken_for_light_theme(0.62, chroma, hue)

        accents.append({
            "module": i + 1,
            "dark": on_dark,
            "light": on_light,
            "hue": round(hue, 1),
            "chroma": round(chroma, 4),
            "contrast_dark": round(contrast(on_dark, BG_DARK), 2),
            "contrast_light": round(contrast(on_light, BG_LIGHT), 2),
        })
    return accents


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    accents = build_arc(n)

    failures = [
        a for a in accents
        if a["contrast_dark"] < MIN_CONTRAST or a["contrast_light"] < MIN_CONTRAST
    ]

    series = {}
    for theme, bg in (("dark", BG_DARK), ("light", BG_LIGHT)):
        measured = oklch_to_hex(MEASURED_L[theme], MEASURED_CHROMA, MEASURED_HUE)
        simulated = oklch_to_hex(SIMULATED_L[theme], SIMULATED_CHROMA, SIMULATED_HUE)
        series[theme] = {
            "measured": measured,
            "simulated": simulated,
            "measured_vs_bg": round(contrast(measured, bg), 2),
            "simulated_vs_bg": round(contrast(simulated, bg), 2),
            "separation": round(contrast(measured, simulated), 2),
        }

    fixed = {
        "bg_dark": BG_DARK,
        "bg_light": BG_LIGHT,
        "series": series,
        "shape_rule": SHAPE_RULE,
    }

    series_failures = []
    for theme, s in series.items():
        if s["measured_vs_bg"] < MIN_GRAPHIC_CONTRAST:
            series_failures.append(f"{theme}: measured vs background {s['measured_vs_bg']}")
        if s["simulated_vs_bg"] < MIN_GRAPHIC_CONTRAST:
            series_failures.append(f"{theme}: simulated vs background {s['simulated_vs_bg']}")
        if s["separation"] < MIN_SERIES_SEPARATION:
            series_failures.append(f"{theme}: the two lines only {s['separation']} apart")

    RESULTS.parent.mkdir(exist_ok=True)
    with io.open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(
            {"fixed": fixed, "accents": accents, "min_contrast": MIN_CONTRAST},
            fh, ensure_ascii=False, indent=2,
        )

    print(f"{n} accents, contrast measured on both themes (AA needs {MIN_CONTRAST})")
    print()
    print("  mod   dark      on bg   light     on bg")
    for a in accents:
        print(
            f"  {a['module']:>3}   {a['dark']}   {a['contrast_dark']:>5.2f}"
            f"   {a['light']}   {a['contrast_light']:>5.2f}"
        )
    print()
    print("  The two series colours, per theme:")
    for theme, s in series.items():
        print(
            f"    {theme:<6} measured {s['measured']} ({s['measured_vs_bg']} vs bg)"
            f"   simulated {s['simulated']} ({s['simulated_vs_bg']} vs bg)"
            f"   apart: {s['separation']}"
        )
    print(f"  Shape rule: {SHAPE_RULE}")
    print()

    if failures:
        print(f"FAIL: {len(failures)} accents below AA -> {[f['module'] for f in failures]}")
    for problem in series_failures:
        print(f"FAIL: {problem}")
    if failures or series_failures:
        raise SystemExit(1)

    print("All accents clear AA on both themes.")
    print(f"Both series colours clear {MIN_GRAPHIC_CONTRAST} vs background "
          f"and {MIN_SERIES_SEPARATION} between each other, in both themes.")
    print(f"Written to {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
