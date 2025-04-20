#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Iniciando instalação do ambiente...${NC}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor, execute como root (sudo)${NC}"
    exit 1
fi

# Atualizar sistema
echo -e "${YELLOW}Atualizando o sistema...${NC}"
apt-get update && apt-get upgrade -y

# Instalar dependências
echo -e "${YELLOW}Instalando dependências...${NC}"
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw

# Adicionar chave GPG do Docker
echo -e "${YELLOW}Configurando repositório do Docker...${NC}"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório do Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
echo -e "${YELLOW}Instalando Docker...${NC}"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar Docker
echo -e "${YELLOW}Iniciando Docker...${NC}"
systemctl start docker
systemctl enable docker

# Configurar firewall
echo -e "${YELLOW}Configurando firewall...${NC}"
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 9443/tcp # Portainer UI
ufw allow 8000/tcp # Portainer Edge
ufw --force enable

# Criar rede para Portainer
echo -e "${YELLOW}Criando rede Docker para Portainer...${NC}"
docker network create portainer

# Criar volume para Portainer
echo -e "${YELLOW}Criando volume para Portainer...${NC}"
docker volume create portainer_data

# Instalar Portainer
echo -e "${YELLOW}Instalando Portainer...${NC}"
docker run -d \
  --name portainer \
  --restart=always \
  -p 8000:8000 \
  -p 9443:9443 \
  --network=portainer \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# Inicializar Docker Swarm
echo -e "${YELLOW}Inicializando Docker Swarm...${NC}"
docker swarm init --advertise-addr $(hostname -i | awk '{print $1}')

# Criar rede overlay para aplicações
echo -e "${YELLOW}Criando rede overlay...${NC}"
docker network create --driver overlay --attachable app-network

# Mostrar informações de acesso
echo -e "${GREEN}Instalação concluída!${NC}"
echo -e "${GREEN}Acesse o Portainer em: https://$(curl -s ifconfig.me):9443${NC}"
echo -e "${YELLOW}Por favor, defina uma senha forte no primeiro acesso.${NC}"
echo -e "${YELLOW}Guarde o token de acesso que será mostrado na tela inicial.${NC}" 