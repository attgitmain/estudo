#!/bin/bash
#
# functions for setting up landing page

#######################################
# installed node packages
# Arguments:
#   None
#######################################
landing_node_dependencies() {
  print_banner
  printf "${WHITE} 💻 Instalando dependências do landing...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  sudo su - deploy <<EOF2
  cd /home/deploy/${instancia_add}/landing
  npm install
EOF2

  sleep 2
}

#######################################
# compiles landing code
# Arguments:
#   None
#######################################
landing_node_build() {
  print_banner
  printf "${WHITE} 💻 Compilando o código do landing...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  sudo su - deploy <<EOF2
  cd /home/deploy/${instancia_add}/landing
  npm run build
EOF2

  sleep 2
}

#######################################
# updates landing code
# Arguments:
#   None
#######################################
landing_update() {
  print_banner
  printf "${WHITE} 💻 Atualizando o landing...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  sudo su - deploy <<EOF2
  cd /home/deploy/${empresa_atualizar}
  pm2 stop ${empresa_atualizar}-landing
  git pull
  cd /home/deploy/${empresa_atualizar}/landing
  npm install
  rm -rf build
  npm run build
  pm2 start ${empresa_atualizar}-landing
  pm2 save
EOF2

  sleep 2
}

#######################################
# sets landing environment variables
# Arguments:
#   None
#######################################
landing_set_env() {
  print_banner
  printf "${WHITE} 💻 Configurando variáveis de ambiente (landing)...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  sudo su - deploy << EOF2
  cat <<[-]EOF3 > /home/deploy/${instancia_add}/landing/.env
REACT_APP_BACKEND_URL=${backend_url}
[-]EOF3
EOF2

  sleep 2

  sudo su - deploy << EOF2
  cat <<[-]EOF3 > /home/deploy/${instancia_add}/landing/server.js
const express = require("express");
const path = require("path");
const app = express();
app.use(express.static(path.join(__dirname, "build")));
app.get("/*", function (req, res) {
        res.sendFile(path.join(__dirname, "build", "index.html"));
});
app.listen(${landing_port});
[-]EOF3
EOF2

  sleep 2
}

#######################################
# starts pm2 for landing
# Arguments:
#   None
#######################################
landing_start_pm2() {
  print_banner
  printf "${WHITE} 💻 Iniciando pm2 (landing)...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  sudo su - deploy <<EOF2
  cd /home/deploy/${instancia_add}/landing
  pm2 start server.js --name ${instancia_add}-landing
  pm2 save
EOF2

 sleep 2

  sudo su - root <<EOF2
   pm2 startup
  sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u deploy --hp /home/deploy
EOF2
  sleep 2
}

#######################################
# sets up nginx for landing
# Arguments:
#   None
#######################################
landing_nginx_setup() {
  print_banner
  printf "${WHITE} 💻 Configurando nginx (landing)...${GRAY_LIGHT}"
  printf "\n\n"

  sleep 2

  landing_hostname=$(echo "${landing_url/https:\/\/}")

sudo su - root << EOF2

cat > /etc/nginx/sites-available/${instancia_add}-landing << 'END'
server {
  server_name $landing_hostname;

  location / {
    proxy_pass http://127.0.0.1:${landing_port};
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_cache_bypass \$http_upgrade;
  }
}
END

ln -s /etc/nginx/sites-available/${instancia_add}-landing /etc/nginx/sites-enabled
EOF2

  sleep 2
}
