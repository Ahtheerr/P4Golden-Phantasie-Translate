@echo off
rem Este comando executa o script PowerShell, ignorando a política de execução apenas para esta sessão.
pwsh.exe -ExecutionPolicy Bypass -File "%~dp0\Compilar.ps1"
pause