"""
Exam Proctor Dashboard — proctor_dashboard.py  (Sovereign Sentinel Edition)
===========================================================================
Standalone PySide6 application.
Run: python proctor_dashboard.py

Design system: "The Sovereign Sentinel" — High-Contrast Dark Editorial
  • Deep atmospheric Navy canvas (#0d1320)
  • Tonal surface layering (no outlines — boundaries through colour shift)
  • Public Sans (Display/Headline) + Inter (Body/Title/Label) type scale
  • Forged-gradient primary CTA, ghost-text tertiary, command chips
  • Z-axis interaction: hover = surface-tint shift, not shadow lift
"""

import math, random, sys, datetime
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import (
    Qt, QTimer, Signal, QSize, QRect, QPoint, QRectF,
)
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPalette, QBrush, QPen,
    QLinearGradient, QPixmap, QCursor, QFontDatabase,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSplitter, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QTextEdit, QSizePolicy, QGridLayout,
    QProgressBar, QTabWidget, QListWidget, QListWidgetItem,
    QStatusBar, QStackedWidget, QDialog, QDialogButtonBox, QComboBox,
)


# ══════════════════════════════════════════════════════════════════
#  THE SOVEREIGN SENTINEL — TOKEN SYSTEM
#  Creative North Star: "High-Contrast Dark Editorial"
#  Seed: Deep atmospheric Navy #0d1320  •  Command Blue #b1c5ff
# ══════════════════════════════════════════════════════════════════

M = {
    # ── Background / Surface (from guide §2) ───────────────────────
    "background":                   "#0d1320",
    "surface":                      "#0d1320",
    "surface_bright":               "#333947",
    "surface_container_lowest":     "#0a1018",  # interpolated: between background & low
    "surface_container_low":        "#151c28",
    "surface_container":            "#19202c",
    "surface_container_high":       "#232a37",
    "surface_container_highest":    "#2d3543",  # interpolated: between high & bright

    # ── On-Surface (from guide §3) ─────────────────────────────────
    "on_surface":                   "#dce2f4",
    "on_surface_variant":           "#c4c6d2",
    "outline":                      "#8e909b",
    "outline_variant":              "#444650",

    # ── Primary — Command Blue (from guide §2, §5) ────────────────
    "primary":                      "#b1c5ff",
    "on_primary":                   "#052c6e",
    "primary_container":            "#00296b",
    "on_primary_fixed_variant":     "#264486",

    # ── Secondary — Command Chip (from guide §5) ──────────────────
    "secondary_container":          "#3c4661",
    "on_secondary_container":       "#abb4d4",
}

# ── State → colour pair (text, container) — ONLY guide colours ──────────────
# Each state distinguished by tonal intensity within the guide palette
STATE_COLORS: dict[str, tuple[str, str]] = {
    "running":             (M["primary"],            M["primary_container"]),      # bright blue = active
    "waiting":             (M["on_surface_variant"],  M["surface_container"]),      # neutral grey = idle
    "admin_paused":        (M["outline"],             M["surface_container_high"]), # dimmed = paused
    "disconnected_paused": (M["outline_variant"],     M["surface_container"]),      # dark = offline
    "violation_paused":    (M["primary"],             M["outline_variant"]),        # blue on dark = alert
    "awaiting_submission": (M["on_secondary_container"], M["secondary_container"]), # chip tone = pending
    "submitted":           (M["on_primary_fixed_variant"], M["surface_container_low"]), # muted = done
    "banned":              (M["on_surface"],          M["outline_variant"]),        # white on dark = final
}

STATE_LABEL: dict[str, str] = {
    "running":             "Running",
    "waiting":             "Waiting",
    "admin_paused":        "Paused",
    "disconnected_paused": "Disconnected",
    "violation_paused":    "Violation",
    "awaiting_submission": "Awaiting File",
    "submitted":           "Submitted ✓",
    "banned":              "Banned",
}

# ── Typography scale ─────────────────────────────────────────────────────────
#   Display/Headline → "Public Sans"  /  Body/Title/Label → "Inter"
#   (size_pt, weight, letter_spacing_px)
TY = {
    "display_large":   (42, 400, -0.50),    # hero moments
    "display_medium":  (32, 400, -0.25),
    "headline_large":  (22, 500, -0.02),    # industrial strength
    "headline_medium": (18, 500,  0.00),
    "headline_small":  (16, 500,  0.00),
    "title_large":     (14, 500,  0.00),
    "title_medium":    (13, 500,  0.10),
    "title_small":     (12, 500,  0.10),
    "body_large":      (13, 400,  0.00),    # high-readability
    "body_medium":     (12, 400,  0.00),
    "body_small":      (11, 400,  0.10),
    "label_large":     (12, 500,  0.10),
    "label_medium":    (11, 500,  0.50),
    "label_small":     (10, 500,  0.50),
}

# ── Shape scale ──────────────────────────────────────────────────────────────
#   Sovereign rule: tight radii — "engineered" precision, not rounded pillows
SHAPE = {
    "none":        0,
    "extra_small": 2,      # sm (0.125rem)
    "small":       4,      # DEFAULT (0.25rem) — the standard
    "medium":      6,
    "large":       8,
    "extra_large": 12,
    "full":        9999,   # status dots & chips only
}

# ── Global stylesheet: "The Sovereign Sentinel" ─────────────────────────────
#   Core rules:
#     ✗ No 1px borders for sectioning — boundaries through colour shift
#     ✓ Tonal layering for depth
#     ✓ Ambient blue glow for floating elements
#     ✓ Alternating surface tones instead of dividers
MD3_STYLE = f"""
* {{
    font-family: "Inter", "Public Sans", "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
    color: {M['on_surface']};
}}
QMainWindow, QWidget {{
    background-color: {M['background']};
}}
/* ─ Scrollbars: minimal, no-border ─ */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 6px; margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {M['outline_variant']}; border-radius: 3px; min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {M['outline']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; margin: 0 4px;
}}
QScrollBar::handle:horizontal {{
    background: {M['outline_variant']}; border-radius: 3px; min-width: 32px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
/* ─ Table: flat, text-only, column separators ─ */
QTableWidget {{
    background: transparent;
    border: none;
    gridline-color: transparent;
    outline: none;
    selection-background-color: transparent;
}}
QTableWidget::item {{
    padding: 4px 10px;
    border: none;
    border-right: 1px solid {M['surface_container']};
}}
QTableWidget::item:last {{
    border-right: none;
}}
QTableWidget::item:selected {{
    background: {M['primary_container']};
    color: {M['on_surface']};
}}
QTableWidget::item:hover:!selected {{
    background: {M['surface_container']};
}}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: transparent;
    color: {M['on_surface_variant']};
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
    padding: 10px 10px;
    border: none;
    border-right: 1px solid {M['surface_container']};
    border-bottom: 1px solid {M['surface_container']};
}}
QHeaderView::section:last {{
    border-right: none;
}}
/* ─ Search / Line Edit: persistent outline ─ */
QLineEdit {{
    background: {M['surface_container_low']};
    border: 1px solid {M['outline_variant']};
    border-radius: {SHAPE['small']}px;
    padding: 7px 15px;
    color: {M['on_surface']};
    font-size: 13px;
}}
QLineEdit:focus {{
    background: {M['surface_container']};
    border: 2px solid {M['outline']};
    padding: 6px 14px;
}}
QLineEdit[placeholderText] {{ color: {M['on_surface_variant']}; }}
/* ─ Splitter: hair-thin, no-border ─ */
QSplitter::handle {{ background: {M['surface_container']}; }}
QSplitter::handle:hover {{ background: {M['primary']}44; }}
/* ─ Tabs: tonal shift, no outer border ─ */
QTabWidget::pane {{
    border: none;
    background: {M['surface_container_low']};
}}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 20px;
    color: {M['on_surface_variant']};
    font-size: 13px;
    font-weight: 500;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {M['primary']};
    border-bottom: 3px solid {M['primary']};
    background: {M['surface_container_low']};
}}
QTabBar::tab:hover:!selected {{
    color: {M['on_surface']};
    background: {M['surface_container']};
}}
QTabBar {{ background: {M['surface_container']}; }}
/* ─ Status Bar: no border-top, tonal separation ─ */
QStatusBar {{
    background: {M['surface_container_lowest']};
    border: none;
    color: {M['on_surface_variant']};
    font-size: 11px;
    font-weight: 500;
    padding: 4px 16px;
}}
/* ─ Menus: no border, tonal container ─ */
QMenu {{
    background: {M['surface_container_highest']};
    border: none;
    border-radius: {SHAPE['small']}px;
}}
QMenu::item {{ padding: 8px 20px; color: {M['on_surface']}; font-size: 13px; }}
QMenu::item:selected {{ background: {M['primary_container']}; color: {M['on_surface']}; }}
/* ─ Tooltip: no border ─ */
QToolTip {{
    background: {M['surface_container_highest']};
    border: none;
    border-radius: {SHAPE['small']}px;
    color: {M['on_surface']};
    padding: 6px 10px;
    font-size: 11px;
}}
"""


# ══════════════════════════════════════════════════════════════════
#  DATA MODEL  (unchanged from original)
# ══════════════════════════════════════════════════════════════════

LABS         = ["LAB-A", "LAB-B", "LAB-C", "LAB-D"]
COMPUTERS    = [f"PC-{i:02d}" for i in range(1, 16)]
BANNED_PROCS = ["discord.exe", "steam.exe", "cheater.exe",
                "teamviewer.exe", "obs64.exe", "whatsapp.exe"]
FIRST_NAMES  = ["Ali","Ayşe","Mehmet","Fatma","Emre","Zeynep","Can","Selin","Berk","Merve",
                "Kaan","Elif","Mert","İrem","Serkan","Büşra","Deniz","Ceren","Ahmet","Naz",
                "Barış","Rana","Ege","Gökçe","Tuna","Yıldız","Ozan","Pınar","Umut","Leyla",
                "Furkan","Hande","Erdem","Cansu","Volkan","Hira","Tolga","Su","Timur","Nil"]
LAST_NAMES   = ["Yılmaz","Kaya","Demir","Şahin","Çelik","Yıldız","Arslan","Doğan","Koç","Aydın",
                "Polat","Taş","Kurt","Avcı","Çetin","Güneş","Akın","Bozkurt","Özdemir","Tuncer"]

random.seed(42)


@dataclass
class Incident:
    id: str; rule_id: str; severity: str; summary: str
    status: str; pid: int; proc_name: str; at: datetime.datetime


@dataclass
class Student:
    login_id: str; full_name: str; lab: str; computer: str
    ip: str; uuid: str; session_state: str; connected: bool
    time_spent_s: float; extra_s: int; exam_duration_s: int
    kick_count: int; blacklist_count: int; last_action: str
    last_proc: str; admin_paused: bool; submission_name: str
    submitted_at: str; incidents: list = field(default_factory=list)
    _sim_disconnect_cd: int = 0; _sim_violation_cd: int = 0

    @property
    def remaining_s(self) -> int:
        return max(0, self.exam_duration_s + self.extra_s - int(self.time_spent_s))

    @property
    def remaining_str(self) -> str:
        s = self.remaining_s
        m, sec = divmod(s, 60); h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

    @property
    def progress_pct(self) -> float:
        dur = self.exam_duration_s + self.extra_s
        return 0.0 if dur == 0 else min(1.0, self.time_spent_s / dur)

    @property
    def risk_score(self) -> int:
        return min(100, self.blacklist_count * 15 + self.kick_count * 10
                   + (20 if self.session_state == "violation_paused" else 0))


def _random_ip(lab: str) -> str:
    sub = {"LAB-A": 10, "LAB-B": 20, "LAB-C": 30, "LAB-D": 40}.get(lab, 10)
    return f"192.168.{sub}.{random.randint(2, 250)}"


def _make_students(n: int = 50, duration_min: int = 90) -> list[Student]:
    dur, students, used = duration_min * 60, [], set()
    for i in range(n):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        while (fn, ln) in used: fn = random.choice(FIRST_NAMES)
        used.add((fn, ln))
        login = f"{fn.lower()[:3]}{ln.lower()[:3]}{100 + i}"
        lab   = random.choice(LABS)
        st    = random.choices(
            ["running", "running", "running", "running",
             "admin_paused", "disconnected_paused", "violation_paused",
             "waiting", "submitted"], k=1)[0]
        connected = st not in ("disconnected_paused", "waiting", "submitted")
        spent     = random.uniform(0, dur * 0.7) if st in ("running", "admin_paused", "violation_paused") else 0
        inc_count = 0 if st not in ("violation_paused", "running") else random.randint(0, 3)
        s = Student(
            login_id=login, full_name=f"{fn} {ln}", lab=lab,
            computer=random.choice(COMPUTERS), ip=_random_ip(lab),
            uuid=f"{i:04x}-" + "-".join(f"{random.randint(0,0xffff):04x}" for _ in range(3)),
            session_state=st, connected=connected, time_spent_s=spent,
            extra_s=0, exam_duration_s=dur,
            kick_count=random.randint(0, 2) if inc_count else 0,
            blacklist_count=inc_count,
            last_action={"running":"Started","waiting":"Connected","submitted":"Submitted file",
                         "admin_paused":"Admin paused","disconnected_paused":"Disconnected paused",
                         "violation_paused":"Blacklist catch"}.get(st, ""),
            last_proc=random.choice(BANNED_PROCS) if inc_count > 0 else "",
            admin_paused=(st == "admin_paused"),
            submission_name=f"{login}_solution.zip" if st == "submitted" else "",
            submitted_at=datetime.datetime.now().strftime("%H:%M:%S") if st == "submitted" else "",
        )
        for j in range(inc_count):
            proc = random.choice(BANNED_PROCS)
            s.incidents.append(Incident(
                id=f"inc-{i:03d}-{j:02d}", rule_id="process_blacklist",
                severity="violation" if j == 0 else "warning",
                summary=f"{proc} detected", status="opened" if j == 0 else "resolved",
                pid=random.randint(1000, 9999), proc_name=proc,
                at=datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 30))))
        students.append(s)
    return students


# ══════════════════════════════════════════════════════════════════
#  MD3 COMPONENT HELPERS
# ══════════════════════════════════════════════════════════════════

_WEIGHT_MAP = {
    400: QFont.Weight.Normal,
    500: QFont.Weight.Medium,
    700: QFont.Weight.Bold,
}

def _apply_font(widget: QWidget, role: str):
    """Apply an MD3 type-scale role to any widget."""
    size, weight, _ = TY.get(role, (13, 400, 0))
    f = widget.font()
    f.setPointSize(size)
    f.setWeight(_WEIGHT_MAP.get(weight, QFont.Weight.Normal))
    widget.setFont(f)


def _label(text: str, role: str = "body_large",
           color: str = M["on_surface"], wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    lbl.setWordWrap(wrap)
    _apply_font(lbl, role)
    return lbl


def _divider(vertical: bool = False) -> QFrame:
    """Sovereign rule: prefer spacing over lines. When truly needed, use a thin
    surface-shift bar — never a visible 1px stroke."""
    f = QFrame()
    f.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
    f.setStyleSheet(f"color: {M['surface_container_low']}; background: {M['surface_container_low']};")
    if vertical: f.setFixedWidth(1)
    else:        f.setFixedHeight(1)
    return f


# ── Sovereign Button variants ─────────────────────────────────────────────────
#   Primary: Solid + forged gradient.  Tonal: container.  Outlined: ghost border.
#   Text: ghost — no bg, no border.   All use SHAPE['small'] radius (4px).

def btn_filled(text: str, color: str = M["primary"],
               on_color: str = M["on_primary"]) -> QPushButton:
    """Sovereign Filled Button — forged metallic gradient for main CTA."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    # Forged gradient: primary_container → on_primary_fixed_variant @ 135°
    grad_start = M.get("primary_container", color)
    grad_end   = M.get("on_primary_fixed_variant", color)
    b.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {grad_start}, stop:1 {grad_end});
            color: {M['on_surface']};
            border: none;
            border-radius: {SHAPE['small']}px;
            padding: 8px 24px;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.1px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {grad_end}, stop:1 {color}44);
        }}
        QPushButton:pressed {{ background-color: {color}88; }}
        QPushButton:disabled {{
            background-color: {M['surface_container']};
            color: {M['on_surface_variant']}66;
        }}
    """)
    return b


def btn_tonal(text: str, container: str = M["secondary_container"],
              on_container: str = M["on_secondary_container"]) -> QPushButton:
    """Sovereign Tonal Button — command-chip feel, medium emphasis."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {container};
            color: {on_container};
            border: none;
            border-radius: {SHAPE['small']}px;
            padding: 8px 24px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover   {{ background-color: {M['surface_container_highest']}; }}
        QPushButton:pressed {{ background-color: {container}99; }}
        QPushButton:disabled {{
            background-color: {M['surface_container']};
            color: {M['on_surface_variant']}66;
        }}
    """)
    return b


def btn_outlined(text: str, color: str = M["primary"]) -> QPushButton:
    """Sovereign Outlined Button — no visible border. Tonal background shift
    on hover per the No-Line Rule. Acts as a low-emphasis button."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {color};
            border: none;
            border-radius: {SHAPE['small']}px;
            padding: 8px 24px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover   {{ background-color: {M['surface_container']}; }}
        QPushButton:pressed {{ background-color: {M['surface_container_high']}; }}
        QPushButton:disabled {{
            color: {M['on_surface_variant']}66;
        }}
    """)
    return b


def btn_text(text: str, color: str = M["primary"]) -> QPushButton:
    """Sovereign Text Button — ghost, no background, no border. Text only."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {color};
            border: none;
            border-radius: {SHAPE['small']}px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover   {{ background-color: {M['surface_container']}; }}
        QPushButton:pressed {{ background-color: {M['surface_container_high']}; }}
        QPushButton:disabled {{ color: {M['on_surface_variant']}66; }}
    """)
    return b


# ── Sovereign Cards ───────────────────────────────────────────────────────────
#   NO BORDERS for sectioning. Boundaries through tonal colour shift only.
#   "The eye identifies the edge through the change in value, not a line."

def card_elevated(parent=None, radius: int = SHAPE["medium"]) -> QFrame:
    """Sovereign Elevated Card — surface_container_high, ambient blue glow."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {M['surface_container_high']};
            border: none;
            border-radius: {radius}px;
        }}
    """)
    return f


def card_filled(parent=None, radius: int = SHAPE["medium"]) -> QFrame:
    """Sovereign Filled Card — one step above base, tonal lift."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {M['surface_container']};
            border: none;
            border-radius: {radius}px;
        }}
    """)
    return f


def card_outlined(parent=None, radius: int = SHAPE["medium"]) -> QFrame:
    """Sovereign Outlined Card — tonal step-up from base. No border stroke.
    The 'outline' is achieved by the tonal shift against the parent surface."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {M['surface_container_low']};
            border: none;
            border-radius: {radius}px;
        }}
    """)
    return f


# ── Sovereign Command Chip (Filter Chip) ──────────────────────────────────────
#   "These should feel like physical toggles on a dashboard."

class FilterChip(QPushButton):
    """Command Chip — toggleable, shows checkmark when engaged."""
    toggled_state = Signal(bool)

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._text = text
        self._update_style()
        self.toggled.connect(self._update_checked_text)

    def _update_checked_text(self, checked: bool):
        self.setText(("✓  " if checked else "") + self._text)
        self._update_style()

    def _update_style(self):
        checked = self.isChecked()
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {M['secondary_container']};
                    color: {M['on_secondary_container']};
                    border: none;
                    border-radius: {SHAPE['small']}px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {M['surface_container_highest']}; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {M['surface_container']};
                    color: {M['on_surface_variant']};
                    border: none;
                    border-radius: {SHAPE['small']}px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {M['surface_container_high']}; color: {M['on_surface']}; }}
            """)


# ── Sovereign State Badge ────────────────────────────────────────────────────

def state_badge(state: str) -> QLabel:
    label_text = STATE_LABEL.get(state, state)
    colors = STATE_COLORS.get(state, (M["on_surface_variant"], M["surface_container_high"]))
    fg, _ = colors
    lbl = QLabel(label_text)
    lbl.setStyleSheet(f"""
        background: transparent;
        color: {fg};
        padding: 0px;
        font-size: 11px;
        font-weight: 500;
        border: none;
    """)
    _apply_font(lbl, "label_large")
    return lbl


# ── MD3 Circular Progress Ring ────────────────────────────────────────────────

class TimerRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pct  = 1.0
        self.text = "00:00"
        self.setFixedSize(128, 128)

    def set_data(self, pct: float, text: str):
        self.pct  = pct
        self.text = text
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sz    = min(self.width(), self.height())
        thick = 10
        pad   = thick // 2 + 2
        r     = QRect(pad, pad, sz - pad * 2, sz - pad * 2)

        # Track (surface_variant)
        track_pen = QPen(QColor(M["outline_variant"]), thick)
        track_pen.setCapStyle(Qt.RoundCap)
        p.setPen(track_pen)
        p.drawArc(r, 0, 360 * 16)

        # Active arc — colour follows time remaining
        if   self.pct > 0.5: arc_color = M["primary"]
        elif self.pct > 0.2: arc_color = M["on_surface_variant"]
        else:                 arc_color = M["outline"]
        arc_pen = QPen(QColor(arc_color), thick)
        arc_pen.setCapStyle(Qt.RoundCap)
        p.setPen(arc_pen)
        span = int(self.pct * 360 * 16)
        p.drawArc(r, 90 * 16, -span)

        # Label — MD3 title_large in centre
        f = p.font()
        f.setPointSize(14)
        f.setWeight(QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(QColor(M["on_surface"]))
        p.drawText(r, Qt.AlignCenter, self.text)


# ── MD3 Linear Progress ───────────────────────────────────────────────────────

def md3_progress(value: int, max_val: int = 100, color: str = M["primary"]) -> QProgressBar:
    pb = QProgressBar()
    pb.setRange(0, max_val)
    pb.setValue(value)
    pb.setTextVisible(False)
    pb.setFixedHeight(4)
    pb.setStyleSheet(f"""
        QProgressBar {{
            background-color: {M['surface_container']};
            border-radius: 2px;
            border: none;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 2px;
        }}
    """)
    return pb


# ── MD3 State dot indicator ───────────────────────────────────────────────────

class StateDot(QWidget):
    def __init__(self, state: str, parent=None):
        super().__init__(parent)
        self.state = state
        self.setFixedSize(12, 12)

    def set_state(self, s: str):
        self.state = s
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        fg = STATE_COLORS.get(self.state, (M["outline"], ""))[0]
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(fg)))
        p.drawEllipse(1, 1, 10, 10)


# ── MD3 Risk indicator ────────────────────────────────────────────────────────

class RiskBar(QWidget):
    def __init__(self, score: int = 0, parent=None):
        super().__init__(parent)
        self.score = score
        self.setFixedSize(72, 6)

    def set_score(self, s: int):
        self.score = s; self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        # Track
        p.setBrush(QColor(M["surface_container"]))
        p.drawRoundedRect(0, 0, self.width(), self.height(), 3, 3)
        # Fill
        w = int(self.width() * min(1.0, self.score / 100))
        if w > 0:
            c = M["on_surface_variant"] if self.score < 30 else M["outline"] if self.score < 70 else M["primary"]
            p.setBrush(QColor(c))
            p.drawRoundedRect(0, 0, w, self.height(), 3, 3)


# ══════════════════════════════════════════════════════════════════
#  STUDENT TABLE
# ══════════════════════════════════════════════════════════════════

COL_HEADS = ["", "Student", "Lab / PC", "State", "Remaining", "Risk", "Violations", "Connection", "Last Action"]
COL_W     = [40, 165, 110, 130, 100, 85, 80, 100, 160]


class StudentTable(QTableWidget):
    student_selected = Signal(object)

    def __init__(self, students: list, parent=None):
        super().__init__(parent)
        self.students   = students
        self._row_map: list[Student] = []

        self.setColumnCount(len(COL_HEADS))
        self.setHorizontalHeaderLabels(COL_HEADS)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setDefaultSectionSize(40)
        self.itemSelectionChanged.connect(self._on_selection)
        
        # Track manual resizing so we don't fight the user
        self._user_resized_cols = False
        self.horizontalHeader().sectionResized.connect(self._on_col_resized)

    def _on_col_resized(self, logicalIndex, oldSize, newSize):
        if self.isVisible(): self._user_resized_cols = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._user_resized_cols:
            w = self.viewport().width()
            if w > 0:
                tw = sum(COL_W)
                # First column (dot) stays fixed at its minimal width, others stretch proportionally
                self.setColumnWidth(0, COL_W[0])
                rem_w = w - COL_W[0]
                rem_tw = tw - COL_W[0]
                for i in range(1, len(COL_HEADS)):
                    self.setColumnWidth(i, int(rem_w * (COL_W[i] / rem_tw)))

    def populate(self, students: list[Student], search: str = "", state_filter: str = "All") -> int:
        self._row_map = []
        filtered = [
            s for s in students
            if (state_filter == "All" or s.session_state == state_filter)
            and (not search or any(search.lower() in x.lower()
                 for x in (s.login_id, s.full_name, s.lab, s.computer)))
        ]
        self.setRowCount(len(filtered))
        for row, st in enumerate(filtered):
            self._row_map.append(st)
            self._set_row(row, st)
        return len(filtered)

    def _cell_widget(self, row: int, col: int, w: QWidget):
        self.setItem(row, col, QTableWidgetItem(""))
        w.setStyleSheet("background: transparent;")
        self.setCellWidget(row, col, w)

    def _set_row(self, row: int, st: Student):
        # ── Col 0: state dot ──
        dw = QWidget()
        dl = QHBoxLayout(dw); dl.setContentsMargins(4, 0, 0, 0)
        dl.addWidget(StateDot(st.session_state)); dl.addStretch()
        self._cell_widget(row, 0, dw)

        # ── Col 1: name + login_id ──
        nw = QWidget(); nl = QVBoxLayout(nw)
        nl.setContentsMargins(4, 3, 4, 3); nl.setSpacing(1)
        nm = QLabel(st.full_name)
        _apply_font(nm, "title_medium")
        nm.setStyleSheet(f"color: {M['on_surface']}; background: transparent; border: none;")
        li = QLabel(st.login_id)
        _apply_font(li, "body_small")
        li.setStyleSheet(f"color: {M['on_surface_variant']}; background: transparent; border: none;")
        nl.addWidget(nm); nl.addWidget(li)
        self._cell_widget(row, 1, nw)

        # ── Col 2: lab / pc ──
        self._item(row, 2, f"{st.lab}  ·  {st.computer}", M["on_surface_variant"])

        # ── Col 3: state badge ──
        sw = QWidget(); sl = QHBoxLayout(sw)
        sl.setContentsMargins(6, 4, 6, 4)
        sl.addWidget(state_badge(st.session_state)); sl.addStretch()
        self._cell_widget(row, 3, sw)

        # ── Col 4: remaining + linear progress ──
        rw = QWidget(); rl = QVBoxLayout(rw)
        rl.setContentsMargins(6, 3, 6, 3); rl.setSpacing(3)
        rc = M["primary"] if st.remaining_s > 600 else M["on_surface_variant"] if st.remaining_s > 120 else M["outline"]
        rt = QLabel(st.remaining_str)
        _apply_font(rt, "title_medium")
        rt.setStyleSheet(f"color: {rc}; background: transparent; border: none;")
        pct_used = st.progress_pct
        pc = M["primary"] if pct_used < 0.5 else M["on_surface_variant"] if pct_used < 0.8 else M["outline"]
        pb = md3_progress(int((1 - pct_used) * 100), color=pc)
        rl.addWidget(rt); rl.addWidget(pb)
        self._cell_widget(row, 4, rw)

        # ── Col 5: risk bar ──
        riskw = QWidget(); riskl = QHBoxLayout(riskw)
        riskl.setContentsMargins(6, 0, 6, 0); riskl.setSpacing(6)
        rb = RiskBar(st.risk_score)
        rs = QLabel(str(st.risk_score))
        _apply_font(rs, "label_large")
        rc2 = M["on_surface_variant"] if st.risk_score < 30 else M["outline"] if st.risk_score < 70 else M["primary"]
        rs.setStyleSheet(f"color: {rc2}; font-weight: 700; background: transparent; border: none;")
        riskl.addWidget(rb); riskl.addWidget(rs); riskl.addStretch()
        self._cell_widget(row, 5, riskw)

        # ── Col 6: violations ──
        vc = M["primary"] if st.blacklist_count > 0 else M["on_surface_variant"]
        self._item(row, 6, str(st.blacklist_count) + ("  ⚠" if st.blacklist_count > 0 else ""), vc)

        # ── Col 7: connection ──
        cc = M["primary"] if st.connected else M["outline_variant"]
        self._item(row, 7, "● Online" if st.connected else "○ Offline", cc)

        # ── Col 8: last action ──
        self._item(row, 8, st.last_action, M["on_surface_variant"])

    def _item(self, row: int, col: int, text: str, color: str):
        it = QTableWidgetItem(text)
        it.setForeground(QColor(color))
        self.setItem(row, col, it)

    def _on_selection(self):
        if not self.selectedItems(): return
        row = self.currentRow()
        if 0 <= row < len(self._row_map):
            self.student_selected.emit(self._row_map[row])

    def refresh_row(self, student: Student):
        for row in range(self.rowCount()):
            if row < len(self._row_map) and self._row_map[row].login_id == student.login_id:
                self._set_row(row, student); break

    def get_selected(self) -> Optional[Student]:
        row = self.currentRow()
        return self._row_map[row] if 0 <= row < len(self._row_map) else None


# ══════════════════════════════════════════════════════════════════
#  MD3 STAT CARD
# ══════════════════════════════════════════════════════════════════

class StatCard(QFrame):
    """MD3 Elevated Card variant used in the stats row."""
    def __init__(self, label: str, value: str, fg: str, bg: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._val_lbl: Optional[QLabel] = None
        self.setFixedHeight(84)
        # MD3 tonal elevation via colour — no drop shadow needed in dark mode
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {M['outline_variant']};
                border-radius: {SHAPE['medium']}px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        if icon:
            ico = QLabel(icon)
            _apply_font(ico, "headline_large")
            ico.setStyleSheet(f"color: {fg}; border: none; background: none;")
            lay.addWidget(ico)

        vbox = QVBoxLayout(); vbox.setSpacing(2)
        self._val_lbl = QLabel(value)
        _apply_font(self._val_lbl, "display_medium")
        self._val_lbl.setStyleSheet(f"color: {fg}; font-weight: 700; border: none; background: none;")
        lbl_w = QLabel(label.upper())
        _apply_font(lbl_w, "label_medium")
        lbl_w.setStyleSheet(f"color: {fg}cc; letter-spacing: 0.5px; border: none; background: none;")
        vbox.addWidget(self._val_lbl); vbox.addWidget(lbl_w)
        lay.addLayout(vbox); lay.addStretch()

    def set_value(self, v: str):
        if self._val_lbl: self._val_lbl.setText(v)


# ══════════════════════════════════════════════════════════════════
#  MD3 STUDENT AVATAR  (coloured circle + initials)
# ══════════════════════════════════════════════════════════════════

_AVATAR_PALETTE = [
    (M["primary_container"],       M["primary"]),
    (M["secondary_container"],     M["on_secondary_container"]),
    (M["outline_variant"],         M["on_surface"]),
    (M["surface_container_high"],  M["primary"]),
    (M["on_primary_fixed_variant"], M["on_surface"]),
    (M["surface_container_highest"], M["on_surface_variant"]),
    (M["surface_container"],       M["primary"]),
]

def _avatar_colors(name: str) -> tuple[str, str]:
    idx = (ord(name[0]) if name else 0) % len(_AVATAR_PALETTE)
    return _AVATAR_PALETTE[idx]

def _initials(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return full_name[:2].upper() if full_name else "?"

class StudentAvatar(QWidget):
    """MD3-style circular avatar showing student initials."""
    def __init__(self, full_name: str, size: int = 36, parent=None):
        super().__init__(parent)
        self._name = full_name
        self._sz   = size
        self.setFixedSize(size, size)

    def set_name(self, name: str):
        self._name = name
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg_hex, fg_hex = _avatar_colors(self._name)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(bg_hex)))
        p.drawEllipse(0, 0, self._sz, self._sz)
        f = p.font()
        f.setPointSize(max(9, self._sz // 3))
        f.setWeight(QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(QColor(fg_hex))
        p.drawText(QRect(0, 0, self._sz, self._sz), Qt.AlignCenter, _initials(self._name))


# ══════════════════════════════════════════════════════════════════
#  MD3 SNACKBAR  (temporary notification at bottom of window)
# ══════════════════════════════════════════════════════════════════

class MD3Snackbar(QWidget):
    """
    Materialdesign.io Snackbar spec:
      • Surface container highest background
      • Single line of body-medium text
      • Optional action button (text button)
      • Auto-dismisses after `duration_ms` milliseconds
      • Appears at bottom-center of parent window
    """
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._dismiss)

        # Floating frame
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {M['surface_container_highest']};
                border-radius: {SHAPE['small']}px;
                border: none;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 8, 0)
        lay.setSpacing(8)
        self._msg = QLabel()
        _apply_font(self._msg, "body_medium")
        self._msg.setStyleSheet(f"color: {M['on_surface']}; background: none; border: none;")
        self._action_btn = btn_text("", M["primary"])
        self._action_btn.setFixedHeight(32)
        self._action_btn.hide()
        lay.addWidget(self._msg, 1)
        lay.addWidget(self._action_btn)
        self.setFixedHeight(52)
        self.hide()

    def show_message(self, text: str, action_label: str = "",
                     action_cb=None, duration_ms: int = 4000):
        self._msg.setText(text)
        if action_label and action_cb:
            self._action_btn.setText(action_label)
            try: self._action_btn.clicked.disconnect()
            except RuntimeError: pass
            self._action_btn.clicked.connect(action_cb)
            self._action_btn.show()
        else:
            self._action_btn.hide()
        self._reposition()
        self.show()
        self.raise_()
        self._hide_timer.start(duration_ms)

    def _reposition(self):
        if not self.parent(): return
        pw = self.parent().width()
        ph = self.parent().height()
        w = min(pw - 48, 560)
        self.setFixedWidth(w)
        self.move((pw - w) // 2, ph - 80)

    def _dismiss(self):
        self.hide()

    def resizeEvent(self, e):
        self._reposition()
        super().resizeEvent(e)


# ══════════════════════════════════════════════════════════════════
#  MD3 CONFIRM DIALOG
# ══════════════════════════════════════════════════════════════════

class ConfirmDialog(QDialog):
    """
    MD3 Dialog spec:
      • surface_container_high surface
      • Headline + supporting text
      • Outlined cancel + Filled confirm (error for destructive)
    """
    def __init__(self, title: str, body: str, confirm_label: str = "Confirm",
                 destructive: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {M['surface_container_high']};
                border-radius: {SHAPE['extra_large']}px;
            }}
        """)
        self.setMinimumWidth(360)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(16)

        # Icon + title
        icon_text = "⛔" if destructive else "ℹ️"
        icon_lbl = QLabel(icon_text)
        _apply_font(icon_lbl, "headline_medium")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: none; border: none;")
        lay.addWidget(icon_lbl)

        title_lbl = _label(title, "headline_small", M["on_surface"])
        title_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(title_lbl)

        body_lbl = _label(body, "body_medium", M["on_surface_variant"], wrap=True)
        body_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(body_lbl)

        lay.addSpacing(8)

        # Buttons — MD3 dialog spec: dismiss left, confirm right
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = btn_outlined("Cancel", M["on_surface_variant"])
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedHeight(38)
        confirm_color = M["on_surface"] if destructive else M["primary"]
        confirm_on    = M["background"] if destructive else M["on_primary"]
        confirm_btn   = btn_filled(confirm_label, confirm_color, confirm_on)
        confirm_btn.clicked.connect(self.accept)
        confirm_btn.setFixedHeight(38)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)
        lay.addLayout(btn_row)


# ══════════════════════════════════════════════════════════════════
#  STUDENT DETAIL PANEL
# ══════════════════════════════════════════════════════════════════

class StudentDetailPanel(QWidget):
    action_requested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._student: Optional[Student] = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── MD3 Top section — Surface Container High ──
        self._hdr = QWidget()
        self._hdr.setStyleSheet(f"""
            background-color: {M['surface_container_high']};
        """)
        hl = QVBoxLayout(self._hdr)
        hl.setContentsMargins(20, 16, 20, 16); hl.setSpacing(4)
        top_row = QHBoxLayout()
        self._avatar    = StudentAvatar("?", size=40)
        self._name_lbl  = _label("Select a student", "headline_small", M["on_surface"])
        self._badge_lbl = QLabel()
        self._badge_lbl.setStyleSheet("border: none; background: transparent;")
        top_row.addWidget(self._avatar)
        top_row.addSpacing(10)
        top_row.addWidget(self._name_lbl, 1)
        top_row.addWidget(self._badge_lbl)
        self._sub_lbl = _label("", "body_medium", M["on_surface_variant"])
        hl.addLayout(top_row); hl.addWidget(self._sub_lbl)
        root.addWidget(self._hdr)

        # ── Stacked: empty state / detail content ──
        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        # Page 0 — empty state
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setAlignment(Qt.AlignCenter)
        el.setSpacing(12)
        empty_icon = QLabel("👨‍🎓")
        _apply_font(empty_icon, "display_large")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet("background: none; border: none;")
        empty_title = _label("No student selected", "title_large", M["on_surface_variant"])
        empty_title.setAlignment(Qt.AlignCenter)
        empty_sub = _label("Click any row in the roster to view\ndetails and take actions.",
                           "body_medium", M["outline"], wrap=True)
        empty_sub.setAlignment(Qt.AlignCenter)
        el.addWidget(empty_icon)
        el.addWidget(empty_title)
        el.addWidget(empty_sub)
        self._stack.addWidget(empty)

        # Page 1 — scrollable detail
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self._lay = QVBoxLayout(content)
        self._lay.setContentsMargins(16, 16, 16, 16); self._lay.setSpacing(16)
        scroll.setWidget(content)
        self._stack.addWidget(scroll)

        # Timer ring + metadata card
        top_info = card_elevated(radius=SHAPE["large"])
        ti_lay = QHBoxLayout(top_info)
        ti_lay.setContentsMargins(16, 16, 16, 16); ti_lay.setSpacing(16)
        self._timer   = TimerRing()
        self._big_avatar = StudentAvatar("?", size=64)
        av_col = QVBoxLayout()
        av_col.setSpacing(8)
        av_col.addWidget(self._big_avatar, 0, Qt.AlignCenter)
        av_col.addWidget(self._timer, 0, Qt.AlignCenter)
        ti_lay.addLayout(av_col)
        ti_lay.addWidget(_divider(True))

        meta_lay = QGridLayout(); meta_lay.setSpacing(8)
        self._meta: dict[str, QLabel] = {}
        for i, (lbl_text, key) in enumerate([
            ("Lab", "lab"), ("Computer", "computer"),
            ("IP Address", "ip"), ("UUID", "uuid"),
            ("Time Spent", "spent"), ("Extra Time", "extra"),
            ("Kicks", "kicks"), ("Incidents", "viols"),
        ]):
            row, col = divmod(i, 2)
            k_lbl = _label(lbl_text, "label_medium", M["on_surface_variant"])
            v_lbl = _label("—", "body_medium", M["on_surface"])
            v_lbl.setWordWrap(True)
            self._meta[key] = v_lbl
            cell = QVBoxLayout(); cell.setSpacing(1)
            cell.addWidget(k_lbl); cell.addWidget(v_lbl)
            meta_lay.addLayout(cell, row, col)
        ti_lay.addLayout(meta_lay, 1)
        self._lay.addWidget(top_info)

        # ── Quick Actions card ──
        act_card = card_outlined(radius=SHAPE["large"])
        act_main = QVBoxLayout(act_card)
        act_main.setContentsMargins(16, 14, 16, 14); act_main.setSpacing(12)
        act_hdr = _label("Quick Actions", "title_medium", M["on_surface_variant"])
        act_main.addWidget(act_hdr)
        act_main.addWidget(_divider())

        act_grid = QGridLayout(); act_grid.setSpacing(8)
        self._act_btns: dict[str, QPushButton] = {}
        actions = [
            ("pause_exam",         "Pause Timer",    btn_tonal,    M["outline_variant"],           M["on_surface"]),
            ("resume_exam",        "Resume Timer",   btn_tonal,    M["primary_container"],         M["primary"]),
            ("add_time",           "+ 5 Minutes",    btn_filled,   M["primary"],                    M["on_primary"]),
            ("forgive_violation",  "Forgive",        btn_tonal,    M["secondary_container"],       M["on_secondary_container"]),
            ("savescreen",         "Save Screen",    btn_outlined, M["on_surface_variant"],        None),
            ("get_processes",      "Get Processes",  btn_outlined, M["on_surface_variant"],        None),
            ("kick",               "Kick",           btn_outlined, M["outline"],                    None),
            ("ban",                "Ban Student",    btn_filled,   M["on_surface"],                M["background"]),
        ]
        for i, (key, label, factory, *args) in enumerate(actions):
            r, c = divmod(i, 2)
            b = factory(label, *[a for a in args if a is not None])
            b.setFixedHeight(36)
            def _make_cb(k): return lambda: self.action_requested.emit(k, self._student)
            b.clicked.connect(_make_cb(key))
            self._act_btns[key] = b
            act_grid.addWidget(b, r, c)
        act_main.addLayout(act_grid)
        self._lay.addWidget(act_card)

        # ── Incidents card ──
        self._inc_card = card_elevated(radius=SHAPE["large"])
        inc_main = QVBoxLayout(self._inc_card)
        inc_main.setContentsMargins(16, 14, 16, 14); inc_main.setSpacing(10)
        inc_hdr = _label("Incidents", "title_medium", M["on_surface_variant"])
        inc_main.addWidget(inc_hdr); inc_main.addWidget(_divider())
        self._inc_vbox = QVBoxLayout(); self._inc_vbox.setSpacing(8)
        self._no_inc = _label("No incidents recorded.", "body_medium", M["on_surface_variant"])
        self._inc_vbox.addWidget(self._no_inc)
        inc_main.addLayout(self._inc_vbox)
        self._lay.addWidget(self._inc_card)
        self._lay.addStretch()

    def load(self, student: Student):
        self._student = student
        self._stack.setCurrentIndex(1)  # show detail page
        fg, bg = STATE_COLORS.get(student.session_state, (M["on_surface_variant"], M["surface_container_high"]))
        self._avatar.set_name(student.full_name)
        self._big_avatar.set_name(student.full_name)
        self._name_lbl.setText(student.full_name)
        self._sub_lbl.setText(f"{student.login_id}  ·  {student.ip}  ·  {student.lab} / {student.computer}")
        self._badge_lbl.setText(STATE_LABEL.get(student.session_state, student.session_state))
        self._badge_lbl.setStyleSheet(f"""
            background-color: {bg}; color: {fg};
            border-radius: {SHAPE['small']}px; padding: 3px 10px;
            font-size: 11px; font-weight: 500; border: none;
        """)
        pct = 1.0 - student.progress_pct
        self._timer.set_data(pct, student.remaining_str)

        def fmts(s: float) -> str:
            m, sec = divmod(int(s), 60); return f"{m}m {sec:02d}s"
        m = self._meta
        m["lab"].setText(student.lab); m["computer"].setText(student.computer)
        m["ip"].setText(student.ip); m["uuid"].setText(student.uuid[:14] + "…")
        m["spent"].setText(fmts(student.time_spent_s))
        m["extra"].setText(f"+{student.extra_s // 60}m" if student.extra_s else "—")
        m["kicks"].setText(str(student.kick_count)); m["viols"].setText(str(student.blacklist_count))

        # Button enable states
        self._act_btns["pause_exam"].setEnabled(student.session_state == "running")
        self._act_btns["resume_exam"].setEnabled(student.session_state in ("admin_paused", "disconnected_paused"))
        self._act_btns["forgive_violation"].setEnabled(student.session_state == "violation_paused")
        self._act_btns["ban"].setEnabled(student.session_state != "banned")

        # Rebuild incidents
        while self._inc_vbox.count():
            it = self._inc_vbox.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        if student.incidents:
            for inc in reversed(student.incidents):
                self._inc_vbox.addWidget(self._incident_row(inc))
        else:
            self._inc_vbox.addWidget(self._no_inc)

    def refresh_timer(self, student: Student):
        if self._student and self._student.login_id == student.login_id:
            self._timer.set_data(1.0 - student.progress_pct, student.remaining_str)
            def fmts(s: float) -> str:
                m, sec = divmod(int(s), 60); return f"{m}m {sec:02d}s"
            self._meta["spent"].setText(fmts(student.time_spent_s))

    def _incident_row(self, inc: Incident) -> QFrame:
        sc = M["primary"] if inc.severity == "violation" else M["on_surface_variant"]
        sc_bg = M["outline_variant"] if inc.severity == "violation" else M["surface_container_high"]
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: {sc_bg};
                border-radius: {SHAPE['small']}px;
                border: none;
            }}
        """)
        lay = QVBoxLayout(f); lay.setContentsMargins(12, 8, 12, 8); lay.setSpacing(3)
        top_row = QHBoxLayout()
        sev = _label(inc.severity.upper(), "label_medium", sc)
        res_c = M["on_surface_variant"] if inc.status == "resolved" else M["primary"]
        res = _label("RESOLVED" if inc.status == "resolved" else "OPEN", "label_medium", res_c)
        ts = _label(inc.at.strftime("%H:%M:%S"), "body_small", M["on_surface_variant"])
        top_row.addWidget(sev); top_row.addStretch(); top_row.addWidget(ts); top_row.addWidget(res)
        sum_lbl = _label(f"{inc.summary}  ·  pid {inc.pid}", "body_medium", M["on_surface"])
        lay.addLayout(top_row); lay.addWidget(sum_lbl)
        return f


# ══════════════════════════════════════════════════════════════════
#  ACTIVITY LOG
# ══════════════════════════════════════════════════════════════════

class ActivityLog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # Log header — MD3 surface_container
        hdr = QWidget()
        hdr.setStyleSheet(f"background: {M['surface_container_high']};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 6, 16, 6)
        l = _label("Activity Log", "title_small", M["on_surface_variant"])
        self._cnt = _label("0 events", "body_small", M["outline"])
        clr = btn_text("Clear", M["outline"]); clr.setFixedHeight(28)
        clr.clicked.connect(lambda: (self._log_view.clear(), setattr(self, "_count", 0)))
        hl.addWidget(l); hl.addStretch(); hl.addWidget(self._cnt); hl.addWidget(clr)
        lay.addWidget(hdr)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setFixedHeight(130)
        self._log_view.setStyleSheet(f"""
            background: {M['surface_container_low']};
            border: none;
            font-family: "Roboto Mono","Cascadia Code","Consolas",monospace;
            font-size: 11px;
            color: {M['on_surface']};
            padding: 6px 14px;
        """)
        lay.addWidget(self._log_view)

    def log(self, msg: str, color: str = M["on_surface"]):
        self._count += 1
        self._cnt.setText(f"{self._count} events")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_view.append(
            f'<span style="color:{M["outline"]}">[{ts}]</span>  '
            f'<span style="color:{color}">{msg}</span>'
        )
        sb = self._log_view.verticalScrollBar(); sb.setValue(sb.maximum())


# ══════════════════════════════════════════════════════════════════
#  TOP APP BAR  (MD3 — medium / contextual)
# ══════════════════════════════════════════════════════════════════

class ExamControlBar(QWidget):
    command = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase   = "waiting"
        self._elapsed = 0
        # MD3 surface_container elevation-3 tint
        self.setStyleSheet(f"""
            background-color: {M['surface_container_high']};
        """)
        self.setFixedHeight(72)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0); lay.setSpacing(16)

        # Left — title block
        title_block = QVBoxLayout(); title_block.setSpacing(2)
        title_row = QHBoxLayout(); title_row.setSpacing(8)
        self._phase_dot = QLabel("●")
        _apply_font(self._phase_dot, "title_large")
        self._phase_dot.setStyleSheet(f"color: {M['outline']}; border: none; background: none;")
        title = _label("Exam Proctor Dashboard", "title_large", M["on_surface"])
        title_row.addWidget(self._phase_dot); title_row.addWidget(title); title_row.addStretch()
        subtitle = _label("CS101 — Final Examination  ·  Lab Complex", "body_medium", M["on_surface_variant"])
        title_block.addLayout(title_row); title_block.addWidget(subtitle)
        lay.addLayout(title_block)
        lay.addStretch()

        # Phase chip
        self._phase_chip = QLabel("⏳  Waiting")
        self._phase_chip.setStyleSheet(f"""
            background-color: {M['surface_container_high']};
            color: {M['outline']};
            border-radius: {SHAPE['small']}px;
            padding: 4px 14px;
            font-size: 12px; font-weight: 500; border: none;
        """)
        lay.addWidget(self._phase_chip)

        lay.addWidget(_divider(True))

        # Exam clock
        self._clock = QLabel("00:00:00")
        _apply_font(self._clock, "headline_large")
        self._clock.setStyleSheet(f"""
            color: {M['primary']};
            font-family: "Roboto Mono","Cascadia Code","Consolas",monospace;
            font-weight: 700; border: none; background: none;
        """)
        lay.addWidget(self._clock)
        lay.addWidget(_divider(True))

        # CTA buttons — MD3 hierarchy: Filled > Tonal > Outlined
        self._start_btn  = btn_filled("▶  Start Exam",  M["primary"],              M["on_primary"])
        self._pause_btn  = btn_tonal("⏸  Pause All",    M["outline_variant"],       M["on_surface"])
        self._screen_btn = btn_outlined("📷  Savescreen All", M["on_surface_variant"])
        self._finish_btn = btn_filled("⏹  End Exam",    M["on_surface"],            M["background"])

        self._finish_btn.setEnabled(False); self._pause_btn.setEnabled(False)
        for b in (self._start_btn, self._pause_btn, self._screen_btn, self._finish_btn):
            b.setFixedHeight(38); lay.addWidget(b)

        self._start_btn.clicked.connect(self._on_start)
        self._finish_btn.clicked.connect(self._on_finish)
        self._pause_btn.clicked.connect(lambda: self.command.emit("pause_all"))
        self._screen_btn.clicked.connect(lambda: self.command.emit("savescreen_all"))

    def _on_start(self):
        if self._phase != "waiting": return
        self._phase = "running"
        self._phase_dot.setStyleSheet(f"color: {M['primary']}; border: none; background: none;")
        self._phase_chip.setText("🟢  Running")
        self._phase_chip.setStyleSheet(f"""
            background-color: {M['primary_container']};
            color: {M['primary']};
            border-radius: {SHAPE['small']}px;
            padding: 4px 14px; font-size: 12px; font-weight: 500; border: none;
        """)
        self._start_btn.setEnabled(False)
        self._finish_btn.setEnabled(True)
        self._pause_btn.setEnabled(True)
        self.command.emit("start_exam")

    def _on_finish(self):
        if self._phase != "running": return
        self._phase = "finished"
        self._phase_dot.setStyleSheet(f"color: {M['outline_variant']}; border: none; background: none;")
        self._phase_chip.setText("🔴  Finished")
        self._phase_chip.setStyleSheet(f"""
            background-color: {M['outline_variant']};
            color: {M['on_surface']};
            border-radius: {SHAPE['small']}px;
            padding: 4px 14px; font-size: 12px; font-weight: 500; border: none;
        """)
        self._finish_btn.setEnabled(False); self._pause_btn.setEnabled(False)
        self.command.emit("finish_exam")

    def tick(self):
        if self._phase == "running":
            self._elapsed += 1
        h, r = divmod(self._elapsed, 3600); m, s = divmod(r, 60)
        self._clock.setText(f"{h:02d}:{m:02d}:{s:02d}")

    @property
    def phase(self) -> str: return self._phase


# ══════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════

class ProctorDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Exam Proctor Dashboard")
        self.resize(1600, 960)
        self.setMinimumSize(1100, 700)

        self._students  = _make_students(50)
        self._selected: Optional[Student] = None
        self._search    = ""
        self._state_flt = "All"
        self._sim_tick  = 0

        self._build_ui()
        self._refresh_stats()
        self._populate_table()
        self._log(f"Dashboard loaded — {len(self._students)} students registered.", M["primary"])

        self._tick_timer = QTimer(self); self._tick_timer.timeout.connect(self._on_tick); self._tick_timer.start(1000)
        self._sim_timer  = QTimer(self); self._sim_timer.timeout.connect(self._sim_event); self._sim_timer.start(4000)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        rl = QVBoxLayout(root); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)
        self.setCentralWidget(root)

        self._ctrl = ExamControlBar(); self._ctrl.command.connect(self._on_global_cmd)
        rl.addWidget(self._ctrl)
        rl.addWidget(self._build_stats_row())

        main_split = QSplitter(Qt.Horizontal); main_split.setHandleWidth(1)
        main_split.setChildrenCollapsible(False)

        # Left ──────────────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(0)
        ll.addWidget(self._build_filter_bar())
        self._table = StudentTable(self._students)
        self._table.student_selected.connect(self._on_student_selected)
        ll.addWidget(self._table, 1)
        main_split.addWidget(left)

        # Right tabs ────────────────────────────────────────────
        tabs = QTabWidget(); tabs.setMinimumWidth(360)
        tabs.setStyleSheet(tabs.styleSheet())
        self._detail = StudentDetailPanel()
        self._detail.action_requested.connect(self._on_action)
        tabs.addTab(self._detail, "Student Detail")
        tabs.addTab(self._build_incidents_tab(), "Incidents")
        tabs.addTab(self._build_blacklist_tab(), "Blacklist")
        main_split.addWidget(tabs)
        main_split.setSizes([1100, 440])

        vsplit = QSplitter(Qt.Vertical); vsplit.setHandleWidth(1)
        vsplit.addWidget(main_split)
        self._log_widget = ActivityLog()
        vsplit.addWidget(self._log_widget)
        vsplit.setSizes([780, 130])
        rl.addWidget(vsplit, 1)

        self._status = QStatusBar(); self.setStatusBar(self._status)
        self._status.setStyleSheet(f"background: {M['surface_container_low']}; color: {M['on_surface_variant']};")
        self._status.showMessage(f"Ready  ·  {len(self._students)} students loaded  ·  Simulated session")

        # MD3 Snackbar — floats over the central widget
        self._snackbar = MD3Snackbar(root)
        self._snackbar.raise_()

    def _build_stats_row(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {M['surface_container']};")
        lay = QHBoxLayout(w); lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(10)
        self._stats: dict[str, StatCard] = {}
        # (label, icon,  fg,                  container)
        defs = [
            ("Connected",    "🔗", M["primary"],            M["primary_container"]),
            ("Running",      "▶",  M["primary"],            M["primary_container"]),
            ("Paused",       "⏸",  M["outline"],            M["surface_container_high"]),
            ("Violations",   "⚠",  M["primary"],            M["outline_variant"]),
            ("Disconnected", "○",  M["outline_variant"],    M["surface_container"]),
            ("Submitted",    "✓",  M["on_surface_variant"], M["surface_container_high"]),
            ("Waiting",      "…",  M["on_secondary_container"], M["secondary_container"]),
        ]
        for key, icon, fg, bg in defs:
            card = StatCard(key, "0", fg, bg, icon)
            self._stats[key] = card; lay.addWidget(card, 1)
        return w

    def _build_filter_bar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {M['surface_container_high']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 10, 16, 8); lay.setSpacing(8)

        # Search + sort row
        top_row = QHBoxLayout(); top_row.setSpacing(8)
        self._search_box = QLineEdit(); self._search_box.setPlaceholderText("Search by name, login, lab…")
        self._search_box.setFixedHeight(40); self._search_box.textChanged.connect(self._on_search)

        sort_label = _label("Sort:", "label_large", M["on_surface_variant"])
        self._sort_options = ["Default", "Name A–Z", "Risk ↑", "Remaining ↑", "State"]
        self._sort_idx = 0
        self._sort_combo = QComboBox()
        self._sort_combo.addItems(self._sort_options)
        self._sort_combo.setFixedHeight(36)
        self._sort_combo.setCursor(Qt.PointingHandCursor)
        self._sort_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
                color: {M['primary']};
                border: none;
                border-radius: {SHAPE['small']}px;
                padding: 4px 16px;
                font-size: 13px; font-weight: 500;
            }}
            QComboBox:hover {{ background-color: {M['surface_container']}; }}
            QComboBox::drop-down {{ border: none; width: 0px; }}
            QComboBox QAbstractItemView {{
                background: {M['surface_container_highest']};
                border: none;
                color: {M['on_surface']};
                selection-background-color: {M['primary_container']};
                outline: none;
            }}
        """)
        self._sort_combo.currentIndexChanged.connect(self._cycle_sort)

        self._count_lbl = _label("50 / 50", "body_medium", M["on_surface_variant"])
        top_row.addWidget(self._search_box, 1)
        top_row.addWidget(sort_label); top_row.addWidget(self._sort_combo)
        top_row.addWidget(self._count_lbl)
        lay.addLayout(top_row)

        # Filter chips row
        chip_row = QHBoxLayout(); chip_row.setSpacing(6)
        chip_row.addWidget(_label("Filter:", "label_medium", M["on_surface_variant"]))
        self._chips: dict[str, FilterChip] = {}
        chip_defs = [
            ("All", "All"), ("Running", "running"), ("Paused", "admin_paused"),
            ("Violation", "violation_paused"), ("Disconnected", "disconnected_paused"),
            ("Submitted", "submitted"), ("Banned", "banned"),
        ]
        for chip_label, chip_key in chip_defs:
            chip = FilterChip(chip_label)
            if chip_key == "All": chip.setChecked(True)
            chip.clicked.connect(lambda checked, k=chip_key, c=chip: self._on_chip(k, c))
            self._chips[chip_key] = chip
            chip_row.addWidget(chip)
        chip_row.addStretch()
        lay.addLayout(chip_row)
        return w

    def _build_incidents_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)
        hdr_row = QHBoxLayout()
        hdr_row.addWidget(_label("All Incidents", "title_medium", M["on_surface_variant"]))
        hdr_row.addStretch()
        clr_btn = btn_text("Clear Resolved", M["outline"])
        clr_btn.clicked.connect(lambda: None); hdr_row.addWidget(clr_btn)
        lay.addLayout(hdr_row); lay.addWidget(_divider())

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self._inc_cont = QWidget()
        self._inc_vbox = QVBoxLayout(self._inc_cont)
        self._inc_vbox.setSpacing(8); self._inc_vbox.setContentsMargins(0, 0, 4, 0)
        self._inc_vbox.addStretch(); scroll.setWidget(self._inc_cont); lay.addWidget(scroll, 1)
        return w

    def _build_blacklist_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)
        lay.addWidget(_label("Process Blacklist", "title_medium", M["on_surface_variant"]))
        lay.addWidget(_label("Processes below trigger a violation if detected on any client.",
                             "body_medium", M["on_surface_variant"], wrap=True))
        lay.addWidget(_divider())

        self._bl_list = QListWidget()
        self._bl_list.setStyleSheet(f"""
            QListWidget {{
                background: {M['surface_container']};
                border: none;
                border-radius: {SHAPE['medium']}px;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                color: {M['primary']};
                font-weight: 500; font-size: 13px;
            }}
            QListWidget::item:selected {{ background: {M['primary_container']}; }}
        """)
        for proc in BANNED_PROCS:
            self._bl_list.addItem(QListWidgetItem(f"●  {proc}"))
        lay.addWidget(self._bl_list, 1)

        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self._bl_input = QLineEdit(); self._bl_input.setPlaceholderText("Add process (e.g. zoom.exe)")
        self._bl_input.setFixedHeight(36)
        add_btn = btn_tonal("Add", M["primary_container"], M["primary"])
        add_btn.setFixedHeight(36); add_btn.clicked.connect(self._add_blacklist)
        rem_btn = btn_outlined("Remove Selected", M["outline"]); rem_btn.setFixedHeight(36)
        rem_btn.clicked.connect(self._remove_blacklist)
        add_row.addWidget(self._bl_input, 1); add_row.addWidget(add_btn); add_row.addWidget(rem_btn)
        lay.addLayout(add_row)

        push_btn = btn_filled("📡  Push Blacklist to All Clients", M["primary"], M["on_primary"])
        push_btn.setFixedHeight(44)
        push_btn.clicked.connect(lambda: self._log("Blacklist pushed to all connected clients.", M["primary"]))
        lay.addWidget(push_btn)
        return w

    # ── State refresh ─────────────────────────────────────────────────────────

    def _refresh_stats(self):
        s = self._students
        self._stats["Connected"].set_value(str(sum(1 for x in s if x.connected)))
        self._stats["Running"].set_value(str(sum(1 for x in s if x.session_state == "running")))
        self._stats["Paused"].set_value(str(sum(1 for x in s if x.session_state in ("admin_paused","disconnected_paused"))))
        self._stats["Violations"].set_value(str(sum(1 for x in s if x.session_state == "violation_paused")))
        self._stats["Disconnected"].set_value(str(sum(1 for x in s if x.session_state == "disconnected_paused")))
        self._stats["Submitted"].set_value(str(sum(1 for x in s if x.session_state in ("submitted","awaiting_submission"))))
        self._stats["Waiting"].set_value(str(sum(1 for x in s if x.session_state == "waiting")))

    def _sorted_students(self) -> list[Student]:
        s = list(self._students)
        sort = self._sort_options[self._sort_idx]
        if   sort == "Name A–Z":   s.sort(key=lambda x: x.full_name)
        elif sort == "Risk ↑":     s.sort(key=lambda x: -x.risk_score)
        elif sort == "Remaining ↑":s.sort(key=lambda x: x.remaining_s)
        elif sort == "State":
            order = ["violation_paused","admin_paused","disconnected_paused",
                     "running","awaiting_submission","waiting","submitted","banned"]
            s.sort(key=lambda x: order.index(x.session_state) if x.session_state in order else 99)
        return s

    def _populate_table(self, *_):
        n = self._table.populate(self._sorted_students(), self._search, self._state_flt)
        self._count_lbl.setText(f"{n} / {len(self._students)}")

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_student_selected(self, student: Student):
        self._selected = student; self._detail.load(student)

    def _on_search(self, text: str):
        self._search = text; self._populate_table()

    def _on_chip(self, key: str, clicked_chip: FilterChip):
        # Deselect all, then select clicked
        for k, c in self._chips.items():
            if c is not clicked_chip:
                c.blockSignals(True); c.setChecked(False); c.blockSignals(False)
                c.setText(c._text); c._update_style()
        self._state_flt = key if clicked_chip.isChecked() else "All"
        if not clicked_chip.isChecked():
            self._chips["All"].blockSignals(True); self._chips["All"].setChecked(True)
            self._chips["All"].blockSignals(False); self._chips["All"].setText("✓  All")
            self._chips["All"]._update_style()
            self._state_flt = "All"
        self._populate_table()

    def _cycle_sort(self, index: int = -1):
        if index >= 0:
            self._sort_idx = index
        self._populate_table()

    def _on_global_cmd(self, cmd: str):
        if cmd == "start_exam":
            for st in self._students:
                if st.session_state == "waiting" and st.connected:
                    st.session_state = "running"; st.last_action = "Started"
            n = sum(1 for s in self._students if s.session_state == 'running')
            self._populate_table(); self._refresh_stats()
            self._snackbar.show_message(f"Exam started — {n} students now running", duration_ms=5000)
            self._log(f"▶  Exam started — {n} students running.", M["primary"])
        elif cmd == "finish_exam":
            for st in self._students:
                if st.session_state in ("running","admin_paused","violation_paused"):
                    st.session_state = "awaiting_submission"; st.last_action = "Exam ended by server"
            self._populate_table(); self._refresh_stats()
            self._snackbar.show_message("Exam finished — students awaiting submission", duration_ms=5000)
            self._log("⏹  Exam finished — all students moved to Awaiting File.", M["on_surface_variant"])
        elif cmd == "pause_all":
            n = sum(1 for s in self._students if s.session_state == "running")
            for st in self._students:
                if st.session_state == "running":
                    st.session_state = "admin_paused"; st.admin_paused = True; st.last_action = "Global pause"
            self._populate_table(); self._refresh_stats()
            self._snackbar.show_message(f"Paused {n} students")
            self._log("⏸  All running students paused.", M["outline"])
        elif cmd == "savescreen_all":
            n = sum(1 for s in self._students if s.connected)
            self._snackbar.show_message(f"📷  Savescreen sent to {n} clients")
            self._log(f"📷  Savescreen sent to {n} clients.", M["on_surface_variant"])

    def _on_action(self, action: str, student: Optional[Student]):
        if not student: return
        st = student

        # ── Destructive actions get an MD3 Confirm Dialog ──
        if action == "kick":
            dlg = ConfirmDialog(
                "Kick Student",
                f"Forcibly disconnect {st.full_name}?\n"
                f"They will appear as Disconnected and can reconnect.",
                confirm_label="Kick", destructive=True, parent=self,
            )
            if dlg.exec() != QDialog.Accepted: return
            st.kick_count += 1; st.connected = False
            if st.session_state == "running": st.session_state = "disconnected_paused"
            st.last_action = "Kicked"
            self._snackbar.show_message(f"Kicked {st.full_name} (#{st.kick_count})")
            self._log(f"👢  Kicked: {st.full_name} (#{st.kick_count})", M["outline"])

        elif action == "ban":
            dlg = ConfirmDialog(
                "Ban Student",
                f"Permanently ban {st.full_name}?\n"
                f"They will be disconnected and cannot rejoin.",
                confirm_label="Ban", destructive=True, parent=self,
            )
            if dlg.exec() != QDialog.Accepted: return
            st.session_state = "banned"; st.connected = False; st.last_action = "Banned"
            self._snackbar.show_message(f"Banned {st.full_name}",
                                        action_label="Undo",
                                        action_cb=lambda: self._undo_ban(st))
            self._log(f"🚫  Banned: {st.full_name}", M["on_surface"])

        elif action == "pause_exam" and st.session_state == "running":
            st.session_state = "admin_paused"; st.admin_paused = True; st.last_action = "Admin paused"
            self._snackbar.show_message(f"Paused {st.full_name}")
            self._log(f"⏸  Paused: {st.full_name}", M["outline"])

        elif action == "resume_exam" and st.session_state in ("admin_paused","disconnected_paused"):
            st.session_state = "running"; st.admin_paused = False; st.connected = True; st.last_action = "Resumed"
            self._snackbar.show_message(f"Resumed {st.full_name}")
            self._log(f"▶  Resumed: {st.full_name}", M["primary"])

        elif action == "add_time":
            st.extra_s += 300; st.last_action = "+5 min granted"
            self._snackbar.show_message(f"+5 min added for {st.full_name}  (total extra: {st.extra_s // 60}m)")
            self._log(f"⏱  +5 min added for {st.full_name}  (total extra: {st.extra_s // 60}m)", M["primary"])

        elif action == "forgive_violation" and st.session_state == "violation_paused":
            st.session_state = "running"; st.last_action = "Violation forgiven"
            for inc in st.incidents:
                if inc.status == "opened": inc.status = "resolved"
            self._snackbar.show_message(f"Violation cleared for {st.full_name}")
            self._log(f"✓  Forgiven: {st.full_name}", M["primary"])

        elif action in ("savescreen", "get_processes"):
            label = "📷  Save Screen" if action == "savescreen" else "📋  Get Processes"
            self._snackbar.show_message(f"{label} → {st.full_name}")
            self._log(f"{label} → {st.full_name}", M["on_surface_variant"])
            return

        self._table.refresh_row(st); self._detail.load(st); self._refresh_stats()

    def _undo_ban(self, st: Student):
        if st.session_state == "banned":
            st.session_state = "disconnected_paused"; st.last_action = "Ban reversed"
            self._table.refresh_row(st)
            if self._selected and self._selected.login_id == st.login_id:
                self._detail.load(st)
            self._refresh_stats()
            self._log(f"↩  Ban reversed for {st.full_name}", M["primary"])

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _on_tick(self):
        self._ctrl.tick()
        if self._ctrl.phase != "running": return
        for st in self._students:
            if st.session_state == "running":
                st.time_spent_s += 1
                if st.remaining_s == 0:
                    st.session_state = "awaiting_submission"; st.last_action = "Time expired"
                    self._log(f"⏰  Time expired: {st.full_name}", M["outline"])
        self._populate_table()
        if self._selected: self._detail.refresh_timer(self._selected)
        self._refresh_stats()
        self._sim_tick += 1
        if self._sim_tick % 10 == 0:
            self._status.showMessage(
                f"Live  ·  {sum(1 for s in self._students if s.connected)} connected  ·  "
                f"{sum(1 for s in self._students if s.session_state == 'running')} running  ·  "
                f"{datetime.datetime.now().strftime('%H:%M:%S')}"
            )

    # ── Simulation ─────────────────────────────────────────────────────────────

    def _sim_event(self):
        if self._ctrl.phase != "running": return
        running = [s for s in self._students if s.session_state == "running"]
        if not running: return
        roll = random.random()
        if roll < 0.12:
            st = random.choice(running)
            st.session_state = "disconnected_paused"; st.connected = False; st.last_action = "Disconnected"
            self._log(f"⚡  Disconnected: {st.full_name}", M["on_surface_variant"])
            self._table.refresh_row(st)
            if self._selected and self._selected.login_id == st.login_id: self._detail.load(st)
        elif roll < 0.22:
            st = random.choice(running)
            proc = random.choice(BANNED_PROCS); pid = random.randint(1000, 9999)
            inc = Incident(id=f"inc-{st.login_id}-{len(st.incidents):02d}", rule_id="process_blacklist",
                           severity="violation", summary=f"{proc} detected",
                           status="opened", pid=pid, proc_name=proc, at=datetime.datetime.now())
            st.incidents.append(inc)
            st.session_state = "violation_paused"; st.blacklist_count += 1
            st.last_proc = proc; st.last_action = f"Violation: {proc}"
            self._log(f"🚨  VIOLATION  {st.full_name} — {proc} (pid {pid})", M["primary"])
            self._push_incident_card(st, inc)
            self._table.refresh_row(st)
            if self._selected and self._selected.login_id == st.login_id: self._detail.load(st)
        elif roll < 0.30:
            discon = [s for s in self._students if s.session_state == "disconnected_paused"]
            if discon:
                st = random.choice(discon)
                st.session_state = "running"; st.connected = True; st.last_action = "Reconnected"
                self._log(f"↩  Reconnected: {st.full_name}", M["primary"])
                self._table.refresh_row(st)
        elif roll < 0.36:
            awaiting = [s for s in self._students if s.session_state == "awaiting_submission"]
            if awaiting:
                st = random.choice(awaiting)
                st.session_state = "submitted"; st.submission_name = f"{st.login_id}_solution.zip"
                st.submitted_at = datetime.datetime.now().strftime("%H:%M:%S"); st.last_action = "Submitted file"
                self._log(f"✓  Submitted: {st.full_name}  →  {st.submission_name}", M["on_secondary_container"])
                self._table.refresh_row(st)
        self._refresh_stats()

    def _push_incident_card(self, student: Student, inc: Incident):
        sc = M["primary"]; sc_bg = M["outline_variant"]
        f = QFrame()
        f.setStyleSheet(f"QFrame {{ background-color: {sc_bg}; border-radius: {SHAPE['medium']}px; border: none; }}")
        lay = QVBoxLayout(f); lay.setContentsMargins(14, 10, 14, 10); lay.setSpacing(4)
        row1 = QHBoxLayout()
        row1.addWidget(_label(f"● {inc.severity.upper()}", "label_medium", sc))
        row1.addWidget(_label(f"{student.full_name}  ({student.login_id})", "body_medium", M["on_surface"]))
        row1.addStretch()
        row1.addWidget(_label(inc.at.strftime("%H:%M:%S"), "body_small", M["on_surface_variant"]))
        row2 = _label(f"{inc.summary}  ·  pid {inc.pid}  ·  {student.lab} / {student.computer}",
                      "body_small", M["on_surface"])
        lay.addLayout(row1); lay.addWidget(row2)
        cnt = self._inc_vbox.count()
        self._inc_vbox.insertWidget(cnt - 1, f)
        QTimer.singleShot(50, lambda: self._inc_cont.update())

    def _add_blacklist(self):
        t = self._bl_input.text().strip()
        if t: self._bl_list.addItem(QListWidgetItem(f"●  {t}")); self._bl_input.clear()
        self._log(f"Added to blacklist: {t}", M["primary"])

    def _remove_blacklist(self):
        row = self._bl_list.currentRow()
        if row >= 0:
            it = self._bl_list.takeItem(row)
            self._log(f"Removed from blacklist: {it.text()}", M["on_surface_variant"])

    def _log(self, msg: str, color: str = M["on_surface"]):
        self._log_widget.log(msg, color)


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Exam Proctor Dashboard")

    # Apply MD3 QPalette (dark scheme)
    pal = QPalette()
    pal.setColor(QPalette.Window,            QColor(M["background"]))
    pal.setColor(QPalette.WindowText,        QColor(M["on_surface"]))
    pal.setColor(QPalette.Base,              QColor(M["surface_container_low"]))
    pal.setColor(QPalette.AlternateBase,     QColor(M["surface_container"]))
    pal.setColor(QPalette.Text,              QColor(M["on_surface"]))
    pal.setColor(QPalette.Button,            QColor(M["surface_container_high"]))
    pal.setColor(QPalette.ButtonText,        QColor(M["on_surface"]))
    pal.setColor(QPalette.Highlight,         QColor(M["primary"]))
    pal.setColor(QPalette.HighlightedText,   QColor(M["on_primary"]))
    pal.setColor(QPalette.PlaceholderText,   QColor(M["on_surface_variant"]))
    pal.setColor(QPalette.ToolTipBase,       QColor(M["surface_container_high"]))
    pal.setColor(QPalette.ToolTipText,       QColor(M["on_surface"]))
    pal.setColor(QPalette.BrightText,        QColor(M["primary"]))
    app.setPalette(pal)
    app.setStyleSheet(MD3_STYLE)

    try:
        win = ProctorDashboard()
        win.show()
        code = app.exec()
    except Exception:
        import traceback
        traceback.print_exc()
        code = 1
    # Qt crash-on-exit (0xC000001D) on some Windows+PySide6 versions is harmless;
    # the application ran successfully if the window was shown.
    sys.exit(code)


if __name__ == "__main__":
    main()
