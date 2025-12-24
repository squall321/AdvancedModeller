@echo off
REM ===============================================
REM KooMesh Modeller - Windows 실행 스크립트
REM ===============================================

cd /d "%~dp0"

echo ===============================================
echo   KooMesh Modeller 시작
echo ===============================================
echo.

REM 가상환경 존재 여부 확인
if not exist "venv\" (
    echo [오류] venv 폴더를 찾을 수 없습니다.
    echo 먼저 가상환경을 생성해주세요:
    echo   python -m venv venv
    echo.
    pause
    exit /b 1
)

REM 가상환경 활성화
echo [1/3] 가상환경 활성화 중...
call venv\Scripts\activate
if errorlevel 1 (
    echo [오류] 가상환경 활성화 실패
    pause
    exit /b 1
)

REM 필수 패키지 설치 확인 및 설치
echo [2/3] 필수 패키지 확인 중...
python -c "import OpenGL" 2>nul
if errorlevel 1 (
    echo [알림] 필수 패키지가 설치되지 않았습니다.
    echo [알림] requirements.txt에서 패키지 설치 중... (시간이 걸릴 수 있습니다)
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [오류] 패키지 설치 실패
        pause
        exit /b 1
    )
) else (
    echo [완료] 필수 패키지 확인 완료
)

REM 프로그램 실행
echo [3/3] 프로그램 실행 중...
echo.
python -m gui.main
if errorlevel 1 (
    echo.
    echo [오류] 프로그램 실행 중 오류가 발생했습니다.
    pause
)
