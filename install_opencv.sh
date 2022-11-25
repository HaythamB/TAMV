######################################
# INSTALL OPENCV ON UBUNTU OR DEBIAN #
######################################
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y dist-upgrade
sudo apt-get -y install python3-dev
sudo apt-get -y install pylint3
sudo apt-get -y install python3-tk
sudo apt-get -y install python3-numpy
sudo apt-get -y install flake8
sudo apt-get -y install python3-matplotlib
sudo apt-get -y install python3-pyqt5
sudo apt-get -y install qtbase5-dev
sudo apt-get -y install curl
cd ~
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py
pip install imutils
pip install imageio[ffmpeg]
sudo apt-get install python3-opencv
sudo apt-get install git
