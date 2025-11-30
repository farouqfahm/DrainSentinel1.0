/**
 * DrainSentinel: ESP32-S3 Embedded Firmware
 * 
 * Multi-modal Edge AI application for drainage blockage detection
 * and flood prediction using Edge Impulse models.
 * 
 * Hardware: Seeed XIAO ESP32-S3 Sense
 * Sensors: OV2640 Camera, HC-SR04 Ultrasonic, DHT22, BMP280
 * 
 * Author: DrainSentinel Team
 * Date: November 30, 2025
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>
#include <ArduinoJson.h>

// Edge Impulse SDK includes
#include "edge-impulse-sdk/classifier.h"
#include "edge-impulse-sdk/model-parameters/model_metadata.h"

// Sensor libraries
#include <Wire.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// WiFi Configuration
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";

// Server Configuration
WebServer server(80);
const int SERVER_PORT = 80;

// Sensor Configuration
#define DHT_PIN 2
#define DHT_TYPE DHT22
#define TRIG_PIN 3
#define ECHO_PIN 4
#define RAIN_SENSOR_PIN 5

// Timing Configuration
#define CAMERA_INTERVAL 5000      // 5 seconds between camera frames
#define SENSOR_INTERVAL 1000      // 1 second for ultrasonic sensor
#define ENV_INTERVAL 60000        // 60 seconds for environmental sensors
#define ALERT_THRESHOLD_HIGH 0.7
#define ALERT_THRESHOLD_MEDIUM 0.5

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Sensor objects
DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_BMP280 bmp280;

// Timing variables
unsigned long last_camera_time = 0;
unsigned long last_sensor_time = 0;
unsigned long last_env_time = 0;

// Data buffers
float water_level_buffer[60];  // 60-second rolling window
int buffer_index = 0;

// Current sensor readings
struct {
    float temperature;
    float humidity;
    float pressure;
    float rainfall;
    float water_level;
} current_env_data = {0, 0, 0, 0, 0};

// Model results
struct {
    float blockage_score;
    int water_level_class;
    float flood_risk;
    float alert_score;
    char alert_level[10];
    char alert_message[256];
} inference_results = {0, 0, 0, 0, "LOW", ""};

// ============================================================================
// SENSOR FUNCTIONS
// ============================================================================

/**
 * Initialize all sensors
 */
void init_sensors() {
    Serial.println("[INIT] Initializing sensors...");
    
    // Initialize DHT22
    dht.begin();
    Serial.println("  ✓ DHT22 initialized");
    
    // Initialize BMP280
    if (!bmp280.begin(0x76)) {
        Serial.println("  ✗ BMP280 initialization failed!");
    } else {
        Serial.println("  ✓ BMP280 initialized");
    }
    
    // Initialize ultrasonic sensor pins
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    Serial.println("  ✓ Ultrasonic sensor initialized");
    
    // Initialize rain sensor
    pinMode(RAIN_SENSOR_PIN, INPUT);
    Serial.println("  ✓ Rain sensor initialized");
}

/**
 * Read temperature and humidity from DHT22
 */
void read_dht22() {
    float temp = dht.readTemperature();
    float humidity = dht.readHumidity();
    
    if (isnan(temp) || isnan(humidity)) {
        Serial.println("[SENSOR] DHT22 read failed");
        return;
    }
    
    current_env_data.temperature = constrain(temp, 15, 40);
    current_env_data.humidity = constrain(humidity, 0, 100);
    
    Serial.printf("[SENSOR] Temperature: %.1f°C, Humidity: %.1f%%\n", 
                  current_env_data.temperature, current_env_data.humidity);
}

/**
 * Read pressure from BMP280
 */
void read_bmp280() {
    float pressure = bmp280.readPressure() / 100.0;  // Convert to hPa
    current_env_data.pressure = constrain(pressure, 990, 1040);
    
    Serial.printf("[SENSOR] Pressure: %.1f hPa\n", current_env_data.pressure);
}

/**
 * Read water level from ultrasonic sensor (HC-SR04)
 */
float read_ultrasonic() {
    // Send trigger pulse
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    // Measure echo time
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
    
    // Calculate distance (speed of sound = 343 m/s)
    float distance = (duration * 0.0343) / 2;
    
    // Constrain to valid range
    distance = constrain(distance, 0, 100);
    
    return distance;
}

/**
 * Read rainfall from rain sensor
 */
void read_rain_sensor() {
    // Simple rain detection (0-100 mm/hour scale)
    // In real implementation, use calibrated sensor
    int rain_value = analogRead(RAIN_SENSOR_PIN);
    current_env_data.rainfall = map(rain_value, 0, 4095, 0, 100);
    
    Serial.printf("[SENSOR] Rainfall: %.1f mm/hour\n", current_env_data.rainfall);
}

/**
 * Update water level buffer (rolling window)
 */
void update_water_level_buffer(float water_level) {
    current_env_data.water_level = constrain(water_level, 0, 100);
    
    // Add to circular buffer
    water_level_buffer[buffer_index] = water_level;
    buffer_index = (buffer_index + 1) % 60;
    
    Serial.printf("[SENSOR] Water Level: %.1f cm\n", water_level);
}

// ============================================================================
// CAMERA FUNCTIONS
// ============================================================================

/**
 * Capture and preprocess camera frame
 * Note: Actual implementation requires camera driver
 */
void capture_camera_frame(uint8_t* frame_buffer) {
    // This is a placeholder - actual implementation depends on camera library
    // For ESP32-S3 with OV2640, use esp32-camera library
    
    Serial.println("[CAMERA] Capturing frame...");
    
    // In real implementation:
    // 1. Capture frame from camera
    // 2. Resize to 96x96
    // 3. Normalize to 0-1 range
    // 4. Store in frame_buffer
}

// ============================================================================
// EDGE IMPULSE INFERENCE FUNCTIONS
// ============================================================================

/**
 * Run visual blockage detection model
 */
float run_visual_inference(uint8_t* frame_data) {
    Serial.println("[INFERENCE] Running visual model...");
    
    // Prepare signal for Edge Impulse
    signal_t signal;
    signal.total_length = EI_CLASSIFIER_INPUT_SIZE;
    signal.get_data = [](size_t offset, size_t length, float *out_ptr) -> int {
        // Copy frame data to output buffer
        // This is a simplified placeholder
        memset(out_ptr, 0, length * sizeof(float));
        return 0;
    };
    
    // Run classifier
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
    
    if (err != EI_IMPULSE_OK) {
        Serial.printf("[ERROR] Visual inference failed: %d\n", err);
        return 0.0;
    }
    
    // Extract blockage probability
    float blockage_score = 0.0;
    for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        if (strcmp(result.classification[ix].label, "blockage") == 0) {
            blockage_score = result.classification[ix].value;
            break;
        }
    }
    
    Serial.printf("[INFERENCE] Visual model output: %.2f\n", blockage_score);
    return blockage_score;
}

/**
 * Run water level monitoring model
 */
int run_sensor_inference() {
    Serial.println("[INFERENCE] Running sensor model...");
    
    // Prepare signal for Edge Impulse
    signal_t signal;
    signal.total_length = 60;  // 60-second window
    signal.get_data = [](size_t offset, size_t length, float *out_ptr) -> int {
        // Copy water level buffer to output
        for (size_t i = 0; i < length; i++) {
            out_ptr[i] = water_level_buffer[(buffer_index + i) % 60] / 100.0;  // Normalize
        }
        return 0;
    };
    
    // Run classifier
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
    
    if (err != EI_IMPULSE_OK) {
        Serial.printf("[ERROR] Sensor inference failed: %d\n", err);
        return 0;
    }
    
    // Determine water level class
    int water_level_class = 0;
    float max_score = 0.0;
    
    for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        if (result.classification[ix].value > max_score) {
            max_score = result.classification[ix].value;
            if (strcmp(result.classification[ix].label, "normal") == 0) {
                water_level_class = 0;
            } else if (strcmp(result.classification[ix].label, "elevated") == 0) {
                water_level_class = 1;
            } else if (strcmp(result.classification[ix].label, "critical") == 0) {
                water_level_class = 2;
            }
        }
    }
    
    Serial.printf("[INFERENCE] Sensor model output: class %d\n", water_level_class);
    return water_level_class;
}

/**
 * Run flood prediction model
 */
float run_environmental_inference() {
    Serial.println("[INFERENCE] Running environmental model...");
    
    // Prepare signal for Edge Impulse
    signal_t signal;
    signal.total_length = 5;  // 5 environmental features
    signal.get_data = [](size_t offset, size_t length, float *out_ptr) -> int {
        // Normalize features to 0-1 range
        out_ptr[0] = (current_env_data.temperature - 15) / 25;
        out_ptr[1] = current_env_data.humidity / 100;
        out_ptr[2] = 1 - ((current_env_data.pressure - 990) / 50);
        out_ptr[3] = current_env_data.rainfall / 100;
        out_ptr[4] = current_env_data.water_level / 100;
        return 0;
    };
    
    // Run classifier
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
    
    if (err != EI_IMPULSE_OK) {
        Serial.printf("[ERROR] Environmental inference failed: %d\n", err);
        return 0.0;
    }
    
    // Extract flood risk probability
    float flood_risk = 0.0;
    for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
        if (strcmp(result.classification[ix].label, "high_risk") == 0) {
            flood_risk = result.classification[ix].value;
            break;
        }
    }
    
    Serial.printf("[INFERENCE] Environmental model output: %.2f\n", flood_risk);
    return flood_risk;
}

// ============================================================================
// FUSION AND DECISION LOGIC
// ============================================================================

/**
 * Fuse outputs from all three models and generate alert
 */
void fuse_and_alert() {
    Serial.println("[FUSION] Fusing model outputs...");
    
    // Weighted combination
    inference_results.alert_score = (
        0.40 * inference_results.blockage_score +
        0.30 * (inference_results.water_level_class / 2.0) +
        0.30 * inference_results.flood_risk
    );
    
    // Decision logic
    if (inference_results.alert_score > ALERT_THRESHOLD_HIGH && 
        inference_results.water_level_class == 2) {
        strcpy(inference_results.alert_level, "HIGH");
        strcpy(inference_results.alert_message, 
               "CRITICAL: Drainage blockage detected with high water level!");
    } else if (inference_results.alert_score > ALERT_THRESHOLD_MEDIUM || 
               inference_results.water_level_class == 1) {
        strcpy(inference_results.alert_level, "MEDIUM");
        strcpy(inference_results.alert_message, 
               "WARNING: Potential blockage or elevated water level detected.");
    } else if (inference_results.flood_risk > 0.7) {
        strcpy(inference_results.alert_level, "MEDIUM");
        strcpy(inference_results.alert_message, 
               "WARNING: Flood risk predicted based on weather patterns.");
    } else {
        strcpy(inference_results.alert_level, "LOW");
        strcpy(inference_results.alert_message, 
               "OK: Drainage system operating normally.");
    }
    
    Serial.printf("[ALERT] Level: %s\n", inference_results.alert_level);
    Serial.printf("[ALERT] Message: %s\n", inference_results.alert_message);
}

/**
 * Send alert via WiFi (HTTP POST)
 */
void send_alert() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[ALERT] WiFi not connected, storing locally");
        return;
    }
    
    Serial.println("[ALERT] Sending alert via WiFi...");
    
    // Create JSON payload
    DynamicJsonDocument doc(512);
    doc["timestamp"] = millis();
    doc["alert_level"] = inference_results.alert_level;
    doc["alert_message"] = inference_results.alert_message;
    doc["blockage_score"] = inference_results.blockage_score;
    doc["water_level_class"] = inference_results.water_level_class;
    doc["flood_risk"] = inference_results.flood_risk;
    doc["temperature"] = current_env_data.temperature;
    doc["humidity"] = current_env_data.humidity;
    doc["water_level"] = current_env_data.water_level;
    
    // Serialize to string
    String payload;
    serializeJson(doc, payload);
    
    // Send via HTTP POST (placeholder - implement with actual server)
    Serial.printf("[ALERT] Payload: %s\n", payload.c_str());
}

// ============================================================================
// WEB SERVER FUNCTIONS
// ============================================================================

/**
 * Handle HTTP GET request for status
 */
void handle_status() {
    DynamicJsonDocument doc(512);
    
    doc["status"] = "running";
    doc["uptime_ms"] = millis();
    doc["alert_level"] = inference_results.alert_level;
    doc["blockage_score"] = inference_results.blockage_score;
    doc["water_level"] = current_env_data.water_level;
    doc["temperature"] = current_env_data.temperature;
    doc["humidity"] = current_env_data.humidity;
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
}

/**
 * Handle HTTP GET request for alerts
 */
void handle_alerts() {
    DynamicJsonDocument doc(512);
    
    doc["alert_level"] = inference_results.alert_level;
    doc["alert_message"] = inference_results.alert_message;
    doc["alert_score"] = inference_results.alert_score;
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
}

/**
 * Initialize web server
 */
void init_web_server() {
    server.on("/status", HTTP_GET, handle_status);
    server.on("/alerts", HTTP_GET, handle_alerts);
    
    server.begin();
    Serial.printf("[SERVER] Web server started on port %d\n", SERVER_PORT);
}

// ============================================================================
// MAIN SETUP AND LOOP
// ============================================================================

/**
 * Arduino setup function
 */
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n=== DrainSentinel ESP32-S3 Firmware ===\n");
    
    // Initialize sensors
    init_sensors();
    
    // Initialize WiFi
    Serial.println("[WIFI] Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WIFI] Connection failed, operating in local mode");
    }
    
    // Initialize web server
    init_web_server();
    
    Serial.println("\n[SYSTEM] Initialization complete!\n");
}

/**
 * Arduino main loop
 */
void loop() {
    // Handle web server requests
    server.handleClient();
    
    unsigned long current_time = millis();
    
    // Read environmental sensors (every 60 seconds)
    if (current_time - last_env_time >= ENV_INTERVAL) {
        read_dht22();
        read_bmp280();
        read_rain_sensor();
        last_env_time = current_time;
    }
    
    // Read ultrasonic sensor (every 1 second)
    if (current_time - last_sensor_time >= SENSOR_INTERVAL) {
        float water_level = read_ultrasonic();
        update_water_level_buffer(water_level);
        last_sensor_time = current_time;
    }
    
    // Run inference (every 5 seconds)
    if (current_time - last_camera_time >= CAMERA_INTERVAL) {
        Serial.println("\n[CYCLE] Running inference cycle...");
        
        // Capture camera frame
        uint8_t frame_buffer[EI_CLASSIFIER_INPUT_SIZE];
        capture_camera_frame(frame_buffer);
        
        // Run all three models
        inference_results.blockage_score = run_visual_inference(frame_buffer);
        inference_results.water_level_class = run_sensor_inference();
        inference_results.flood_risk = run_environmental_inference();
        
        // Fuse outputs and generate alert
        fuse_and_alert();
        
        // Send alert if needed
        if (strcmp(inference_results.alert_level, "LOW") != 0) {
            send_alert();
        }
        
        last_camera_time = current_time;
    }
    
    delay(100);  // Small delay to prevent watchdog timeout
}

// ============================================================================
// END OF FIRMWARE
// ============================================================================
