import network
import urequests as requests
import time
import machine
from machine import Pin
from dht import DHT22
from ntptime import settime

# Identifiants WiFi
ssid = "wifi"
password = "1234567890"

# Configuration du serveur
serverName = "http://IP:5000/api/send-data"  # Remplacez IP par l'adresse IP de votre serveur
device_id = "NodeMCU002"

# Configuration des broches
dht_pin = Pin(2, Pin.IN)
dht_sensor = DHT22(dht_pin)
motion_pin = Pin(12, Pin.IN)
led_pin = Pin(4, Pin.OUT)

# Initialisation des objets
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def setupWiFi():
    """Configure la connexion WiFi."""
    if not wlan.isconnected():
        print('Connexion au WiFi en cours...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.')
        print('\nConnecté au WiFi')
        print('Configuration réseau:', wlan.ifconfig())

def sendSensorData(temp, humidity, motion):
    """Envoie les données des capteurs au serveur."""
    if wlan.isconnected():
        try:
            # Récupération de l'heure
            try:
                settime()  # Synchronise l'heure avec un serveur NTP
                current_time = time.localtime()
                timestamp = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
            except OSError as e:
                print("Erreur lors de la récupération de l'heure:", e)
                timestamp = "Erreur Heure"

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
                print("Données envoyées avec succès!")
                print("Données:", data)  # Affiche les données envoyées
            else:
                print("Erreur lors de l'envoi des données. Code d'état:", response.status_code)
                print("Réponse:", response.text)

            response.close()

        except OSError as e:
            print("Erreur lors de l'envoi des données:", e)

# Programme principal
setupWiFi()

last_data_send = time.time()

while True:
    current_time = time.time()

    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        motionDetected = motion_pin.value() == 1
        led_pin.value(not motionDetected)  # Allume la LED si un mouvement est détecté (logique inversée)

        print("Température: {:.1f}°C, Humidité: {:.1f}%, Mouvement: {}".format(
            temperature, humidity, "true" if motionDetected else "false"
        ))

    except OSError as e:
        print("Erreur lors de la lecture du capteur:", e)
        temperature = float('nan')  # Assigne NaN (Not a Number) si la lecture du capteur échoue
        humidity = float('nan')

    # Envoie les données toutes les 10 secondes
    if current_time - last_data_send >= 10:
        if not (isinstance(temperature, float) and isinstance(humidity, float) and (temperature != float('nan')) and (humidity != float('nan'))):
            print("Envoi des données ignoré en raison de lectures de capteur invalides.")
        else:
            sendSensorData(temperature, humidity, motionDetected)

        last_data_send = current_time

    time.sleep(1)
