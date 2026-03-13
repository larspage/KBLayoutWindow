"""
Tests for Layer State Module

This module contains unit tests for the LayerState class, which provides
thread-safe layer state management with PyQt6 signals for UI updates.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.layer_state import LayerState


class TestLayerStateInitialization:
    """Test suite for LayerState initialization."""

    def test_initial_state(self, layer_state: LayerState) -> None:
        """
        Test initial layer state.

        Verifies that a newly created LayerState has layer 0 as
        the current layer and default layer names.
        """
        assert layer_state.get_current_layer() == 0
        assert layer_state.get_layer_name(0) == "Base"
        assert layer_state.get_layer_name(1) == "Layer 1"

    def test_initialization_default_max_layers(self) -> None:
        """
        Test initialization with default max_layers.

        Verifies that LayerState is initialized with the default
        maximum number of layers (16).
        """
        state = LayerState()
        assert state.max_layers == 16

    def test_initialization_custom_max_layers(self) -> None:
        """
        Test initialization with custom max_layers.

        Verifies that LayerState can be initialized with a custom
        maximum number of layers.
        """
        state = LayerState(max_layers=8)
        assert state.max_layers == 8

    def test_initialization_invalid_max_layers(self) -> None:
        """
        Test initialization with invalid max_layers.

        Verifies that ValueError is raised when max_layers is
        less than 1.
        """
        with pytest.raises(ValueError, match="max_layers must be at least 1"):
            LayerState(max_layers=0)

        with pytest.raises(ValueError, match="max_layers must be at least 1"):
            LayerState(max_layers=-5)

    def test_initialization_default_names(self, layer_state: LayerState) -> None:
        """
        Test that default layer names are initialized correctly.

        Verifies that all layers have default names after
        initialization.
        """
        names = layer_state.get_all_layer_names()

        assert names[0] == "Base"
        for i in range(1, layer_state.max_layers):
            assert names[i] == f"Layer {i}"


class TestUpdateLayer:
    """Test suite for update_layer method."""

    def test_update_layer(self, layer_state: LayerState) -> None:
        """
        Test updating the current layer.

        Verifies that the current layer can be updated and the
        layer_changed signal is emitted.
        """
        # Track signal emissions
        signal_emitted = []
        layer_state.layer_changed.connect(lambda l: signal_emitted.append(l))

        layer_state.update_layer(3)

        assert layer_state.get_current_layer() == 3
        assert signal_emitted == [3]

    def test_update_layer_same_value(self, layer_state: LayerState) -> None:
        """
        Test updating to the same layer value.

        Verifies that updating to the same layer doesn't emit
        the signal multiple times.
        """
        signal_emitted = []
        layer_state.layer_changed.connect(lambda l: signal_emitted.append(l))

        layer_state.update_layer(2)
        layer_state.update_layer(2)

        assert signal_emitted == [2]

    def test_update_layer_invalid_negative(self, layer_state: LayerState) -> None:
        """
        Test updating to a negative layer.

        Verifies that ValueError is raised when trying to update
        to a negative layer number.
        """
        with pytest.raises(ValueError, match="layer must be between 0 and"):
            layer_state.update_layer(-1)

    def test_update_layer_invalid_too_large(self, layer_state: LayerState) -> None:
        """
        Test updating to a layer beyond max_layers.

        Verifies that ValueError is raised when trying to update
        to a layer number beyond max_layers.
        """
        with pytest.raises(ValueError, match="layer must be between 0 and"):
            layer_state.update_layer(layer_state.max_layers)

    def test_update_layer_invalid_type(self, layer_state: LayerState) -> None:
        """
        Test updating with invalid type.

        Verifies that TypeError is raised when trying to update
        with a non-integer value.
        """
        with pytest.raises(TypeError, match="layer must be an integer"):
            layer_state.update_layer("2")  # type: ignore

        with pytest.raises(TypeError, match="layer must be an integer"):
            layer_state.update_layer(2.5)  # type: ignore

    def test_update_layer_sequence(self, layer_state: LayerState) -> None:
        """
        Test updating layer in sequence.

        Verifies that multiple layer updates work correctly
        and emit signals for each change.
        """
        signal_emitted = []
        layer_state.layer_changed.connect(lambda l: signal_emitted.append(l))

        layer_state.update_layer(1)
        layer_state.update_layer(2)
        layer_state.update_layer(0)

        assert layer_state.get_current_layer() == 0
        assert signal_emitted == [1, 2, 0]


class TestLayerChangedSignal:
    """Test suite for layer_changed signal."""

    def test_layer_changed_signal_emitted(self, layer_state: LayerState) -> None:
        """
        Test that layer_changed signal is emitted on change.

        Verifies that the signal is emitted with the correct
        layer number when the layer changes.
        """
        received_layers = []

        def on_layer_changed(layer: int) -> None:
            received_layers.append(layer)

        layer_state.layer_changed.connect(on_layer_changed)
        layer_state.update_layer(5)

        assert received_layers == [5]

    def test_layer_changed_signal_multiple_connections(self, layer_state: LayerState) -> None:
        """
        Test multiple connections to layer_changed signal.

        Verifies that multiple slots can be connected to the
        signal and all receive the emission.
        """
        results1 = []
        results2 = []

        layer_state.layer_changed.connect(lambda l: results1.append(l))
        layer_state.layer_changed.connect(lambda l: results2.append(l))

        layer_state.update_layer(3)

        assert results1 == [3]
        assert results2 == [3]

    def test_layer_changed_signal_not_emitted_on_same(self, layer_state: LayerState) -> None:
        """
        Test that signal is not emitted when layer doesn't change.

        Verifies that the signal is not emitted when updating
        to the same layer value.
        """
        signal_count = [0]

        def count_signal(_: int) -> None:
            signal_count[0] += 1

        layer_state.layer_changed.connect(count_signal)
        layer_state.update_layer(2)
        layer_state.update_layer(2)

        assert signal_count[0] == 1


class TestGetLayerName:
    """Test suite for get_layer_name method."""

    def test_get_layer_name_default(self, layer_state: LayerState) -> None:
        """
        Test getting default layer names.

        Verifies that default layer names are returned correctly.
        """
        assert layer_state.get_layer_name(0) == "Base"
        assert layer_state.get_layer_name(1) == "Layer 1"
        assert layer_state.get_layer_name(5) == "Layer 5"

    def test_get_layer_name_custom(self, layer_state: LayerState) -> None:
        """
        Test getting custom layer names.

        Verifies that custom layer names are returned after
        being set.
        """
        layer_state.set_layer_name(2, "Gaming")
        assert layer_state.get_layer_name(2) == "Gaming"

    def test_get_layer_name_invalid_negative(self, layer_state: LayerState) -> None:
        """
        Test getting name for negative layer.

        Verifies that "Unknown" is returned for negative
        layer numbers.
        """
        assert layer_state.get_layer_name(-1) == "Unknown"

    def test_get_layer_name_invalid_too_large(self, layer_state: LayerState) -> None:
        """
        Test getting name for layer beyond max_layers.

        Verifies that "Unknown" is returned for layer numbers
        beyond max_layers.
        """
        assert layer_state.get_layer_name(layer_state.max_layers) == "Unknown"
        assert layer_state.get_layer_name(999) == "Unknown"

    def test_get_layer_name_invalid_type(self, layer_state: LayerState) -> None:
        """
        Test getting name with invalid type.

        Verifies that TypeError is raised when trying to get
        name with a non-integer value.
        """
        with pytest.raises(TypeError, match="layer must be an integer"):
            layer_state.get_layer_name("0")  # type: ignore


class TestSetLayerName:
    """Test suite for set_layer_name method."""

    def test_set_layer_name(self, layer_state: LayerState) -> None:
        """
        Test setting a custom layer name.

        Verifies that a custom name can be set for a layer.
        """
        layer_state.set_layer_name(3, "Media")
        assert layer_state.get_layer_name(3) == "Media"

    def test_set_layer_name_override(self, layer_state: LayerState) -> None:
        """
        Test overriding an existing layer name.

        Verifies that an existing layer name can be overridden.
        """
        layer_state.set_layer_name(2, "First")
        layer_state.set_layer_name(2, "Second")
        assert layer_state.get_layer_name(2) == "Second"

    def test_set_layer_name_invalid_negative(self, layer_state: LayerState) -> None:
        """
        Test setting name for negative layer.

        Verifies that ValueError is raised when trying to set
        name for a negative layer.
        """
        with pytest.raises(ValueError, match="layer must be between 0 and"):
            layer_state.set_layer_name(-1, "Test")

    def test_set_layer_name_invalid_too_large(self, layer_state: LayerState) -> None:
        """
        Test setting name for layer beyond max_layers.

        Verifies that ValueError is raised when trying to set
        name for a layer beyond max_layers.
        """
        with pytest.raises(ValueError, match="layer must be between 0 and"):
            layer_state.set_layer_name(layer_state.max_layers, "Test")

    def test_set_layer_name_invalid_layer_type(self, layer_state: LayerState) -> None:
        """
        Test setting name with invalid layer type.

        Verifies that TypeError is raised when trying to set
        name with a non-integer layer value.
        """
        with pytest.raises(TypeError, match="layer must be an integer"):
            layer_state.set_layer_name("0", "Test")  # type: ignore

    def test_set_layer_name_invalid_name_type(self, layer_state: LayerState) -> None:
        """
        Test setting name with invalid name type.

        Verifies that TypeError is raised when trying to set
        name with a non-string value.
        """
        with pytest.raises(TypeError, match="name must be a string"):
            layer_state.set_layer_name(0, 123)  # type: ignore


class TestGetAllLayerNames:
    """Test suite for get_all_layer_names method."""

    def test_get_all_layer_names(self, layer_state: LayerState) -> None:
        """
        Test getting all layer names.

        Verifies that all layer names are returned in a dictionary.
        """
        names = layer_state.get_all_layer_names()

        assert isinstance(names, dict)
        assert len(names) == layer_state.max_layers
        assert names[0] == "Base"

    def test_get_all_layer_names_returns_copy(self, layer_state: LayerState) -> None:
        """
        Test that get_all_layer_names returns a copy.

        Verifies that modifying the returned dictionary doesn't
        affect the internal state.
        """
        names = layer_state.get_all_layer_names()
        names[0] = "Modified"

        assert layer_state.get_layer_name(0) == "Base"

    def test_get_all_layer_names_with_custom(self, layer_state: LayerState) -> None:
        """
        Test getting all names with custom names set.

        Verifies that custom names are included in the result.
        """
        layer_state.set_layer_name(2, "Custom")
        names = layer_state.get_all_layer_names()

        assert names[2] == "Custom"


class TestResetLayerNames:
    """Test suite for reset_layer_names method."""

    def test_reset_layer_names(self, layer_state: LayerState) -> None:
        """
        Test resetting layer names to defaults.

        Verifies that all layer names are reset to their
        default values.
        """
        layer_state.set_layer_name(0, "Custom Base")
        layer_state.set_layer_name(2, "Custom Layer")

        layer_state.reset_layer_names()

        assert layer_state.get_layer_name(0) == "Base"
        assert layer_state.get_layer_name(2) == "Layer 2"

    def test_reset_layer_names_no_custom(self, layer_state: LayerState) -> None:
        """
        Test resetting when no custom names are set.

        Verifies that resetting doesn't change anything when
        no custom names were set.
        """
        original_name = layer_state.get_layer_name(0)

        layer_state.reset_layer_names()

        assert layer_state.get_layer_name(0) == original_name


class TestIsValidLayer:
    """Test suite for is_valid_layer method."""

    def test_is_valid_layer_true(self, layer_state: LayerState) -> None:
        """
        Test checking valid layer numbers.

        Verifies that valid layer numbers return True.
        """
        assert layer_state.is_valid_layer(0) is True
        assert layer_state.is_valid_layer(1) is True
        assert layer_state.is_valid_layer(layer_state.max_layers - 1) is True

    def test_is_valid_layer_false_negative(self, layer_state: LayerState) -> None:
        """
        Test checking negative layer numbers.

        Verifies that negative layer numbers return False.
        """
        assert layer_state.is_valid_layer(-1) is False
        assert layer_state.is_valid_layer(-100) is False

    def test_is_valid_layer_false_too_large(self, layer_state: LayerState) -> None:
        """
        Test checking layer numbers beyond max_layers.

        Verifies that layer numbers beyond max_layers return False.
        """
        assert layer_state.is_valid_layer(layer_state.max_layers) is False
        assert layer_state.is_valid_layer(999) is False

    def test_is_valid_layer_invalid_type(self, layer_state: LayerState) -> None:
        """
        Test checking with invalid type.

        Verifies that non-integer values return False.
        """
        assert layer_state.is_valid_layer("0") is False  # type: ignore
        assert layer_state.is_valid_layer(2.5) is False  # type: ignore
        assert layer_state.is_valid_layer(None) is False  # type: ignore


class TestGetLayerInfo:
    """Test suite for get_layer_info method."""

    def test_get_layer_info_valid(self, layer_state: LayerState) -> None:
        """
        Test getting info for a valid layer.

        Verifies that layer information is returned correctly.
        """
        layer_state.update_layer(3)
        info = layer_state.get_layer_info(3)

        assert info is not None
        assert info["layer"] == 3
        assert info["name"] == "Layer 3"
        assert info["is_current"] is True

    def test_get_layer_info_not_current(self, layer_state: LayerState) -> None:
        """
        Test getting info for a layer that's not current.

        Verifies that is_current is False for non-current layers.
        """
        layer_state.update_layer(2)
        info = layer_state.get_layer_info(5)

        assert info is not None
        assert info["layer"] == 5
        assert info["is_current"] is False

    def test_get_layer_info_custom_name(self, layer_state: LayerState) -> None:
        """
        Test getting info for a layer with custom name.

        Verifies that custom names are included in the info.
        """
        layer_state.set_layer_name(4, "Custom Name")
        info = layer_state.get_layer_info(4)

        assert info is not None
        assert info["name"] == "Custom Name"

    def test_get_layer_info_invalid(self, layer_state: LayerState) -> None:
        """
        Test getting info for an invalid layer.

        Verifies that None is returned for invalid layer numbers.
        """
        assert layer_state.get_layer_info(-1) is None
        assert layer_state.get_layer_info(layer_state.max_layers) is None


class TestThreadSafety:
    """Test suite for thread safety of LayerState."""

    def test_concurrent_layer_updates(self, layer_state: LayerState) -> None:
        """
        Test concurrent layer updates from multiple threads.

        Verifies that layer state remains consistent when
        multiple threads update the layer simultaneously.
        """
        signal_count = [0]
        layer_state.layer_changed.connect(lambda _: signal_count.__setitem__(0, signal_count[0] + 1))

        def update_layer_randomly() -> None:
            for i in range(100):
                layer = i % layer_state.max_layers
                layer_state.update_layer(layer)

        threads = [
            threading.Thread(target=update_layer_randomly),
            threading.Thread(target=update_layer_randomly),
            threading.Thread(target=update_layer_randomly),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify final state is valid
        current = layer_state.get_current_layer()
        assert 0 <= current < layer_state.max_layers

    def test_concurrent_name_access(self, layer_state: LayerState) -> None:
        """
        Test concurrent layer name access from multiple threads.

        Verifies that layer names can be safely accessed from
        multiple threads simultaneously.
        """
        def read_names() -> None:
            for _ in range(100):
                for i in range(layer_state.max_layers):
                    name = layer_state.get_layer_name(i)
                    assert isinstance(name, str)

        threads = [
            threading.Thread(target=read_names),
            threading.Thread(target=read_names),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def test_concurrent_set_and_get(self, layer_state: LayerState) -> None:
        """
        Test concurrent set and get operations.

        Verifies that setting and getting layer names works
        correctly with concurrent access.
        """
        def set_names() -> None:
            for i in range(50):
                layer_state.set_layer_name(i % layer_state.max_layers, f"Thread1-{i}")

        def get_names() -> None:
            for _ in range(50):
                for i in range(layer_state.max_layers):
                    name = layer_state.get_layer_name(i)
                    assert isinstance(name, str)

        thread1 = threading.Thread(target=set_names)
        thread2 = threading.Thread(target=get_names)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()


class TestMaxLayersProperty:
    """Test suite for max_layers property."""

    def test_max_layers_property(self) -> None:
        """
        Test max_layers property.

        Verifies that the max_layers property returns the
        correct value.
        """
        state = LayerState(max_layers=10)
        assert state.max_layers == 10

    def test_max_layers_readonly(self, layer_state: LayerState) -> None:
        """
        Test that max_layers is read-only.

        Verifies that max_layers cannot be modified after
        initialization.
        """
        original_max = layer_state.max_layers
        with pytest.raises(AttributeError):
            layer_state.max_layers = 20  # type: ignore

        assert layer_state.max_layers == original_max
