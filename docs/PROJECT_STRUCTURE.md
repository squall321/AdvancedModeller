# Project Structure

## Overview

LaminateModeller has been organized with a clean, professional structure suitable for distribution and collaboration.

## Root Directory

The root directory contains only essential files:

```
LaminateModeller/
├── README.md              # Project documentation
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── build.sh / build.bat   # Build scripts for C++ parser
├── run_gui.sh / run_gui.bat         # Application launchers
├── start.sh               # Alternative launcher
└── KooMeshModeller.spec   # PyInstaller specification
```

## Core Application Structure

### `gui/` - Main Application
```
gui/
├── main.py                # Application entry point
├── shell.py               # Main window shell
├── home_screen.py         # Home screen
├── sidebar.py             # Navigation sidebar
├── app_context.py         # Application context manager
│
├── widgets/               # Reusable widgets
│   ├── file_input.py      # File selection widget
│   ├── part_list.py       # Part list display
│   ├── layer_table.py     # Layer table editor
│   ├── layer_preview.py   # Layer visualization
│   └── log_viewer.py      # Log output viewer
│
├── dialogs/               # Dialog windows
│   ├── preview_dialog.py  # Preview dialog
│   └── settings_dialog.py # Settings dialog
│
├── modules/               # Feature modules
│   ├── base.py            # Base module class
│   ├── advanced_laminate/ # Laminate modeling module
│   └── advanced_contact/  # Contact manipulation module
│
└── styles/                # Styling
    └── theme.py           # Theme definitions
```

### `core/` - Core Functionality
```
core/
├── KooDynaKeyword.py      # High-level K-file API
│
└── kfile_parser/          # C++/Python hybrid parser (optional)
    ├── README.md          # Parser documentation
    ├── build.sh / build.bat        # Build scripts
    ├── setup.py           # Python build configuration
    │
    ├── src/               # C++ source code
    │   ├── parser.hpp/cpp # Main parser
    │   ├── bindings.cpp   # Python bindings
    │   ├── node.hpp       # Node structures
    │   ├── part.hpp       # Part structures
    │   ├── element.hpp    # Element structures
    │   ├── set.hpp        # Set structures
    │   ├── section.hpp    # Section structures
    │   ├── contact.hpp    # Contact structures
    │   ├── material.hpp   # Material structures
    │   ├── curve.hpp      # Curve structures
    │   ├── boundary.hpp   # Boundary structures
    │   ├── load.hpp       # Load structures
    │   ├── control.hpp    # Control structures
    │   ├── database.hpp   # Database structures
    │   ├── initial.hpp    # Initial condition structures
    │   └── constrained.hpp # Constrained structures
    │
    └── kfile_parser/      # Python package
        ├── __init__.py    # Package initialization
        └── wrapper.py     # Python wrapper layer
```

## Supporting Directories

### `examples/` - Examples and Tests
```
examples/
├── csv_inputs/            # Sample CSV input files
│   ├── B5.csv
│   ├── B6.csv
│   ├── B7_DV1.csv
│   ├── B7_PV1.csv
│   └── B8_MetalBPI.csv
│
├── generated_kfiles/      # Generated K-file examples
│   ├── B5.k
│   ├── B5_display.txt
│   ├── B6.k
│   ├── B6_display.txt
│   └── ...
│
├── scripts/               # Utility scripts
│   ├── dyna_material_generator.py  # Material generator
│   ├── MaterialSource.txt          # Material reference
│   └── displaySample.txt           # Display example
│
├── DropSet.k              # Large test K-file (9.3 MB, 118K lines)
├── test_keywords_simple.py         # Simple parser test
└── test_all_keywords.py            # Comprehensive parser test
```

### `docs/` - Documentation
```
docs/
├── BUILD_GUIDE.md         # Build instructions
├── DEVELOPMENT_PLAN.md    # Development roadmap
├── IMPLEMENTATION_SUMMARY.md       # K-file parser implementation
├── MODULE_DEVELOPMENT_GUIDE.md     # Module development guide
├── PROGRESS.md            # Progress tracking
└── PROJECT_STRUCTURE.md   # This file
```

### `models/` - Model Files
```
models/
└── (User LS-DYNA model files)
```

### `config/` - Configuration
```
config/
└── (Application configuration files)
```

### `references/` - Reference Materials
```
references/
└── (Reference documentation and materials)
```

## Key Design Principles

### 1. Separation of Concerns
- **GUI Layer** (`gui/`): User interface and interaction
- **Core Layer** (`core/`): Business logic and parsing
- **Examples** (`examples/`): Testing and demonstration
- **Documentation** (`docs/`): Project documentation

### 2. Module-Based Architecture
Each feature is a self-contained module in `gui/modules/`:
- Can be enabled/disabled independently
- Has its own widgets and logic
- Follows base module interface

### 3. Optional C++ Parser
- K-file parser is completely optional
- Main application works without it
- Parser can be built separately when needed
- No impact on main application if not built

### 4. Clean Root Directory
- Only essential build/run scripts
- All examples moved to `examples/`
- All documentation moved to `docs/`
- No clutter, easy to navigate

### 5. Distribution-Ready
- Clear separation between source and build artifacts
- `.gitignore` configured properly
- PyInstaller spec file ready
- Cross-platform support

## Distribution Structure

When building for distribution:

```
dist/
└── LaminateModeller/      # or LaminateModeller.exe on Windows
    ├── (Bundled executable and libraries)
    └── (No source code included)
```

## Development Workflow

1. **Working on GUI**: Modify files in `gui/`
2. **Working on parser**: Modify files in `core/kfile_parser/src/`, rebuild
3. **Adding examples**: Add to `examples/`
4. **Updating docs**: Modify files in `docs/`
5. **Testing**: Run scripts from `examples/`

## File Counts

- **Python source files**: ~50 files
- **C++ source files**: ~20 header files
- **Documentation**: 5 major documents
- **Examples**: 20+ example files
- **Total lines of code**: ~15,000+ lines

## Version Control

`.gitignore` configured to exclude:
- Python bytecode (`__pycache__/`, `*.pyc`)
- Build artifacts (`build/`, `dist/`)
- Virtual environments (`venv/`)
- IDE files (`.vscode/`, `.idea/`)
- Temporary files (`*.tmp`, `*.bak`)
- LS-DYNA outputs (`d3*`, `messag`)

## Notes

- `venv/` is excluded from version control
- Generated K-files in `examples/generated_kfiles/` can be regenerated
- C++ parser builds are platform-specific (`.so` for Linux, `.pyd` for Windows)
- Configuration files in `config/` may contain user-specific settings
