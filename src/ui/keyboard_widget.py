"""
Keyboard Layout Widget

Renders the physical keyboard layout for the current (or selected) layer,
matching the style shown in Vial's Keymap tab:
  - Layer selector tabs across the top (active layer highlighted)
  - Each key drawn as a rounded rectangle with its label
  - Hovering a key shows a tooltip with the full keycode description
  - Clicking a layer tab switches the displayed layer
  - Zoom in/out scales the entire layout

Classes:
    KeyboardWidget: Main widget containing the layer tabs and key canvas
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import (
    QPoint, QRect, QRectF, QSize, Qt, pyqtSignal
)
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPen, QBrush
)
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QToolTip, QVBoxLayout, QWidget
)

from src.utils.keycode_labels import keycode_to_description, keycode_to_label

# ---------------------------------------------------------------------------
# Colours (match Vial's dark theme)
# ---------------------------------------------------------------------------
COLOR_BG           = QColor(0x2B, 0x2B, 0x2B)
COLOR_KEY_NORMAL   = QColor(0x3C, 0x3F, 0x41)
COLOR_KEY_ACTIVE   = QColor(0x4C, 0x4F, 0x51)   # hover
COLOR_KEY_BORDER   = QColor(0x5A, 0x5A, 0x5A)
COLOR_KEY_TEXT     = QColor(0xD4, 0xD4, 0xD4)
COLOR_TAB_ACTIVE   = QColor(0x4A, 0x88, 0xC7)
COLOR_TAB_INACTIVE = QColor(0x3C, 0x3F, 0x41)
COLOR_TAB_TEXT     = QColor(0xE8, 0xE8, 0xE8)
COLOR_CANVAS_BG    = QColor(0x2B, 0x2B, 0x2B)

# One "key unit" in pixels at zoom 1.0
KEY_UNIT = 54
KEY_GAP  = 4
KEY_RADIUS = 6


class _KeyCanvasWidget(QWidget):
    """
    Internal widget that draws all keys for a single layer.
    Emits layer_tab_clicked(int) when a layer button is pressed.
    """

    layer_tab_clicked = pyqtSignal(int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._key_defs: List[Dict[str, Any]] = []      # from extract_layout_keys()
        self._keycodes: List[int]            = []      # one per key_def entry
        self._zoom: float                    = 1.0
        self._hovered_idx: int               = -1
        self._key_rects: List[QRectF]        = []      # cached screen rects
        self._offset_x: float                = 16.0
        self._offset_y: float                = 16.0
        self.setMinimumSize(400, 200)
        self.setStyleSheet(f"background-color: {COLOR_CANVAS_BG.name()};")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_layout(self, key_defs: List[Dict[str, Any]]) -> None:
        """Set the physical key definitions (position / size)."""
        self._key_defs = key_defs
        self._recompute_rects()
        self.update()

    def set_keycodes(self, keycodes: List[int]) -> None:
        """Set the keycode list for the currently displayed layer."""
        self._keycodes = keycodes
        self.update()

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.4, min(3.0, zoom))
        self._recompute_rects()
        self.update()

    def get_zoom(self) -> float:
        return self._zoom

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _unit(self) -> float:
        return KEY_UNIT * self._zoom

    def _gap(self) -> float:
        return KEY_GAP * self._zoom

    def _recompute_rects(self) -> None:
        u = self._unit()
        g = self._gap()
        ox = self._offset_x
        oy = self._offset_y

        self._key_rects = []
        max_x = 0.0
        max_y = 0.0

        for key in self._key_defs:
            x = ox + key["x"] * (u + g)
            y = oy + key["y"] * (u + g)
            w = key["w"] * (u + g) - g
            h = key["h"] * (u + g) - g
            self._key_rects.append(QRectF(x, y, w, h))
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

        needed_w = int(max_x + self._offset_x) + 4
        needed_h = int(max_y + self._offset_y) + 4
        self.setMinimumSize(needed_w, needed_h)

    def _key_label(self, idx: int) -> str:
        if idx < len(self._keycodes):
            return keycode_to_label(self._keycodes[idx])
        return ""

    def _key_description(self, idx: int) -> str:
        if idx < len(self._keycodes):
            return keycode_to_description(self._keycodes[idx])
        return ""

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        u = self._unit()
        font_size = max(7, int(10 * self._zoom))
        font = QFont("Segoe UI", font_size)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for idx, rect in enumerate(self._key_rects):
            is_hovered = idx == self._hovered_idx

            # Key background
            bg = COLOR_KEY_ACTIVE if is_hovered else COLOR_KEY_NORMAL
            painter.setBrush(QBrush(bg))
            painter.setPen(QPen(COLOR_KEY_BORDER, 1.2))
            painter.drawRoundedRect(rect, KEY_RADIUS, KEY_RADIUS)

            # Key label
            label = self._key_label(idx)
            if label and label != "▽":
                painter.setPen(QPen(COLOR_KEY_TEXT))
                # Fit multi-word labels by reducing font if needed
                draw_rect = rect.adjusted(3, 3, -3, -3)
                painter.drawText(
                    draw_rect,
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                    label,
                )

        painter.end()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position() if hasattr(event, "position") else event.pos()
        px = pos.x()
        py = pos.y()

        new_hovered = -1
        for idx, rect in enumerate(self._key_rects):
            if rect.contains(px, py):
                new_hovered = idx
                break

        if new_hovered != self._hovered_idx:
            self._hovered_idx = new_hovered
            self.update()

        if new_hovered >= 0:
            desc = self._key_description(new_hovered)
            if desc:
                QToolTip.showText(event.globalPosition().toPoint(), desc, self)
        else:
            QToolTip.hideText()

    def leaveEvent(self, event) -> None:
        self._hovered_idx = -1
        self.update()

    def sizeHint(self) -> QSize:
        if self._key_rects:
            max_x = max(r.right() for r in self._key_rects)
            max_y = max(r.bottom() for r in self._key_rects)
            return QSize(int(max_x + self._offset_x), int(max_y + self._offset_y))
        return QSize(600, 250)


class KeyboardWidget(QWidget):
    """
    Full keyboard layout widget with layer tabs and zoom controls.

    Signals:
        layer_selected(int): emitted when the user clicks a layer tab
    """

    layer_selected = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._num_layers    = 8
        self._active_layer  = 0          # layer currently active on keyboard
        self._displayed_layer = 0        # layer shown in the widget
        self._key_defs: List[Dict[str, Any]] = []
        self._all_keymaps: List[List[int]] = []   # [layer][key_index]
        self._tab_buttons: List[QPushButton] = []

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- top bar: "Layer" label + tabs + zoom buttons ---
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {COLOR_BG.name()};")
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(8, 6, 8, 6)
        top_layout.setSpacing(4)

        layer_label = QLabel("Layer")
        layer_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        top_layout.addWidget(layer_label)

        self._tabs_layout = QHBoxLayout()
        self._tabs_layout.setSpacing(3)
        top_layout.addLayout(self._tabs_layout)
        top_layout.addStretch()

        # Zoom buttons on the right
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(24, 24)
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.setStyleSheet(self._tab_btn_style(False, False))
        zoom_in_btn.clicked.connect(self._zoom_in)

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(24, 24)
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.setStyleSheet(self._tab_btn_style(False, False))
        zoom_out_btn.clicked.connect(self._zoom_out)

        top_layout.addWidget(zoom_in_btn)
        top_layout.addWidget(zoom_out_btn)

        top_bar.setLayout(top_layout)
        root.addWidget(top_bar)

        # --- scrollable canvas ---
        self._canvas = _KeyCanvasWidget()
        scroll = QScrollArea()
        scroll.setWidget(self._canvas)
        scroll.setWidgetResizable(False)
        scroll.setStyleSheet(f"background-color: {COLOR_CANVAS_BG.name()}; border: none;")
        root.addWidget(scroll, 1)

        self.setLayout(root)
        self._rebuild_tabs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_keyboard_data(
        self,
        key_defs: List[Dict[str, Any]],
        all_keymaps: List[List[int]],
        num_layers: int,
    ) -> None:
        """
        Load full keyboard data into the widget.

        Args:
            key_defs:     List of key position dicts from extract_layout_keys()
            all_keymaps:  [layer][key_index] → 16-bit keycode
            num_layers:   Total number of layers
        """
        self._key_defs     = key_defs
        self._all_keymaps  = all_keymaps
        self._num_layers   = num_layers
        self._canvas.set_layout(key_defs)
        self._rebuild_tabs()
        self._show_layer(self._active_layer)

    def set_active_layer(self, layer: int) -> None:
        """
        Update which layer is currently active on the keyboard.

        Only changes the displayed layer automatically on first activation
        or when the user hasn't manually selected a different tab.
        The active layer tab gets a distinct visual indicator regardless.
        """
        prev_active = self._active_layer
        self._active_layer = layer

        # Auto-follow the active layer only if the user hasn't manually
        # clicked a different tab (i.e. displayed == previous active layer)
        if self._displayed_layer == prev_active:
            self._displayed_layer = layer
            self._show_layer(layer)
        else:
            # Just update the tab highlights without changing the view
            self._update_tab_styles()

    def set_num_layers(self, n: int) -> None:
        self._num_layers = n
        self._rebuild_tabs()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_tabs(self) -> None:
        # Clear existing tabs
        while self._tabs_layout.count():
            item = self._tabs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tab_buttons.clear()

        for i in range(self._num_layers):
            btn = QPushButton(str(i))
            btn.setFixedSize(30, 24)
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_btn_style(
                i == self._displayed_layer,
                i == self._active_layer,
            ))
            btn.clicked.connect(lambda checked, layer=i: self._on_tab_clicked(layer))
            self._tabs_layout.addWidget(btn)
            self._tab_buttons.append(btn)

    def _update_tab_styles(self) -> None:
        for i, btn in enumerate(self._tab_buttons):
            is_displayed = (i == self._displayed_layer)
            is_active    = (i == self._active_layer)
            btn.setStyleSheet(self._tab_btn_style(is_displayed, is_active))
            btn.setChecked(is_displayed)

    def _show_layer(self, layer: int) -> None:
        self._displayed_layer = layer
        self._update_tab_styles()
        if layer < len(self._all_keymaps):
            self._canvas.set_keycodes(self._all_keymaps[layer])
        else:
            self._canvas.set_keycodes([])

    def _on_tab_clicked(self, layer: int) -> None:
        self._show_layer(layer)
        self.layer_selected.emit(layer)

    def _zoom_in(self) -> None:
        self._canvas.set_zoom(self._canvas.get_zoom() + 0.1)

    def _zoom_out(self) -> None:
        self._canvas.set_zoom(self._canvas.get_zoom() - 0.1)

    @staticmethod
    def _tab_btn_style(displayed: bool, active_kb: bool) -> str:
        """
        displayed  — this tab's layer is currently shown in the UI
        active_kb  — this layer is currently active on the physical keyboard
        """
        if displayed:
            bg     = COLOR_TAB_ACTIVE.name()
            border = COLOR_TAB_ACTIVE.name()
        else:
            bg     = COLOR_TAB_INACTIVE.name()
            border = "#777777" if active_kb else "#555555"

        # Active keyboard layer gets an underline indicator
        underline = "border-bottom: 2px solid #FFCC00;" if active_kb and not displayed else ""

        return (
            f"QPushButton {{"
            f"  background-color: {bg};"
            f"  color: {COLOR_TAB_TEXT.name()};"
            f"  border: 1px solid {border};"
            f"  border-radius: 3px;"
            f"  font-size: 11px;"
            f"  {underline}"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {COLOR_TAB_ACTIVE.name()};"
            f"}}"
        )
