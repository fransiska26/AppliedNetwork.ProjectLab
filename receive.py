# Receiver code for Raspberry Pi
import RPi.GPIO as GPIO
import time
import board
import paho.mqtt.client as mqtt
import can
import struct
import os
import glob


# MQTT broker configuration
MQTT_BROKER = "public.mqtthq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/temperature"
WebSocket_PORT = 8083
WebSocket_PATH = "/mqtt"

# Initialize CAN bus interface
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Initialize the 1-Wire interface
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Find the file that holds the temperature readings
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_dht11():
    try:
        message = bus.recv()
        
        # Extract data bytes from the received message
        h_bytes = message.data[:4]
        t_bytes = message.data[4:]
        
        # Convert byte arrays back to float values
        h = struct.unpack('<f', bytes(h_bytes))[0]
        t = struct.unpack('<f', bytes(t_bytes))[0]

        return t, h
    except RuntimeError as e:
        print("Failed to read sensor data:", e)
        return None, None


# Function to read the raw temperature data from the sensor
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# Function to parse the raw temperature data and return the temperature in Celsius
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
#TBD: better error handling


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code "+str(rc))

try:
    # Initialize MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect

    # Connect to MQTT broker
    # client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.ws_set_options(path=WebSocket_PATH)
    client.connect(MQTT_BROKER, WebSocket_PORT, 60)
    while True:
        # Read temperature and humidity values
        temperature, humidity = read_dht11()
        temperature_2 = read_temp()
        
        if temperature is not None and temperature_2 is not None and humidity is not None:
            # Publish temperature to MQTT broker
            client.publish(MQTT_TOPIC, payload='Temperature (DHT11): {:.1f}°C'.format(temperature))
            client.publish(MQTT_TOPIC, payload='Humidity (DHT11): {:.1f}%'.format(humidity))
            client.publish(MQTT_TOPIC, payload='Temperature (DS18B20): {:.1f}°C'.format(temperature_2))
            
            print("Temperature (DHT11): {:.1f}°C".format(temperature))
            print("Humidity (DHT11): {:.1f}%".format(humidity))
            print("Temperature (DS18B20): {:.1f}°C".format(temperature_2))
        else:
            print("Failed to retrieve sensor data. Trying again...")

        # Wait for a few seconds before reading again
        time.sleep(2)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    # Cleanup GPIO
    GPIO.cleanup()
    # Disconnect from MQTT broker
    client.disconnect()
