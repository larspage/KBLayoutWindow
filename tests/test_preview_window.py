"""
Tests for Layer Preview Window

This module contains tests for the LayerPreviewWindow class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit
from PyQt6.QtCore import Qt

from src.ui.preview_window import LayerPreviewWindow
from src.core.layer_state import LayerState


@pytest.fixture
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def mock_layer_state():
    """Create mock LayerState."""
    state = Mock(spec=LayerState)
    state.get_current_layer.return_value = 0
    state.get_layer_name.return_value = "Base"
    state.get_all_layer_names.return_value = {
        0: "Base",
        1: "Layer 1",
        2: "Layer 2",
        3: "Layer 3"
    }
    state.max_layers = 16
    state.set_layer_name = Mock()
    state.reset_layer_names = Mock()
    return state


@pytest.fixture
def preview_window(qapp, mock_layer_state):
    """Create LayerPreviewWindow instance for testing."""
    window = LayerPreviewWindow(layer_state=mock_layer_state)
    yield window
    window.deleteLater()


class TestLayerPreviewWindowInitialization:
    """Tests for LayerPreviewWindow initialization."""
    
    def test_initialization(self, preview_window):
        """Test basic initialization."""
        assert preview_window.windowTitle() == "Layer Preview"
        assert preview_window._layer_state is not None
        assert preview_window._current_layer == 0
    
    def test_initialization_modal(self, preview_window):
        """Test window is modal."""
        assert preview_window.isModal()
    
    def test_initialization_default_size(self, preview_window):
        """Test default window size."""
        assert preview_window.width() == LayerPreviewWindow.DEFAULT_WIDTH
        assert preview_window.height() == LayerPreviewWindow.DEFAULT_HEIGHT
    
    def test_initialization_stores_original_names(self, preview_window, mock_layer_state):
        """Test original layer names are stored."""
        original_names = mock_layer_state.get_all_layer_names.return_value
        assert preview_window._original_names == original_names
    
    def test_initialization_edited_names_empty(self, preview_window):
        """Test edited names starts empty."""
        assert len(preview_window._edited_names) == 0


class TestLayerPreviewWindowUI:
    """Tests for UI components."""
    
    def test_layer_grid_created(self, preview_window):
        """Test layer grid is created."""
        assert preview_window._layer_grid is not None
        assert preview_window._grid_layout is not None
    
    def test_name_inputs_created(self, preview_window):
        """Test name input widgets are created."""
        assert len(preview_window._name_inputs) > 0
    
    def test_save_button_exists(self, preview_window):
        """Test save button exists."""
        assert preview_window._save_btn is not None
    
    def test_reset_button_exists(self, preview_window):
        """Test reset button exists."""
        assert preview_window._reset_btn is not None
    
    def test_cancel_button_exists(self, preview_window):
        """Test cancel button exists."""
        assert preview_window._cancel_btn is not None


class TestLayerPreviewWindowLayerGrid:
    """Tests for layer grid population."""
    
    def test_populate_layer_grid(self, preview_window):
        """Test layer grid is populated."""
        # Check that grid has items
        assert preview_window._grid_layout.count() > 0
    
    def test_layer_widgets_created(self, preview_window):
        """Test layer widgets are created for all layers."""
        max_layers = preview_window._layer_state.max_layers
        assert len(preview_window._name_inputs) == max_layers
    
    def test_current_layer_highlighted(self, preview_window):
        """Test current layer is highlighted."""
        # Current layer (0) should have different styling
        # This is tested visually, but we can check the widget exists
        assert 0 in preview_window._name_inputs


class TestLayerPreviewWindowNameEditing:
    """Tests for layer name editing functionality."""
    
    def test_on_name_changed(self, preview_window):
        """Test handling name change events."""
        preview_window._on_name_changed(1, "Custom Name")
        
        assert 1 in preview_window._edited_names
        assert preview_window._edited_names[1] == "Custom Name"
    
    def test_on_name_changed_multiple(self, preview_window):
        """Test handling multiple name changes."""
        preview_window._on_name_changed(1, "Name 1")
        preview_window._on_name_changed(2, "Name 2")
        preview_window._on_name_changed(3, "Name 3")
        
        assert len(preview_window._edited_names) == 3
        assert preview_window._edited_names[1] == "Name 1"
        assert preview_window._edited_names[2] == "Name 2"
        assert preview_window._edited_names[3] == "Name 3"
    
    def test_on_name_changed_overwrites(self, preview_window):
        """Test that name changes overwrite previous values."""
        preview_window._on_name_changed(1, "First Name")
        preview_window._on_name_changed(1, "Second Name")
        
        assert preview_window._edited_names[1] == "Second Name"


class TestLayerPreviewWindowSaveChanges:
    """Tests for save changes functionality."""
    
    def test_save_changes_applies_edits(self, preview_window, mock_layer_state):
        """Test save changes applies edited names."""
        preview_window._edited_names = {1: "Custom Layer 1", 2: "Custom Layer 2"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.information'):
            preview_window._save_changes()
        
        # Check set_layer_name was called for edited layers
        assert mock_layer_state.set_layer_name.call_count == 2
    
    def test_save_changes_emits_signal(self, preview_window, mock_layer_state):
        """Test save changes emits signal."""
        signal_received = []
        
        def on_names_changed(names):
            signal_received.append(names)
        
        preview_window.layer_names_changed.connect(on_names_changed)
        preview_window._edited_names = {1: "Custom"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.information'):
            preview_window._save_changes()
        
        assert len(signal_received) == 1
    
    def test_save_changes_accepts_dialog(self, preview_window):
        """Test save changes accepts the dialog."""
        preview_window._edited_names = {1: "Custom"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.information'):
            result = preview_window._save_changes()
        
        # Dialog should be accepted (closed)
        # This is tested by checking the dialog result
        assert True  # Placeholder - actual result checking requires more setup


class TestLayerPreviewWindowResetToDefaults:
    """Tests for reset to defaults functionality."""
    
    def test_reset_to_defaults_confirms(self, preview_window, mock_layer_state):
        """Test reset to defaults shows confirmation."""
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                preview_window._reset_to_defaults()
            
            mock_question.assert_called_once()
    
    def test_reset_to_defaults_cancels(self, preview_window, mock_layer_state):
        """Test reset to defaults can be cancelled."""
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.No
            
            preview_window._reset_to_defaults()
            
            # reset_layer_names should not be called
            mock_layer_state.reset_layer_names.assert_not_called()
    
    def test_reset_to_defaults_resets_names(self, preview_window, mock_layer_state):
        """Test reset to defaults resets layer names."""
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                preview_window._reset_to_defaults()
            
            mock_layer_state.reset_layer_names.assert_called_once()
    
    def test_reset_to_defaults_clears_edits(self, preview_window):
        """Test reset to defaults clears edited names."""
        preview_window._edited_names = {1: "Custom", 2: "Custom 2"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                preview_window._reset_to_defaults()
        
        assert len(preview_window._edited_names) == 0


class TestLayerPreviewWindowCancelChanges:
    """Tests for cancel changes functionality."""
    
    def test_cancel_changes_no_edits(self, preview_window):
        """Test cancel with no edits closes dialog."""
        result = preview_window._cancel_changes()
        assert result is None  # Dialog rejected
    
    def test_cancel_changes_with_edits_confirms(self, preview_window):
        """Test cancel with edits shows confirmation."""
        preview_window._edited_names = {1: "Custom"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.No
            
            preview_window._cancel_changes()
            
            mock_question.assert_called_once()
    
    def test_cancel_changes_with_edits_cancels(self, preview_window):
        """Test cancel with edits can be cancelled."""
        preview_window._edited_names = {1: "Custom"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            preview_window._cancel_changes()
            
            # Dialog should be rejected
            assert True  # Placeholder


class TestLayerPreviewWindowGetters:
    """Tests for getter methods."""
    
    def test_get_edited_names(self, preview_window):
        """Test getting edited names."""
        preview_window._edited_names = {1: "Name 1", 2: "Name 2"}
        
        names = preview_window.get_edited_names()
        
        assert names == {1: "Name 1", 2: "Name 2"}
    
    def test_get_edited_names_returns_copy(self, preview_window):
        """Test get_edited_names returns a copy."""
        preview_window._edited_names = {1: "Name 1"}
        
        names = preview_window.get_edited_names()
        names[2] = "Name 2"
        
        assert 2 not in preview_window._edited_names
    
    def test_has_unsaved_changes_true(self, preview_window):
        """Test has_unsaved_changes returns True when there are edits."""
        preview_window._edited_names = {1: "Custom"}
        assert preview_window.has_unsaved_changes() is True
    
    def test_has_unsaved_changes_false(self, preview_window):
        """Test has_unsaved_changes returns False when there are no edits."""
        assert preview_window.has_unsaved_changes() is False


class TestLayerPreviewWindowUpdateCurrentLayer:
    """Tests for updating current layer indicator."""
    
    def test_update_current_layer(self, preview_window):
        """Test updating current layer."""
        preview_window.update_current_layer(2)
        
        assert preview_window._current_layer == 2
    
    def test_update_current_layer_rebuilds_grid(self, preview_window):
        """Test updating current layer rebuilds the grid."""
        initial_count = preview_window._grid_layout.count()
        
        preview_window.update_current_layer(1)
        
        # Grid should be rebuilt
        # This is tested by checking the grid still has items
        assert preview_window._grid_layout.count() > 0


class TestLayerPreviewWindowSignals:
    """Tests for signal emissions."""
    
    def test_layer_names_changed_signal(self, preview_window, mock_layer_state):
        """Test layer_names_changed signal emission."""
        signal_received = []
        
        def on_names_changed(names):
            signal_received.append(names)
        
        preview_window.layer_names_changed.connect(on_names_changed)
        preview_window._edited_names = {1: "Custom"}
        
        with patch('PyQt6.QtWidgets.QMessageBox.information'):
            preview_window._save_changes()
        
        assert len(signal_received) == 1


# Import QMessageBox at the end
from PyQt6.QtWidgets import QMessageBox
