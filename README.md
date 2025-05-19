# sds011-air-quality-monitor
A Python 3 interface for the SDS011 Nova PM Sensor intended for the Raspberry Pi Zero. Also contains an opitonal integration with Prometheus and Grafana.

Inspired by [zefanja/aqi](https://github.com/zefanja/aqi/tree/master) and modified using an LLM. Part of this README was also written by an LLM.


## Using with a Raspberry Pi

### Requirements
* Raspberry Pi (The Zero W works well)
* SDS011 particulate matter sensor
* USB adapter for the sensor (comes with the sensor)

### Instructions

1. [Set up an SSH connection to the Raspberry Pi](https://www.mikekasberg.com/blog/2020/06/19/headless-setup-for-a-raspberry-pi-zero-w.html).
2. `sudo apt update && sudo apt upgrade -y`
3. Install packages: `sudo apt install git python3-pip git-core python3-serial python3-enum34`
4. Download the script to your Pi `wget https://raw.githubusercontent.com/CaioCamatta/sds011-air-quality-monitor/refs/heads/main/aqm.py`
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

Example output:
```
pi@pi:~/air $ python aqm.py --prometheus --port 8080
Prometheus metrics server started on port 8080
Prometheus metrics available at http://localhost:8080/metrics
Starting air quality monitoring...
Settings:
  Debug mode: Disabled
  Sleep mode: Enabled
  Verbosity: Full
  Prometheus metrics: Enabled
  Prometheus port: 8080
Setting up sensor...
Starting main loop...
PM2.5: 0.4 μg/m³, PM10: 1.8 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.8 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.7 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.4 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.4 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.3 μg/m³
PM2.5: 0.4 μg/m³, PM10: 1.3 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.7 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.6 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.9 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.8 μg/m³
PM2.5: 0.3 μg/m³, PM10: 0.6 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.6 μg/m³
PM2.5: 0.3 μg/m³, PM10: 0.6 μg/m³
PM2.5: 0.4 μg/m³, PM10: 0.6 μg/m³
AVERAGE: PM2.5: 0.4 μg/m³, PM10: 1.1 μg/m³ (from 15 readings)
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
sudo systemctl enable air-quality.service
sudo systemctl start air-quality.service
```


### Optional: Connect to grafana

You can also connect the AQM to Prometheus and use the GrafanaLabs cloud so you can visualize the air quality over the internet.

#### Set up Prometheus

1. Install Prometheus: `sudo apt install -y python3-prometheus-client prometheus prometheus-node-exporter `

2. Create a Prometheus configuration file: `sudo nano /etc/prometheus/prometheus.yml`

3. Add this configuration (replace placeholders with your Grafana Cloud credentials):
```
yamlglobal:
  scrape_interval: 60s

scrape_configs:
  - job_name: 'air_quality'
    static_configs:
      - targets: ['localhost:8000']

remote_write:
  - url: "YOUR_GRAFANA_ALLOY_URL"
    basic_auth:
      username: "YOUR_INSTANCE_ID"
      password: "YOUR_API_KEY"
```

4. Restart Prometheus: `sudo systemctl restart prometheus`

5. Verify Prometheus is running: `sudo systemctl status prometheus`


#### Integrate Grafana Cloud

1. Sign up for a free Grafana Cloud account at https://grafana.com/products/cloud/

2. Get your stack details:
  a. Navigate to your Grafana Cloud stack
  b. Look for Prometheus details
  c. Note down the Remote Write URL, Instance ID (username), and generate an API key

3. Update your Prometheus configuration with these details (as shown in the previous section)
4. Metrics should begin flowing to Grafana Cloud within a few minutes
5. From there you can create dashboards.
