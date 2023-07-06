#============================================================================
# Name        : cek_wifi.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : for checking WIFI connection, and shutdown the raspi if there is no connection
#============================================================================

import subprocess
import time

def check_internet_connection():
    result = subprocess.call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result == 0

def get_wifi_interfaces():
    result = subprocess.Popen(['ifconfig', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.read().lower()

    interfaces = []
    lines = output.split('\n')
    for line in lines:
        if line.startswith(('wlan', 'wl')):
            interface = line.split(':')[0]
            interfaces.append(interface)

    return interfaces

def get_saved_networks(interface):
    result = subprocess.Popen(['sudo', 'wpa_cli', '-i', interface, 'list_networks'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.read().lower()

    networks = []
    lines = output.split('\n')[1:-1]
    for line in lines:
        network_info = line.split('\t')
        network_id = network_info[0]
        ssid = network_info[1]
        networks.append((network_id, ssid))

    return networks

def shutdown_callback():
    print("Shutdown command received.")
    subprocess.call(['sudo', 'pkill', '-f', 'python2'])
    subprocess.call(['sudo', 'shutdown', '-h', 'now'])

def connect_to_wifi(interface, network_id):
    subprocess.call(['sudo', 'wpa_cli', '-i', interface, 'reconnect'])
    time.sleep(5)

def disable_wifi(interface):
    subprocess.call(['sudo', 'ifconfig', interface, 'down'])

def enable_wifi(interface):
    subprocess.call(['sudo', 'ifconfig', interface, 'up'])
    time.sleep(2)

counter = 0
# Main loop
while True:
    if check_internet_connection():
        print("Raspberry Pi terhubung ke internet.")
        break
    else:
        time.sleep(1)
        counter += 1
        print(counter)
        if counter > 35:
            counter = 0
            shutdown_callback()
            break
