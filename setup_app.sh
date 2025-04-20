#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor, execute como root (sudo)${NC}"
    exit 1
fi

# Definir variáveis
APP_DIR="/opt/guardadocs"
DOMAIN=""
EMAIL=""

# Função para solicitar informações
get_info() {
    echo -e "${YELLOW}Digite o domínio para a aplicação (ex: app.exemplo.com):${NC}"
    read -r DOMAIN
    echo -e "${YELLOW}Digite o email do administrador:${NC}"
    read -r EMAIL
}

# Criar diretório da aplicação
echo -e "${YELLOW}Criando diretório da aplicação...${NC}"
mkdir -p "$APP_DIR"
cd "$APP_DIR" || exit

# Clonar repositório
echo -e "${YELLOW}Clonando repositório...${NC}"
git clone https://github.com/Romarck/guardadocs.git .

# Criar diretórios necessários
echo -e "${YELLOW}Criando diretórios...${NC}"
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p uploads
chmod -R 755 uploads

# Solicitar informações
get_info

# Gerar senha segura para o banco de dados
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)

# Criar arquivo de ambiente
echo -e "${YELLOW}Criando arquivo de ambiente...${NC}"
cat > stack.env << EOL
# Project settings
PROJECT_NAME=GuardaDocs
VERSION=1.0.0
API_V1_STR=/api/v1

# Database settings
POSTGRES_USER=guardadocs
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=guardadocs
DATABASE_URL=postgresql://guardadocs:$DB_PASSWORD@db:5432/guardadocs

# Security settings
SECRET_KEY=$SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=11520
ALGORITHM=HS256

# Domain and SSL settings
DOMAIN=$DOMAIN
ADMIN_EMAIL=$EMAIL
NGINX_PORT=80
NGINX_SSL_PORT=443

# File upload settings
MAX_UPLOAD_SIZE=5242880
UPLOAD_FOLDER=/app/uploads

# Storage settings
STORAGE_TYPE=local
EOL

# Ajustar permissões
echo -e "${YELLOW}Ajustando permissões...${NC}"
chown -R 1000:1000 "$APP_DIR"
chmod 600 stack.env

# Mostrar informações importantes
echo -e "${GREEN}Configuração concluída!${NC}"
echo -e "${YELLOW}Informações importantes:${NC}"
echo -e "Diretório da aplicação: ${GREEN}$APP_DIR${NC}"
echo -e "Arquivo de ambiente: ${GREEN}$APP_DIR/stack.env${NC}"
echo -e "Senha do banco de dados: ${GREEN}$DB_PASSWORD${NC}"
echo -e "Chave secreta: ${GREEN}$SECRET_KEY${NC}"
echo -e "\n${YELLOW}Guarde essas informações em um local seguro!${NC}"
echo -e "\n${GREEN}Agora você pode criar uma nova stack no Portainer usando o arquivo stack.yml${NC}" 