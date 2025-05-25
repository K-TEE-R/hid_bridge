sudo cp etc/systemd/system/usbhidg_initializer.service /etc/systemd/system
sudo cp etc/systemd/system/hid_bridge.service /etc/systemd/system
sudo mkdir -p /usr/lib/hid_bridge
sudo cp hid_bridge.py /usr/lib/hid_bridge
sudo cp usbhidg_initializer /usr/bin
