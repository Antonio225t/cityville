@echo off
title CityVille Server
cd server
python "./app.py"
if %ERRORLEVEL% GTR 0 (
	echo "An error occurred!"
	pause
)
