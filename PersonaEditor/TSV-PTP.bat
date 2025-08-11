$files = Get-Childitem -Recurse -Force *.PTP
ForEach ($file in $files) {PersonaEditorCMD.exe $file -imptext /sub /auto 600 -save /ovrw}