$files = Get-Childitem -Recurse -Force *.PTP
ForEach ($file in $files) {PersonaEditorCMD.exe $file -exptext /sub}