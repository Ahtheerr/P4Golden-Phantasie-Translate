# =================================================================================
#    SCRIPT POWERSHELL PARA PROCESSAMENTO PARALELO DE ARQUIVOS PERSONA (v2)
# =================================================================================
# Autor: Seu Nome/Comunidade
# Versão: 2.0
# Descrição: Automatiza a importação de textos para arquivos de jogo usando
#            PersonaEditorCMD.exe, com processamento paralelo para máxima velocidade.
# =================================================================================

# --- Configuração Inicial ---
Clear-Host
$Host.UI.RawUI.WindowTitle = "Processador de Arquivos Persona (PowerShell Paralelo)"

# --- Configuração de Variáveis ---
$EditorCmd      = ".\PersonaEditor\PersonaEditorCMD.exe"
$PythonScript   = ".\XLSX-TSV.py"
$SourceDir      = ".\IN"
$OutputDir      = ".\OUT"
$TextDir        = ".\Text"

# !! IMPORTANTE !!
# Limita quantos arquivos são processados ao mesmo tempo.
# Um bom valor inicial é o número de núcleos da sua CPU (ex: 4, 8, 12).
# Se o seu PC ficar lento, diminua este valor. Se tiver um PC potente, pode aumentar.
$ThrottleLimit = 8

# =================================================================================
#                           INÍCIO DO PROCESSO
# =================================================================================
Write-Host "#######################################################" -ForegroundColor Green
Write-Host "###      INICIANDO SCRIPT DE PROCESSAMENTO      ###" -ForegroundColor Green
Write-Host "#######################################################"
Write-Host

# Bloco principal para capturar erros fatais
try {
    # --- Verificação Inicial ---
    Write-Host "--- Verificando arquivos e pastas necessários..." -ForegroundColor Yellow
    if (-not (Test-Path $EditorCmd))      { throw "ERRO: O programa '$EditorCmd' não foi encontrado!" }
    if (-not (Test-Path $PythonScript))   { throw "ERRO: O script '$PythonScript' não foi encontrado!" }
    if (-not (Test-Path $SourceDir))      { throw "ERRO: A pasta '$SourceDir' não foi encontrada!" }
    Write-Host "--- Verificação concluída com sucesso." -ForegroundColor Green
    Write-Host

    # --- Passo 1: Executar o script Python ---
    Write-Host "-------------------------------------------------------"
    Write-Host "--- Passo 1: Executando script Python (gerador de TXT)..." -ForegroundColor Cyan
    & python.exe $PythonScript
    if ($LASTEXITCODE -ne 0) { throw "O script Python falhou com o código de saída $LASTEXITCODE." }
    Write-Host "--- Script Python executado com sucesso." -ForegroundColor Green
    Write-Host

    # --- Passo 2: Copiar conteúdo de IN para OUT ---
    Write-Host "-------------------------------------------------------"
    Write-Host "--- Passo 2: Copiando arquivos de '$SourceDir' para '$OutputDir'..." -ForegroundColor Cyan
    if (-not (Test-Path $OutputDir)) { New-Item -Path $OutputDir -ItemType Directory | Out-Null }
    Copy-Item -Path "$SourceDir\*" -Destination $OutputDir -Recurse -Force
    Write-Host "--- Cópia concluída." -ForegroundColor Green
    Write-Host

    # --- Passo 3: Executar PersonaEditorCMD.exe (EM PARALELO) ---
    Write-Host "-------------------------------------------------------"
    Write-Host "--- Passo 3: Processando arquivos com PersonaEditorCMD (em paralelo)..." -ForegroundColor Cyan
    Write-Host "AVISO: A ordem das mensagens 'Processando...' pode aparecer misturada. Isso é normal." -ForegroundColor Yellow
    Write-Host "-------------------------------------------------------"

    # [1/11] Importando Nomes para todos os arquivos
    Write-Host "-> [1] Importando nomes de 'Names.txt' para todos os arquivos..."
    $mapArgument = '%OLDNM %NEWNM'
    Get-ChildItem -Path $OutputDir -Recurse -File | ForEach-Object -Parallel {
        $file = $_
        # Dentro de um bloco -Parallel, use $using: para acessar variáveis de fora do escopo.
        & $using:EditorCmd $file.FullName -imptext "$using:TextDir\Names.txt" /sub /map "%OLDNM %NEWNM" -save /ovrw
        # A linha abaixo é opcional, mas útil para ver o progresso.
        Write-Host "  - Nome importado para $($file.Name)"
    } -ThrottleLimit $ThrottleLimit

    # Mapeamento de pastas para os respectivos arquivos de texto.
    # *** TODAS AS EXTENSÕES ATUALIZADAS PARA .TXT ***
    $folderToTxtMap = @{
        "battle"     = "Battle.txt"
        "camp"       = "Camp.txt"
        "commu"      = "commu.txt"
        "Event_Data" = "event_data.txt"
        "event"      = "Events.txt"
        "facility"   = "facility.txt"
        "field"      = "field.txt"
        "title"      = "Title.txt"
    }

    # Loop pelas pastas para importar os textos específicos
    foreach ($folder in $folderToTxtMap.Keys) {
        $textFile = $folderToTxtMap[$folder]
        $fullFolderPath = Join-Path -Path $OutputDir -ChildPath $folder
        
        Write-Host "-> Processando pasta '$folder' com '$textFile'..."
        if (Test-Path $fullFolderPath) {
            Get-ChildItem -Path $fullFolderPath -Recurse -File | ForEach-Object -Parallel {
                $file = $_
                & $using:EditorCmd $file.FullName -imptext "$using:TextDir\$($using:textFile)" /sub -save /ovrw
            } -ThrottleLimit $ThrottleLimit
        } else {
            Write-Warning "AVISO: Pasta '$fullFolderPath' não encontrada. Pulando."
        }
    }

    # [10/11] & [11/11] Comandos para arquivos específicos (não precisam de paralelismo)
    Write-Host "-> Processando arquivos de inicialização..."
    if (Test-Path "$OutputDir\init.bin") {
        & $EditorCmd "$OutputDir\init.bin" -imptext "$TextDir\Title.txt" /sub -save /ovrw
    } else {
        Write-Warning "AVISO: Arquivo 'init.bin' não encontrado. Pulando."
    }
    if (Test-Path "$OutputDir\init_free.bin") {
        & $EditorCmd "$OutputDir\init_free.bin" -imptext "$TextDir\Title.txt" /sub -save /ovrw
    } else {
        Write-Warning "AVISO: Arquivo 'init_free.bin' não encontrado. Pulando."
    }
    Write-Host

    # --- Finalização ---
    Write-Host "-------------------------------------------------------" -ForegroundColor Green
    Write-Host "          PROCESSO CONCLUÍDO COM SUCESSO!          " -ForegroundColor Green
    Write-Host "-------------------------------------------------------" -ForegroundColor Green
}
catch {
    # Este bloco é executado se o comando 'throw' for chamado
    Write-Error "Ocorreu um erro fatal durante a execução do script:"
    Write-Error $_.Exception.Message
}
finally {
    # Este bloco é sempre executado no final, com ou sem erro.
    Write-Host
    Read-Host "Pressione Enter para fechar esta janela..."
}