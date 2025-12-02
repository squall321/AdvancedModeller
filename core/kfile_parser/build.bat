@echo off
REM ===============================================================================
REM K-File Parser 빌드 스크립트 (Windows)
REM
REM 사용법:
REM   build.bat          - 기본 빌드
REM   build.bat clean    - 빌드 파일 정리
REM   build.bat test     - 빌드 후 테스트 실행
REM   build.bat all      - 정리 + 빌드 + 테스트
REM ===============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ================================================
echo   K-File Parser 빌드 스크립트 (Windows)
echo ================================================
echo.

if "%1"=="clean" goto :clean
if "%1"=="test" goto :test
if "%1"=="all" goto :all
goto :build

:clean
echo 빌드 파일 정리 중...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist *.egg-info rmdir /s /q *.egg-info 2>nul
del /q *.pyd 2>nul
del /q kfile_parser\*.pyd 2>nul
if exist kfile_parser\__pycache__ rmdir /s /q kfile_parser\__pycache__ 2>nul
if exist tests\__pycache__ rmdir /s /q tests\__pycache__ 2>nul
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
echo [OK] 정리 완료
if "%1"=="clean" goto :end
goto :eof

:check_deps
echo 의존성 확인 중...

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않거나 PATH에 없습니다
    echo         https://www.python.org/downloads/ 에서 설치하세요
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM pip 확인
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip가 설치되어 있지 않습니다
    exit /b 1
)
echo [OK] pip 설치됨

REM Visual Studio 빌드 도구 확인
where cl >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MSVC 컴파일러를 찾을 수 없습니다
    echo          Visual Studio Build Tools가 필요합니다:
    echo          https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo          또는 Developer Command Prompt에서 실행하세요
    echo.
)

REM pybind11 설치
echo pybind11 설치 확인...
python -m pip install pybind11 -q
if errorlevel 1 (
    echo [ERROR] pybind11 설치 실패
    exit /b 1
)
echo [OK] pybind11 설치됨
echo.
goto :eof

:build
call :check_deps
if errorlevel 1 exit /b 1

echo C++ 확장 모듈 빌드 중...
python setup.py build_ext --inplace
if errorlevel 1 (
    echo.
    echo [ERROR] 빌드 실패!
    echo.
    echo 해결 방법:
    echo   1. Visual Studio Build Tools 설치
    echo   2. Developer Command Prompt에서 실행
    echo   3. 또는 Python 폴백 파서 사용 (C++ 빌드 없이 작동)
    exit /b 1
)

echo.
echo [OK] 빌드 완료!
echo.

REM 빌드 결과 확인
if exist kfile_parser\_kfile_parser*.pyd (
    echo 생성된 파일:
    dir /b kfile_parser\_kfile_parser*.pyd
) else (
    echo [WARNING] .pyd 파일이 생성되지 않았습니다
)

goto :usage

:test
call :check_deps
if errorlevel 1 exit /b 1
call :build
if errorlevel 1 exit /b 1
echo.
echo 테스트 실행 중...
python tests\test_parser.py
goto :end

:all
call :clean
call :check_deps
if errorlevel 1 exit /b 1
call :build
if errorlevel 1 exit /b 1
echo.
echo 테스트 실행 중...
python tests\test_parser.py
goto :usage

:usage
echo.
echo ================================================
echo   사용법
echo ================================================
echo.
echo   # 이 프로젝트에서 사용
echo   from core.kfile_parser import KFileParser
echo.
echo   # 또는 KooDynaKeyword 호환 방식
echo   from core.KooDynaKeyword import KFileReader
echo.
echo ================================================
echo   배포 방법
echo ================================================
echo.
echo   KooDynaKeyword.py와 kfile_parser\ 폴더를 함께 복사
echo.
goto :end

:end
echo.
echo [OK] 완료!
echo.
pause
