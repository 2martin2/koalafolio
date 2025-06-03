@echo off
echo Building and testing koalafolio package...
echo usage: tools\build_test_package.bat [--skip-upload]

REM Check for --skip-upload argument
set skip_upload=false
if "%~1"=="--skip-upload" (
    set skip_upload=true
    echo Skipping upload to Test PyPI.
) else (
    echo Uploading to Test PyPI.
)

set start_dir=%cd%

REM Switch to project root
set project_root="%~dp0.."
set project_parent_dir="%~dp0../.."
cd /d %project_root%
REM print dir
echo project root: %cd%

REM Clean previous builds
cd %project_parent_dir%
rmdir /s /q test_koala_venv
if %ERRORLEVEL% neq 0 (
    echo Failed to remove previous test environment!
    exit /b 1
)
cd %project_root%
REM check skip upload
if "%skip_upload%"=="true" (
    echo Skipping upload to Test PyPI.
    REM goto start_test
    goto start_test
)
rmdir /s /q dist
rmdir /s /q build


:build
REM call tools/addBuildNrForTest.py to set test version
python tools\addBuildNrForTest.py add
if %ERRORLEVEL% neq 0 (
    echo Failed to add build number!
    exit /b 1
)

REM Build package
python setup.py sdist bdist_wheel
if %ERRORLEVEL% neq 0 (
    echo Build failed!
    exit /b 1
)

REM Check package
python -m twine check dist/*
if %ERRORLEVEL% neq 0 (
    echo Package check failed!
    exit /b 1
)


:upload
REM Upload to Test PyPI
python -m twine upload --repository testpypi dist/*
if %ERRORLEVEL% neq 0 (
    echo Upload to Test PyPI failed!
    exit /b 1
)

REM call tools/addBuildNrForTest.py to remove test version
python tools\addBuildNrForTest.py remove
if %ERRORLEVEL% neq 0 (
    echo Failed to remove build number!
    exit /b 1
)

:start_test
REM Create virtual environment for testing one folder up
cd %project_parent_dir%
python -m venv test_koala_venv
cd test_koala_venv
set venv_dir=%cd%
echo venv root: %cd%
call Scripts\activate.bat

REM Install package dependencies first (since testpypi might not have all dependencies)
pip install ccxt openpyxl "pandas>=1.5.3" "pycoingecko<=2.3.0" pycryptodomex pyqt5 pyqtchart requests "tzlocal>=5.0.1" xlrd pytest

REM Install the package from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps koalafolio

REM check installed version of koalafolio
pip show koalafolio

REM Basic import test
python -c "from koalafolio import gui_root; print('Package import successful!')"
if %ERRORLEVEL% neq 0 (
    echo Package import test failed!
    deactivate
    exit /b 1
)

REM copy test_scripts from project_root/koalafolio/tests into test environment
mkdir koalafolio\tests
xcopy /s /i /y "%project_root%\tests\*" "%venv_dir%\tests"
if %ERRORLEVEL% neq 0 (
    echo Failed to copy test scripts!
    deactivate
    exit /b 1
)

REM run all test files in tests
python -m pytest "%venv_dir%\tests" --tb=short --disable-warnings
if %ERRORLEVEL% neq 0 (
    echo Test suite failed!
    deactivate
    exit /b 1
)

REM start gui with data path to test_data and wait for close
python -m koalafolio.gui_root --datadir "%project_parent_dir%\koalafolio_testdata\koalaData" --username testUser

echo Package build, upload and test completed successfully!
deactivate

REM Clean up test environment
cd %project_parent_dir%
rmdir /s /q test_koala_venv
cd %start_dir%