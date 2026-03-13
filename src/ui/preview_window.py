"""
Layer Preview Window

This module provides a dialog for previewing all available keyboard layers
and editing layer names.

Classes:
    LayerPreviewWindow: Dialog for viewing and editing all layers
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QFrame, QGridLayout, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.core.layer_state import LayerState


class LayerPreviewWindow(QDialog):
    """
    Dialog for previewing all available keyboard layers.
    
    This dialog provides:
    - Grid view of all layers
    - Layer name editing capability
    - Visual indication of current layer
    - Save/Cancel buttons for applying changes
    
    Signals:
        layer_names_changed: Emitted when layer names are modified
    
    Attributes:
        layer_state: Layer state manager
        current_layer: Currently active layer
    """
    
    # Signals
    layer_names_changed = pyqtSignal(dict)
    
    # Default settings
    DEFAULT_WIDTH = 500
    DEFAULT_HEIGHT = 400
    LAYERS_PER_ROW = 4
    
    def __init__(
        self,
        layer_state: LayerState,
        parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the layer preview window.
        
        Args:
            layer_state: Layer state manager
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Store reference
        self._layer_state = layer_state
        
        # Get current layer
        self._current_layer = layer_state.get_current_layer()
        
        # Store original layer names for cancel functionality
        self._original_names = layer_state.get_all_layer_names().copy()
        
        # Store edited names
        self._edited_names: Dict[int, str] = {}
        
        # Layer name input widgets
        self._name_inputs: Dict[int, QLineEdit] = {}
        
        # Setup dialog
        self._setup_dialog()
        
        # Setup UI
        self._setup_ui()
    
    def _setup_dialog(self) -> None:
        """Setup dialog properties."""
        self.setWindowTitle("Layer Preview")
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setModal(True)
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Layer Preview")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Current layer indicator
        current_label = QLabel(f"Current Layer: {self._current_layer}")
        current_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(current_label)
        
        # Scroll area for layer grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        
        # Layer grid container
        self._layer_grid = QWidget()
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(10)
        self._layer_grid.setLayout(self._grid_layout)
        
        # Populate layer grid
        self._populate_layer_grid()
        
        # Set scroll area widget
        scroll_area.setWidget(self._layer_grid)
        main_layout.addWidget(scroll_area)
        
        # Instructions
        instructions = QLabel(
            "Click on a layer name to edit it. Click 'Save' to apply changes."
        )
        instructions.setStyleSheet("color: #666; font-style: italic;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(instructions)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Save button
        self._save_btn = QPushButton("Save")
        self._save_btn.setMinimumWidth(100)
        self._save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(self._save_btn)
        
        # Reset button
        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.setMinimumWidth(120)
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)
        
        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.clicked.connect(self._cancel_changes)
        button_layout.addWidget(self._cancel_btn)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(main_layout)
    
    def _populate_layer_grid(self) -> None:
        """Populate the layer grid with layer widgets."""
        # Get all layer names
        layer_names = self._layer_state.get_all_layer_names()
        
        # Get max layers
        max_layers = self._layer_state.max_layers
        
        # Create layer widgets
        row = 0
        col = 0
        
        for layer in range(max_layers):
            # Create layer widget
            layer_widget = self._create_layer_widget(layer, layer_names.get(layer, f"Layer {layer}"))
            
            # Add to grid
            self._grid_layout.addWidget(layer_widget, row, col)
            
            # Update position
            col += 1
            if col >= self.LAYERS_PER_ROW:
                col = 0
                row += 1
        
        # Add stretch to fill remaining space
        self._grid_layout.setRowStretch(row + 1, 1)
    
    def _create_layer_widget(self, layer: int, name: str) -> QFrame:
        """
        Create a widget for a single layer.
        
        Args:
            layer: Layer number
            name: Layer name
            
        Returns:
            Layer widget frame
        """
        # Create frame
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setLineWidth(2)
        
        # Style based on whether this is the current layer
        if layer == self._current_layer:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #E8F5E9;
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background-color: #F5F5F5;
                    border: 2px solid #BDBDBD;
                    border-radius: 5px;
                }
            """)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Layer number
        number_label = QLabel(f"Layer {layer}")
        number_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(number_label)
        
        # Layer name input
        name_input = QLineEdit(name)
        name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_input.textChanged.connect(
            lambda text, l=layer: self._on_name_changed(l, text)
        )
        layout.addWidget(name_input)
        
        # Store reference
        self._name_inputs[layer] = name_input
        
        # Set layout
        frame.setLayout(layout)
        
        return frame
    
    def _on_name_changed(self, layer: int, name: str) -> None:
        """
        Handle layer name change events.
        
        Args:
            layer: Layer number
            name: New layer name
        """
        self._edited_names[layer] = name
    
    def _save_changes(self) -> None:
        """Save the edited layer names."""
        # Apply all edited names
        for layer, name in self._edited_names.items():
            self._layer_state.set_layer_name(layer, name)
        
        # Emit signal
        self.layer_names_changed.emit(self._layer_state.get_all_layer_names())
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Success",
            "Layer names have been saved."
        )
        
        # Close dialog
        self.accept()
    
    def _reset_to_defaults(self) -> None:
        """Reset all layer names to defaults."""
        # Confirm reset
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all layer names to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset layer names
            self._layer_state.reset_layer_names()
            
            # Update input fields
            layer_names = self._layer_state.get_all_layer_names()
            for layer, name_input in self._name_inputs.items():
                name_input.setText(layer_names.get(layer, f"Layer {layer}"))
            
            # Clear edited names
            self._edited_names.clear()
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Reset Complete",
                "Layer names have been reset to defaults."
            )
    
    def _cancel_changes(self) -> None:
        """Cancel changes and close dialog."""
        # Check if there are unsaved changes
        if self._edited_names:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Close dialog without saving
        self.reject()
    
    def get_edited_names(self) -> Dict[int, str]:
        """
        Get the edited layer names.
        
        Returns:
            Dictionary of layer numbers to names
        """
        return self._edited_names.copy()
    
    def has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes.
        
        Returns:
            True if there are unsaved changes, False otherwise
        """
        return len(self._edited_names) > 0
    
    def update_current_layer(self, layer: int) -> None:
        """
        Update the current layer indicator.
        
        Args:
            layer: New current layer number
        """
        self._current_layer = layer
        
        # Rebuild grid to update styling
        # Clear existing widgets
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear name inputs
        self._name_inputs.clear()
        
        # Repopulate grid
        self._populate_layer_grid()
