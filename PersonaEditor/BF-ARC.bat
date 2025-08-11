$files = Get-Childitem -Recurse -Force *.BF
ForEach ($file in $files) {PersonaEditorCMD.exe $file -impall /sub -save /ovrw}