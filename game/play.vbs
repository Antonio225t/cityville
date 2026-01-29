' Ejecutar el archivo .bat
Set objShell = CreateObject("WScript.Shell")
objShell.Run "run_server.bat", 0, False

' Esperar un momento para que el archivo .bat se ejecute
WScript.Sleep 2000

' Abrir el navegador con la dirección fija
objShell.Run """chromium-82-0-4050\chrome-win\chrome.exe"" http://127.0.0.1:5000/", 0, False

' Esperar un momento para que el navegador se abra
WScript.Sleep 5000

' Verificar si el navegador sigue abierto
Do While True
    ' Verificar si el proceso del navegador está en ejecución
    Set colProcesses = GetObject("winmgmts:").ExecQuery("Select * from Win32_Process Where Name = 'chrome.exe'")
    If colProcesses.Count = 0 Then
        ' Si el navegador se cerró, cerrar el proceso específico
        objShell.Run "taskkill /f /im flask.exe", 0, False
        objShell.Run "taskkill /f /im python.exe", 0, False
        Exit Do
    End If
    WScript.Sleep 1000 ' Esperar 1 segundo antes de verificar nuevamente
Loop