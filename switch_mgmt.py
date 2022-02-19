import time
import datetime
import requests
import logging, warnings

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(level="INFO", format=FORMAT)
#warnings.filterwarnings('ignore')
logger = logging.getLogger("eco-smart")

HA_states_url = "http://<HOST IP ADDRES>:8123/api/states/"
HA_script_url = "http://<HOST IP ADDRES>:8123/api/services/script/"
headers = {
    "Authorization": "Bearer <YOUR HOME ASSISTANT TOKEN>",
    "content-type": "application/json",
}

# Heat devices current(A) consumption
MINIMUM_LOAD_1_CURRENT = 3.9
MINIMUM_LOAD_2_CURRENT = 6
SAFE_MARGIN_CURRENT = 0.5
SAFE_MARGIN_CONSUMPTION_W = SAFE_MARGIN_CURRENT * 230

# Return net excedent current(A)
def get_net_excedent_rmsCurrent():
    ## Poll Prometheus API
    # power_url = 'http://<HOST IP ADDRES>:9090/api/v1/query?query=consumption_now_watts'
    # power = requests.get(power_url).json()
    # net_consumption = power['data']['result'][0]['value'][1]

    # Poll Enphase Envoy-S
    power_url = 'http://envoy:<ENVOY PASS>@<ENVOY IP ADDRESS>/production.json'
    power = requests.get(power_url).json()
    #print(power)
    production = power['production'][1]['wNow']
    production_rmsCurrent = power['production'][1]['rmsCurrent']
    production_rmsVoltage = power['production'][1]['rmsVoltage']
    total_consumption = power['consumption'][0]['wNow']
    net_excedent_rmsCurrent = (production - total_consumption)/production_rmsVoltage
    logger.info("Net excedent current(A): {:.2f}".format(net_excedent_rmsCurrent))

    return net_excedent_rmsCurrent


## Main loop

while (True):
    switch_1 = requests.get(HA_states_url + "switch.switch_1", headers=headers).json()
    switch_2 = requests.get(HA_states_url + "switch.switch_2", headers=headers).json()
    logger.info("Status: {}".format(switch_1["state"]) + " {}".format(switch_2["state"]))

    if not ((switch_1["state"] == "unavailable") and (switch_2["state"] == "unavailable")):

        # New poll of excendents
        logger.info("Waiting for excedents poll...")
        net_excedent_rmsCurrent = get_net_excedent_rmsCurrent()

        # Start charging if minimal excedents reached and production greater than minimal
        #print(switch_1)
        #print(switch_2)
        if not (switch_1["state"] == "unavailable"):
            switch_1_current_A = switch_1["attributes"]["current"] / 1000
        else:
            switch_1_current_A = 0
        if not (switch_2["state"] == "unavailable"):
            switch_2_current_A = switch_2["attributes"]["current"] / 1000
        else:
            switch_2_current_A = 0
        switches_current = switch_1_current_A + switch_2_current_A

        switches_previous_current = switches_current
        if ((net_excedent_rmsCurrent >= MINIMUM_LOAD_2_CURRENT) and (switch_2["state"] == "off")):
            logger.info("Turning on Switch_2...")
            turn_on_switch_2 = requests.post(HA_script_url + "turn_on_switch_2", headers=headers).json()
        elif ((net_excedent_rmsCurrent >= MINIMUM_LOAD_1_CURRENT) and (switch_1["state"] == "off")):
            logger.info("Turning on Switch_1...")
            turn_on_switch_1 = requests.post(HA_script_url + "turn_on_switch_1", headers=headers).json()
            time.sleep(30)
        else:
            logger.info("Minimal production not reached or not enough excedents")
            # At least one switch is already on
            if (switches_current > 0):
                if (net_excedent_rmsCurrent < -SAFE_MARGIN_CURRENT):
                    # Wait 10 seconds and poll consumption one more time before turning off switches
                    time.sleep(10)
                    power_url = 'http://envoy:<ENVOY PASS>@<ENVOY IP ADDRESS>/production.json'
                    power = requests.get(power_url).json()
                    net_consumption = power['consumption'][1]['wNow']
                    if (net_consumption > SAFE_MARGIN_CONSUMPTION_W):
                        if (switch_1["state"] == "on"):
                            logger.info("Turning off Switch_1...")
                            turn_off_switch_1 = requests.post(HA_script_url + "turn_off_switch_1", headers=headers).json()
                            switch_1_current_A = 0
                        elif (switch_2["state"] == "on"):
                            logger.info("Turning off Switch_2...")
                            turn_off_switch_1 = requests.post(HA_script_url + "turn_off_switch_2", headers=headers).json()
                            switch_2_current_A = 0


    time.sleep(60)
