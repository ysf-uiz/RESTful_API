
import network
import urequests as requests
import time
import machine
from machine import Pin
from dht import DHT22
from ntptime import settime  

# WiFi credentials
ssid = "wifi"
password = "1234567890"

# Server configuration
serverName = "http://IP:5000/api/send-data"
device_id = "NodeMCU002"  

# Pin Configuration
dht_pin = Pin(2, Pin.IN) 
dht_sensor = DHT22(dht_pin)
motion_pin = Pin(12, Pin.IN) 
led_pin = Pin(4, Pin.OUT)  

# Initialize objects
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def setupWiFi():
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.')
    print('\nConnected to WiFi')
    print('Network config:', wlan.ifconfig())

def sendSensorData(temp, humidity, motion):
    if wlan.isconnected():
        try:
            # Get timestamp
            try:
                settime()
                current_time = time.localtime()
                timestamp = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
            except OSError as e:
                print("Error getting time:", e)
                timestamp = "Time Error"

            data = {
                "device_id": device_id,
                "temperature": temp,
                "humidity": humidity,
                "movement": "true" if motion else "false",
                "timestamp": timestamp
            }

            headers = {'Content-Type': 'application/json'}
            response = requests.post(serverName, json=data, headers=headers)

            if response.status_code == 200:
                print("Data sent successfully!")
                print("Data:", data)  # Print the data that was sent
            else:
                print("Error sending data. Status code:", response.status_code)
                print("Response:", response.text)

            response.close()

        except OSError as e:
            print("Error sending data:", e)

# Main program
setupWiFi()

last_data_send = time.time()

while True:
    current_time = time.time()

    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        motionDetected = motion_pin.value() == 1
        led_pin.value(not motionDetected) # Turn on LED if motion is detected (active LOW)

        print("Temperature: {:.1f}C, Humidity: {:.1f}%, Motion: {}".format(
            temperature, humidity, "Detected" if motionDetected else "None"
        ))

    except OSError as e:
        print("Error reading sensor:", e)
        temperature = float('nan') # Assign NaN if sensor read fails
        humidity = float('nan')

    # Send data every 10 seconds
    if current_time - last_data_send >= 10:
        if not (isinstance(temperature, float) and isinstance(humidity, float) and (temperature != float('nan')) and (humidity != float('nan'))):
          print("Skipping data send due to invalid sensor readings.")
        else:
          sendSensorData(temperature, humidity, motionDetected)

        last_data_send = current_time

    time.sleep(1)

