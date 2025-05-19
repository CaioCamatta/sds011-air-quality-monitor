# sds011-air-quality-monitor
A Python 3 interface for the SDS011 Nova PM Sensor. Works on Raspberry Pi Zero.

## Using with a Raspberry Pi

### Requirements
* Raspberry Pi (The Zero W works well)
* SDS011 particulate matter sensor
* USB adapter for the sensor (comes with the sensor)

### Instructions

1. [Set up an SSH connection to the Raspberry Pi](https://www.mikekasberg.com/blog/2020/06/19/headless-setup-for-a-raspberry-pi-zero-w.html).
2. `sudo apt update && sudo apt upgrade -y`
3. Install packages: `sudo apt install git python3-pip git-core python3-serial python3-enum34`
4. Download the script to your pi
6. Use the script

```
# Basic usage - display readings on console
./aqi_prometheus.py

# Enable Prometheus metrics
./aqi_prometheus.py --prometheus

# Continuous monitoring (no sleep cycles)
./aqi_prometheus.py --prometheus --no-sleep

# Quiet mode with only averages displayed
./aqi_prometheus.py --prometheus --quiet

# Debug mode for troubleshooting
./aqi_prometheus.py --debug
```


#### Auto-start on boot

To make the script run when the Pi is booted up,

First, `sudo nano /etc/systemd/system/air-quality.service` and paste in the following:

```
[Unit]
Description=Air Quality Monitor with SDS011
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/aqi_prometheus.py --prometheus --no-sleep
WorkingDirectory=/home/pi
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```
bashsudo systemctl enable air-quality.service
sudo systemctl start air-quality.service
```


Optional: connect to grafana


sudo apt install -y python3-prometheus-client prometheus prometheus-node-exporter 
