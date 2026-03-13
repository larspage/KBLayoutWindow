# Vial Layer Display - Project Summary

## 🎯 Project Overview

**Vial Layer Display** is a lightweight desktop application that shows the current active layer from Vial-compatible mechanical keyboards in a small, customizable window.

**Target Users**: Mechanical keyboard enthusiasts who use multiple layers and want a visual indicator of their current layer.

## 📋 Quick Facts

- **Language**: Python 3.11+
- **Framework**: PyQt6 (GUI), hidapi (USB HID)
- **Platforms**: Windows 10/11, macOS 12+
- **License**: MIT
- **Status**: Phase 1 - Core Infrastructure Development

## 🏗️ Architecture at a Glance

```
┌─────────────┐
│ USB Keyboard│ → [HID] → [Monitor] → [State] → [UI Display]
└─────────────┘                                       ↓
                                                [Config Files]
```

The application polls the keyboard every 100ms, detects layer changes, updates internal state, and renders the current layer in a small, always-on-top window.

## 📁 Project Structure

```
vial-layer-display/
├── README.md              # Project introduction
├── ARCHITECTURE.md        # Detailed system design (READ THIS FIRST)
├── CHANGELOG.md          # Version history
├── LICENSE               # MIT License
├── requirements.txt      # Runtime dependencies
├── requirements-dev.txt  # Development dependencies
├── .gitignore           # Git ignore rules
│
├── src/                 # Source code
│   ├── main.py         # Application entry point (to be created)
│   ├── core/           # Core business logic
│   │   ├── keyboard_monitor.py  # USB HID monitoring
│   │   └── layer_state.py       # State management
│   ├── ui/             # User interface components
│   │   ├── main_window.py       # Main window
│   │   ├── layer_display.py     # Layer display widget
│   │   └── preview_window.py    # Layer preview dialog
│   ├── config/         # Configuration management
│   │   └── config_manager.py    # Config loader/saver
│   └── utils/          # Utility functions
│       └── hid_utils.py         # HID communication helpers
│
├── tests/              # Test suite
│   ├── test_keyboard_monitor.py
│   ├── test_layer_state.py
│   ├── test_config_manager.py
│   └── test_hid_utils.py
│
├── docs/               # Documentation
│   ├── DEVELOPMENT.md  # Development guide
│   ├── AGENT_GUIDE.md  # AI agent collaboration guide
│   ├── API.md          # API documentation
│   └── USER_GUIDE.md   # User guide (to be created)
│
├── config/             # Configuration files
│   └── default_config.toml  # Default settings
│
└── assets/             # Assets
    └── icons/          # Application icons
```

## 🚀 Development Phases

### Phase 1: Core Infrastructure (Current)
**Agents can work in parallel on these modules:**

1. **Core/HID Module** (`keyboard_monitor.py`, `hid_utils.py`, `layer_state.py`)
   - USB HID device enumeration
   - Vial keyboard detection
   - Layer state polling
   - State management

2. **Configuration Module** (`config_manager.py`)
   - TOML configuration loading/saving
   - Platform-specific config paths
   - Configuration validation

3. **Project Setup** (scaffolding, dependencies, documentation)
   - Package structure
   - Requirements files
   - Documentation framework

### Phase 2: User Interface
**Depends on Phase 1 completion:**

4. **Layer Display** (`layer_display.py`)
   - Visual layer rendering
   - Zoom functionality
   - Styling/theming

5. **Main Window** (`main_window.py`)
   - Application window
   - System tray integration
   - Window management

6. **Preview Window** (`preview_window.py`)
   - Multi-layer preview
   - Layer name editing

### Phase 3: Integration & Polish
**All agents collaborate:**

7. **Integration testing**
8. **Performance optimization**
9. **Bug fixes**
10. **Binary builds** (PyInstaller)

## 📖 Documentation Guide

### For AI Agents (Start Here!)

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** ← READ THIS FIRST
   - Complete system design
   - Module specifications with code examples
   - Threading model
   - Design decisions

2. **[docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md)** ← READ THIS SECOND
   - How to claim modules
   - Development workflow
   - Testing guidelines
   - Code style
   - Communication protocols

3. **[docs/API.md](docs/API.md)**
   - All public interfaces
   - Type definitions
   - Usage examples

### For Developers

4. **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**
   - Setup instructions
   - Running tests
   - Building executables
   - Debugging tips

### For Users (Future)

5. **docs/USER_GUIDE.md** (to be created)
   - Installation
   - Configuration
   - Troubleshooting

## 🔑 Key Design Decisions

1. **Polling vs Events**: Using 100ms polling for simplicity and reliability
2. **PyQt6**: Native GUI with minimal footprint (<50MB)
3. **TOML Config**: Human-readable configuration format
4. **Thread-Safe**: Qt signals/slots for cross-thread communication
5. **Modular**: Clean separation allows parallel development

## 🧪 Testing Strategy

- **Unit Tests**: Every module has isolated tests
- **Mocking**: HID devices mocked for testing without hardware
- **Coverage Target**: >80%
- **Integration Tests**: Full flow testing
- **Manual Tests**: Real hardware validation

## 📊 Success Metrics

- ✅ Detects Vial keyboards automatically
- ✅ Layer change latency <150ms
- ✅ Memory usage <50MB
- ✅ CPU usage <1% idle, <5% active
- ✅ Cross-platform (Windows/macOS)
- ✅ Single executable <20MB
- ✅ Test coverage >80%

## 🎨 UI Mockup

```
┌─────────────────┐
│  Vial Layer     │ ← Title bar (optional)
├─────────────────┤
│                 │
│   Layer 2       │ ← Large text
│   [Function]    │ ← Layer name
│                 │
│   [-] [+] [P]   │ ← Zoom controls, Preview
└─────────────────┘
```

## 🔧 Tech Stack

- **Python 3.11+**: Modern Python with type hints
- **PyQt6**: Cross-platform GUI framework
- **hidapi**: USB HID communication
- **tomli/tomli-w**: TOML parsing
- **pytest**: Testing framework
- **PyInstaller**: Executable building

## 🤝 Collaboration Model

### For AI Agents

1. **Read Documentation**: ARCHITECTURE.md → AGENT_GUIDE.md
2. **Claim Module**: Comment on GitHub issue
3. **Create Branch**: `feature/module-name`
4. **Develop**: Follow specs in ARCHITECTURE.md
5. **Test**: Write unit tests (>80% coverage)
6. **Document**: Update API.md
7. **Submit PR**: With detailed description

### Communication

- **GitHub Issues**: Questions and discussions
- **Pull Requests**: Code reviews
- **Commit Messages**: Clear, descriptive (see AGENT_GUIDE.md)

## 🎯 Getting Started (For AI Agents)

### Step 1: Read Documentation
```bash
# Priority order:
1. This file (PROJECT_SUMMARY.md) ← You are here!
2. ARCHITECTURE.md
3. docs/AGENT_GUIDE.md
4. docs/API.md
```

### Step 2: Claim a Module
```bash
# Phase 1 modules available:
- keyboard_monitor.py + hid_utils.py + layer_state.py
- config_manager.py
- Project setup (requirements, docs, etc.)
```

### Step 3: Setup Development Environment
```bash
git clone [repository]
cd vial-layer-display
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

### Step 4: Start Coding
```bash
# Create branch
git checkout -b feature/my-module

# Follow specifications in ARCHITECTURE.md
# Write tests as you go
# Update API.md with your interfaces
```

## 📝 Current Status

**Phase 1: Core Infrastructure** - 🟡 In Progress

| Module | Status | Agent |
|--------|--------|-------|
| keyboard_monitor.py | 🟡 Available | Unclaimed |
| hid_utils.py | 🟡 Available | Unclaimed |
| layer_state.py | 🟡 Available | Unclaimed |
| config_manager.py | 🟡 Available | Unclaimed |
| Project Setup | 🟡 Available | Unclaimed |

**Phase 2: User Interface** - ⏳ Waiting on Phase 1

**Phase 3: Integration** - ⏳ Waiting on Phase 2

## 🎓 Learning Resources

- **Vial**: https://get.vial.today/docs/
- **QMK Firmware**: https://docs.qmk.fm/
- **PyQt6**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **hidapi**: https://github.com/libusb/hidapi

## 🐛 Known Challenges

1. **HID Protocol**: Vial protocol needs reverse engineering/documentation
2. **Platform Differences**: USB permissions vary by OS
3. **Keyboard Diversity**: Many different Vial keyboard implementations
4. **Threading**: Must be thread-safe for UI updates

## 💡 Tips for Success

1. **Read ARCHITECTURE.md thoroughly** - It has detailed specs
2. **Follow the type hints** - Makes code self-documenting
3. **Write tests first** - TDD helps catch issues early
4. **Mock liberally** - Don't need real hardware for most tests
5. **Ask questions** - Use GitHub Issues for clarification

## 🎉 Project Goals

### Technical Goals
- Clean, maintainable code
- Comprehensive test coverage
- Professional documentation
- Efficient resource usage

### User Experience Goals
- Simple, intuitive interface
- Reliable layer detection
- Customizable appearance
- Minimal performance impact

### Development Goals
- Enable parallel development
- Clear module boundaries
- Good agent collaboration
- Excellent documentation

## 📞 Contact & Support

- **Repository**: [GitHub URL]
- **Issues**: [GitHub Issues URL]
- **Discussions**: [GitHub Discussions URL]
- **Email**: [Contact email]

## 🏆 Contributing

We welcome contributions! Whether you're an AI agent or human developer:

1. Read the documentation
2. Claim a module or open an issue
3. Follow the coding standards
4. Write tests
5. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🚀 Ready to Start?

### For AI Agents:
1. ✅ Read ARCHITECTURE.md
2. ✅ Read docs/AGENT_GUIDE.md
3. ✅ Claim a Phase 1 module
4. ✅ Start coding!

### For Human Developers:
1. ✅ Read README.md
2. ✅ Read docs/DEVELOPMENT.md
3. ✅ Setup environment
4. ✅ Pick a module or create an issue

---

**Let's build something great together! 🎹✨**

*Last Updated: 2025-02-09*
*Version: 1.0.0-draft*
