#!/bin/bash
#
# KooMesh Modeller - 실행파일 빌드 스크립트
#
# 사용법:
#   ./build_executable.sh [pyinstaller|nuitka|both]
#
# 기본값은 nuitka (권장)
#

set -e  # 오류 발생시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  KooMesh Modeller - 실행파일 빌드${NC}"
echo -e "${GREEN}================================================${NC}"

# 빌드 방법 선택
BUILD_METHOD=${1:-nuitka}

# 가상환경 활성화
if [ -d "venv" ]; then
    echo -e "${YELLOW}가상환경 활성화 중...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}오류: venv 폴더를 찾을 수 없습니다${NC}"
    exit 1
fi

# PyInstaller 빌드
build_pyinstaller() {
    echo -e "${YELLOW}PyInstaller로 빌드 중...${NC}"

    # PyInstaller 설치 확인
    pip show pyinstaller > /dev/null 2>&1 || pip install pyinstaller

    # 이전 빌드 정리
    rm -rf dist build

    # 빌드 실행
    pyinstaller --clean KooMeshModeller.spec

    echo -e "${GREEN}✓ PyInstaller 빌드 완료!${NC}"
    ls -lh dist/KooMeshModeller
}

# Nuitka 빌드
build_nuitka() {
    echo -e "${YELLOW}Nuitka로 빌드 중 (시간이 걸립니다...)${NC}"

    # Nuitka 설치 확인
    pip show nuitka > /dev/null 2>&1 || pip install nuitka ordered-set zstandard

    # 이전 빌드 정리
    rm -rf dist_nuitka

    # 빌드 실행
    python -m nuitka \
        --standalone \
        --onefile \
        --enable-plugin=pyside6 \
        --disable-console \
        --output-dir=dist_nuitka \
        --include-data-dir=config=config \
        --include-package=gui.modules.advanced_laminate \
        --include-package=gui.modules.advanced_contact \
        gui/main.py

    # 파일명 변경
    mv dist_nuitka/main.bin dist_nuitka/KooMeshModeller
    chmod +x dist_nuitka/KooMeshModeller

    echo -e "${GREEN}✓ Nuitka 빌드 완료!${NC}"
    ls -lh dist_nuitka/KooMeshModeller
}

# 배포 패키지 생성
create_release_package() {
    echo -e "${YELLOW}배포 패키지 생성 중...${NC}"

    # 이전 패키지 정리
    rm -rf LaminateModeller-Release
    rm -f LaminateModeller-Linux-x64.tar.gz

    # 디렉토리 생성
    mkdir -p LaminateModeller-Release

    # 파일 복사
    cp dist_nuitka/KooMeshModeller LaminateModeller-Release/
    cp README.md BUILD_COMPARISON.md LaminateModeller-Release/
    cp -r examples LaminateModeller-Release/
    cp -r docs LaminateModeller-Release/

    # 실행방법.txt 생성
    cat > LaminateModeller-Release/실행방법.txt << 'EOF'
=================================================================
KooMesh Modeller - 실행 방법
=================================================================

## Linux에서 실행:

1. 터미널에서 실행:
   ./KooMeshModeller

2. 또는 파일 매니저에서:
   - KooMeshModeller 파일을 더블클릭
   - 권한 오류가 나면: chmod +x KooMeshModeller

## 포함된 파일:

- KooMeshModeller   : 실행파일 (Nuitka 빌드, 36MB)
- README.md         : 프로젝트 설명
- BUILD_COMPARISON.md : 빌드 방법 비교
- examples/         : 예제 파일들
- docs/             : 문서

## 특징:

✅ Python 설치 불필요
✅ 모든 의존성 포함
✅ 단일 실행파일
✅ 하드카피 가능
✅ 크기 최적화 (36MB)

=================================================================
EOF

    # 압축 파일 생성
    tar -czf LaminateModeller-Linux-x64.tar.gz LaminateModeller-Release/

    echo -e "${GREEN}✓ 배포 패키지 생성 완료!${NC}"
    ls -lh LaminateModeller-Linux-x64.tar.gz
}

# 빌드 실행
case $BUILD_METHOD in
    pyinstaller)
        build_pyinstaller
        ;;
    nuitka)
        build_nuitka
        create_release_package
        ;;
    both)
        build_pyinstaller
        build_nuitka
        create_release_package
        ;;
    *)
        echo -e "${RED}오류: 알 수 없는 빌드 방법: $BUILD_METHOD${NC}"
        echo "사용법: $0 [pyinstaller|nuitka|both]"
        exit 1
        ;;
esac

echo -e ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  빌드 완료!${NC}"
echo -e "${GREEN}================================================${NC}"

if [ "$BUILD_METHOD" = "nuitka" ] || [ "$BUILD_METHOD" = "both" ]; then
    echo -e ""
    echo -e "${YELLOW}배포 파일:${NC}"
    echo -e "  - 단일 실행파일: ${GREEN}dist_nuitka/KooMeshModeller${NC}"
    echo -e "  - 배포 패키지:   ${GREEN}LaminateModeller-Linux-x64.tar.gz${NC}"
    echo -e ""
    echo -e "${YELLOW}사용 방법:${NC}"
    echo -e "  실행: ./dist_nuitka/KooMeshModeller"
    echo -e "  배포: LaminateModeller-Linux-x64.tar.gz 파일을 전달"
fi

if [ "$BUILD_METHOD" = "pyinstaller" ] || [ "$BUILD_METHOD" = "both" ]; then
    echo -e ""
    echo -e "${YELLOW}PyInstaller 파일:${NC}"
    echo -e "  - ${GREEN}dist/KooMeshModeller${NC}"
fi
