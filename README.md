This program requires CHDK installed on the camera and several libraries to work.

The instructions to install CHDK on the SD card of the Canon Camera are here:
https://chdk.fandom.com/wiki/CHDK_quick_install_Guide

The latest CHDK version is here under PowerShot M10:
http://mighty-hoernsche.de/trunk/

Once CHDK is properly installed on the camera you need the following libraries
lua5.2 and liblua5.2-dev
libusb
opencv
libraw
libjpeg
imageio
chdkptp
rawpy
remi

I use then this sequence to install everything

```
sudo apt-get install python3-pip lua5.2 liblua5.2-dev libusb-dev libusb-1.0-0-dev python3-setuptools python3-dev python3-six python3-opencv libraw-dev cmake zlib1g-dev libnova-dev libcurl4-gnutls-dev libgsl-dev libjpeg-dev libcfitsio-dev python3-imageio
```

```
pip3 install wheel
echo "export PATH=\$PATH:/home/ema/.local/bin" >> ~/.bashrc
. ~/.bashrc
```
```
pip3 install lupa --install-option='--no-luajit'
```
```
git clone --recursive -j8  https://github.com/5up3rD4n1/chdkptp.py.git
cd chdkptp.py
python3 setup.py sdist
sudo python3 setup.py install
cd ..
rm -rf chdkptp.py
```
```
pip3 install rawpy
pip3 instal git+https://github.com/dddomodossola/remi.git
```

Then you are ready to execute the GUI with
```
python3 ./Canon-M10.py
```
The GUI is then available on http://computer_ip:8081/

<img src=https://github.com/emanuelelaface/Canon-M10/blob/master/screenshots/screenshot1.png></img>
