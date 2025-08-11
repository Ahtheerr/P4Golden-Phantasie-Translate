$files = Get-Childitem -Recurse -Force *.BMD
ForEach ($file in $files) {PersonaEditorCMD.exe $file -expptp /sub}