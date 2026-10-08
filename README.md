# Pacman Projects

This an updated version of the PacMan projects from [_UC Berkeley CS188 Intro to AI -- Course Materials_](https://ai.berkeley.edu) 
which run in Python3.X. The covered projects are:
* [Project 1 - Search](https://github.com/aig-upf/pacman-projects/blob/main/search/README.md)
* [Project 2 - Multiagent](https://github.com/aig-upf/pacman-projects/blob/main/multiagent/README.md)
* [Project 3 - Reinforcement Learning](https://github.com/aig-upf/pacman-projects/blob/main/reinforcement/README.md)

### Setting up Python3.8 in Ubuntu

A requirement for this project is to install Python3.8 in your Operating System. The next script is an example for installing that python version in Ubuntu.

```shell
sudo apt-get update

sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
                        libreadline-dev libsqlite3-dev wget curl llvm \
                        libncurses5-dev libncursesw5-dev xz-utils tk-dev \
                        libffi-dev liblzma-dev python3-openssl git
mkdir ~/python38
cd ~/python38
wget https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz
tar -xf Python-3.8.6.tgz
cd Python-3.8.6
./configure --enable-optimizations
make -j$(nproc)
sudo make install
python3.8 --version
```

