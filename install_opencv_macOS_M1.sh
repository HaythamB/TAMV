####################################
# INSTALL OPENCV AND TAMV ON MACOS #
####################################

echo "*******************************************************************************************"
echo "  Welcome to the macOS TAMV/openCV installer!"
echo "*******************************************************************************************"

# move to user home folder
cd
echo "Your current home user directory is: "
pwd

echo "*******************************************************************************************"
echo "     Installing pip and setuptools "
echo "*******************************************************************************************"
# install pip dependencies
python3 -m pip install --upgrade setuptools
python3 -m pip install --upgrade pip
# pip - install packages needed for image processing
echo "*******************************************************************************************"
echo "     Installing imutils "
echo "*******************************************************************************************"
pip install imutils

# install homebrew
echo "*******************************************************************************************"
echo "     Installing homebrew and miniforge source"
echo "*******************************************************************************************"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# install miniforge to ensure compatability with M1 chips
brew install miniforge

# create a conda environment called cv
echo "*******************************************************************************************"
echo "     Creating conda environment for python 3.8.6 "
echo "*******************************************************************************************"
conda init zsh
conda create -n cv python=3.8.6
conda activate cv

echo "*******************************************************************************************"
echo "     Installing python libraries into conda environment: cv "
echo "*******************************************************************************************"
# install dependencies for TAMV and openCV into the new environment
conda install -c conda-forge python3-dev
conda install -c conda-forge pylint3
conda install -c conda-forge python3-tk
conda install -c conda-forge python3-numpy
conda install -c conda-forge flake8
conda install -c conda-forge python3-matplotlib
conda install -c conda-forge python3-pyqt5
conda install -c conda-forge qtbase5-dev
conda install -c conda-forge curl
conda install -c conda-forge opencv

# install git
echo "*******************************************************************************************"
echo "     Installing git using homebrew "
echo "*******************************************************************************************"
brew install git

# clone TAMV repository
echo "*******************************************************************************************"
echo "     Cloning TAMV repository into the TAMV folder "
echo "*******************************************************************************************"
git clone https://github.com/HaythamB/TAMV.git

echo "*******************************************************************************************"
echo "     Installing pip and setuptools "
echo "*******************************************************************************************"
