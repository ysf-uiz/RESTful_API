from machine import Pin, I2C, reset
from time import sleep, ticks_ms
import network
import urequests
import ssd1306
import dht
import gc
import ntptime

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SCREEN_ADDRESS = 0x3C
WIFI_SSID = "wifi"  # Replace with your Wi-Fi SSID
WIFI_PASSWORD = "PWD"  # Replace with your Wi-Fi password
SERVER_URL = "https://IP/api/send-data"  # Replace with your server URL if you want to test it with postman or another tool just replace this url by http://your_ip_adress:port/api/send-data 
DEVICE_ID = "NodeMCU001"
DHT_PIN = 14
MOTION_PIN = 26
LED_PIN = 4

class SensorMonitor:
    def __init__(self):
        self.wifi = None
        self.last_valid_temp = None
        self.last_valid_humidity = None
        self.init_hardware()
        self.setup_wifi()
        self.prev_display_millis = 0
        self.prev_data_millis = 0
        self.show_logo = True
        self.sync_time()

    def init_hardware(self):
        print("Initializing hardware...")
        self.motion_sensor = Pin(MOTION_PIN, Pin.IN)
        self.led = Pin(LED_PIN, Pin.OUT)
        self.dht_sensor = dht.DHT11(Pin(DHT_PIN))
        i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        self.display = ssd1306.SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)
        self.display_initialized = True
        print("Hardware initialized.")
        sleep(2)

    def setup_wifi(self):
        print("Setting up Wi-Fi...")
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.active(True)
        
        if not self.wifi.isconnected():
            print(f"Connecting to {WIFI_SSID}...")
            self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            timeout = 20
            while timeout > 0 and not self.wifi.isconnected():
                print(f"Waiting for connection... ({timeout})")
                sleep(1)
                timeout -= 1
        
        if self.wifi.isconnected():
            print(f"Connected to Wi-Fi. IP: {self.wifi.ifconfig()[0]}")
        else:
            print("Failed to connect to Wi-Fi.")
        return self.wifi.isconnected()

    def sync_time(self):
        print("Syncing time...")
        if self.wifi.isconnected():
            try:
                ntptime.settime()
                print("Time synced successfully.")
            except Exception as e:
                print(f"Error syncing time: {e}")
        else:
            print("Cannot sync time: Wi-Fi not connected.")

    def read_sensor_data(self):
        print("Reading sensor data...")
        temperature = humidity = None
        try:
            self.dht_sensor.measure()
            temperature = self.dht_sensor.temperature()
            humidity = self.dht_sensor.humidity()
            
            if temperature is not None and humidity is not None:
                self.last_valid_temp = temperature
                self.last_valid_humidity = humidity
                print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
            else:
                print("Failed to read valid data from DHT sensor.")
        except Exception as e:
            print(f"Error reading from DHT sensor: {e}")
            if self.last_valid_temp is not None:
                temperature = self.last_valid_temp
                humidity = self.last_valid_humidity
        
        motion_detected = self.motion_sensor.value() == 1
        self.led.value(motion_detected)
        print(f"Motion detected: {'Yes' if motion_detected else 'No'}")
        return temperature, humidity, motion_detected

    def display_data(self, temp, humidity, motion):
        if not self.display_initialized:
            print("Display not initialized.")
            return
            
        self.display.fill(0)
        
        if self.show_logo:
            self.display.text("Master IISE", 20, 28, 1)
        else:
            self.display.text(f"Temp: {temp:.1f}C" if temp is not None else "Temp: Error", 0, 0, 1)
            self.display.text(f"Humidity: {humidity:.1f}%" if humidity is not None else "Humidity: Error", 0, 16, 1)
            self.display.text(f"Motion: {'Yes' if motion else 'No'}", 0, 32, 1)
            
            import time
            current_time = time.localtime()
            time_str = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
            self.display.text(f"Time: {time_str}", 0, 48, 1)
        
        self.display.show()
        print("Data displayed on OLED.")

    def send_sensor_data(self, temp, humidity, motion):
        print("Sending sensor data...")
        if not self.wifi.isconnected():
            print("Wi-Fi not connected. Attempting to reconnect...")
            if not self.setup_wifi():
                print("Failed to reconnect to Wi-Fi.")
                return
        
        try:
            import time
            current_time = time.localtime()
            timestamp = f"{current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}"
            
            data = {
                "device_id": DEVICE_ID,
                "temperature": temp,
                "humidity": humidity,
                "movement": "true" if motion else "false",
                "timestamp": timestamp
            }
            print(f"Data to send: {data}")
            response = urequests.post(
                SERVER_URL,
                headers={'Content-Type': 'application/json'},
                json=data,
                timeout=10
            )
            print(f"Server response: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error sending data: {e}")
        finally:
            gc.collect()

    def run(self):
        print("Starting main loop...")
        while True:
            current_millis = ticks_ms()
            temp, humidity, motion = self.read_sensor_data()
            
            if current_millis - self.prev_display_millis >= 3000:
                self.prev_display_millis = current_millis
                self.show_logo = not self.show_logo
                self.display_data(temp, humidity, motion)
            
            if current_millis - self.prev_data_millis >= 10000:
                self.prev_data_millis = current_millis
                if temp is not None and humidity is not None:
                    self.send_sensor_data(temp, humidity, motion)
            
            sleep(10)

def main():
    while True:
        try:
            monitor = SensorMonitor()
            monitor.run()
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Restarting in 40 seconds...")
            sleep(40)
            reset()

if __name__ == "__main__":
    main()
