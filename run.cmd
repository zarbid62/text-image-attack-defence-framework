@echo off
setlocal
if /I "%~1"=="--check" (
	python "%~dp0aegisai_text_injection_test\bootstrap.py" --check
	exit /b %ERRORLEVEL%
)
python "%~dp0aegisai_text_injection_test\bootstrap.py" -- %*
exit /b %ERRORLEVEL%