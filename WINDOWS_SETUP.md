# Windows 설치 및 실행 가이드

## 빠른 시작 (Quick Start)

### 1단계: Python 설치 확인
```cmd
python --version
```
- Python 3.8 이상이 필요합니다
- 없다면 [python.org](https://www.python.org/downloads/)에서 설치

### 2단계: 가상환경 생성 (최초 1회만)
```cmd
python -m venv venv
```

### 3단계: 프로그램 실행
```cmd
run_gui.bat
```
- 더블클릭하거나 명령프롬프트에서 실행
- 첫 실행 시 필수 패키지가 자동으로 설치됩니다 (시간이 걸릴 수 있음)

---

## 상세 설치 가이드

### 필수 요구사항
- **Python**: 3.8 이상 (3.10 권장)
- **운영체제**: Windows 10/11
- **디스크 공간**: 약 500MB (가상환경 포함)

### 수동 설치

#### 1. 저장소 클론 또는 다운로드
```cmd
git clone https://github.com/squall321/AdvancedModeller.git
cd AdvancedModeller
```

#### 2. 가상환경 생성 및 활성화
```cmd
python -m venv venv
venv\Scripts\activate
```

#### 3. 필수 패키지 설치
```cmd
pip install -r requirements.txt
```

설치되는 패키지:
- **PySide6**: Qt 기반 GUI 프레임워크
- **PyOpenGL**: 3D 그래픽 렌더링
- **numpy, scipy, pandas**: 과학 계산
- **matplotlib**: 데이터 시각화
- **qtawesome**: 아이콘 라이브러리

#### 4. 프로그램 실행
```cmd
python -m gui.main
```

또는 배치 파일 사용:
```cmd
run_gui.bat
```

---

## 문제 해결 (Troubleshooting)

### 1. ModuleNotFoundError: No module named 'OpenGL'
**원인**: PyOpenGL이 설치되지 않음

**해결**:
```cmd
venv\Scripts\activate
pip install PyOpenGL PyOpenGL-accelerate
```

### 2. ModuleNotFoundError: No module named 'PySide6'
**원인**: PySide6가 설치되지 않음

**해결**:
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 'python'은(는) 내부 또는 외부 명령이 아닙니다
**원인**: Python이 PATH에 없음

**해결**:
1. Python 재설치 시 "Add Python to PATH" 체크
2. 또는 수동으로 PATH 추가:
   - `제어판` → `시스템` → `고급 시스템 설정` → `환경 변수`
   - `Path`에 Python 설치 경로 추가 (예: `C:\Python310\`)

### 4. DLL 로드 실패 오류
**원인**: Visual C++ 재배포 패키지 누락

**해결**:
Microsoft Visual C++ 재배포 패키지 설치:
- [다운로드 링크](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

### 5. OpenGL 렌더링 오류
**원인**: 그래픽 드라이버 문제

**해결**:
1. 그래픽 카드 드라이버 최신 버전으로 업데이트
2. 또는 소프트웨어 렌더링 모드 사용:
   ```cmd
   set LIBGL_ALWAYS_SOFTWARE=1
   python -m gui.main
   ```

---

## 실행 파일 빌드 (배포용)

### Nuitka로 단일 실행파일 만들기

#### 1. Nuitka 설치
```cmd
pip install nuitka ordered-set zstandard
```

#### 2. 빌드 실행
```cmd
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-disable-console ^
    --output-dir=dist_nuitka ^
    --include-data-dir=config=config ^
    --include-package=gui.modules.advanced_laminate ^
    --include-package=gui.modules.advanced_contact ^
    --include-package=gui.modules.adjacent_parts_viewer ^
    gui/main.py
```

#### 3. 실행파일 위치
- 빌드 완료 후: `dist_nuitka\main.exe`
- 파일명 변경: `KooMeshModeller.exe`

#### 빌드 결과
- ✅ Python 설치 불필요
- ✅ 모든 의존성 포함
- ✅ 단일 실행파일 (~40-50MB)
- ✅ 포터블 (USB로 복사 가능)

---

## 개발 환경 설정

### VS Code 권장 확장
- Python
- Pylance
- autoDocstring
- Better Comments

### 디버깅 설정 (.vscode/launch.json)
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run GUI",
            "type": "python",
            "request": "launch",
            "module": "gui.main",
            "console": "integratedTerminal"
        }
    ]
}
```

---

## 버전 정보

- **프로젝트**: KooMesh Modeller (Advanced Laminate Modeller)
- **Python**: 3.8 이상
- **PySide6**: 6.5.0 이상
- **OpenGL**: 3.1.10 이상

---

## 추가 도움말

### 로그 확인
프로그램 실행 중 오류가 발생하면 로그를 확인하세요:
- GUI 내 로그 패널에서 확인 가능
- 터미널에서 실행 시 콘솔 출력 확인

### 성능 최적화
- **C++ 파서 사용**: K-file 파싱 속도 향상
- **Voxel 기반 충돌 검사**: DOE 생성 정확도 향상
- **GPU 가속**: OpenGL 3D 렌더링 (GPU 권장)

### 지원 및 문의
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **문서**: `docs/` 폴더 참조

---

## 라이선스
프로젝트 라이선스 정보는 LICENSE 파일을 참조하세요.
