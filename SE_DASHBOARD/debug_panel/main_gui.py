"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              EXAM SYSTEM — DEBUG DASHBOARD  (main_gui.py)                   ║
║                                                                              ║
║  USAGE GUIDE                                                                 ║
║  ──────────                                                                  ║
║  Run:  python debug_panel/main_gui.py                                        ║
║  Req:  pip install PySide6                                                   ║
║                                                                              ║
║  1. SELECT a module group in the left sidebar.                               ║
║  2. CLICK a function in the Function Navigator list.                         ║
║  3. FILL IN the parameter fields that appear in the center form.             ║
║     • Text fields → str                                                      ║
║     • Spin boxes  → int / float                                              ║
║     • Checkboxes  → bool                                                     ║
║  4. CLICK "▶  Invoke Function" — the validation layer checks types,         ║
║     then calls the mock and displays the result in the Result Console.       ║
║  5. Use "⊘  Clear Console" to wipe the output log.                          ║
║  6. Use "⎘  Copy Result" to copy the last JSON result to the clipboard.     ║
║                                                                              ║
║  ALL FUNCTIONS ARE MOCK / DUMMY — no real server, DB or network is used.    ║
║  Safe to invoke at any time without side effects.                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import sys
import datetime
from typing import Any

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QPalette,
    QSyntaxHighlighter, QTextCharFormat, QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDoubleSpinBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QStackedWidget, QStatusBar, QTextEdit,
    QVBoxLayout, QWidget,
)

# ── import registry (works whether run as script or as package) ────────────────
import os, importlib.util

_here = os.path.dirname(os.path.abspath(__file__))
_reg_path = os.path.join(_here, "registry.py")
_spec = importlib.util.spec_from_file_location("debug_panel.registry", _reg_path)
_reg_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reg_mod)
REGISTRY = _reg_mod.REGISTRY


# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    "bg_base":        "#0f1117",
    "bg_panel":       "#161b22",
    "bg_surface":     "#1c2333",
    "bg_elevated":    "#21262d",
    "bg_input":       "#0d1117",
    "border":         "#30363d",
    "border_active":  "#58a6ff",
    "accent_blue":    "#58a6ff",
    "accent_green":   "#3fb950",
    "accent_red":     "#f85149",
    "accent_orange":  "#d29922",
    "accent_purple":  "#a371f7",
    "accent_cyan":    "#39d3f5",
    "text_primary":   "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted":     "#484f58",
    "text_success":   "#3fb950",
    "text_error":     "#f85149",
    "text_warning":   "#d29922",
    "text_json_key":  "#79c0ff",
    "text_json_str":  "#a5d6ff",
    "text_json_num":  "#f2cc60",
    "text_json_bool": "#ff7b72",
    "module_colors": [
        "#58a6ff", "#3fb950", "#a371f7",
        "#d29922", "#39d3f5", "#ff7b72",
        "#ffa657",
    ],
}

MODULE_ORDER = [
    "Server — Auth & Login",
    "Server — Session State",
    "Server — Exam Control",
    "Protocol — Event Builders",
    "Security",
    "Process Monitor",
    "Incident System",
    "Baris Fork — Legacy API",
]


def _module_color(module_name: str) -> str:
    idx = MODULE_ORDER.index(module_name) if module_name in MODULE_ORDER else 0
    return COLORS["module_colors"][idx % len(COLORS["module_colors"])]


def _apply_palette(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.WindowText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Base,            QColor(COLORS["bg_input"]))
    palette.setColor(QPalette.AlternateBase,   QColor(COLORS["bg_elevated"]))
    palette.setColor(QPalette.ToolTipBase,     QColor(COLORS["bg_surface"]))
    palette.setColor(QPalette.ToolTipText,     QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Text,            QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Button,          QColor(COLORS["bg_elevated"]))
    palette.setColor(QPalette.ButtonText,      QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.BrightText,      QColor(COLORS["accent_red"]))
    palette.setColor(QPalette.Highlight,       QColor(COLORS["accent_blue"]))
    palette.setColor(QPalette.HighlightedText, QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.PlaceholderText, QColor(COLORS["text_muted"]))
    app.setPalette(palette)


APP_STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QMainWindow, QWidget {{
    background-color: {COLORS['bg_base']};
}}

/* ── Sidebar ── */
#sidebar {{
    background-color: {COLORS['bg_panel']};
    border-right: 1px solid {COLORS['border']};
}}

#sidebar_header {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1f2d4a, stop:1 #1a2535);
    border-bottom: 1px solid {COLORS['border']};
    padding: 16px 12px;
}}

#app_title {{
    font-size: 15px;
    font-weight: 700;
    color: {COLORS['accent_blue']};
    letter-spacing: 0.5px;
}}

#app_subtitle {{
    font-size: 10px;
    color: {COLORS['text_muted']};
}}

/* ── Module section labels ── */
#module_label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: {COLORS['text_muted']};
    padding: 10px 12px 4px 12px;
    text-transform: uppercase;
}}

/* ── Function list ── */
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    padding: 7px 12px 7px 20px;
    border-radius: 4px;
    margin: 1px 6px;
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_elevated']};
    color: {COLORS['text_primary']};
}}

QListWidget::item:selected {{
    background-color: rgba(88, 166, 255, 0.12);
    color: {COLORS['accent_blue']};
    border-left: 2px solid {COLORS['accent_blue']};
}}

/* ── Center panel ── */
#center_panel {{
    background-color: {COLORS['bg_base']};
}}

#fn_header {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {COLORS['bg_panel']}, stop:1 {COLORS['bg_base']});
    border-bottom: 1px solid {COLORS['border']};
    padding: 16px 20px;
}}

#fn_name_label {{
    font-size: 17px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

#fn_desc_label {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
    padding-top: 4px;
}}

#module_badge {{
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    letter-spacing: 0.3px;
}}

/* ── Parameters form ── */
#params_scroll_content {{
    background-color: {COLORS['bg_base']};
    padding: 20px;
}}

#param_section_title {{
    font-size: 11px;
    font-weight: 700;
    color: {COLORS['text_muted']};
    letter-spacing: 1px;
    padding-bottom: 8px;
}}

#param_container {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px;
}}

QLabel#param_label {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
    min-width: 160px;
}}

QLabel#type_badge {{
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
}}

QLineEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_blue']};
}}

QLineEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['border_active']};
    background-color: {COLORS['bg_base']};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 5px 8px;
    color: {COLORS['text_primary']};
    min-width: 120px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['border_active']};
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS['bg_elevated']};
    border: 1px solid {COLORS['border']};
    width: 18px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLORS['accent_blue']};
}}

QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
    image: none;
}}

/* ── Invoke button ── */
#invoke_btn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1f6feb, stop:1 #1158c7);
    color: white;
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    letter-spacing: 0.3px;
}}

#invoke_btn:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #388bfd, stop:1 #1f6feb);
}}

#invoke_btn:pressed {{
    background: #1158c7;
    padding-left: 26px;
}}

#clear_btn {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    font-size: 12px;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
}}

#clear_btn:hover {{
    border-color: {COLORS['accent_red']};
    color: {COLORS['accent_red']};
}}

#copy_btn {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    font-size: 12px;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
}}

#copy_btn:hover {{
    border-color: {COLORS['accent_green']};
    color: {COLORS['accent_green']};
}}

/* ── Console ── */
#console_panel {{
    background-color: {COLORS['bg_panel']};
    border-top: 1px solid {COLORS['border']};
}}

#console_header {{
    background-color: {COLORS['bg_elevated']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px 16px;
}}

#console_label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    color: {COLORS['text_muted']};
}}

QTextEdit#console {{
    background-color: {COLORS['bg_input']};
    border: none;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    padding: 12px;
    color: {COLORS['text_primary']};
    line-height: 1.5;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:hover {{
    background-color: {COLORS['accent_blue']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    border-radius: 4px;
}}

/* ── Status bar ── */
QStatusBar {{
    background-color: {COLORS['bg_panel']};
    border-top: 1px solid {COLORS['border']};
    color: {COLORS['text_muted']};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── Validation error ── */
.validation-error {{
    border-color: {COLORS['accent_red']} !important;
}}

#error_label {{
    color: {COLORS['accent_red']};
    font-size: 11px;
}}

/* ── Welcome screen ── */
#welcome_screen {{
    background-color: {COLORS['bg_base']};
}}

#welcome_icon {{
    font-size: 56px;
    color: {COLORS['accent_blue']};
}}

#welcome_title {{
    font-size: 24px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}

#welcome_sub {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

#stat_card {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px 24px;
}}

#stat_num {{
    font-size: 28px;
    font-weight: 700;
    color: {COLORS['accent_blue']};
}}

#stat_label {{
    font-size: 11px;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  JSON SYNTAX HIGHLIGHTER
# ══════════════════════════════════════════════════════════════════════════════

class JSONHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._key_fmt = QTextCharFormat()
        self._key_fmt.setForeground(QColor(COLORS["text_json_key"]))
        self._str_fmt = QTextCharFormat()
        self._str_fmt.setForeground(QColor(COLORS["text_json_str"]))
        self._num_fmt = QTextCharFormat()
        self._num_fmt.setForeground(QColor(COLORS["text_json_num"]))
        self._bool_fmt = QTextCharFormat()
        self._bool_fmt.setForeground(QColor(COLORS["text_json_bool"]))
        self._bool_fmt.setFontWeight(700)
        self._ts_fmt = QTextCharFormat()
        self._ts_fmt.setForeground(QColor(COLORS["text_muted"]))

    def highlightBlock(self, text: str):
        import re
        # Timestamps
        for m in re.finditer(r'\d{4}-\d{2}-\d{2}T[\d:.+Z]+', text):
            self.setFormat(m.start(), m.end() - m.start(), self._ts_fmt)
        # Keys
        for m in re.finditer(r'"([^"\\]|\\.)*"\s*:', text):
            self.setFormat(m.start(), m.end() - 1 - m.start(), self._key_fmt)
        # String values (only after colon-space)
        for m in re.finditer(r':\s*"([^"\\]|\\.)*"', text):
            s = m.start() + m.group().index('"')
            self.setFormat(s, m.end() - s, self._str_fmt)
        # Booleans / null
        for m in re.finditer(r'\b(true|false|null)\b', text):
            self.setFormat(m.start(), m.end() - m.start(), self._bool_fmt)
        # Numbers
        for m in re.finditer(r'(?<!["\w])-?\d+(\.\d+)?(?!["\w])', text):
            self.setFormat(m.start(), m.end() - m.start(), self._num_fmt)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

def _make_type_badge(type_obj: type) -> QLabel:
    name = {str: "str", int: "int", float: "float", bool: "bool", list: "list", dict: "dict"}.get(type_obj, str(type_obj))
    color = {
        "str":   ("#1f4e79", "#58a6ff"),
        "int":   ("#1a3d2b", "#3fb950"),
        "float": ("#2d2a0e", "#f2cc60"),
        "bool":  ("#3d1a1a", "#f85149"),
        "list":  ("#2d1a3d", "#a371f7"),
        "dict":  ("#1a2d3d", "#39d3f5"),
    }.get(name, ("#1c2333", "#8b949e"))
    lbl = QLabel(name)
    lbl.setObjectName("type_badge")
    lbl.setStyleSheet(f"background-color: {color[0]}; color: {color[1]}; border-radius: 4px; padding: 1px 6px; font-size: 10px; font-weight: 600;")
    return lbl


# ══════════════════════════════════════════════════════════════════════════════
#  PARAMETER FORM
# ══════════════════════════════════════════════════════════════════════════════

class ParamField:
    """Wraps one parameter's widget + metadata."""
    def __init__(self, param: dict):
        self.param = param
        self.widget = self._build_widget()

    def _build_widget(self) -> QWidget:
        t = self.param["type"]
        default = self.param.get("default")
        if t == bool:
            w = QCheckBox()
            w.setChecked(bool(default))
            return w
        if t == int:
            w = QSpinBox()
            w.setRange(-2_000_000, 2_000_000)
            w.setValue(int(default) if default is not None else 0)
            return w
        if t == float:
            w = QDoubleSpinBox()
            w.setRange(-1_000_000.0, 1_000_000.0)
            w.setDecimals(2)
            w.setSingleStep(0.5)
            w.setValue(float(default) if default is not None else 0.0)
            return w
        # str / list / dict / fallback
        w = QLineEdit()
        w.setText(str(default) if default is not None else "")
        w.setPlaceholderText(self.param.get("help", ""))
        return w

    def get_value(self) -> Any:
        t = self.param["type"]
        if t == bool:
            return self.widget.isChecked()
        if t == int:
            return self.widget.value()
        if t == float:
            return self.widget.value()
        return self.widget.text()

    def validate(self) -> tuple[bool, str]:
        t = self.param["type"]
        name = self.param["name"]
        val = self.get_value()
        if t in (bool, int, float):
            return True, ""
        # str: no further validation needed
        return True, ""

    def mark_error(self, error: bool):
        if isinstance(self.widget, QLineEdit):
            self.widget.setStyleSheet(
                f"border-color: {COLORS['accent_red']};" if error else ""
            )


class ParamForm(QWidget):
    def __init__(self, fn_name: str, fn_info: dict, parent=None):
        super().__init__(parent)
        self.fn_name = fn_name
        self.fn_info = fn_info
        self.fields: list[ParamField] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        params = self.fn_info.get("params", [])
        if not params:
            lbl = QLabel("This function takes no parameters.")
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-style: italic; padding: 16px;")
            outer.addWidget(lbl)
            return

        header = QLabel("PARAMETERS")
        header.setObjectName("param_section_title")
        outer.addWidget(header)

        container = QWidget()
        container.setObjectName("param_container")
        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(16, 16, 16, 16)

        for param in params:
            field = ParamField(param)
            self.fields.append(field)

            row = QHBoxLayout()
            row.setSpacing(10)

            left = QVBoxLayout()
            left.setSpacing(2)
            name_lbl = QLabel(param["name"])
            name_lbl.setObjectName("param_label")
            name_lbl.setFixedWidth(160)
            help_lbl = QLabel(param.get("help", ""))
            help_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
            help_lbl.setWordWrap(True)
            left.addWidget(name_lbl)
            left.addWidget(help_lbl)

            badge = _make_type_badge(param["type"])
            badge.setAlignment(Qt.AlignTop)

            w_container = QVBoxLayout()
            w_container.setSpacing(2)
            w_container.addWidget(field.widget)
            if isinstance(field.widget, QLineEdit):
                field.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            row.addLayout(left)
            row.addWidget(badge)
            row.addLayout(w_container, 1)
            form_layout.addLayout(row)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"color: {COLORS['border']}; background-color: {COLORS['border']};")
            sep.setFixedHeight(1)
            form_layout.addWidget(sep)

        outer.addWidget(container)

    def get_kwargs(self) -> dict:
        return {f.param["name"]: f.get_value() for f in self.fields}

    def validate_all(self) -> list[str]:
        errors = []
        for f in self.fields:
            ok, msg = f.validate()
            f.mark_error(not ok)
            if not ok:
                errors.append(msg)
        return errors


# ══════════════════════════════════════════════════════════════════════════════
#  WELCOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class WelcomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcome_screen")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        icon = QLabel("🔬")
        icon.setObjectName("welcome_icon")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        layout.addSpacing(16)

        title = QLabel("Exam System — Debug Dashboard")
        title.setObjectName("welcome_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(8)

        sub = QLabel("Select a function from the navigator to begin testing.")
        sub.setObjectName("welcome_sub")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(40)

        # Stats
        modules = set(v["module"] for v in REGISTRY.values())
        stats = [
            (str(len(REGISTRY)), "Functions"),
            (str(len(modules)), "Modules"),
            ("0", "Side Effects"),
        ]

        stat_row = QHBoxLayout()
        stat_row.setSpacing(16)
        stat_row.setContentsMargins(40, 0, 40, 0)
        for num, label in stats:
            card = QWidget()
            card.setObjectName("stat_card")
            card_layout = QVBoxLayout(card)
            card_layout.setAlignment(Qt.AlignCenter)
            n = QLabel(num)
            n.setObjectName("stat_num")
            n.setAlignment(Qt.AlignCenter)
            l = QLabel(label)
            l.setObjectName("stat_label")
            l.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(n)
            card_layout.addWidget(l)
            stat_row.addWidget(card)

        layout.addLayout(stat_row)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class DebugDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exam System — Debug Dashboard")
        self.resize(1400, 860)
        self.setMinimumSize(900, 600)

        self._current_fn: str | None = None
        self._current_form: ParamForm | None = None
        self._last_result: dict | None = None
        self._invoke_count: int = 0

        self._build_ui()
        self._status_bar.showMessage(f"Ready  •  {len(REGISTRY)} mock functions loaded")

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        root_layout.addWidget(self._build_sidebar())

        # Main splitter: center form | console
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(3)
        splitter.addWidget(self._build_center_panel())
        splitter.addWidget(self._build_console_panel())
        splitter.setSizes([560, 260])
        root_layout.addWidget(splitter, 1)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

    # ── Sidebar ────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("sidebar_header")
        h_layout = QVBoxLayout(header)
        h_layout.setSpacing(2)
        h_layout.setContentsMargins(12, 14, 12, 14)
        title = QLabel("🔬  DEBUG PANEL")
        title.setObjectName("app_title")
        subtitle = QLabel("Exam System • Mock Functions")
        subtitle.setObjectName("app_subtitle")
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Scrollable function navigator
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 6, 0, 6)
        nav_layout.setSpacing(0)

        # Group functions by module
        by_module: dict[str, list[str]] = {}
        for fn_name, info in REGISTRY.items():
            mod = info["module"]
            by_module.setdefault(mod, []).append(fn_name)

        # Sort modules by MODULE_ORDER
        sorted_mods = sorted(by_module.keys(), key=lambda m: MODULE_ORDER.index(m) if m in MODULE_ORDER else 999)

        for mod in sorted_mods:
            color = _module_color(mod)
            mod_lbl = QLabel(mod.upper())
            mod_lbl.setObjectName("module_label")
            mod_lbl.setStyleSheet(f"color: {color}; padding: 10px 12px 4px 12px; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
            nav_layout.addWidget(mod_lbl)

            fn_list = QListWidget()
            fn_list.setSpacing(1)
            fn_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            for fn_name in sorted(by_module[mod]):
                short = fn_name.split(".")[-1]
                item = QListWidgetItem(short)
                item.setData(Qt.UserRole, fn_name)
                item.setToolTip(fn_name)
                fn_list.addItem(item)

            fn_list.itemClicked.connect(self._on_function_selected)
            fn_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            fn_list.setFixedHeight(fn_list.count() * 29 + 4)
            nav_layout.addWidget(fn_list)

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll)

        # Footer count
        footer = QLabel(f"{len(REGISTRY)} functions  •  {len(by_module)} modules")
        footer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 8px 12px; border-top: 1px solid {COLORS['border']};")
        layout.addWidget(footer)

        return sidebar

    # ── Center panel ────────────────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        self._center = QStackedWidget()

        # Page 0: Welcome
        self._center.addWidget(WelcomeScreen())

        # Page 1: Function view
        fn_view = QWidget()
        fn_view.setObjectName("center_panel")
        fn_layout = QVBoxLayout(fn_view)
        fn_layout.setContentsMargins(0, 0, 0, 0)
        fn_layout.setSpacing(0)

        # Function header
        self._fn_header = QWidget()
        self._fn_header.setObjectName("fn_header")
        h_layout = QVBoxLayout(self._fn_header)
        h_layout.setSpacing(4)
        h_layout.setContentsMargins(20, 14, 20, 14)
        top_row = QHBoxLayout()
        self._fn_name_label = QLabel()
        self._fn_name_label.setObjectName("fn_name_label")
        self._module_badge = QLabel()
        self._module_badge.setObjectName("module_badge")
        top_row.addWidget(self._fn_name_label, 1)
        top_row.addWidget(self._module_badge)
        self._fn_desc_label = QLabel()
        self._fn_desc_label.setObjectName("fn_desc_label")
        self._fn_desc_label.setWordWrap(True)
        h_layout.addLayout(top_row)
        h_layout.addWidget(self._fn_desc_label)
        fn_layout.addWidget(self._fn_header)

        # Params scroll area
        self._params_scroll = QScrollArea()
        self._params_scroll.setWidgetResizable(True)
        self._params_scroll.setFrameShape(QFrame.NoFrame)
        self._params_content = QWidget()
        self._params_content.setObjectName("params_scroll_content")
        self._params_vbox = QVBoxLayout(self._params_content)
        self._params_vbox.setContentsMargins(24, 20, 24, 12)
        self._params_vbox.setSpacing(16)
        self._params_scroll.setWidget(self._params_content)
        fn_layout.addWidget(self._params_scroll, 1)

        # Action bar
        action_bar = QWidget()
        action_bar.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-top: 1px solid {COLORS['border']};")
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(20, 12, 20, 12)
        ab_layout.setSpacing(10)

        self._error_label = QLabel()
        self._error_label.setObjectName("error_label")
        self._error_label.setWordWrap(True)
        ab_layout.addWidget(self._error_label, 1)

        self._invoke_btn = QPushButton("▶   Invoke Function")
        self._invoke_btn.setObjectName("invoke_btn")
        self._invoke_btn.setCursor(Qt.PointingHandCursor)
        self._invoke_btn.setFixedHeight(40)
        self._invoke_btn.clicked.connect(self._invoke_function)

        ab_layout.addWidget(self._invoke_btn)
        fn_layout.addWidget(action_bar)
        self._center.addWidget(fn_view)
        return self._center

    # ── Console panel ───────────────────────────────────────────────────────

    def _build_console_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("console_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("console_header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 6, 8, 6)
        h.setSpacing(8)
        label = QLabel("RESULT CONSOLE")
        label.setObjectName("console_label")
        h.addWidget(label, 1)

        self._copy_btn = QPushButton("⎘  Copy Result")
        self._copy_btn.setObjectName("copy_btn")
        self._copy_btn.setCursor(Qt.PointingHandCursor)
        self._copy_btn.setFixedHeight(28)
        self._copy_btn.clicked.connect(self._copy_result)

        self._clear_btn = QPushButton("⊘  Clear Console")
        self._clear_btn.setObjectName("clear_btn")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setFixedHeight(28)
        self._clear_btn.clicked.connect(self._clear_console)

        h.addWidget(self._copy_btn)
        h.addWidget(self._clear_btn)
        layout.addWidget(header)

        self._console = QTextEdit()
        self._console.setObjectName("console")
        self._console.setReadOnly(True)
        self._highlighter = JSONHighlighter(self._console.document())
        layout.addWidget(self._console)

        return panel

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_function_selected(self, item: QListWidgetItem):
        fn_name = item.data(Qt.UserRole)
        self._load_function(fn_name)

    def _load_function(self, fn_name: str):
        info = REGISTRY.get(fn_name)
        if not info:
            return

        self._current_fn = fn_name
        self._center.setCurrentIndex(1)
        self._error_label.clear()

        # Update header
        self._fn_name_label.setText(fn_name)
        self._fn_desc_label.setText(info.get("description", ""))

        mod = info.get("module", "")
        color = _module_color(mod)
        self._module_badge.setText(mod)
        self._module_badge.setStyleSheet(
            f"background-color: rgba(88,166,255,0.1); color: {color}; border: 1px solid {color}33; "
            f"border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 700;"
        )

        # Clear params area and rebuild form
        while self._params_vbox.count():
            item = self._params_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._current_form = ParamForm(fn_name, info)
        self._params_vbox.addWidget(self._current_form)
        self._params_vbox.addStretch()

        self._status_bar.showMessage(f"Selected: {fn_name}  •  {len(info.get('params', []))} parameter(s)")

    def _invoke_function(self):
        if not self._current_fn or not self._current_form:
            return

        errors = self._current_form.validate_all()
        if errors:
            self._error_label.setText("⚠  " + " | ".join(errors))
            return

        self._error_label.clear()
        kwargs = self._current_form.get_kwargs()
        fn = REGISTRY[self._current_fn]["fn"]

        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._invoke_count += 1

        try:
            result = fn(**kwargs)
            self._last_result = result
            pretty = json.dumps(result, indent=2, default=str)

            # Color the header line based on status
            status = result.get("status", "") if isinstance(result, dict) else ""
            ok = result.get("ok", None) if isinstance(result, dict) else None
            if status == "error" or ok is False:
                header_color = COLORS["accent_red"]
                icon = "✗"
            elif status == "ok" or ok is True:
                header_color = COLORS["accent_green"]
                icon = "✓"
            else:
                header_color = COLORS["accent_blue"]
                icon = "→"

            divider = "─" * 60
            entry = (
                f'<span style="color:{COLORS["text_muted"]}">'
                f'[{ts}]  #{self._invoke_count}  <span style="color:{COLORS["accent_purple"]}">{self._current_fn}</span>'
                f'</span><br>'
                f'<span style="color:{header_color}">{icon} Invoked successfully</span>'
                f'<br><span style="color:{COLORS["text_muted"]}">{divider}</span><br>'
            )
            self._console.insertHtml(entry)
            self._console.insertPlainText(pretty + "\n\n")
            self._console.verticalScrollBar().setValue(self._console.verticalScrollBar().maximum())
            self._status_bar.showMessage(f"✓  Invoked {self._current_fn} [{ts}]  •  Invocations: {self._invoke_count}")

        except Exception as exc:
            ts2 = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            err_entry = (
                f'<span style="color:{COLORS["text_muted"]}">[{ts2}]  #{self._invoke_count}</span>  '
                f'<span style="color:{COLORS["accent_red"]}">✗ EXCEPTION in {self._current_fn}</span><br>'
                f'<span style="color:{COLORS["accent_red"]}">{type(exc).__name__}: {exc}</span><br><br>'
            )
            self._console.insertHtml(err_entry)
            self._error_label.setText(f"✗  {type(exc).__name__}: {exc}")
            self._status_bar.showMessage(f"✗  Exception in {self._current_fn}")

    def _clear_console(self):
        self._console.clear()
        self._invoke_count = 0
        self._status_bar.showMessage("Console cleared.")

    def _copy_result(self):
        if self._last_result is None:
            self._status_bar.showMessage("Nothing to copy yet.")
            return
        text = json.dumps(self._last_result, indent=2, default=str)
        QApplication.clipboard().setText(text)
        self._copy_btn.setText("✓  Copied!")
        QTimer.singleShot(1800, lambda: self._copy_btn.setText("⎘  Copy Result"))
        self._status_bar.showMessage("Result JSON copied to clipboard.")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Exam Debug Dashboard")
    app.setOrganizationName("SWE Project Team")
    _apply_palette(app)
    app.setStyleSheet(APP_STYLESHEET)

    # Load a monospace font for the console
    QFontDatabase.addApplicationFont(":/fonts/CascadiaCode.ttf")

    window = DebugDashboard()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
