#!/bin/bash
set -e

echo "=== KooMesh Modeller 빌드 ==="

# 프로젝트 폴더로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 의존성 확인
pip install pyinstaller -q

# 기존 빌드 정리
rm -rf build dist *.spec

# 빌드
pyinstaller \
    --onefile \
    --windowed \
    --name KooMeshModeller \
    --add-data "config:config" \
    --hidden-import gui.modules.advanced_laminate \
    --hidden-import gui.modules.advanced_contact \
    gui/main.py

echo ""
echo "=== 빌드 완료 ==="
echo "실행 파일: dist/KooMeshModeller"
