# ==============================================================================
# Script de Instalação Automática - Tradução Persona 4 Golden (Phantasie Translate)
# Execução: irm <link-raw-do-github> | iex
# ==============================================================================

# Força o uso do TLS 1.2+ para evitar problemas na API do GitHub no PowerShell 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 1. Função para invocar a janela do Windows Explorer e pedir a pasta
function Get-FolderBrowser {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Selecione a pasta raiz do Persona 4 Golden"
    $dialog.ShowNewFolderButton = $false
    
    # Tenta trazer a janela para frente
    $form = New-Object System.Windows.Forms.Form
    $form.TopMost = $true
    
    if ($dialog.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {
        return $dialog.SelectedPath
    }
    return $null
}

# Pergunta a versão do jogo via terminal
$title = "Instalador da Tradução - Phantasie Translate"
$message = "Qual a versão do seu Persona 4 Golden?"
$choices = [System.Management.Automation.Host.ChoiceDescription[]] @(
    "&1. 64-bits (Versão mais atual/Steam)",
    "&2. 32-bits (Versão antiga)"
)
$decision = $host.ui.PromptForChoice($title, $message, $choices, 0)
$is64Bit = ($decision -eq 0)

$gamePath = $null

# 1.1 - Lógica de busca de diretório
if ($is64Bit) {
    Write-Host "`nProcurando a pasta do jogo automaticamente..." -ForegroundColor Cyan
    $pathsToTest = @("C:\Program Files (x86)\Steam\steamapps\common\Persona 4 Golden")
    
    # Busca por 'SteamLibrary' em todos os discos menos o C:
    $otherDrives = Get-PSDrive -PSProvider FileSystem | Where-Object Name -ne 'C'
    foreach ($drive in $otherDrives) {
        $pathsToTest += "$($drive.Name):\SteamLibrary\steamapps\common\Persona 4 Golden"
    }

    foreach ($path in $pathsToTest) {
        if (Test-Path $path) {
            $gamePath = $path
            break
        }
    }
    
    # Se não achou na busca rápida, aciona o Explorer
    if (-not $gamePath) {
        Write-Host "O jogo não foi encontrado nos caminhos padrão da Steam." -ForegroundColor Yellow
        Write-Host "Abrindo o explorador de arquivos para você selecionar a pasta manualmente..." -ForegroundColor Yellow
        $gamePath = Get-FolderBrowser
    }
} else {
    # Versão 32-bits vai direto pro explorer
    Write-Host "`nAbrindo o explorador de arquivos para você selecionar a pasta do jogo..." -ForegroundColor Yellow
    $gamePath = Get-FolderBrowser
}

# Verifica se o usuário cancelou a janela de seleção
if (-not $gamePath) {
    Write-Host "Instalação cancelada: Nenhuma pasta foi selecionada." -ForegroundColor Red
    exit
}

Write-Host "Pasta de destino: $gamePath`n" -ForegroundColor Green

# 1.2 - Conecta na API do GitHub para pegar o release mais recente
Write-Host "Buscando a versão mais recente da tradução no GitHub..." -ForegroundColor Cyan
$repoUrl = "https://api.github.com/repos/Ahtheerr/P4Golden-Phantasie-Translate/releases/latest"
$release = Invoke-RestMethod -Uri $repoUrl

# Filtra o arquivo correto baseado na escolha do usuário
if ($is64Bit) { # Se a pessoa escolheu a opção 1 (64-bits)
    # Pega o asset que NÃO tem '32-bits' no nome
    $asset = $release.assets | Where-Object { $_.name -notmatch "32-bits" }
} else { # Se a pessoa escolheu a opção 2 (32-bits)
    # Pega o asset que TEM '32-bits' no nome
    $asset = $release.assets | Where-Object { $_.name -match "32-bits" }
}

if (-not $asset) {
    Write-Host "Erro: Não foi possível encontrar o arquivo .zip para essa versão no último release do GitHub." -ForegroundColor Red
    exit
}

# Pega o link exato de download do arquivo escolhido
$downloadUrl = $asset[0].browser_download_url
$zipName = $asset[0].name
$tempZip = Join-Path $env:TEMP $zipName
$tempExtractDir = Join-Path $env:TEMP "P4G_Tradu_Temp"

# Baixando
Write-Host "Baixando: $zipName ..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip

# 1.3 - Extraindo
Write-Host "Extraindo os arquivos..." -ForegroundColor Cyan
if (Test-Path $tempExtractDir) { Remove-Item -Path $tempExtractDir -Recurse -Force }
Expand-Archive -Path $tempZip -DestinationPath $tempExtractDir -Force

# 1.4 - Movendo os arquivos para a pasta do jogo
Write-Host "Instalando na pasta do Persona 4 Golden..." -ForegroundColor Cyan
# O \* garante que ele copie o conteúdo de dentro do temp, não a pasta temp em si
Copy-Item -Path "$tempExtractDir\*" -Destination $gamePath -Recurse -Force

# Limpeza
Write-Host "Limpando arquivos temporários..." -ForegroundColor DarkGray
Remove-Item -Path $tempZip -Force
Remove-Item -Path $tempExtractDir -Recurse -Force

Write-Host "`nTradução instalada com sucesso! Aproveite o jogo." -ForegroundColor Green
