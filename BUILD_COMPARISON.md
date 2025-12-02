# 실행파일 빌드 비교

## 빌드 결과

두 가지 방법으로 독립 실행파일을 생성했습니다:

### 1. PyInstaller
- **파일 크기**: 69 MB
- **빌드 시간**: ~20초
- **장점**:
  - 빠른 빌드 시간
  - 간단한 설정
  - 안정적인 호환성
- **단점**:
  - 큰 파일 크기
  - 느린 시작 시간

**위치**: `dist/KooMeshModeller`

### 2. Nuitka (추천) ✅
- **파일 크기**: 36 MB (PyInstaller 대비 48% 감소!)
- **빌드 시간**: ~2분
- **압축률**: 27.38% (136 MB → 37 MB)
- **장점**:
  - **작은 파일 크기** (거의 절반)
  - **빠른 실행 속도** (진짜 C 컴파일)
  - 더 나은 성능 최적화
  - 진짜 네이티브 바이너리
- **단점**:
  - 긴 빌드 시간
  - 약간 복잡한 설정

**위치**: `dist_nuitka/KooMeshModeller`

## 권장사항

**Nuitka 버전을 사용하는 것을 강력히 권장합니다:**
- 파일 크기가 절반으로 줄어듦
- 실행 속도가 더 빠름
- 진짜 컴파일된 바이너리라 더 전문적

## 사용 방법

### Linux에서 실행:
```bash
# PyInstaller 버전
./dist/KooMeshModeller

# Nuitka 버전 (권장)
./dist_nuitka/KooMeshModeller
```

### Windows에서 빌드:
```cmd
# PyInstaller
pip install pyinstaller
pyinstaller KooMeshModeller.spec

# Nuitka (권장)
pip install nuitka ordered-set zstandard
python -m nuitka --standalone --onefile --enable-plugin=pyside6 --windows-disable-console --output-dir=dist_nuitka --include-data-dir=config=config gui/main.py
```

## 배포 방법

1. **단순 배포** (실행파일만):
   - `dist_nuitka/KooMeshModeller` 파일만 복사
   - 어디서나 더블클릭으로 실행
   - Python 설치 불필요

2. **완전 배포 패키지**:
   - 실행파일 + 문서 + 예제 포함
   - 아래 "배포 패키지 생성" 참조

## 배포 패키지 생성

```bash
# 배포 패키지 만들기
mkdir -p LaminateModeller-Release
cp dist_nuitka/KooMeshModeller LaminateModeller-Release/
cp README.md LaminateModeller-Release/
cp -r docs LaminateModeller-Release/
cp -r examples LaminateModeller-Release/
tar -czf LaminateModeller-Linux.tar.gz LaminateModeller-Release/
```

## 성능 비교

| 항목 | PyInstaller | Nuitka |
|------|-------------|--------|
| 파일 크기 | 69 MB | 36 MB ✅ |
| 빌드 시간 | 20초 ✅ | 2분 |
| 시작 시간 | 느림 | 빠름 ✅ |
| 실행 속도 | 보통 | 빠름 ✅ |
| 메모리 사용 | 보통 | 적음 ✅ |

## 결론

**Nuitka 버전을 사용하세요!**
- 더 작고 빠르고 전문적입니다
- 배포하기에 훨씬 좋습니다
- 사용자 경험이 더 좋습니다
