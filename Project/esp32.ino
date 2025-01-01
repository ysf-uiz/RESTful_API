

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


// OLED Display Configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C


// WiFi credentials
const char* ssid = "wifi";
const char* password = "1234567890";


// Server configuration
const char* serverName = "IP/api/send-data";
const char* device_id = "NodeMCU001";


// Pin Configuration
#define DHTPIN 26
#define DHTTYPE DHT22
#define MOTION_PIN 14
#define LED_PIN 4


// Display timing
unsigned long previousMillis = 0;
const long interval = 3000;  // 3 seconds
bool showLogo = true;


// Initialize objects
DHT dht(DHTPIN, DHTTYPE);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org");
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


void setup() {
  Serial.begin(115200);
  pinMode(MOTION_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
 
  dht.begin();
  setupDisplay();
  setupWiFi();
 
  timeClient.begin();
  timeClient.setTimeOffset(0);
}


void loop() {
  unsigned long currentMillis = millis();
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  bool motionDetected = digitalRead(MOTION_PIN) == HIGH;
  digitalWrite(LED_PIN, motionDetected);


  // Switch display every 3 seconds
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    showLogo = !showLogo;  // Toggle between screens
   
    if (showLogo) {
      displayLogo();
    } else {
      displaySensorData(temperature, humidity, motionDetected);
    }
  }


  // Send data every 10 seconds
  static unsigned long lastDataSend = 0;
  if (currentMillis - lastDataSend >= 10000) {
    lastDataSend = currentMillis;
    if (!isnan(temperature) && !isnan(humidity)) {
      sendSensorData(temperature, humidity, motionDetected);
    }
  }
}


void setupDisplay() {
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    return;
  }
  display.display();
  delay(1000);
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
}


void displayLogo() {
  display.clearDisplay();
 
  // Draw IISE in center
  display.setTextSize(3);
  display.setTextColor(SSD1306_WHITE);
 
  // Calculate center position for "IISE"
  int16_t x1, y1;
  uint16_t w, h;
  display.getTextBounds("IISE", 0, 0, &x1, &y1, &w, &h);
  int x = (SCREEN_WIDTH - w) / 2;
  int y = (SCREEN_HEIGHT - h) / 2;
 
  display.setCursor(x, y);
  display.println("IISE");
 
  display.display();
}


void displaySensorData(float temp, float humidity, bool motion) {
  display.clearDisplay();
  display.setTextSize(1);
 
  // Temperature
  display.setCursor(0, 0);
  display.print("Temperature: ");
  if (!isnan(temp)) {
    display.print(temp, 1);
    display.println("C");
  } else {
    display.println("Error");
  }
 
  // Humidity
  display.setCursor(0, 16);
  display.print("Humidity: ");
  if (!isnan(humidity)) {
    display.print(humidity, 1);
    display.println("%");
  } else {
    display.println("Error");
  }
 
  // Motion Status
  display.setCursor(0, 32);
  display.print("Motion: ");
  display.println(motion ? "Detected" : "None");
 
  // Time
  display.setCursor(0, 48);
  timeClient.update();
  display.print("Time: ");
  display.println(timeClient.getFormattedTime());
 
  display.display();
}


void setupWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
 
  Serial.println("\nConnected to WiFi");
}


void sendSensorData(float temp, float humidity, bool motion) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");
   
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["movement"] = motion ? "true" : "false";
   
    String timestamp = timeClient.getFormattedTime();
    doc["timestamp"] = timestamp;
   
    String jsonString;
    serializeJson(doc, jsonString);
   
    int httpResponseCode = http.POST(jsonString);
    if (httpResponseCode > 0) {
      Serial.printf("HTTP Response code: %d\n", httpResponseCode);
    } else {
      Serial.printf("Error code: %d\n", httpResponseCode);
    }
   
    http.end();
  }
}




