@echo off
REM ===============================================
REM KooMesh Modeller - Windows 빌드 스크립트
REM ===============================================

chcp 65001 > nul
cd /d "%~dp0"

echo ===============================================
echo   KooMesh Modeller - Windows 빌드
echo ===============================================
echo.

REM 빌드 방법 선택
set BUILD_METHOD=%1
if "%BUILD_METHOD%"=="" set BUILD_METHOD=nuitka

echo [설정] 빌드 방법: %BUILD_METHOD%
echo.

REM 가상환경 활성화
if not exist "venv\" (
    echo [오류] venv 폴더를 찾을 수 없습니다.
    echo 먼저 가상환경을 생성해주세요:
    echo   python -m venv venv
    pause
    exit /b 1
)

echo [1/4] 가상환경 활성화 중...
call venv\Scripts\activate
if errorlevel 1 (
    echo [오류] 가상환경 활성화 실패
    pause
    exit /b 1
)

REM 빌드 방법에 따라 분기
if /i "%BUILD_METHOD%"=="pyinstaller" goto BUILD_PYINSTALLER
if /i "%BUILD_METHOD%"=="nuitka" goto BUILD_NUITKA
if /i "%BUILD_METHOD%"=="both" goto BUILD_BOTH

echo [오류] 알 수 없는 빌드 방법: %BUILD_METHOD%
echo 사용법: build.bat [pyinstaller^|nuitka^|both]
pause
exit /b 1

:BUILD_PYINSTALLER
echo ===============================================
echo   PyInstaller 빌드
echo ===============================================
echo.

REM PyInstaller 설치
echo [2/4] PyInstaller 설치 확인 중...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [알림] PyInstaller 설치 중...
    pip install pyinstaller
    if errorlevel 1 (
        echo [오류] PyInstaller 설치 실패
        pause
        exit /b 1
    )
)

REM 이전 빌드 정리
echo [3/4] 이전 빌드 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM PyInstaller 빌드 실행
echo [4/4] 빌드 실행 중 (시간이 걸립니다...)
echo.
pyinstaller ^
    --onefile ^
    --windowed ^
    --name KooMeshModeller ^
    --add-data "config;config" ^
    --hidden-import gui.modules.advanced_laminate ^
    --hidden-import gui.modules.advanced_contact ^
    --hidden-import gui.modules.adjacent_parts_viewer ^
    --hidden-import gui.modules.file_loader ^
    --hidden-import gui.modules.model_viewer ^
    gui/main.py

if errorlevel 1 (
    echo.
    echo [오류] PyInstaller 빌드 실패
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   PyInstaller 빌드 완료!
echo ===============================================
echo.
echo 실행 파일: dist\KooMeshModeller.exe
dir dist\KooMeshModeller.exe
echo.
goto END

:BUILD_NUITKA
echo ===============================================
echo   Nuitka 빌드 (최적화, 시간이 오래 걸림)
echo ===============================================
echo.

REM Nuitka 설치
echo [2/4] Nuitka 및 의존성 설치 확인 중...
pip show nuitka >nul 2>&1
if errorlevel 1 (
    echo [알림] Nuitka 설치 중...
    pip install nuitka ordered-set zstandard
    if errorlevel 1 (
        echo [오류] Nuitka 설치 실패
        pause
        exit /b 1
    )
)

REM 이전 빌드 정리
echo [3/4] 이전 빌드 정리 중...
if exist dist_nuitka rmdir /s /q dist_nuitka

REM Nuitka 빌드 실행
echo [4/4] 빌드 실행 중... (최적화로 인해 10-20분 소요)
echo.
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
    --include-package=gui.modules.file_loader ^
    --include-package=gui.modules.model_viewer ^
    --assume-yes-for-downloads ^
    gui/main.py

if errorlevel 1 (
    echo.
    echo [오류] Nuitka 빌드 실패
    pause
    exit /b 1
)

REM 파일명 변경
echo.
echo [정리] 파일명 변경 중...
if exist dist_nuitka\main.exe (
    move /y dist_nuitka\main.exe dist_nuitka\KooMeshModeller.exe
)

echo.
echo ===============================================
echo   Nuitka 빌드 완료!
echo ===============================================
echo.
echo 실행 파일: dist_nuitka\KooMeshModeller.exe
dir dist_nuitka\KooMeshModeller.exe
echo.
echo [참고] Nuitka는 최적화된 네이티브 코드를 생성하여
echo       PyInstaller보다 빠르고 크기가 작습니다.
echo.
goto END

:BUILD_BOTH
echo ===============================================
echo   양쪽 빌드 (PyInstaller + Nuitka)
echo ===============================================
echo.
call :BUILD_PYINSTALLER
echo.
echo.
call :BUILD_NUITKA
goto END

:END
echo ===============================================
echo   빌드 프로세스 완료
echo ===============================================
echo.
if exist dist\KooMeshModeller.exe (
    echo [PyInstaller] dist\KooMeshModeller.exe
)
if exist dist_nuitka\KooMeshModeller.exe (
    echo [Nuitka]      dist_nuitka\KooMeshModeller.exe
)
echo.
echo 사용법:
echo   build.bat              - Nuitka 빌드 (기본, 권장)
echo   build.bat pyinstaller  - PyInstaller 빌드 (빠름)
echo   build.bat nuitka       - Nuitka 빌드 (최적화)
echo   build.bat both         - 양쪽 빌드
echo.
pause
