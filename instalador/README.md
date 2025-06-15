# Instalador Whaticket SaaS

Antes de iniciar a instalação, digite esse código abaixo no terminal da sua VPS.

apt-get update & apt-get upgrade -y

Depois rode o comando abaixo

sudo apt install -y git && git clone https://github.com/Villela-Tech/instalador.git && sudo chmod -R 777 instalador && chmod +x install_primaria
 && cd instalador && sudo ./install_primaria

## Requisitos

| --- | Mínimo | Recomendado |
| --- | --- | --- |
| Node JS | 20.x | 20.x |
| Ubuntu | 20.x | 20.x |
| Memória RAM | 4Gb | 8Gb |  
