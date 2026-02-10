"""
Tests for Layer Display Widget

This module contains tests for the LayerDisplay widget.
"""

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.ui.layer_display import LayerDisplay


@pytest.fixture
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def sample_display_config():
    """Sample display configuration."""
    return {
        "display": {
            "font_family": "Arial",
            "font_size": 24,
            "bg_color": "#282C34",
            "text_color": "#ABB2BF",
            "border_color": "#3C4048",
            "accent_color": "#61AFEF"
        }
    }


@pytest.fixture
def layer_display(qapp, sample_display_config):
    """Create LayerDisplay instance for testing."""
    display = LayerDisplay(config=sample_display_config)
    yield display
    display.deleteLater()


class TestLayerDisplayInitialization:
    """Tests for LayerDisplay initialization."""
    
    def test_initialization_default(self, qapp):
        """Test initialization with default parameters."""
        display = LayerDisplay()
        assert display.current_layer == 0
        assert display.layer_name == "Base"
        assert display.zoom_level == 1.0
        display.deleteLater()
    
    def test_initialization_with_config(self, layer_display):
        """Test initialization with configuration."""
        assert layer_display.current_layer == 0
        assert layer_display.layer_name == "Base"
        assert layer_display.zoom_level == 1.0
    
    def test_initialization_with_parent(self, qapp):
        """Test initialization with parent widget."""
        parent = QWidget()
        display = LayerDisplay(parent=parent)
        assert display.parent() == parent
        display.deleteLater()
        parent.deleteLater()


class TestLayerDisplayUpdateLayer:
    """Tests for update_layer method."""
    
    def test_update_layer_basic(self, layer_display):
        """Test basic layer update."""
        layer_display.update_layer(2, "Function")
        assert layer_display.current_layer == 2
        assert layer_display.layer_name == "Function"
    
    def test_update_layer_zero(self, layer_display):
        """Test updating to layer 0."""
        layer_display.update_layer(0, "Base")
        assert layer_display.current_layer == 0
        assert layer_display.layer_name == "Base"
    
    def test_update_layer_multiple(self, layer_display):
        """Test multiple layer updates."""
        layer_display.update_layer(1, "Layer 1")
        assert layer_display.current_layer == 1
        
        layer_display.update_layer(2, "Layer 2")
        assert layer_display.current_layer == 2
        
        layer_display.update_layer(0, "Base")
        assert layer_display.current_layer == 0


class TestLayerDisplayZoom:
    """Tests for zoom functionality."""
    
    def test_set_zoom_default(self, layer_display):
        """Test setting zoom to default value."""
        layer_display.set_zoom(1.0)
        assert layer_display.zoom_level == 1.0
    
    def test_set_zoom_increase(self, layer_display):
        """Test increasing zoom level."""
        layer_display.set_zoom(1.5)
        assert layer_display.zoom_level == 1.5
    
    def test_set_zoom_decrease(self, layer_display):
        """Test decreasing zoom level."""
        layer_display.set_zoom(0.8)
        assert layer_display.zoom_level == 0.8
    
    def test_set_zoom_clamp_min(self, layer_display):
        """Test zoom level is clamped to minimum."""
        layer_display.set_zoom(0.1)
        assert layer_display.zoom_level == LayerDisplay.DEFAULT_MIN_ZOOM
    
    def test_set_zoom_clamp_max(self, layer_display):
        """Test zoom level is clamped to maximum."""
        layer_display.set_zoom(5.0)
        assert layer_display.zoom_level == LayerDisplay.DEFAULT_MAX_ZOOM
    
    def test_zoom_in(self, layer_display):
        """Test zoom in functionality."""
        initial_zoom = layer_display.zoom_level
        layer_display.zoom_in()
        assert layer_display.zoom_level == initial_zoom + LayerDisplay.DEFAULT_ZOOM_STEP
    
    def test_zoom_out(self, layer_display):
        """Test zoom out functionality."""
        layer_display.set_zoom(1.5)
        initial_zoom = layer_display.zoom_level
        layer_display.zoom_out()
        assert layer_display.zoom_level == initial_zoom - LayerDisplay.DEFAULT_ZOOM_STEP
    
    def test_reset_zoom(self, layer_display):
        """Test reset zoom functionality."""
        layer_display.set_zoom(2.0)
        layer_display.reset_zoom()
        assert layer_display.zoom_level == 1.0
    
    def test_zoom_in_clamp(self, layer_display):
        """Test zoom in is clamped at maximum."""
        layer_display.set_zoom(LayerDisplay.DEFAULT_MAX_ZOOM)
        layer_display.zoom_in()
        assert layer_display.zoom_level == LayerDisplay.DEFAULT_MAX_ZOOM
    
    def test_zoom_out_clamp(self, layer_display):
        """Test zoom out is clamped at minimum."""
        layer_display.set_zoom(LayerDisplay.DEFAULT_MIN_ZOOM)
        layer_display.zoom_out()
        assert layer_display.zoom_level == LayerDisplay.DEFAULT_MIN_ZOOM


class TestLayerDisplayTheme:
    """Tests for theme customization."""
    
    def test_set_theme_bg_color(self, layer_display):
        """Test setting background color."""
        new_color = QColor(100, 100, 100)
        layer_display.set_theme(bg_color=new_color)
        assert layer_display._bg_color == new_color
    
    def test_set_theme_text_color(self, layer_display):
        """Test setting text color."""
        new_color = QColor(255, 255, 255)
        layer_display.set_theme(text_color=new_color)
        assert layer_display._text_color == new_color
    
    def test_set_theme_border_color(self, layer_display):
        """Test setting border color."""
        new_color = QColor(50, 50, 50)
        layer_display.set_theme(border_color=new_color)
        assert layer_display._border_color == new_color
    
    def test_set_theme_accent_color(self, layer_display):
        """Test setting accent color."""
        new_color = QColor(0, 255, 0)
        layer_display.set_theme(accent_color=new_color)
        assert layer_display._accent_color == new_color
    
    def test_set_theme_all_colors(self, layer_display):
        """Test setting all theme colors."""
        bg = QColor(10, 10, 10)
        text = QColor(200, 200, 200)
        border = QColor(30, 30, 30)
        accent = QColor(255, 0, 0)
        
        layer_display.set_theme(bg, text, border, accent)
        
        assert layer_display._bg_color == bg
        assert layer_display._text_color == text
        assert layer_display._border_color == border
        assert layer_display._accent_color == accent


class TestLayerDisplayFont:
    """Tests for font customization."""
    
    def test_set_font(self, layer_display):
        """Test setting font family and size."""
        layer_display.set_font("Courier New", 30)
        assert layer_display._font_family == "Courier New"
        assert layer_display._font_size == 30
    
    def test_set_font_updates_display(self, layer_display):
        """Test that setting font updates the display."""
        layer_display.set_font("Times New Roman", 20)
        # Font should be updated in labels
        assert layer_display._layer_number_label.font().family() == "Times New Roman"


class TestLayerDisplaySignals:
    """Tests for signal emissions."""
    
    def test_zoom_changed_signal(self, layer_display, qapp):
        """Test zoom_changed signal emission."""
        signal_received = []
        
        def on_zoom_changed(zoom):
            signal_received.append(zoom)
        
        layer_display.zoom_changed.connect(on_zoom_changed)
        layer_display.set_zoom(1.5)
        
        # Process events
        qapp.processEvents()
        
        assert len(signal_received) == 1
        assert signal_received[0] == 1.5
    
    def test_zoom_changed_not_emitted_same_value(self, layer_display, qapp):
        """Test zoom_changed signal not emitted for same value."""
        signal_received = []
        
        def on_zoom_changed(zoom):
            signal_received.append(zoom)
        
        layer_display.zoom_changed.connect(on_zoom_changed)
        layer_display.set_zoom(1.0)  # Already at 1.0
        
        # Process events
        qapp.processEvents()
        
        assert len(signal_received) == 0
    
    def test_clicked_signal(self, layer_display, qapp):
        """Test clicked signal emission."""
        signal_received = []
        
        def on_clicked():
            signal_received.append(True)
        
        layer_display.clicked.connect(on_clicked)
        
        # Simulate mouse click
        from PyQt6.QtTest import QTest
        from PyQt6.QtCore import Qt, QPoint
        QTest.mouseClick(layer_display, Qt.MouseButton.LeftButton)
        
        # Process events
        qapp.processEvents()
        
        assert len(signal_received) == 1


class TestLayerDisplaySize:
    """Tests for size hints."""
    
    def test_size_hint_default(self, layer_display):
        """Test default size hint."""
        size = layer_display.sizeHint()
        assert size.width() == 150
        assert size.height() == 100
    
    def test_size_hint_with_zoom(self, layer_display):
        """Test size hint with zoom."""
        layer_display.set_zoom(2.0)
        size = layer_display.sizeHint()
        assert size.width() == 300  # 150 * 2.0
        assert size.height() == 200  # 100 * 2.0
    
    def test_minimum_size_hint(self, layer_display):
        """Test minimum size hint."""
        size = layer_display.minimumSizeHint()
        assert size.width() == 50  # 100 * 0.5
        assert size.height() == 35  # 70 * 0.5


class TestLayerDisplayColorParsing:
    """Tests for color parsing."""
    
    def test_parse_color_hex(self, layer_display):
        """Test parsing hex color string."""
        color = layer_display._parse_color("#FF0000", QColor(0, 0, 0))
        assert color.red() == 255
        assert color.green() == 0
        assert color.blue() == 0
    
    def test_parse_color_tuple(self, layer_display):
        """Test parsing RGB tuple."""
        color = layer_display._parse_color((0, 255, 0), QColor(0, 0, 0))
        assert color.red() == 0
        assert color.green() == 255
        assert color.blue() == 0
    
    def test_parse_color_list(self, layer_display):
        """Test parsing RGB list."""
        color = layer_display._parse_color([0, 0, 255], QColor(0, 0, 0))
        assert color.red() == 0
        assert color.green() == 0
        assert color.blue() == 255
    
    def test_parse_color_qcolor(self, layer_display):
        """Test parsing QColor object."""
        original = QColor(128, 128, 128)
        color = layer_display._parse_color(original, QColor(0, 0, 0))
        assert color == original
    
    def test_parse_color_none(self, layer_display):
        """Test parsing None returns default."""
        default = QColor(50, 50, 50)
        color = layer_display._parse_color(None, default)
        assert color == default
    
    def test_parse_color_invalid(self, layer_display):
        """Test parsing invalid value returns default."""
        default = QColor(50, 50, 50)
        color = layer_display._parse_color("invalid", default)
        assert color == default
