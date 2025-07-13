@echo off

:: Set initial variables
call :SetVariables
call :SetColors

::-----------------------------Startup-Verifications-----------------------------::
:: - Verify if the files exists and the administrator privileges to define which ::
::      menu will show to the user                                               ::
::-------------------------------------------------------------------------------::
:Verifications
powershell -ExecutionPolicy Bypass exit
SETLOCAL EnableDelayedExpansion
:: Check Administrator Privileges
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :verifyAndCreateFolders
    call :SplashAscii
    goto MainMenu
) else (
    echo Open without admin wrights
    set /p input=%WHITE%: 
    goto end
)

:VerifyAndCreateFolders

echo Verifying required folders...

:: List of required folders
set "RequiredFolders=%InputDir% %OutputDir% %LogDir% %AsciiDir%"

:: Loop through each folder and check if it exists
for %%F in (%RequiredFolders%) do (
    if not exist "%%F" (
        echo Creating folder: %CYAN%"%YELLOW%%%F%CYAN%"%WHITE%
        mkdir "%%F" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo Folder %CYAN%"%YELLOW%%%F%CYAN%" %WHITE%created successfully.
        ) else (
            echo Failed to create folder %CYAN%"%YELLOW%%%F%CYAN%"%WHITE%. Please check permissions.
        )
    ) else (
        echo Folder %CYAN%"%YELLOW%%%F%CYAN%" %WHITE%already exists.
    )
)

exit /b 0


:MainMenu
    setlocal EnableDelayedExpansion
    cls
    call :MainMenuAscii
    :: Array to store the scritps names 
    echo %BLUE%═════════════════════════════════════════════════════════════════════════════════════════════════════════
    echo %YELLOW% "%CYAN%Main menu%YELLOW%"
    echo %BLUE%═════════════════════════════════════════════════════════════════════════════════════════════════════════
    set "input="
    set /a j=1
    :: Read archive lines
    for /f "delims=" %%a in ('dir /b "%InputDir%"') do (
        set "input[!j!]=%%a"
        set /a j+=1
    )
    set /a j-=1
    if !j! EQU 0 (
        echo %RED%Warning %WHITE%- No input files found:%WHITE% Please verify the input folder %CYAN%"%YELLOW%%InputDir%%CYAN%"
        pause>nul|set/p =%WHITE%Press any key to exit...
        exit /b 0
    )
    :: Show option to the user
    echo  %WHITE%Choose a input to run

    echo   !YELLOW![!WHITE!%Exit%!YELLOW!] -!WHITE! Exit program
    call echo   !YELLOW![!WHITE!a!YELLOW!] - %WHITE%Run all inputs
    call echo  -----------------------------------
    set /a index=1
    for /L %%a in (1,1,!j!) do ( 
        @REM call :PrintAuxiliarArchive !input[%%a]! "title.txt" "!YELLOW![!WHITE!%%a!YELLOW!] - !WHITE!%1" "T"
        echo !YELLOW![!WHITE!%%a!YELLOW!] - %WHITE%!input[%%a]!
        set "options[!index!]=!input[%%a]!"
        set /a index+=1
    )

    

    :: Read option and execute script if is valid
    echo %WHITE%
    set /p input=
    if /i "%input%" equ "%Exit%" (
        echo %RED%Exiting program...%WHITE%
        exit /b 0
    ) else if /i %input% LEQ %j% (
        call :runPythonWithInput !options[%input%]!
    ) else if /i "%input%" equ "a" (
        for /L %%a in (1,1,!j!) do ( 
            if exist %InputDir%\!input[%%a]! (
                call :runPythonWithInputNoStop !input[%%a]!
            ) else (
                echo %RED%Input !input[%%a]! does not exist
            )
        )
        pause>nul|set/p =%WHITE%Press any key to go back...
    ) else ( 
        call :inputMissmatch %input%
    )
    goto MainMenu

:runPythonWithInput
    setlocal EnableDelayedExpansion
    cls
    echo %WHITE%Executing python script with input: %YELLOW% %InputDir%%1 
    @REM powershell "Get-Content %InputDir%%1 | python tratamento.py .\bd.csv %OutputDir%%1 | Out-File -FilePath '%LogDir%log_%1.txt'"
    python tratamento.py .\bd.csv %OutputDir%%1 < %InputDir%%1 >  "%LogDir%log_%1.txt" 
    call :CommandMensage %ERRORLEVEL% "Python script executed" "execution of python script"
    pause>nul|set/p =%WHITE%Press any key to go back...
    exit /b 0

:runPythonWithInputNoStop
    setlocal EnableDelayedExpansion
    echo %WHITE%Executing python script with input: %YELLOW% %InputDir%%1
    @REM powershell "Get-Content %InputDir%%1 | python tratamento.py .\bd.csv %OutputDir%%1 | Out-File -FilePath '%LogDir%log_%1.txt'"
    python tratamento.py .\bd.csv %OutputDir%%1 < %InputDir%%1 >  "%LogDir%log_%1.txt"
    call :CommandMensage %ERRORLEVEL% "Python script executed" "execution of python script"
    exit /b 0

:CommandMensage
    if %1 equ 0 (
        echo %GREEN%%~2 succesfully
    ) else (
        echo %RED%An error occurred during the %~3
    )
    exit /b 0

::---------------------------------------------------------------------::
::------------------------------END-SETUP------------------------------::
::---------------------------------------------------------------------::

:end
    pause>nul|set/p =%WHITE%Press any key to close program...
    exit
:: Style functions

:SplashAscii
echo %BLUE%
@REM for /f "tokens=*" %%a in (%AsciiDir%\splashFull.txt) do ( echo %%a )
echo ╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
echo ║													║
echo ║													║  
echo ║      ██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗	                                        ║
echo ║      ██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║	                                        ║
echo ║      ██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║	                                        ║
echo ║      ██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║	                                        ║
echo ║      ██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║	                                        ║
echo ║      ╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝	                                        ║
echo ║													║
echo ║			██████╗ ██╗   ██╗███╗   ██╗███╗   ██╗███████╗██████╗  				║
echo ║			██╔══██╗██║   ██║████╗  ██║████╗  ██║██╔════╝██╔══██╗				║
echo ║			██████╔╝██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝				║
echo ║			██╔══██╗██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗				║
echo ║			██║  ██║╚██████╔╝██║ ╚████║██║ ╚████║███████╗██║  ██║				║
echo ║			╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝	%CYAN%V %Version%%BLUE%			║
echo ║ %CYAN%Made by LuisAugusto0 (GitHub)%BLUE%										║
echo ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝         

pause>nul|set/p =%CYAN%Press any key to start...
exit /b 0

:ErrorAscii
echo %BLUE%
for /f "tokens=*" %%a in (%AsciiDir%\erro.txt) do ( echo %%a )   
echo %WHITE%                   
exit /b 0

:SetupAscii
echo %BLUE%
for /f "tokens=*" %%a in (.\asciiArts\setup.txt) do ( echo %%a )
echo %WHITE%
exit /b 0

:MainMenuAscii
echo %BLUE%
for /f "tokens=*" %%a in (%AsciiDir%\menu.txt) do ( echo %%a )
echo %WHITE%
exit /b 0

:ModuleAscii
echo %BLUE%
for /f "tokens=*" %%a in (%AsciiDir%\modules.txt) do ( echo %%a )
echo %WHITE%
exit /b 0

:ScriptAscii
echo %BLUE%
for /f "tokens=*" %%a in (%AsciiDir%\splash.txt) do ( echo %%a )
echo %WHITE%
exit /b 0

:RestorePointAscii
echo %BLUE%
for /f "tokens=*" %%a in (%AsciiDir%\restore.txt) do ( echo %%a )
echo %WHITE%
exit /b 0

:inputMissmatch
cls
call :ErrorAscii
echo Input '%1' does not correspond to any option in menu
pause > nul|set/p =%WHITE%Press any key and try again...
exit /b 0

::SET

:SetColors
:: Color and other ascii support config
chcp 65001 >nul 2>&1
mode con lines=60 cols=140
title WindowScript Setup
for /f "tokens=*" %%a in ('echo prompt $E^|cmd') do set "ESC=%%a"
:: Colors
set BLACK=%ESC%[30m
set RED=%ESC%[31m
set GREEN=%ESC%[32m
set YELLOW=%ESC%[33m
set BLUE=%ESC%[34m
set MAGENTA=%ESC%[35m
set CYAN=%ESC%[36m
set WHITE=%ESC%[37m
@REM set BRIGHT_BLACK=%ESC%[90m
@REM set BRIGHT_RED=%ESC%[91m
@REM set BRIGHT_GREEN=%ESC%[92m
@REM set BRIGHT_YELLOW=%ESC%[93m
@REM set BRIGHT_BLUE=%ESC%[94m
@REM set BRIGHT_MAGENTA=%ESC%[95m
@REM set BRIGHT_CYAN=%ESC%[96m
@REM set BRIGHT_WHITE=%ESC%[97m
exit /b 0

:: Common variables
:SetVariables
set "StartDir="
set "InputDir=input\"
set "OutputDir=output\"
set "LogDir=output\logs\"
set "AsciiDir=asciiArts\"



set "Version=1.0"
set /a input=0
set /a Exit=0

@REM :: Creating a Newline variable (the two blank lines are required!)
@REM set NLM=^


@REM set NL=^^^%NLM%%NLM%^%NLM%%NLM%
exit /b 0