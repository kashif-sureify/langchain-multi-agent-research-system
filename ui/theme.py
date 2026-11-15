"""
Light, dark and system themes for the Researchers UI.

Streamlit has no API for switching themes from inside an app, so the theme is applied with
CSS variables: each palette below becomes a set of variables on :root, and one stylesheet styles
Streamlit's native widgets (through their data-testid attributes) and our own HTML with them.
"System" emits both palettes and lets the browser's prefers-color-scheme setting pick one.
"""

from ui.icons import icon_css, mask_url

THEME_LABELS = {
    "light": ":material/light_mode: Light",
    "dark": ":material/dark_mode: Dark",
    "system": ":material/desktop_windows: System",
}

LIGHT = {
    "color-scheme": "light",
    "bg-canvas": "#EDE6D9",
    "bg-sidebar": "#E3D9C7",
    "surface-card": "#F7F2E9",
    "surface-sunken": "#EEE6D8",  # text areas, chips, topic cards
    "surface-raised": "#E8DFCF",  # toggle track, "Waiting" pill, progress track
    "border-subtle": "#D8CCB7",
    "border-strong": "#BCAC91",  # text area and secondary button borders
    "text-primary": "#1F1B16",
    "text-secondary": "#5E5447",
    "text-muted": "#8B7F6D",
    "brand-primary": "#0E5E5A",  # primary button, selected chip, links
    "brand-on-primary": "#F7F2E9",
    "brand-soft": "#D2E2DA",  # selected chip background, agent icon tile
    "accent": "#B9502C",  # eyebrow and feature pill icons
    "accent-soft": "#F0D8C8",
    "status-running": "#9A6512",
    "status-running-soft": "#F1DFBC",
    "status-done": "#2F6B3F",
    "status-done-soft": "#D4E4D0",
    "status-failed": "#A3372A",
    "status-failed-soft": "#F2D3CC",
    "shadow-card": "0 1px 2px rgba(31,27,22,0.04), 0 10px 28px rgba(31,27,22,0.06)",
    "shadow-segment": "0 1px 2px rgba(31,27,22,0.14)",
}

DARK = {
    "color-scheme": "dark",
    "bg-canvas": "#121417",
    "bg-sidebar": "#171A1E",
    "surface-card": "#1D2126",
    "surface-sunken": "#15181C",
    "surface-raised": "#262B31",
    "border-subtle": "#2D333A",
    "border-strong": "#414952",
    "text-primary": "#EDE7DC",
    "text-secondary": "#B4AB9D",
    "text-muted": "#7E776C",
    "brand-primary": "#5CC2B2",
    "brand-on-primary": "#0D1918",
    "brand-soft": "#1C3936",
    "accent": "#E8845E",
    "accent-soft": "#3A2620",
    "status-running": "#E0B25A",
    "status-running-soft": "#3A3020",
    "status-done": "#80C290",
    "status-done-soft": "#1F3324",
    "status-failed": "#E5877A",
    "status-failed-soft": "#3B2220",
    "shadow-card": "0 1px 2px rgba(0,0,0,0.30), 0 10px 28px rgba(0,0,0,0.28)",
    "shadow-segment": "0 1px 2px rgba(0,0,0,0.5)",
}


def _variables(palette: dict) -> str:
    return "; ".join(f"--{name}: {value}" for name, value in palette.items())


def theme_css(mode: str) -> str:
    """Return a <style> block for "light", "dark" or "system"."""
    if mode == "light":
        root = ":root { " + _variables(LIGHT) + " }"
    elif mode == "dark":
        root = ":root { " + _variables(DARK) + " }"
    else:
        root = (
            ":root { " + _variables(LIGHT) + " }\n"
            "@media (prefers-color-scheme: dark) { :root { " + _variables(DARK) + " } }"
        )
    return f"<style>\n{FONT_IMPORT}\n{root}\n{STYLESHEET}\n</style>"


FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700"
    "&family=Fraunces:ital,opsz,wght@0,9..144,600;1,9..144,600"
    "&family=JetBrains+Mono:wght@500&display=swap');"
)

STYLESHEET = """
:root {
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SFMono-Regular', monospace;
}

/* ── Page and Streamlit chrome ────────────────────── */
html, body, [data-testid="stApp"] { color-scheme: var(--color-scheme); }
[data-testid="stApp"] { background: var(--bg-canvas); color: var(--text-primary); font-family: var(--font-body); }
[data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] :is(p, li, a, strong, em, td, th),
[data-testid="stApp"] button, [data-testid="stApp"] textarea, [data-testid="stApp"] input, [data-testid="stExpander"] summary {
  font-family: var(--font-body) !important;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"], [data-testid="stToolbarActions"], footer { display: none !important; }
[data-testid="stExpandSidebarButton"] { color: var(--text-secondary); }
[data-testid="stMainBlockContainer"] { max-width: 1138px; padding: 56px 64px 88px; }

/* ── Text ─────────────────────────────────────────── */
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] :is(p, li, strong, h1, h2, h3, h4),
[data-testid="stWidgetLabel"] p { color: var(--text-primary); }
[data-testid="stWidgetLabel"] p { font-size: 14px; font-weight: 600; }
/* Widget labels (buttons, chips, tabs) take their button's color instead of the default text color */
button [data-testid="stMarkdownContainer"], button [data-testid="stMarkdownContainer"] p { color: inherit !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; font-size: 13px; }
[data-testid="stMarkdownContainer"] a { color: var(--brand-primary); text-decoration: none; }
[data-testid="stMarkdownContainer"] a:hover { text-decoration: underline; }
[data-testid="stMarkdownContainer"] code { background: var(--surface-raised); color: var(--text-primary); border-radius: 6px; padding: 0.1em 0.35em; }
[data-testid="stMarkdownContainer"] hr, hr { border-color: var(--border-subtle) !important; }
[data-testid="stMarkdownContainer"] blockquote { border-left-color: var(--brand-primary); color: var(--text-secondary); }
.rs-mono { font-family: var(--font-mono); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; }
.rs-icon { flex-shrink: 0; }
.rs-spinner {
  width: 12px; height: 12px; border-radius: 50%; border: 2px solid currentColor; border-right-color: transparent;
  display: inline-block; flex-shrink: 0; animation: rs-rotate 0.8s linear infinite;
}
@keyframes rs-rotate { to { transform: rotate(360deg); } }

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] { background: var(--bg-sidebar); border-right: 1px solid var(--border-subtle); }
[data-testid="stSidebarCollapseButton"] button { color: var(--text-muted); }
[data-testid="stSidebarContent"] { display: flex; flex-direction: column; }
[data-testid="stSidebarUserContent"] { flex: 1; display: flex; flex-direction: column; padding: 4px 4px 24px; }
[data-testid="stSidebarUserContent"] > div { flex: 1; display: flex; flex-direction: column; }
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] { flex: 1; gap: 12px; }
/* Pin "Built by" to the bottom: Streamlit wraps the keyed container in a layout wrapper, which gets the auto margin */
[data-testid="stLayoutWrapper"]:has(> .st-key-side_footer) { margin-top: auto; padding-top: 14px; }
.rs-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.rs-brand-tile {
  width: 42px; height: 42px; border-radius: 12px; flex-shrink: 0; display: grid; place-items: center;
  background: var(--brand-primary); color: var(--brand-on-primary);
}
.rs-brand-name { font-family: var(--font-display); font-weight: 600; font-size: 20px; line-height: 1.2; color: var(--text-primary); }
.rs-brand-sub { font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }
.rs-side-label { color: var(--text-muted); margin: 14px 0 0; }
.rs-convo-empty {
  display: flex; gap: 10px; align-items: flex-start; padding: 14px; border: 1px dashed var(--border-strong);
  border-radius: 12px; color: var(--text-muted);
}
.rs-convo-empty .rs-icon { margin-top: 1px; }
.rs-convo-empty b { display: block; font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.rs-convo-empty div > span { display: block; font-size: 12.5px; line-height: 1.45; color: var(--text-secondary); margin-top: 2px; }
.rs-history { display: flex; flex-direction: column; gap: 8px; }
.rs-history-item {
  display: flex; gap: 10px; align-items: flex-start; padding: 10px 12px; background: var(--surface-card);
  border: 1px solid var(--border-subtle); border-radius: 12px;
}
.rs-history-num {
  width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0; display: grid; place-items: center;
  background: var(--brand-soft); color: var(--brand-primary); font: 600 11px var(--font-mono);
}
.rs-history-q {
  font-size: 13.5px; line-height: 19px; font-weight: 500; color: var(--text-primary);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.rs-history-meta { font-size: 10.5px; color: var(--text-muted); margin-top: 4px; letter-spacing: 0.06em; }
.rs-history-meta--running { color: var(--status-running); }
.rs-flow { display: flex; flex-direction: column; gap: 14px; }
.rs-flow-item { display: flex; gap: 12px; align-items: flex-start; }
.rs-flow-num {
  width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0; display: grid; place-items: center;
  border: 1px solid var(--border-strong); color: var(--text-secondary); font: 500 11px var(--font-mono);
}
.rs-flow-item:first-child .rs-flow-num { background: var(--brand-primary); border-color: var(--brand-primary); color: var(--brand-on-primary); }
.rs-flow-item b { display: block; font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.rs-flow-item div > span { display: block; font-size: 12.5px; line-height: 18px; color: var(--text-secondary); margin-top: 1px; }
.rs-side-footer { border-top: 1px solid var(--border-subtle); padding-top: 14px; font-size: 12.5px; color: var(--text-muted); }
.rs-side-footer b { font-weight: 600; color: var(--text-secondary); }

/* Theme switch: a segmented control on a raised track */
.st-key-theme_choice [role="radiogroup"] {
  display: flex; flex-wrap: nowrap; gap: 2px; padding: 3px; border-radius: 10px; background: var(--surface-raised);
}
.st-key-theme_choice button {
  flex: 1 1 auto !important; min-width: 0 !important; min-height: 32px; padding: 0 4px !important;
  background: transparent !important; border: none !important; border-radius: 8px !important;
  color: var(--text-secondary) !important; box-shadow: none !important;
}
.st-key-theme_choice button[aria-checked="true"] {
  background: var(--surface-card) !important; color: var(--text-primary) !important; box-shadow: var(--shadow-segment) !important;
}
.st-key-theme_choice button p { font-size: 12.5px !important; font-weight: 500; color: inherit !important; white-space: nowrap; }
.st-key-theme_choice button > div { gap: 4px !important; }
.st-key-theme_choice [data-testid="stIconMaterial"] { font-size: 15px !important; }

/* ── Buttons ──────────────────────────────────────── */
[data-testid^="stBaseButton-secondary"], [data-testid="stDownloadButton"] button[kind="secondary"] {
  background: var(--surface-card) !important; color: var(--text-primary) !important;
  border: 1px solid var(--border-strong) !important; border-radius: 12px; min-height: 42px; transition: border-color 0.15s, color 0.15s;
}
[data-testid^="stBaseButton-secondary"]:hover:not(:disabled), [data-testid="stDownloadButton"] button[kind="secondary"]:hover {
  border-color: var(--brand-primary) !important; color: var(--brand-primary) !important;
}
[data-testid^="stBaseButton-secondary"]:disabled { opacity: 0.5; }
[data-testid^="stBaseButton-secondary"] p, [data-testid="stDownloadButton"] button[kind="secondary"] p { color: inherit !important; font-weight: 600; font-size: 14px; }
[data-testid="stBaseButton-primary"] {
  background: var(--brand-primary) !important; color: var(--brand-on-primary) !important; border: none !important;
  border-radius: 12px; min-height: 46px; padding: 0 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.12);
  transition: transform 0.15s ease, filter 0.15s ease;
}
[data-testid="stBaseButton-primary"]:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(1.08); }
[data-testid="stBaseButton-primary"]:disabled { background: var(--brand-primary) !important; color: var(--brand-on-primary) !important; opacity: 0.6; }
[data-testid="stBaseButton-primary"] p { color: inherit !important; font-weight: 600; font-size: 15px; }
[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"], [data-testid="stBaseButton-primary"] [role="img"] { color: inherit !important; }
.st-key-start_row [data-testid="stBaseButton-primary"]:disabled [data-testid="stIconMaterial"] { animation: rs-rotate 1s linear infinite; }

/* "Shuffle ideas": a link-style button at the right of the sample topics header */
.st-key-more_ideas { width: 100% !important; display: flex; justify-content: flex-end; }
.st-key-more_ideas button { color: var(--brand-primary) !important; padding: 0 !important; min-height: 0 !important; }
.st-key-more_ideas button p { color: inherit !important; font-size: 13.5px; font-weight: 600; }
.st-key-more_ideas button:hover p { text-decoration: underline; }

/* ── Text area and text input ─────────────────────── */
[data-testid="stTextAreaRootElement"], [data-testid="stTextInputRootElement"] {
  background: var(--surface-sunken) !important; border: 1px solid var(--border-strong) !important; transition: border-color 0.15s, box-shadow 0.15s;
}
[data-testid="stTextAreaRootElement"] { border-radius: 14px !important; }
[data-testid="stTextInputRootElement"] { border-radius: 12px !important; }
[data-testid="stTextAreaRootElement"] > div, [data-testid="stTextInputRootElement"] > div { background: transparent !important; border: none !important; }
[data-testid="stTextAreaRootElement"]:focus-within, [data-testid="stTextInputRootElement"]:focus-within {
  border-color: var(--brand-primary) !important; box-shadow: 0 0 0 0.5px var(--brand-primary);
}
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
  background: transparent !important; color: var(--text-primary) !important; caret-color: var(--brand-primary);
  font-size: 15.5px; line-height: 1.55;
}
[data-testid="stTextArea"] textarea { padding: 14px 16px; }
[data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder { color: var(--text-muted); opacity: 1; }
[data-testid="InputInstructions"] { color: var(--text-muted); }

/* ── Query card ───────────────────────────────────── */
.st-key-input_card {
  background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: 20px;
  padding: 28px; box-shadow: var(--shadow-card); gap: 18px;
}
.st-key-input_card [data-testid="stTextArea"] [data-testid="stWidgetLabel"] p {
  font-family: var(--font-display) !important; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;
}
.st-key-input_card [data-testid="stTextArea"] [data-testid="stWidgetLabel"] { margin-bottom: 6px; }
.st-key-input_card [data-testid="InputInstructions"] { display: none; }
.rs-input-footer { display: flex; justify-content: space-between; gap: 12px; margin-top: -10px; font-size: 12.5px; color: var(--text-muted); }
.rs-input-footer .rs-mono { letter-spacing: 0.04em; white-space: nowrap; }
.rs-field-label { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-primary); }
.rs-accent-icon { color: var(--accent); }
.rs-help { font-size: 12.5px; color: var(--text-muted); margin-top: -8px; }
.st-key-topics_head [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; align-items: center; }
.st-key-topics_head [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-topics_head [data-testid="stColumn"]:last-child { flex: 0 0 auto !important; width: auto !important; }
.st-key-start_row { border-top: 1px solid var(--border-subtle); padding-top: 20px; margin-top: 4px; }
.st-key-start_row [data-testid="stHorizontalBlock"] { align-items: center; flex-wrap: wrap; gap: 16px; }
.rs-hint { display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: var(--text-muted); }

/* Category chips */
.st-key-category_pick [role="radiogroup"] { gap: 8px; flex-wrap: wrap; }
.st-key-category_pick button {
  background: var(--surface-sunken) !important; border: 1px solid var(--border-subtle) !important; border-radius: 999px !important;
  color: var(--text-secondary) !important; padding: 6px 14px !important; min-height: 34px; transition: all 0.15s ease;
}
.st-key-category_pick button:hover { border-color: var(--border-strong) !important; color: var(--text-primary) !important; }
.st-key-category_pick button[aria-checked="true"] {
  background: var(--brand-soft) !important; border-color: var(--brand-primary) !important; color: var(--brand-primary) !important;
}
.st-key-category_pick button p { color: inherit !important; font-size: 13.5px; font-weight: 500; }
.st-key-category_pick button > div { gap: 6px !important; }

/* Sample topics: a two-column grid of topic cards */
.st-key-sample_pick [role="radiogroup"] { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; width: 100%; }
.st-key-sample_pick button {
  width: 100%; min-height: 52px; padding: 12px 14px !important; border-radius: 12px !important; justify-content: flex-start !important;
  background: var(--surface-sunken) !important; border: 1px solid var(--border-subtle) !important; color: var(--text-primary) !important;
  text-align: left; transition: all 0.15s ease;
}
.st-key-sample_pick button > div { width: 100%; justify-content: flex-start !important; }
.st-key-sample_pick button p { color: inherit !important; font-size: 14.5px; line-height: 1.4; white-space: normal; text-align: left; }
.st-key-sample_pick button::after {
  content: ""; flex-shrink: 0; width: 16px; height: 16px; margin-left: 12px; background: var(--text-muted);
  -webkit-mask: ARROW_UP_RIGHT center / contain no-repeat; mask: ARROW_UP_RIGHT center / contain no-repeat;
}
.st-key-sample_pick button:hover { border-color: var(--brand-primary) !important; }
.st-key-sample_pick button:hover::after { background: var(--brand-primary); }
/* The topic now in the text box is highlighted by a rule app.py adds for its position (nth-of-type) */

/* "Others": your own category */
.st-key-custom_category_form [data-testid="stHorizontalBlock"] { gap: 10px; }

/* ── Hero ─────────────────────────────────────────── */
.rs-hero { margin-bottom: 28px; }
.rs-eyebrow {
  display: inline-flex; align-items: center; padding: 6px 12px; border-radius: 999px; background: var(--accent-soft);
  color: var(--accent); font: 500 11px var(--font-mono); text-transform: uppercase; letter-spacing: 0.1em;
}
.rs-headline {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 56px !important; line-height: 62px !important;
  letter-spacing: -0.02em; color: var(--text-primary) !important; margin: 18px 0 14px !important; padding: 0 !important;
}
.rs-headline em { font-style: italic; color: var(--brand-primary); }
.rs-subtitle { font-size: 18px; line-height: 28px; color: var(--text-secondary); max-width: 680px; margin: 0; }
.rs-features { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }
.rs-feature {
  display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px;
  border: 1px solid var(--border-subtle); background: var(--surface-card); font-size: 14px; font-weight: 500; color: var(--text-secondary);
}
.rs-feature .rs-icon { color: var(--accent); }

/* ── Section titles ───────────────────────────────── */
.rs-section { margin: 28px 0 6px; }
.rs-section-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.rs-section h2 {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 28px !important; line-height: 36px !important;
  letter-spacing: -0.01em; color: var(--text-primary) !important; margin: 0 !important; padding: 0 !important;
}
.rs-tag {
  display: inline-flex; padding: 4px 10px; border-radius: 999px; background: var(--surface-raised); color: var(--text-secondary);
  font: 500 11px var(--font-mono); text-transform: uppercase; letter-spacing: 0.1em;
}
.rs-section-sub { margin: 6px 0 0; font-size: 15px; line-height: 23px; color: var(--text-secondary); }

/* ── Agent cards ──────────────────────────────────── */
.rs-agents { display: grid; grid-template-columns: minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1fr); gap: 4px; }
.rs-connector { display: grid; place-items: center; color: var(--text-muted); }
.rs-agent {
  display: flex; flex-direction: column; background: var(--surface-card); border: 1px solid var(--border-subtle);
  border-radius: 16px; padding: 18px 18px 16px; box-shadow: var(--shadow-card); transition: border-color 0.25s, box-shadow 0.25s;
}
.rs-agent-top { display: flex; justify-content: space-between; align-items: flex-start; }
.rs-agent-icon {
  width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center;
  background: var(--brand-soft); color: var(--brand-primary);
}
.rs-agent-step { color: var(--text-muted); margin-top: 16px; }
.rs-agent-name { font-family: var(--font-display); font-weight: 600; font-size: 19px; line-height: 26px; color: var(--text-primary); margin: 4px 0; }
.rs-agent-desc { font-size: 13.5px; line-height: 20px; color: var(--text-secondary); flex: 1; }
.rs-progress { height: 4px; border-radius: 999px; background: var(--surface-raised); margin-top: 16px; overflow: hidden; }
.rs-progress span { display: block; height: 100%; width: 0; border-radius: inherit; }
.rs-pill {
  display: inline-flex; align-items: center; gap: 5px; padding: 4px 9px; border-radius: 999px;
  font-size: 12px; font-weight: 600; line-height: 1.2; white-space: nowrap;
}
.rs-pill .rs-spinner { width: 9px; height: 9px; border-width: 1.5px; }
.rs-pill--waiting { background: var(--surface-raised); color: var(--text-muted); }
.rs-pill--running { background: var(--status-running-soft); color: var(--status-running); }
.rs-pill--done { background: var(--status-done-soft); color: var(--status-done); }
.rs-pill--failed { background: var(--status-failed-soft); color: var(--status-failed); }
.rs-agent--running { border-color: var(--brand-primary); box-shadow: 0 0 0 0.5px var(--brand-primary), var(--shadow-card); }
.rs-agent--running .rs-progress span { width: 40%; background: var(--brand-primary); animation: rs-slide 1.6s ease-in-out infinite; }
.rs-agent--done .rs-progress span { width: 100%; background: var(--status-done); }
.rs-agent--failed { border-color: var(--status-failed); }
.rs-agent--failed .rs-progress span { width: 100%; background: var(--status-failed); }
@keyframes rs-slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(250%); } }

/* ── Run header, live status, empty state ─────────── */
.rs-run-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; margin: 28px 0 4px; }
.rs-run-title { min-width: 0; flex: 1 1 420px; }
.rs-run-kicker { color: var(--brand-primary); }
.rs-run-head h2 {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 28px !important; line-height: 36px !important;
  letter-spacing: -0.01em; color: var(--text-primary) !important; margin: 6px 0 0 !important; padding: 0 !important;
}
.rs-run-status {
  display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px;
  font-size: 13.5px; font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums;
}
.rs-run-status--running { background: var(--status-running-soft); color: var(--status-running); }
.rs-run-status--done { background: var(--status-done-soft); color: var(--status-done); }
.rs-run-status--failed { background: var(--status-failed-soft); color: var(--status-failed); }
/* "\\3c" is a CSS escape for the less-than sign: st.html drops style blocks whose text contains a raw tag-like sequence */
@property --rs-min { syntax: '\\3c integer>'; inherits: false; initial-value: 0; }
@property --rs-sec { syntax: '\\3c integer>'; inherits: false; initial-value: 0; }
.rs-timer {
  animation: rs-minutes 3600s steps(60, end) forwards, rs-seconds 60s steps(60, end) infinite;
  counter-reset: rs-m var(--rs-min) rs-s var(--rs-sec);
}
.rs-timer::after { content: counter(rs-m) ":" counter(rs-s, decimal-leading-zero); }
@keyframes rs-minutes { from { --rs-min: 0; } to { --rs-min: 60; } }
@keyframes rs-seconds { from { --rs-sec: 0; } to { --rs-sec: 60; } }
.rs-live {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 12px;
  background: var(--status-running-soft); color: var(--status-running);
}
.rs-live-text { flex: 1; font-size: 14.5px; font-weight: 500; color: var(--text-primary); }
.rs-empty {
  margin-top: 16px; padding: 40px 32px; text-align: center; background: var(--surface-sunken);
  border: 1px dashed var(--border-strong); border-radius: 20px;
}
.rs-empty-icon {
  width: 56px; height: 56px; border-radius: 50%; margin: 0 auto 16px; display: grid; place-items: center;
  background: var(--brand-soft); color: var(--brand-primary);
}
.rs-empty h3 {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 22px !important; line-height: 30px !important;
  color: var(--text-primary) !important; margin: 0 0 8px !important; padding: 0 !important;
}
.rs-empty p { font-size: 15px; line-height: 23px; color: var(--text-secondary); max-width: 520px; margin: 0 auto; }
.rs-empty b { font-weight: 600; color: var(--text-primary); }

/* ── Expanders (step outputs) and tabs ────────────── */
[data-testid="stExpander"] details {
  background: var(--surface-card); border: 1px solid var(--border-subtle) !important; border-radius: 14px; box-shadow: none;
}
[data-testid="stExpander"] summary {
  position: relative; padding: 12px 48px 12px 14px !important; border-radius: 14px; background: transparent !important;
}
[data-testid="stExpander"] details[open] > summary { border-bottom: 1px solid var(--border-subtle); border-radius: 14px 14px 0 0; }
[data-testid="stExpander"] summary:hover { background: var(--surface-sunken) !important; }
[data-testid="stExpander"] summary::after {
  content: ""; position: absolute; right: 18px; top: 50%; width: 16px; height: 16px; margin-top: -8px;
  background: var(--text-muted); transform: rotate(-90deg); transition: transform 0.2s ease;
  -webkit-mask: CHEVRON_DOWN center / contain no-repeat; mask: CHEVRON_DOWN center / contain no-repeat;
}
[data-testid="stExpander"] details[open] > summary::after { transform: rotate(0deg); }
[data-testid="stExpanderToggleIcon"] { display: none !important; }
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span { color: var(--text-primary) !important; }
[data-testid="stExpander"] summary p { font-weight: 600; font-size: 15px; }
/* The expander icon becomes a small tile; its wrapper span is sized for a bare icon, so let it grow */
[data-testid="stExpander"] summary span:has(> [data-testid="stExpanderIcon"]) {
  width: auto !important; height: auto !important; overflow: visible !important; margin-right: 6px;
}
[data-testid="stExpander"] summary [data-testid="stExpanderIcon"] {
  width: 28px; height: 28px; border-radius: 8px; display: inline-grid !important; place-items: center; flex-shrink: 0;
  background: var(--brand-soft); color: var(--brand-primary) !important; font-size: 17px !important;
}
[data-testid="stExpander"] summary p span[style*="background-color"] {
  background: var(--surface-raised) !important; color: var(--text-secondary) !important; border-radius: 999px; padding: 3px 9px !important;
  margin-left: 8px; font: 500 10.5px var(--font-mono) !important; text-transform: uppercase; letter-spacing: 0.08em;
  vertical-align: middle; position: relative; top: -1px;
}
[data-testid="stExpanderDetails"] { padding: 16px 20px 18px !important; }
[data-testid="stTabs"] button[role="tab"] p { color: var(--text-muted); font-weight: 500; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p { color: var(--brand-primary); font-weight: 600; }
[data-baseweb="tab-highlight"] { background: var(--brand-primary) !important; }
[data-baseweb="tab-border"] { background: var(--border-subtle) !important; }

/* ── Final report ─────────────────────────────────── */
.st-key-report_header [data-testid="stHorizontalBlock"] { align-items: flex-end; flex-wrap: wrap; gap: 12px; }
.st-key-report_header .rs-section { margin-bottom: 0; }
[class*="st-key-report_card"], [class*="st-key-critic_raw"] {
  background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: 20px; box-shadow: var(--shadow-card);
}
[class*="st-key-report_card"] { padding: 44px 56px; gap: 14px; }
[class*="st-key-critic_raw"] { padding: 32px; }
[class*="st-key-report_card"] > div { max-width: 760px; }
.rs-report-kicker { color: var(--text-muted); }
.rs-report-title {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 36px !important; line-height: 44px !important;
  letter-spacing: -0.015em; color: var(--text-primary) !important; margin: 10px 0 4px !important; padding: 0 !important;
}
[class*="st-key-report_summary"] {
  background: var(--brand-soft); border-left: 3px solid var(--brand-primary); border-radius: 4px 12px 12px 4px; padding: 18px 22px; gap: 6px;
}
.rs-summary-label { color: var(--brand-primary); }
[class*="st-key-report_card"] [data-testid="stMarkdownContainer"] :is(p, li) { font-size: 16px; line-height: 28px; }
[class*="st-key-report_summary"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0; }
[class*="st-key-report_card"] [data-testid="stMarkdownContainer"] h2 {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 24px !important; line-height: 32px !important;
  letter-spacing: -0.01em; margin: 30px 0 8px !important; padding: 0 !important;
}
[class*="st-key-report_card"] [data-testid="stMarkdownContainer"] h3 {
  font-family: var(--font-body) !important; font-weight: 600 !important; font-size: 17.5px !important; line-height: 26px !important;
  margin: 22px 0 6px !important; padding: 0 !important;
}
[class*="st-key-report_card"] .stMarkdownColoredText { color: var(--brand-primary) !important; font-weight: 600; }
.rs-sources-title {
  font-family: var(--font-display) !important; font-weight: 600 !important; font-size: 24px !important; line-height: 32px !important;
  color: var(--text-primary) !important; margin: 18px 0 6px !important; padding: 0 !important;
}
.rs-sources { list-style: none; margin: 0 !important; padding: 0 !important; }
.rs-sources li { display: flex; gap: 12px; align-items: flex-start; padding: 12px 0; border-top: 1px solid var(--border-subtle); }
.rs-sources li:first-child { border-top: none; }
.rs-source-num {
  min-width: 24px; height: 24px; padding: 0 4px; border-radius: 6px; display: grid; place-items: center; flex-shrink: 0;
  background: var(--surface-raised); color: var(--text-secondary); letter-spacing: 0;
}
.rs-sources b { display: block; font-size: 15px; line-height: 22px; font-weight: 600; color: var(--text-primary); }
.rs-sources a {
  display: inline-flex; align-items: center; gap: 5px; margin-top: 2px; font-size: 13.5px; color: var(--brand-primary);
  text-decoration: none; word-break: break-all;
}
.rs-sources a:hover { text-decoration: underline; }

/* ── Critic review ────────────────────────────────── */
.rs-critic {
  background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: 20px; padding: 32px; box-shadow: var(--shadow-card);
}
.rs-critic-head { display: flex; align-items: center; gap: 28px; padding-bottom: 24px; border-bottom: 1px solid var(--border-subtle); }
/* Score ring: a conic gradient (arc = score / 10) with the middle covered, since st.html strips SVG */
.rs-ring {
  position: relative; width: 108px; height: 108px; flex-shrink: 0; border-radius: 50%;
  background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), var(--surface-raised) 0);
}
.rs-ring::before { content: ""; position: absolute; inset: 8px; border-radius: 50%; background: var(--surface-card); }
.rs-ring--done { --ring-color: var(--status-done); }
.rs-ring--running { --ring-color: var(--status-running); }
.rs-ring-value {
  position: absolute; inset: 0; display: flex; align-items: baseline; justify-content: center; padding-top: 32px;
  font-family: var(--font-display); font-weight: 600; font-size: 40px; line-height: 1; color: var(--text-primary);
}
.rs-ring-value small { font-family: var(--font-body); font-size: 15px; font-weight: 500; color: var(--text-muted); margin-left: 2px; }
.rs-critic-verdict { min-width: 0; }
.rs-label { color: var(--text-muted); }
.rs-verdict { margin: 6px 0 12px; font-size: 19px; line-height: 28px; font-weight: 600; color: var(--text-primary); }
.rs-critic-meta { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.rs-grade { display: inline-flex; align-items: center; gap: 6px; padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600; }
.rs-grade--done { background: var(--status-done-soft); color: var(--status-done); }
.rs-grade--running { background: var(--status-running-soft); color: var(--status-running); }
.rs-checked { font-size: 13px; color: var(--text-muted); }
.rs-delta {
  display: inline-flex; align-items: center; gap: 5px; padding: 5px 11px; border-radius: 999px;
  font-size: 12.5px; font-weight: 600; background: var(--surface-raised); color: var(--text-secondary);
}
.rs-delta--up { background: var(--status-done-soft); color: var(--status-done); }
.rs-delta--down { background: var(--status-failed-soft); color: var(--status-failed); }
.st-key-improve_row { margin-top: 4px; }
.rs-critic-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
.rs-col { border-radius: 14px; padding: 18px 20px; }
.rs-col h4 {
  display: flex; align-items: center; gap: 8px; margin: 0 0 10px !important; padding: 0 !important;
  font-family: var(--font-body) !important; font-size: 15.5px !important; font-weight: 600 !important;
}
.rs-col ul { list-style: none; margin: 0; padding: 0; }
.rs-col li { position: relative; padding-left: 16px; margin: 8px 0; font-size: 14.5px; line-height: 22px; color: var(--text-primary); }
.rs-col li::before { content: ""; position: absolute; left: 0; top: 8px; width: 6px; height: 6px; border-radius: 50%; }
.rs-col--good { background: var(--status-done-soft); }
.rs-col--good h4 { color: var(--status-done) !important; }
.rs-col--good li::before { background: var(--status-done); }
.rs-col--improve { background: var(--status-running-soft); }
.rs-col--improve h4 { color: var(--status-running) !important; }
.rs-col--improve li::before { background: var(--status-running); }

/* ── Alerts, spinner, code ────────────────────────── */
[data-testid="stAlertContainer"] { border-radius: 12px; }
[data-testid="stAlertContainer"] p { color: var(--text-primary) !important; }
[data-testid="stSpinner"], [data-testid="stSpinner"] p { color: var(--text-secondary) !important; }
[data-testid="stCode"] pre, [data-testid="stCode"] code { background: var(--surface-sunken) !important; color: var(--text-primary) !important; }

/* ── Smaller screens ──────────────────────────────── */
@media (max-width: 1000px) {
  [data-testid="stMainBlockContainer"] { padding: 40px 32px 72px; }
  .st-key-sample_pick [role="radiogroup"] { grid-template-columns: 1fr; }
  .rs-agents { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .rs-connector { display: none; }
  .rs-headline { font-size: 44px !important; line-height: 50px !important; }
  [class*="st-key-report_card"] { padding: 32px 32px; }
}
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding: 28px 16px 64px; }
  .st-key-input_card { padding: 20px; }
  .rs-headline { font-size: 36px !important; line-height: 42px !important; }
  .rs-agents, .rs-critic-cols { grid-template-columns: 1fr; }
  .rs-critic-head { flex-direction: column; align-items: flex-start; }
  [class*="st-key-report_card"] { padding: 24px 20px; }
  .rs-report-title { font-size: 28px !important; line-height: 36px !important; }
}
"""

# Icons are drawn with CSS masks: our HTML uses the .rs-i-* classes, and Streamlit's own
# elements (topic cards, expander chevrons) get theirs through the two placeholders below
STYLESHEET = STYLESHEET.replace("ARROW_UP_RIGHT", mask_url("arrow-up-right")).replace("CHEVRON_DOWN", mask_url("chevron-down"))
STYLESHEET += "\n" + icon_css() + "\n"
