"""
Layer Display Widget

This module provides a custom PyQt6 widget for displaying the current keyboard layer.
It supports zoom functionality, custom styling, and theming.

Classes:
    LayerDisplay: Custom widget for displaying current layer with zoom support
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPalette


class LayerDisplay(QWidget):
    """
    Custom widget for displaying the current keyboard layer.
    
    This widget shows the current layer number and name with support for:
    - Zoom functionality (adjustable display size)
    - Custom styling and theming
    - Smooth rendering with anti-aliasing
    
    Signals:
        zoom_changed: Emitted when zoom level changes
        clicked: Emitted when widget is clicked
    
    Attributes:
        current_layer: Current layer number (0-indexed)
        layer_name: Name of the current layer
        zoom_level: Current zoom level (1.0 = 100%)
    """
    
    # Signals
    zoom_changed = pyqtSignal(float)
    clicked = pyqtSignal()
    
    # Default styling
    DEFAULT_FONT_FAMILY = "Arial"
    DEFAULT_FONT_SIZE = 24
    DEFAULT_MIN_ZOOM = 0.5
    DEFAULT_MAX_ZOOM = 3.0
    DEFAULT_ZOOM_STEP = 0.1
    
    # Default colors
    DEFAULT_BG_COLOR = QColor(40, 44, 52)
    DEFAULT_TEXT_COLOR = QColor(220, 223, 228)
    DEFAULT_BORDER_COLOR = QColor(60, 64, 72)
    DEFAULT_ACCENT_COLOR = QColor(97, 175, 239)
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the LayerDisplay widget.
        
        Args:
            parent: Parent widget (optional)
            config: Configuration dictionary with display settings
        """
        super().__init__(parent)
        
        # Configuration
        self._config = config or {}
        
        # State
        self._current_layer = 0
        self._layer_name = "Base"
        self._zoom_level = 1.0
        
        # Styling
        self._font_family = self._config.get(
            "display", {}
        ).get("font_family", self.DEFAULT_FONT_FAMILY)
        self._font_size = self._config.get(
            "display", {}
        ).get("font_size", self.DEFAULT_FONT_SIZE)
        
        # Colors
        self._bg_color = self._parse_color(
            self._config.get("display", {}).get("bg_color"),
            self.DEFAULT_BG_COLOR
        )
        self._text_color = self._parse_color(
            self._config.get("display", {}).get("text_color"),
            self.DEFAULT_TEXT_COLOR
        )
        self._border_color = self._parse_color(
            self._config.get("display", {}).get("border_color"),
            self.DEFAULT_BORDER_COLOR
        )
        self._accent_color = self._parse_color(
            self._config.get("display", {}).get("accent_color"),
            self.DEFAULT_ACCENT_COLOR
        )
        
        # Setup UI
        self._setup_ui()
        self._apply_style()
        
        # Enable mouse tracking for click detection
        self.setMouseTracking(True)
    
    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Layer number label
        self._layer_number_label = QLabel("0")
        self._layer_number_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self._layer_number_label.setFont(
            QFont(self._font_family, int(self._font_size * 1.5), QFont.Weight.Bold)
        )
        
        # Layer name label
        self._layer_name_label = QLabel("Base")
        self._layer_name_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self._layer_name_label.setFont(
            QFont(self._font_family, int(self._font_size * 0.6))
        )
        
        # Add labels to layout
        layout.addWidget(self._layer_number_label)
        layout.addWidget(self._layer_name_label)
        
        # Set layout
        self.setLayout(layout)
    
    def _apply_style(self) -> None:
        """Apply styling to the widget."""
        # Update label colors
        self._layer_number_label.setStyleSheet(
            f"color: {self._text_color.name()};"
        )
        self._layer_name_label.setStyleSheet(
            f"color: {self._text_color.name()};"
        )
        
        # Update widget background
        self.setStyleSheet(
            f"""
            LayerDisplay {{
                background-color: {self._bg_color.name()};
                border: 2px solid {self._border_color.name()};
                border-radius: 8px;
            }}
            """
        )
        
        # Update font sizes based on zoom
        self._update_font_sizes()
    
    def _update_font_sizes(self) -> None:
        """Update font sizes based on current zoom level."""
        base_font_size = self._font_size * self._zoom_level
        
        self._layer_number_label.setFont(
            QFont(
                self._font_family,
                int(base_font_size * 1.5),
                QFont.Weight.Bold
            )
        )
        self._layer_name_label.setFont(
            QFont(
                self._font_family,
                int(base_font_size * 0.6)
            )
        )
    
    def _parse_color(
        self,
        color_value: Any,
        default: QColor
    ) -> QColor:
        """
        Parse color value from config.
        
        Args:
            color_value: Color value (hex string, tuple, or QColor)
            default: Default color if parsing fails
            
        Returns:
            QColor object
        """
        if color_value is None:
            return default
        
        if isinstance(color_value, QColor):
            return color_value
        
        if isinstance(color_value, str):
            # Parse hex color
            if color_value.startswith("#"):
                return QColor(color_value)
            # Parse named color
            return QColor(color_value)
        
        if isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
            # Parse RGB tuple
            return QColor(
                int(color_value[0]),
                int(color_value[1]),
                int(color_value[2])
            )
        
        return default
    
    def update_layer(self, layer: int, layer_name: str) -> None:
        """
        Update the displayed layer.
        
        Args:
            layer: Layer number (0-indexed)
            layer_name: Name of the layer
        """
        self._current_layer = layer
        self._layer_name = layer_name
        
        # Update labels
        self._layer_number_label.setText(str(layer))
        self._layer_name_label.setText(layer_name)
        
        # Trigger repaint
        self.update()
    
    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level.
        
        Args:
            zoom: Zoom level (0.5 to 3.0, where 1.0 = 100%)
        """
        # Clamp zoom level
        zoom = max(self.DEFAULT_MIN_ZOOM, min(self.DEFAULT_MAX_ZOOM, zoom))
        
        if self._zoom_level != zoom:
            self._zoom_level = zoom
            self._update_font_sizes()
            self.zoom_changed.emit(zoom)
            self.update()
    
    def zoom_in(self) -> None:
        """Increase zoom level."""
        self.set_zoom(self._zoom_level + self.DEFAULT_ZOOM_STEP)
    
    def zoom_out(self) -> None:
        """Decrease zoom level."""
        self.set_zoom(self._zoom_level - self.DEFAULT_ZOOM_STEP)
    
    def reset_zoom(self) -> None:
        """Reset zoom level to default (1.0)."""
        self.set_zoom(1.0)
    
    def get_zoom(self) -> float:
        """
        Get current zoom level.
        
        Returns:
            Current zoom level
        """
        return self._zoom_level
    
    def set_theme(
        self,
        bg_color: Optional[QColor] = None,
        text_color: Optional[QColor] = None,
        border_color: Optional[QColor] = None,
        accent_color: Optional[QColor] = None
    ) -> None:
        """
        Set the widget theme colors.
        
        Args:
            bg_color: Background color
            text_color: Text color
            border_color: Border color
            accent_color: Accent color
        """
        if bg_color is not None:
            self._bg_color = bg_color
        if text_color is not None:
            self._text_color = text_color
        if border_color is not None:
            self._border_color = border_color
        if accent_color is not None:
            self._accent_color = accent_color
        
        self._apply_style()
    
    def set_font(self, family: str, size: int) -> None:
        """
        Set the font family and size.
        
        Args:
            family: Font family name
            size: Font size in points
        """
        self._font_family = family
        self._font_size = size
        self._update_font_sizes()
    
    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press events.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def paintEvent(self, event) -> None:
        """
        Custom paint event for additional rendering.
        
        Args:
            event: Paint event
        """
        super().paintEvent(event)
        
        # Optional: Add custom painting here
        # For example, draw a subtle gradient or accent border
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw accent border at bottom
        pen = QPen(self._accent_color, 3)
        painter.setPen(pen)
        
        rect = self.rect()
        painter.drawLine(
            rect.bottomLeft(),
            rect.bottomRight()
        )
    
    def sizeHint(self) -> QSize:
        """
        Get the recommended size for the widget.
        
        Returns:
            Recommended size
        """
        base_size = QSize(150, 100)
        return QSize(
            int(base_size.width() * self._zoom_level),
            int(base_size.height() * self._zoom_level)
        )
    
    def minimumSizeHint(self) -> QSize:
        """
        Get the minimum recommended size for the widget.
        
        Returns:
            Minimum recommended size
        """
        base_size = QSize(100, 70)
        return QSize(
            int(base_size.width() * self.DEFAULT_MIN_ZOOM),
            int(base_size.height() * self.DEFAULT_MIN_ZOOM)
        )
    
    # Properties
    @property
    def current_layer(self) -> int:
        """Get current layer number."""
        return self._current_layer
    
    @property
    def layer_name(self) -> str:
        """Get current layer name."""
        return self._layer_name
    
    @property
    def zoom_level(self) -> float:
        """Get current zoom level."""
        return self._zoom_level
