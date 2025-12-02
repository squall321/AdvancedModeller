# 빌드 가이드

KooMesh Modeller 개발 환경 설정 및 배포 빌드 절차입니다.

---

## 목차
1. [개발 환경 설정](#개발-환경-설정)
2. [실행 방법](#실행-방법)
3. [배포 빌드 (PyInstaller)](#배포-빌드-pyinstaller)
4. [트러블슈팅](#트러블슈팅)

---

## 개발 환경 설정

### 요구사항
- Python 3.10+
- pip

### 1. 가상환경 생성

```bash
# 프로젝트 폴더로 이동
cd /path/to/LaminateModeller

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
PySide6>=6.5.0
qtawesome>=1.2.0
```

### 3. 추가 의존성 (선택)

```bash
# 배포 빌드용
pip install pyinstaller

# 메시 뷰어용 (향후)
pip install pyvista pyvistaqt
```

---

## 실행 방법

### 개발 모드

```bash
# 가상환경 활성화 후
source venv/bin/activate

# 실행
python -m gui.main
```

### 스크립트로 실행

**Linux/Mac (run_gui.sh):**
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m gui.main
```

**Windows (run_gui.bat):**
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python -m gui.main
```

---

## 배포 빌드 (PyInstaller)

### 1. PyInstaller 설치

```bash
pip install pyinstaller
```

### 2. spec 파일 생성

**koomesh_modeller.spec:**
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 리소스 파일 포함
        ('config', 'config'),
        ('MaterialSource.txt', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'qtawesome',
        # 모듈 자동 임포트
        'gui.modules.advanced_laminate',
        'gui.modules.advanced_contact',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KooMeshModeller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # 아이콘 파일 (선택)
)
```

### 3. 빌드 실행

```bash
# 단일 실행 파일로 빌드
pyinstaller koomesh_modeller.spec

# 또는 폴더 형태로 빌드 (디버깅 용이)
pyinstaller --onedir gui/main.py --name KooMeshModeller --windowed
```

### 4. 빌드 결과

```
dist/
└── KooMeshModeller      # 실행 파일 (Windows: KooMeshModeller.exe)
```

### 간단 빌드 스크립트

**build.sh (Linux/Mac):**
```bash
#!/bin/bash
set -e

echo "=== KooMesh Modeller 빌드 ==="

# 가상환경 활성화
source venv/bin/activate

# 의존성 확인
pip install pyinstaller -q

# 기존 빌드 정리
rm -rf build dist

# 빌드
pyinstaller \
    --onefile \
    --windowed \
    --name KooMeshModeller \
    --add-data "config:config" \
    --add-data "MaterialSource.txt:." \
    --hidden-import gui.modules.advanced_laminate \
    --hidden-import gui.modules.advanced_contact \
    gui/main.py

echo "=== 빌드 완료: dist/KooMeshModeller ==="
```

**build.bat (Windows):**
```batch
@echo off
echo === KooMesh Modeller Build ===

call venv\Scripts\activate

pip install pyinstaller -q

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller ^
    --onefile ^
    --windowed ^
    --name KooMeshModeller ^
    --add-data "config;config" ^
    --add-data "MaterialSource.txt;." ^
    --hidden-import gui.modules.advanced_laminate ^
    --hidden-import gui.modules.advanced_contact ^
    gui/main.py

echo === Build Complete: dist\KooMeshModeller.exe ===
pause
```

---

## 새 모듈 추가 시 빌드 설정

새 모듈을 추가한 경우, `--hidden-import` 에 등록해야 합니다:

```bash
--hidden-import gui.modules.my_new_module
```

또는 spec 파일의 `hiddenimports` 리스트에 추가:

```python
hiddenimports=[
    ...
    'gui.modules.my_new_module',
],
```

---

## 트러블슈팅

### 1. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'gui.modules.xxx'
```

**해결:** `--hidden-import` 또는 spec 파일에 모듈 추가

### 2. qtawesome 아이콘 누락

```python
# spec 파일의 datas에 추가
datas=[
    ...
    (os.path.join(site_packages, 'qtawesome'), 'qtawesome'),
],
```

### 3. PySide6 플러그인 누락

```
qt.qpa.plugin: Could not find the Qt platform plugin "windows"
```

**해결:**
```python
# spec 파일에 추가
from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files('PySide6', include_py_files=False)
```

### 4. 큰 파일 크기

```bash
# UPX 압축 사용
pip install upx
pyinstaller --upx-dir=/path/to/upx ...

# 불필요한 패키지 제외
--exclude-module matplotlib
--exclude-module numpy
```

---

## 배포 체크리스트

- [ ] 가상환경에서 테스트 실행
- [ ] requirements.txt 최신화
- [ ] 새 모듈 hidden-import 추가
- [ ] 리소스 파일 포함 확인 (config, MaterialSource.txt)
- [ ] 빌드 후 실행 테스트
- [ ] 버전 번호 업데이트 (gui/shell.py, sidebar.py)

---

## 버전 관리

버전 번호 위치:
- `gui/shell.py` → `_show_about()` 메서드
- `gui/sidebar.py` → 하단 버전 라벨

```python
# shell.py
"<p>Version 1.0.0</p>"

# sidebar.py
version_label = QLabel("v1.0.0")
```
