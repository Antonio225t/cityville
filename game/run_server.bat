@echo off
title CityVille Server
cd server
python -m flask run
if %ERRORLEVEL% GTR 0 (
	echo "An error occurred!"
	pause
)
