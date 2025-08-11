$files = Get-Childitem -Recurse -Force *.ARC
ForEach ($file in $files) {PersonaEditorCMD.exe $file -expbf /sub}