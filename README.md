# LaminateModeller

Cross-platform GUI application for LS-DYNA laminate modeling and K-file manipulation.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Application

**Linux/Mac:**
```bash
./run_gui.sh
```

**Windows:**
```cmd
run_gui.bat
```

## Project Structure

```
LaminateModeller/
├── gui/                    # GUI application (PySide6)
│   ├── main.py            # Entry point
│   ├── widgets/           # Custom widgets
│   ├── dialogs/           # Dialog windows
│   ├── modules/           # Feature modules
│   └── styles/            # Themes and styling
│
├── core/                   # Core functionality
│   ├── kfile_parser/      # High-performance K-file parser (C++/Python)
│   └── KooDynaKeyword.py  # K-file API wrapper
│
├── examples/              # Example files and test scripts
│   ├── csv_inputs/        # Sample CSV input files
│   ├── generated_kfiles/  # Generated K-file examples
│   ├── scripts/           # Utility scripts
│   ├── DropSet.k          # Large test K-file
│   ├── test_all_keywords.py        # Comprehensive parser test
│   └── test_keywords_simple.py     # Simple parser test
│
├── docs/                  # Documentation
│   ├── BUILD_GUIDE.md     # Build instructions
│   ├── DEVELOPMENT_PLAN.md         # Development roadmap
│   ├── IMPLEMENTATION_SUMMARY.md   # K-file parser implementation
│   └── PROGRESS.md        # Progress tracking
│
├── models/                # LS-DYNA model files
├── config/                # Configuration files
├── references/            # Reference materials
│
├── requirements.txt       # Python dependencies
├── build.sh / build.bat   # Build scripts (for C++ parser)
├── run_gui.sh / run_gui.bat       # Application launchers
└── KooMeshModeller.spec   # PyInstaller spec file
```

## Features

### Current Features
- Advanced laminate modeling interface
- Contact removal and manipulation
- Layer-by-layer visualization
- CSV-based layer definition import
- Part and material management
- Real-time preview

### K-File Parser (Optional)
- High-performance C++/Python hybrid parser
- 24+ LS-DYNA keyword types supported
- 100x faster than pure Python parsing
- **Note**: Parser is NOT required for main GUI application

## Building for Distribution

### Windows Executable

```cmd
pip install pyinstaller
pyinstaller KooMeshModeller.spec
```

The executable will be in `dist/` directory.

### Linux/Mac

```bash
pip install pyinstaller
pyinstaller KooMeshModeller.spec
```

## Dependencies

**Required:**
- Python 3.8+
- PySide6 >= 6.5.0 (Qt for Python)
- qtawesome >= 1.2.0

**Optional (for K-file parser):**
- C++ compiler (g++, clang++, or Visual Studio Build Tools)
- pybind11 (auto-installed during build)

## Platform Support

- **Windows**: ✅ Fully supported
- **Linux**: ✅ Fully supported
- **macOS**: ✅ Fully supported (PySide6 is cross-platform)

## Development

### Building the K-File Parser (Optional)

**Linux/Mac:**
```bash
cd core/kfile_parser
./build.sh
```

**Windows:**
```cmd
cd core\kfile_parser
build.bat
```

### Running Tests

```bash
# Test K-file parser
python examples/test_keywords_simple.py

# Test with high-level API
python examples/test_all_keywords.py
```

## Documentation

- [Build Guide](docs/BUILD_GUIDE.md) - Detailed build instructions
- [Development Plan](docs/DEVELOPMENT_PLAN.md) - Roadmap and architecture
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - K-file parser details
- [Progress](docs/PROGRESS.md) - Development progress tracking

## License

MIT License

## Contributing

Contributions are welcome! Please check the development plan and progress documents before starting work.
