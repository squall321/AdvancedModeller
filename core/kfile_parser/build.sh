#!/bin/bash
#===============================================================================
# K-File Parser 빌드 스크립트 (Linux/Mac)
#
# 사용법:
#   ./build.sh          # 기본 빌드
#   ./build.sh clean    # 빌드 파일 정리
#   ./build.sh test     # 빌드 후 테스트 실행
#   ./build.sh all      # 정리 + 빌드 + 테스트
#===============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  K-File Parser 빌드 스크립트${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 정리 함수
clean() {
    echo "빌드 파일 정리 중..."
    rm -rf build/ dist/ *.egg-info/
    rm -f *.so *.pyd
    rm -f kfile_parser/*.so kfile_parser/*.pyd
    rm -rf kfile_parser/__pycache__/
    rm -rf tests/__pycache__/
    rm -rf __pycache__/
    print_success "정리 완료"
}

# 의존성 확인 함수
check_dependencies() {
    echo "의존성 확인 중..."

    # Python 확인
    if ! command -v python3 &> /dev/null; then
        print_error "Python3가 설치되어 있지 않습니다"
        exit 1
    fi
    print_success "Python3: $(python3 --version)"

    # pip 확인
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip가 설치되어 있지 않습니다"
        exit 1
    fi

    # C++ 컴파일러 확인
    if command -v g++ &> /dev/null; then
        print_success "g++: $(g++ --version | head -1)"
    elif command -v clang++ &> /dev/null; then
        print_success "clang++: $(clang++ --version | head -1)"
    else
        print_warning "C++ 컴파일러를 찾을 수 없습니다. 빌드가 실패할 수 있습니다."
    fi

    # pybind11 설치/확인
    echo "pybind11 설치 확인..."
    python3 -m pip install pybind11 -q
    print_success "pybind11 설치됨"

    echo ""
}

# 빌드 함수
build() {
    echo "C++ 확장 모듈 빌드 중..."
    python3 setup.py build_ext --inplace

    # 빌드 결과 확인
    if ls kfile_parser/*.so 1> /dev/null 2>&1 || ls kfile_parser/*.pyd 1> /dev/null 2>&1; then
        print_success "빌드 완료!"
        echo ""
        echo "생성된 파일:"
        ls -la kfile_parser/*.so 2>/dev/null || ls -la kfile_parser/*.pyd 2>/dev/null || true
    else
        print_error "빌드 파일이 생성되지 않았습니다"
        exit 1
    fi
}

# 테스트 함수
run_tests() {
    echo ""
    echo "테스트 실행 중..."
    python3 tests/test_parser.py
}

# 사용법 출력
print_usage() {
    echo ""
    echo -e "${GREEN}사용법:${NC}"
    echo "  # 이 프로젝트에서 사용"
    echo "  from core.kfile_parser import KFileParser"
    echo ""
    echo "  # 또는 KooDynaKeyword 호환 방식"
    echo "  from core.KooDynaKeyword import KFileReader"
    echo ""
    echo -e "${GREEN}배포 방법:${NC}"
    echo "  KooDynaKeyword.py와 kfile_parser/ 폴더를 함께 복사"
    echo ""
}

# 메인 로직
print_header

case "${1:-build}" in
    clean)
        clean
        ;;
    test)
        check_dependencies
        build
        run_tests
        ;;
    all)
        clean
        check_dependencies
        build
        run_tests
        print_usage
        ;;
    build|*)
        check_dependencies
        build
        print_usage
        ;;
esac

echo ""
print_success "완료!"
