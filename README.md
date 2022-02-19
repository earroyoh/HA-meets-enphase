# HA-meets-enphase
Tuya switches Home Assistant integration with enphase envoy-S to leverage excedents production. You need Home-Assistant running on a host (e.g. raspberrypi) at port 8123 and localtuya custom component installed. You also need to create HA scripts for turning on and off tuya switches.

You can even run in a raspberrypi docker container:\
docker build -t localtuya:1.0 .\
docker run -d -t --name switch_mgmt localtuya:1.0
