"""
Translator Pro — Smooth Hover Animation Effects.

Provides real-time, buttery smooth color-changing hover animations using
QVariantAnimation for text boxes, action buttons, volume/listen buttons,
dropdowns, and toolbars.
"""
from __future__ import annotations

from typing import Optional, List
from PySide6.QtCore import QEvent, QObject, QVariantAnimation, QEasingCurve, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget, QPushButton, QPlainTextEdit, QComboBox
import qtawesome as qta


# Global registry of active animated controllers so theme changes update instantly
_ACTIVE_CONTROLLERS: List[AnimatedWidgetController] = []


def notify_theme_changed(is_dark: bool) -> None:
    """Notify all registered animation controllers that the theme has changed."""
    for controller in list(_ACTIVE_CONTROLLERS):
        try:
            controller.set_dark_mode(is_dark)
        except Exception:
            pass


class AnimatedWidgetController(QObject):
    """Base controller providing smooth QVariantAnimation on hover enter / leave."""

    def __init__(self, widget: QWidget, duration_ms: int = 180, is_dark: bool = True):
        super().__init__(widget)
        self.widget = widget
        self.duration_ms = duration_ms
        self.is_dark = is_dark
        self.is_hovered = False

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(duration_ms)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_animation_frame)

        self.widget.installEventFilter(self)
        _ACTIVE_CONTROLLERS.append(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.widget:
            if event.type() == QEvent.Type.Enter:
                self.is_hovered = True
                self._start_transition(forward=True)
            elif event.type() == QEvent.Type.Leave:
                self.is_hovered = False
                self._start_transition(forward=False)
        return super().eventFilter(watched, event)

    def set_dark_mode(self, is_dark: bool) -> None:
        self.is_dark = is_dark
        self._anim.stop()
        self.apply_state(0.0 if not self.is_hovered else 1.0)

    def _start_transition(self, forward: bool) -> None:
        self._anim.stop()
        start_val = self._anim.currentValue() if self._anim.state() == QVariantAnimation.State.Running else (0.0 if forward else 1.0)
        end_val = 1.0 if forward else 0.0
        self._anim.setStartValue(start_val)
        self._anim.setEndValue(end_val)
        self._anim.start()

    def _on_animation_frame(self, value: float) -> None:
        self.apply_state(value)

    def apply_state(self, progress: float) -> None:
        """Subclasses override to apply color interpolation based on 0.0 -> 1.0 progress."""
        pass


def _interpolate_color(c1: QColor, c2: QColor, t: float) -> QColor:
    """Linear interpolation between two QColors."""
    r = int(c1.red() + (c2.red() - c1.red()) * t)
    g = int(c1.green() + (c2.green() - c1.green()) * t)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
    a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * t)
    return QColor(r, g, b, a)


class AnimatedTextBox(AnimatedWidgetController):
    """
    Smooth color-changing hover animation for QPlainTextEdit text boxes.
    Dark Mode: Transitions border from dark subtle (#242426) to pure white (#FFFFFF).
    Light Mode: Transitions border from soft (#E4E4E7) to pure black (#000000).
    """

    def apply_state(self, progress: float) -> None:
        if self.is_dark:
            # Dark mode: normal -> white
            border_norm = QColor(36, 36, 38)
            border_hov = QColor(255, 255, 255)
            bg_norm = QColor(10, 10, 10)
            bg_hov = QColor(16, 16, 18)
            text_color = "#FFFFFF"
            placeholder_color = "#71717A"
        else:
            # Light mode: normal -> black
            border_norm = QColor(228, 228, 231)
            border_hov = QColor(0, 0, 0)
            bg_norm = QColor(255, 255, 255)
            bg_hov = QColor(255, 255, 255)
            text_color = "#000000"
            placeholder_color = "#71717A"

        solid_qcolor = QColor(255, 255, 255) if self.is_dark else QColor(0, 0, 0)
        palette = self.widget.palette()
        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
            palette.setColor(group, QPalette.ColorRole.Text, solid_qcolor)
            palette.setColor(group, QPalette.ColorRole.WindowText, solid_qcolor)
        self.widget.setPalette(palette)

        current_border = _interpolate_color(border_norm, border_hov, progress)
        current_bg = _interpolate_color(bg_norm, bg_hov, progress)

        self.widget.setStyleSheet(f"""
            background-color: {current_bg.name()};
            color: {text_color};
            border: 1.5px solid {current_border.name()};
            border-radius: 12px;
            padding: 14px;
            font-size: 15px;
            font-weight: 500;
            selection-background-color: {'#27272A' if self.is_dark else '#000000'};
            selection-color: #FFFFFF;
        """)


class AnimatedIconButton(AnimatedWidgetController):
    """
    Smooth color-changing hover animation for icon buttons (Volume, Copy, Clear, Layout).
    Dark Mode: Animates icon from #71717A to bright pure white #FFFFFF with soft glow background.
    Light Mode: Animates icon from #71717A to pure black #000000 with soft background.
    """

    def __init__(self, btn: QPushButton, icon_name: str, duration_ms: int = 180, is_dark: bool = True):
        self.icon_name = icon_name
        super().__init__(btn, duration_ms, is_dark)
        self.apply_state(0.0)

    def apply_state(self, progress: float) -> None:
        btn: QPushButton = self.widget
        if self.is_dark:
            icon_norm = QColor(113, 113, 122)   # #71717A
            icon_hov = QColor(255, 255, 255)    # Pure white #FFFFFF
            bg_norm = QColor(0, 0, 0, 0)
            bg_hov = QColor(24, 24, 27, 255)    # #18181B
            border_norm = QColor(0, 0, 0, 0)
            border_hov = QColor(63, 63, 70, 255)
        else:
            icon_norm = QColor(113, 113, 122)   # #71717A
            icon_hov = QColor(0, 0, 0)          # Pure black #000000
            bg_norm = QColor(0, 0, 0, 0)
            bg_hov = QColor(244, 244, 245, 255) # #F4F4F5
            border_norm = QColor(0, 0, 0, 0)
            border_hov = QColor(212, 212, 216, 255)

        cur_icon = _interpolate_color(icon_norm, icon_hov, progress)
        cur_bg = _interpolate_color(bg_norm, bg_hov, progress)
        cur_border = _interpolate_color(border_norm, border_hov, progress)

        btn.setIcon(qta.icon(self.icon_name, color=cur_icon.name()))
        btn.setStyleSheet(f"""
            QPushButton#iconBtn {{
                background-color: rgba({cur_bg.red()}, {cur_bg.green()}, {cur_bg.blue()}, {cur_bg.alpha()});
                border: 1px solid rgba({cur_border.red()}, {cur_border.green()}, {cur_border.blue()}, {cur_border.alpha()});
                border-radius: 6px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }}
        """)


class AnimatedSwapButton(AnimatedWidgetController):
    """
    Smooth color-changing hover animation for Swap Button.
    Dark Mode: Animates border to #FFFFFF, icon to #FFFFFF, background to #1E1E22.
    Light Mode: Animates border to #000000, icon to #000000, background to #F4F4F5.
    """

    def __init__(self, btn: QPushButton, duration_ms: int = 180, is_dark: bool = True):
        super().__init__(btn, duration_ms, is_dark)
        self.apply_state(0.0)

    def apply_state(self, progress: float) -> None:
        btn: QPushButton = self.widget
        if self.is_dark:
            icon_norm = QColor(148, 163, 184)
            icon_hov = QColor(255, 255, 255)
            bg_norm = QColor(13, 13, 13)
            bg_hov = QColor(28, 28, 32)
            border_norm = QColor(39, 39, 42)
            border_hov = QColor(255, 255, 255)
        else:
            icon_norm = QColor(100, 116, 139)
            icon_hov = QColor(0, 0, 0)
            bg_norm = QColor(255, 255, 255)
            bg_hov = QColor(244, 244, 245)
            border_norm = QColor(228, 228, 231)
            border_hov = QColor(0, 0, 0)

        cur_icon = _interpolate_color(icon_norm, icon_hov, progress)
        cur_bg = _interpolate_color(bg_norm, bg_hov, progress)
        cur_border = _interpolate_color(border_norm, border_hov, progress)

        btn.setIcon(qta.icon("fa5s.exchange-alt", color=cur_icon.name()))
        btn.setStyleSheet(f"""
            QPushButton#swapBtn {{
                background-color: {cur_bg.name()};
                border: 1.5px solid {cur_border.name()};
                border-radius: 20px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }}
        """)


class AnimatedTranslateButton(AnimatedWidgetController):
    """
    Smooth color-changing hover animation for the Translate Button.
    Dark Mode: Pure white base, animates on hover to a glowing high-contrast hover.
    Light Mode: Pure black base, animates on hover to sleek zinc-black hover.
    """

    def apply_state(self, progress: float) -> None:
        btn: QPushButton = self.widget
        if not btn.isEnabled():
            return

        if self.is_dark:
            # Base white -> bright hover
            bg_norm = QColor(255, 255, 255)
            bg_hov = QColor(240, 240, 242)
            border_norm = QColor(255, 255, 255)
            border_hov = QColor(255, 255, 255)
            text_color = "#000000"
            icon_color = "#000000"
        else:
            # Base black -> dark zinc hover
            bg_norm = QColor(0, 0, 0)
            bg_hov = QColor(39, 39, 42)
            border_norm = QColor(0, 0, 0)
            border_hov = QColor(0, 0, 0)
            text_color = "#FFFFFF"
            icon_color = "#FFFFFF"

        cur_bg = _interpolate_color(bg_norm, bg_hov, progress)
        cur_border = _interpolate_color(border_norm, border_hov, progress)

        btn.setIcon(qta.icon("fa5s.language", color=icon_color))
        btn.setStyleSheet(f"""
            QPushButton#translateBtn {{
                background-color: {cur_bg.name()};
                color: {text_color};
                border: 1px solid {cur_border.name()};
                border-radius: 10px;
                padding: 10px 28px;
                font-size: 14px;
                font-weight: 700;
            }}
        """)


class AnimatedComboBox(AnimatedWidgetController):
    """
    Smooth color-changing hover animation for Language Selector ComboBox.
    Dark Mode: Animates border to pure white #FFFFFF on hover.
    Light Mode: Animates border to pure black #000000 on hover.
    """

    def apply_state(self, progress: float) -> None:
        combo: QComboBox = self.widget
        if self.is_dark:
            border_norm = QColor(39, 39, 42)
            border_hov = QColor(255, 255, 255)
            bg_norm = QColor(13, 13, 13)
            bg_hov = QColor(18, 18, 20)
            text_color = "#FFFFFF"
            arrow_icon = "assets/icons/chevron-down-dark.svg"
            item_bg = "#0D0D0D"
            item_sel = "#27272A"
        else:
            border_norm = QColor(228, 228, 231)
            border_hov = QColor(0, 0, 0)
            bg_norm = QColor(255, 255, 255)
            bg_hov = QColor(250, 250, 250)
            text_color = "#09090B"
            arrow_icon = "assets/icons/chevron-down-light.svg"
            item_bg = "#FFFFFF"
            item_sel = "#09090B"

        cur_border = _interpolate_color(border_norm, border_hov, progress)
        cur_bg = _interpolate_color(bg_norm, bg_hov, progress)

        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {cur_bg.name()};
                color: {text_color};
                border: 1.5px solid {cur_border.name()};
                border-radius: 8px;
                padding: 8px 30px 8px 14px;
                font-size: 13px;
                font-weight: 600;
                min-width: 180px;
            }}
            QComboBox:focus {{
                border-color: {'#FFFFFF' if self.is_dark else '#000000'};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_icon}");
                width: 13px;
                height: 13px;
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {item_bg};
                color: {text_color};
                border: 1px solid {'#27272A' if self.is_dark else '#E4E4E7'};
                border-radius: 8px;
                selection-background-color: {item_sel};
                selection-color: #FFFFFF;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                border-radius: 4px;
            }}
            QComboBox QLineEdit {{
                background: transparent;
                color: {text_color};
                border: none;
                padding: 0;
                font-size: 13px;
                font-weight: 600;
            }}
        """)
