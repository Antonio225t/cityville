This guide will help you set up and install the game.
Readme date: 10 September 2025

WARNING: WINDOWS ONLY!!!


==================
1. INSTALL FLASH
==================

Simply double click on the file "flashplayer32_0r0_371_winpep.exe" and wait for the window to pop-up.
Check the "I have read and agree the terms of..." box and click the "INSTALL" button on the
bottom right.

After it installs check the "Never check for updates" box and click "DONE".


===================
2. INSTALL PYTHON
===================

Open this website: "https://www.python.org/downloads/" and hit the "Download Python" button.
After it downloads open it and check the "Add python.exe to PATH" box at the bottom,
then click on "Install now" and wait until it finishes installing.

After it installs click the "Done" button and it should close.


=========================
3. INSTALL REQUIREMENTS
=========================

In this folder (the folder where this README.txt file is located) hold the SHIFT key on your
keyboard and right-click on a blank space of the folder. Then select "Open PowerShell window here"

Inside of the PowerShell window type this command "pip install -r .\requirements.txt" and press
enter; if you see some green texts it means that it's install all the required packages in order
to run the game (if this command is not showing any text, please go read the FAQ & Troubleshooting
section down below).

After it finishes installing the packages (to check if it's done installing them check if the last
line of PowerShell starts with "PS", if it does it means it's done installing) you can close the
PowerShell window.


========================
4. FLASH BROWSER SETUP
========================

When you want to play the game, you can start it by going on the "game" folder and double
clicking the "play.vbs" file; if it asks you to run some applications click on "Open".

You should see that a browser opened up at a white page with a Flash icon. Click the Flash
icon and when a pop-up appears saying "<link> wants to Run Flash" click on "Allow", then click
on "Run this time" and you should have the game.

WARNING: DO NOT USE THIS BROWSER TO SURF THE INTERNET AS IT'S OUTDATED!!!











======================================================
  Frequently Asked Questions (FAQ) & Troubleshooting
======================================================

**** DO I NEED TO DO ALL THESE STEPS EVERY TIME I WANT TO RUN THE GAME? ****

No you don't. When you install everything you can simply just go in the "game" folder and
double click the "play.vbs" file, similar to step 5.



**** THE BROWSER DOESN'T RUN FLASH! ****

If your game doesn't run then in the browser before the "127.0.0.1:5000" link click the "ⓘ"
and click on "Site settings"; Find the "Flash" text and change the permission to "Allow".
Go back and refresh the page. It should work.

If you're confused check this message with images on our discord server:
 → https://discord.com/channels/536575691563466772/927596177774493766/1367575764303614082



**** IT SAYS "This site cannot be reached" WHEN CLICKING ON THE PLAY.VBS FILE! ****

If the browser says that, it means that the python server is not running.
This is how you can fix this issue:

> Open a PowerShell terminal:
  Open the "server" folder then holding the SHIFT key on your keyboard and right-click on a
  blank space of the folder. Then select "Open PowerShell window here".

> Check if python is correctly installed:
  Type "python --version" and press enter, if you see an error like "python : The term 'python' is
  not recognized..." it means that you need to install python, go on step 2 almost at the start of
  this file.

> Check if flask is installed:
  If it doesn't give you an error then type "python -m flask run" and press enter. If it says
  something like "python.exe: No module named flask" then flask is not installed.

> Install flask:
  Type "pip install flask" and press enter to install flask. Then run "python -m flask run" again
  and if it says "Press CTRL+C to quit" then press & hold the "CTRL" key on your keyboard, while
  still holding it press the "C" key and the problem is solved. You can close the PowerShell and
  double click the "play.vbs" file.



**** IT STILL DOESN'T WORK! ****

If something isn't right feel free to join our discord server:
 → https://discord.gg/xrNE6Hg
 → #cityville
Please be kind :D



**** HOW DO I ADD NEIGHBOUR? ****

At the moment it's not possible to add neighbour, It'll probably be possible later in the
development.



**** ARE THERE GOING TO BE MORE BUILDINGS? ****

Absolutely, when we're going to find more and more assets, we'll add them in the game.



**** WHEN ARE YOU GOING TO SUPPORT MACOS, LINUX, ANDROID, (OTHER PLATFORMS)? ****

It currently only works for Windows, but when we'll have the required technology in order to
run Flash games without having to install Flash on your machine, then other platform will 99%
be supported.



**** DOES THE GAME SAVE MY PROGRESS? ****

Yes it does. When you close & re-open the game, you'll continue from where you left.



**** THE COMMAND "pip install -r .\requirements.txt" DOESN'T WORK! ****

Try to type "python -m pip install -r .\requirements.txt" instead. I do not know why the "pip"
command sometimes does not work properly.

If even this doesn't work, try re-installing python from step 2.



**** I WANT TO CONTRIBUTE, HOW CAN I? ****

Thank you so much! We're happy that you want to contribute to preserve this amazing game!
You can first off join our discord server and you can:
 1. Search for missing assets in old computers that you used to play the game;
 2. Help with translations;
 3. Update the "gamesettings.xml" file to include more buildings.
