#!/bin/bash
# ==============================================================================
# Script de Instalação Automática - Tradução Persona 4 Golden (Phantasie Translate)
# Execução: curl -sL <link-raw-do-github> | bash
# ==============================================================================

# Cores para o terminal
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sem Cor

# Verifica se os pacotes essenciais estão instalados
if ! command -v curl &> /dev/null || ! command -v unzip &> /dev/null; then
    echo -e "${RED}Erro: Os pacotes 'curl' e 'unzip' são obrigatórios.${NC}"
    echo "Instale-os usando o gerenciador de pacotes da sua distribuição (ex: sudo apt install curl unzip)."
    exit 1
fi

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}  Instalador da Tradução - Phantasie Translate${NC}"
echo -e "${CYAN}====================================================${NC}"

# Pergunta a versão
echo -e "\nQual a versão do seu Persona 4 Golden?"
echo "1) 64-bits (Versão mais atual/Steam)"
echo "2) 32-bits (Versão antiga)"
read -p "Escolha uma opção (1 ou 2): " choice

if [[ "$choice" != "1" && "$choice" != "2" ]]; then
    echo -e "${RED}Opção inválida. Cancelando.${NC}"
    exit 1
fi

GAME_PATH=""

# 1.1 - Lógica de busca de diretório
if [ "$choice" == "1" ]; then
    echo -e "\n${CYAN}Procurando a pasta do jogo automaticamente...${NC}"
    
    # Caminhos comuns da Steam no Linux (Nativo e Flatpak)
    COMMON_PATHS=(
        "$HOME/.local/share/Steam/steamapps/common/Persona 4 Golden"
        "$HOME/.steam/steam/steamapps/common/Persona 4 Golden"
        "$HOME/.steam/root/steamapps/common/Persona 4 Golden"
        "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Persona 4 Golden"
    )

    for path in "${COMMON_PATHS[@]}";; do
        if [ -d "$path" ]; then
            GAME_PATH="$path"
            break
        fi
    done
fi

# Se não achou (ou se for a versão 32-bits), pede pro usuário
if [ -z "$GAME_PATH" ]; then
    echo -e "${YELLOW}A pasta do jogo não foi encontrada automaticamente.${NC}"
    
    # Tenta usar o Zenity (Interface Gráfica de seleção nativa de muitas distros)
    if command -v zenity &> /dev/null; then
        echo -e "${YELLOW}Abrindo o explorador de arquivos para você selecionar a pasta...${NC}"
        GAME_PATH=$(zenity --file-selection --directory --title="Selecione a pasta do Persona 4 Golden")
    else
        # Fallback pro terminal caso não tenha interface gráfica instalada
        read -p "Cole o caminho completo para a pasta do Persona 4 Golden: " GAME_PATH
    fi
fi

# Checa se o usuário cancelou ou mandou vazio
if [ -z "$GAME_PATH" ] || [ ! -d "$GAME_PATH" ]; then
    echo -e "${RED}Instalação cancelada: Diretório inválido ou não selecionado.${NC}"
    exit 1
fi

echo -e "${GREEN}Pasta de destino confirmada: $GAME_PATH${NC}\n"

# 1.2 - API do GitHub
echo -e "${CYAN}Buscando a versão mais recente da tradução no GitHub...${NC}"
API_URL="https://api.github.com/repos/Ahtheerr/P4Golden-Phantasie-Translate/releases/latest"

# Extrai o link de download filtrando pela string '32-bits'
# grep busca a linha do link, grep -iv (inverso) exclui o 32-bits, cut pega só a URL entre aspas
if [ "$choice" == "1" ]; then
    DOWNLOAD_URL=$(curl -s "$API_URL" | grep "browser_download_url" | grep -iv "32-bits" | cut -d '"' -f 4 | head -n 1)
else
    DOWNLOAD_URL=$(curl -s "$API_URL" | grep "browser_download_url" | grep -i "32-bits" | cut -d '"' -f 4 | head -n 1)
fi

if [ -z "$DOWNLOAD_URL" ]; then
    echo -e "${RED}Erro: Não foi possível encontrar o arquivo .zip para essa versão no GitHub.${NC}"
    exit 1
fi

ZIP_NAME=$(basename "$DOWNLOAD_URL")

# Cria um diretório temporário seguro no /tmp
TEMP_DIR=$(mktemp -d)
TEMP_ZIP="$TEMP_DIR/$ZIP_NAME"
TEMP_EXTRACT="$TEMP_DIR/P4G_Tradu_Temp"
mkdir -p "$TEMP_EXTRACT"

# Baixando
echo -e "${CYAN}Baixando: $ZIP_NAME ...${NC}"
curl -L "$DOWNLOAD_URL" -o "$TEMP_ZIP"

# 1.3 - Extraindo
echo -e "${CYAN}Extraindo os arquivos...${NC}"
unzip -q -o "$TEMP_ZIP" -d "$TEMP_EXTRACT"

# 1.4 - Movendo os arquivos
echo -e "${CYAN}Instalando na pasta do Persona 4 Golden...${NC}"
# O comando cp -r vai mesclar e substituir os arquivos nativamente
cp -r "$TEMP_EXTRACT"/* "$GAME_PATH/"

# Limpeza
echo -e "${NC}Limpando arquivos temporários...${NC}"
rm -rf "$TEMP_DIR"

echo -e "\n${GREEN}Tradução instalada com sucesso! Aproveite o jogo.${NC}"
