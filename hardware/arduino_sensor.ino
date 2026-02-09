/**
 * DrainSentinel: Arduino Sensor Hub
 * 
 * Reads ultrasonic sensor (HC-SR04) for water level measurement
 * and sends data to Metis AI Accelerator via USB serial.
 * 
 * Hardware: Arduino Uno Rev 4 (WiFi or Minima)
 * Sensor: HC-SR04 Ultrasonic Distance Sensor
 * 
 * Wiring:
 *   HC-SR04 VCC  → Arduino 5V
 *   HC-SR04 GND  → Arduino GND
 *   HC-SR04 TRIG → Arduino Pin 9
 *   HC-SR04 ECHO → Arduino Pin 10
 * 
 * Output: JSON over serial at 9600 baud
 *   {"water_level_cm": 45.2, "distance_raw": 45.2, "valid": true}
 */

// Pin definitions
#define TRIG_PIN 9
#define ECHO_PIN 10

// Configuration
#define SERIAL_BAUD 9600
#define MEASUREMENT_INTERVAL_MS 1000  // 1 second between readings
#define NUM_SAMPLES 5                  // Average this many readings
#define MAX_DISTANCE_CM 400            // Maximum measurable distance
#define MIN_DISTANCE_CM 2              // Minimum measurable distance

// Calibration values (set during calibration)
float emptyDistance = 100.0;  // Distance (cm) when drain is empty (0%)
float fullDistance = 10.0;    // Distance (cm) when water is critical (100%)

// Timing
unsigned long lastMeasurement = 0;

// Rolling average buffer
float readings[NUM_SAMPLES];
int readIndex = 0;
float total = 0;
bool bufferFilled = false;

void setup() {
    // Initialize serial communication
    Serial.begin(SERIAL_BAUD);
    
    // Configure pins
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    
    // Ensure trigger is low
    digitalWrite(TRIG_PIN, LOW);
    
    // Initialize readings buffer
    for (int i = 0; i < NUM_SAMPLES; i++) {
        readings[i] = 0;
    }
    
    // Startup message
    Serial.println("{\"status\": \"DrainSentinel Arduino Sensor Hub started\"}");
    
    // Initial delay for sensor stabilization
    delay(500);
}

/**
 * Measure distance using ultrasonic sensor
 * Returns distance in centimeters, or -1 if invalid
 */
float measureDistance() {
    // Send trigger pulse
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    // Measure echo pulse duration (with timeout)
    // Timeout = max distance * 2 / speed of sound (in microseconds)
    unsigned long timeout = (MAX_DISTANCE_CM * 2 * 1000000UL) / 34300;
    long duration = pulseIn(ECHO_PIN, HIGH, timeout);
    
    // Check for timeout
    if (duration == 0) {
        return -1;  // No echo received
    }
    
    // Calculate distance
    // Speed of sound = 343 m/s = 0.0343 cm/µs
    // Distance = (duration * 0.0343) / 2
    float distance = (duration * 0.0343) / 2.0;
    
    // Validate range
    if (distance < MIN_DISTANCE_CM || distance > MAX_DISTANCE_CM) {
        return -1;  // Out of range
    }
    
    return distance;
}

/**
 * Get averaged distance from multiple samples
 */
float getAveragedDistance() {
    float distance = measureDistance();
    
    if (distance < 0) {
        // Invalid reading - don't update average
        return (bufferFilled) ? (total / NUM_SAMPLES) : -1;
    }
    
    // Update rolling average
    total -= readings[readIndex];
    readings[readIndex] = distance;
    total += readings[readIndex];
    
    readIndex = (readIndex + 1) % NUM_SAMPLES;
    
    if (readIndex == 0) {
        bufferFilled = true;
    }
    
    if (bufferFilled) {
        return total / NUM_SAMPLES;
    } else {
        // Not enough samples yet
        float sum = 0;
        for (int i = 0; i < readIndex; i++) {
            sum += readings[i];
        }
        return sum / readIndex;
    }
}

/**
 * Convert distance to water level percentage
 * 0% = empty (water far from sensor)
 * 100% = critical (water close to sensor)
 */
float distanceToPercent(float distance) {
    if (distance < 0) return -1;
    
    // Invert the relationship (smaller distance = higher water)
    float percent = 100.0 - ((distance - fullDistance) / (emptyDistance - fullDistance) * 100.0);
    
    // Clamp to valid range
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    
    return percent;
}

/**
 * Send sensor data as JSON
 */
void sendData(float distance, float waterLevelPercent, bool valid) {
    Serial.print("{");
    Serial.print("\"water_level_cm\": ");
    Serial.print(distance, 1);
    Serial.print(", \"water_level_percent\": ");
    Serial.print(waterLevelPercent, 1);
    Serial.print(", \"distance_raw\": ");
    Serial.print(distance, 1);
    Serial.print(", \"valid\": ");
    Serial.print(valid ? "true" : "false");
    Serial.print(", \"timestamp\": ");
    Serial.print(millis());
    Serial.println("}");
}

/**
 * Check for calibration commands from serial
 */
void checkSerialCommands() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("CAL_EMPTY")) {
            // Calibrate empty distance (current reading)
            float current = getAveragedDistance();
            if (current > 0) {
                emptyDistance = current;
                Serial.print("{\"calibration\": \"empty\", \"value\": ");
                Serial.print(emptyDistance, 1);
                Serial.println("}");
            }
        }
        else if (command.startsWith("CAL_FULL")) {
            // Calibrate full/critical distance (current reading)
            float current = getAveragedDistance();
            if (current > 0) {
                fullDistance = current;
                Serial.print("{\"calibration\": \"full\", \"value\": ");
                Serial.print(fullDistance, 1);
                Serial.println("}");
            }
        }
        else if (command.startsWith("SET_EMPTY:")) {
            // Set empty distance manually
            emptyDistance = command.substring(10).toFloat();
            Serial.print("{\"set\": \"empty\", \"value\": ");
            Serial.print(emptyDistance, 1);
            Serial.println("}");
        }
        else if (command.startsWith("SET_FULL:")) {
            // Set full distance manually
            fullDistance = command.substring(9).toFloat();
            Serial.print("{\"set\": \"full\", \"value\": ");
            Serial.print(fullDistance, 1);
            Serial.println("}");
        }
        else if (command == "STATUS") {
            // Report current calibration
            Serial.print("{\"empty_distance\": ");
            Serial.print(emptyDistance, 1);
            Serial.print(", \"full_distance\": ");
            Serial.print(fullDistance, 1);
            Serial.println("}");
        }
    }
}

void loop() {
    // Check for calibration commands
    checkSerialCommands();
    
    // Time for a new measurement?
    unsigned long currentTime = millis();
    if (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL_MS) {
        lastMeasurement = currentTime;
        
        // Get averaged distance
        float distance = getAveragedDistance();
        
        // Calculate water level percentage
        float waterLevelPercent = distanceToPercent(distance);
        
        // Send data
        bool valid = (distance > 0 && waterLevelPercent >= 0);
        sendData(distance, waterLevelPercent, valid);
    }
}
