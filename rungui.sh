#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

# NVIDIA GPU 강제 사용 (RTX 5070 Ti)
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia

PYTHONPATH="core/kfile_parser:$PYTHONPATH" python3 gui/main.py
