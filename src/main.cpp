#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "FS.h"
#include "SD.h"
#include "SPI.h"

// Pin definitions for XIAO ESP32S3 SENSE
// LED_BUILTIN is already defined in the framework (pin 21)
#define BUTTON_PIN 0    // Boot button (can be used as input)

// Camera pin definitions for XIAO ESP32S3 SENSE
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39
#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15
#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13

// Microphone and SD card pins
#define MIC_PIN           42  // Digital microphone data pin
#define MIC_CLOCK_PIN     41  // Digital microphone clock pin
#define SD_CS_PIN         21  // SD card chip select

// WiFi credentials (change these to your network)
const char* ssid = "Buffalo-G-B158";
const char* password = "fnf3h4igtvtb6";

// AP Mode settings
const char* ap_ssid = "XIAO-ESP32S3-SENSE";
const char* ap_password = "12345678";

// Variables
unsigned long previousMillis = 0;
unsigned long previousScanMillis = 0;
const long interval = 1000;  // LED blink interval
const long scanInterval = 30000;  // WiFi scan interval (30 seconds)
bool ledState = false;
bool wifiConnected = false;
bool apMode = false;

// Web server
AsyncWebServer server(80);

// System monitoring variables
struct SystemStats {
  unsigned long uptime;
  uint32_t freeHeap;
  int wifiRSSI;
  bool ledStatus;
  int temperature; // Placeholder for future sensor
  bool motionDetected; // Placeholder for PIR sensor
};

// Debug settings
#define DEBUG_SERIAL 1
#define DEBUG_WIFI 1
#define DEBUG_CAMERA 1
#define DEBUG_WEB 1

// Debug macros
#if DEBUG_SERIAL
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(fmt, ...) Serial.printf(fmt, ##__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(fmt, ...) do {} while(0)
#endif

// Function declarations
void setupWebServer();
bool initCamera();
void handleCameraStream(AsyncWebServerRequest *request);
void debugSystemInfo();
void debugWiFiInfo();
void debugCameraInfo();

// Camera state
bool cameraInitialized = false;
String lastError = "";

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(2000); // Longer delay for serial stabilization
  
  DEBUG_PRINTLN("\n========================================");
  DEBUG_PRINTLN("XIAO ESP32S3 SENSE Debug Mode Starting");
  DEBUG_PRINTLN("========================================");
  
  // System info debugging
  debugSystemInfo();
  

  
  // Initialize pins with debugging
  DEBUG_PRINTLN("\n--- Pin Initialization ---");
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(LED_BUILTIN, LOW);
  DEBUG_PRINTF("LED_BUILTIN (Pin %d): OUTPUT mode set\n", LED_BUILTIN);
  DEBUG_PRINTF("BUTTON_PIN (Pin %d): INPUT_PULLUP mode set\n", BUTTON_PIN);
  DEBUG_PRINTF("Initial LED state: %s\n", digitalRead(LED_BUILTIN) ? "HIGH" : "LOW");
  
  // WiFi connection attempt with debugging
  DEBUG_PRINTLN("\n--- WiFi Diagnostics ---");
  debugWiFiInfo();
  DEBUG_PRINTF("Target SSID: '%s'\n", ssid);
  DEBUG_PRINTF("Password length: %d characters\n", strlen(password));
  DEBUG_PRINTF("WiFi mode before scan: %d\n", WiFi.getMode());
  
  // Scan for available networks first
  Serial.println("Scanning for WiFi networks...");
  int n = WiFi.scanNetworks();
  Serial.printf("Found %d networks:\n", n);
  bool ssidFound = false;
  
  for (int i = 0; i < n; ++i) {
    Serial.printf("%d: %s (%d dBm) %s\n", 
                  i + 1, 
                  WiFi.SSID(i).c_str(), 
                  WiFi.RSSI(i),
                  (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Encrypted");
    
    if (WiFi.SSID(i) == ssid) {
      ssidFound = true;
      Serial.printf("*** Target SSID found with signal strength: %d dBm\n", WiFi.RSSI(i));
    }
  }
  
  if (!ssidFound) {
    Serial.printf("WARNING: SSID '%s' not found in scan!\n", ssid);
  }
  
  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    // Show status every 10 attempts
    if (attempts % 10 == 0) {
      Serial.printf("\nAttempt %d/30, Status: %d\n", attempts, WiFi.status());
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nWiFi connected successfully!");
    Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("Signal strength: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\nWiFi connection failed - starting AP mode");
    
    // Start Access Point mode
    Serial.println("Starting Access Point mode...");
    WiFi.mode(WIFI_AP);
    WiFi.softAP(ap_ssid, ap_password);
    
    IPAddress IP = WiFi.softAPIP();
    Serial.printf("AP IP address: %s\n", IP.toString().c_str());
    Serial.printf("AP SSID: %s\n", ap_ssid);
    Serial.printf("AP Password: %s\n", ap_password);
    Serial.println("Connect your device to this AP to access the camera!");
    apMode = true;
  }
  
  // Initialize camera with detailed debugging
  DEBUG_PRINTLN("\n--- Camera Initialization ---");
  debugCameraInfo();
  DEBUG_PRINTLN("Starting camera initialization...");
  
  cameraInitialized = initCamera();
  if (cameraInitialized) {
    DEBUG_PRINTLN("✓ Camera initialized successfully!");
    DEBUG_PRINTF("PSRAM found: %s\n", psramFound() ? "YES" : "NO");
    if (psramFound()) {
      DEBUG_PRINTF("PSRAM size: %d bytes\n", ESP.getPsramSize());
      DEBUG_PRINTF("Free PSRAM: %d bytes\n", ESP.getFreePsram());
    }
  } else {
    DEBUG_PRINTLN("✗ Camera initialization FAILED!");
    DEBUG_PRINTF("Last error: %s\n", lastError.c_str());
  }
  
  // Setup web server
  setupWebServer();
  
  DEBUG_PRINTLN("\n========================================");
  DEBUG_PRINTLN("SETUP COMPLETE - System Status:");
  DEBUG_PRINTF("- Camera: %s\n", cameraInitialized ? "✓ OK" : "✗ FAILED");
  DEBUG_PRINTF("- WiFi: %s\n", wifiConnected ? "✓ Connected" : (apMode ? "✓ AP Mode" : "✗ Failed"));
  DEBUG_PRINTF("- Web Server: ✓ Running\n");
  DEBUG_PRINTF("- Free Heap: %d bytes\n", ESP.getFreeHeap());
  DEBUG_PRINTLN("========================================\n");
}

void setupWebServer() {
  // Serve main monitoring page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>XIAO ESP32S3 Monitoring System</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .status-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }
        .status-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .status-label { color: #666; font-size: 14px; }
        .led-control { text-align: center; margin: 20px 0; }
        .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0056b3; }
        .log-area { background: #000; color: #00ff00; padding: 15px; border-radius: 5px; font-family: monospace; height: 200px; overflow-y: scroll; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 XIAO ESP32S3 Monitoring System</h1>
            <p>Real-time system status and control</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="status-value" id="uptime">--</div>
                <div class="status-label">Uptime (seconds)</div>
            </div>
            <div class="status-card">
                <div class="status-value" id="heap">--</div>
                <div class="status-label">Free Heap (bytes)</div>
            </div>
            <div class="status-card">
                <div class="status-value" id="wifi">--</div>
                <div class="status-label">WiFi RSSI (dBm)</div>
            </div>
            <div class="status-card">
                <div class="status-value" id="led">--</div>
                <div class="status-label">LED Status</div>
            </div>
        </div>
        
        <div class="led-control">
            <button class="btn" onclick="toggleLED()">Toggle LED</button>
            <button class="btn" onclick="scanWiFi()">Scan WiFi</button>
            <button class="btn" onclick="restartDevice()">Restart Device</button>
        </div>
        
        <div class="alert alert-success" id="status-message">
            System online and monitoring...
        </div>
        
        <div class="log-area" id="logs">
            Connecting to system...<br>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uptime').textContent = data.uptime;
                    document.getElementById('heap').textContent = data.freeHeap.toLocaleString();
                    document.getElementById('wifi').textContent = data.wifiRSSI;
                    document.getElementById('led').textContent = data.ledStatus ? 'ON' : 'OFF';
                    
                    // Add to log
                    const logs = document.getElementById('logs');
                    const timestamp = new Date().toLocaleTimeString();
                    logs.innerHTML += `[${timestamp}] Status updated - Heap: ${data.freeHeap}, RSSI: ${data.wifiRSSI}<br>`;
                    logs.scrollTop = logs.scrollHeight;
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('status-message').className = 'alert alert-warning';
                    document.getElementById('status-message').textContent = 'Connection error - retrying...';
                });
        }
        
        function toggleLED() {
            fetch('/api/led/toggle', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status-message').textContent = `LED ${data.status}`;
                });
        }
        
        function scanWiFi() {
            document.getElementById('status-message').textContent = 'Scanning WiFi networks...';
            fetch('/api/wifi/scan', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status-message').textContent = `Found ${data.networks} WiFi networks`;
                });
        }
        
        function restartDevice() {
            if(confirm('Are you sure you want to restart the device?')) {
                document.getElementById('status-message').textContent = 'Restarting device...';
                fetch('/api/restart', {method: 'POST'});
            }
        }
        
        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus(); // Initial load
    </script>
</body>
</html>
)rawliteral";
    request->send(200, "text/html", html);
  });

  // API endpoint for system status
  server.on("/api/status", HTTP_GET, [](AsyncWebServerRequest *request){
    SystemStats stats;
    stats.uptime = millis() / 1000;
    stats.freeHeap = ESP.getFreeHeap();
    stats.wifiRSSI = WiFi.RSSI();
    stats.ledStatus = ledState;
    stats.temperature = 25; // Placeholder
    stats.motionDetected = false; // Placeholder
    
    JsonDocument doc;
    doc["uptime"] = stats.uptime;
    doc["freeHeap"] = stats.freeHeap;
    doc["wifiRSSI"] = stats.wifiRSSI;
    doc["ledStatus"] = stats.ledStatus;
    doc["temperature"] = stats.temperature;
    doc["motionDetected"] = stats.motionDetected;
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });

  // API endpoint for LED control
  server.on("/api/led/toggle", HTTP_POST, [](AsyncWebServerRequest *request){
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState);
    
    JsonDocument doc;
    doc["status"] = ledState ? "ON" : "OFF";
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });

  // API endpoint for WiFi scan
  server.on("/api/wifi/scan", HTTP_POST, [](AsyncWebServerRequest *request){
    int n = WiFi.scanNetworks();
    
    JsonDocument doc;
    doc["networks"] = n;
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
  });

  // API endpoint for device restart
  server.on("/api/restart", HTTP_POST, [](AsyncWebServerRequest *request){
    JsonDocument doc;
    doc["status"] = "restarting";
    
    String response;
    serializeJson(doc, response);
    request->send(200, "application/json", response);
    
    delay(1000);
    ESP.restart();
  });

  // Camera stream endpoint
  server.on("/camera", HTTP_GET, handleCameraStream);
  
  // Camera capture endpoint
  server.on("/api/camera/capture", HTTP_GET, [](AsyncWebServerRequest *request){
    if (!cameraInitialized) {
      request->send(500, "application/json", "{\"error\":\"Camera not initialized\"}");
      return;
    }
    
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      request->send(500, "application/json", "{\"error\":\"Camera capture failed\"}");
      return;
    }
    
    AsyncWebServerResponse *response = request->beginResponse(200, "image/jpeg", fb->buf, fb->len);
    response->addHeader("Cache-Control", "no-cache");
    request->send(response);
    
    esp_camera_fb_return(fb);
  });

  server.begin();
  Serial.println("Web server started!");
  
  if (apMode) {
    Serial.printf("Access monitoring system at: http://%s\n", WiFi.softAPIP().toString().c_str());
    if (cameraInitialized) {
      Serial.printf("Camera stream available at: http://%s/camera\n", WiFi.softAPIP().toString().c_str());
    }
  } else if (wifiConnected) {
    Serial.printf("Access monitoring system at: http://%s\n", WiFi.localIP().toString().c_str());
    if (cameraInitialized) {
      Serial.printf("Camera stream available at: http://%s/camera\n", WiFi.localIP().toString().c_str());
    }
  }
}

bool initCamera() {
  DEBUG_PRINTLN("Configuring camera pins...");
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  // Suppress deprecated warnings for camera pin configuration
  #pragma GCC diagnostic push
  #pragma GCC diagnostic ignored "-Wdeprecated-declarations"
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  #pragma GCC diagnostic pop
  
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  DEBUG_PRINTLN("Camera pin configuration:");
  DEBUG_PRINTF("  XCLK: %d, PCLK: %d, VSYNC: %d, HREF: %d\n", 
               config.pin_xclk, config.pin_pclk, config.pin_vsync, config.pin_href);
  DEBUG_PRINTF("  SDA: %d, SCL: %d\n", config.pin_sccb_sda, config.pin_sccb_scl);
  DEBUG_PRINTF("  Data pins: %d,%d,%d,%d,%d,%d,%d,%d\n", 
               config.pin_d0, config.pin_d1, config.pin_d2, config.pin_d3,
               config.pin_d4, config.pin_d5, config.pin_d6, config.pin_d7);
  
  // Frame size and quality settings
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA; // 1600x1200
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Initialize camera with warning suppression
  #pragma GCC diagnostic push
  #pragma GCC diagnostic ignored "-Wdeprecated-declarations"
  esp_err_t err = esp_camera_init(&config);
  #pragma GCC diagnostic pop
  
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    lastError = "Camera init failed with error 0x" + String(err, HEX);
    return false;
  }
  
  // Get camera sensor
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    // Initial sensor setup
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 0);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0-No Effect, 1-Negative, 2-Grayscale, 3-Red Tint, 4-Green Tint, 5-Blue Tint, 6-Sepia)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
  }
  
  return true;
}

void handleCameraStream(AsyncWebServerRequest *request) {
  if (!cameraInitialized) {
    request->send(500, "text/plain", "Camera not initialized");
    return;
  }
  
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>XIAO ESP32S3 SENSE - Camera Stream</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #000; color: white; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        .camera-view { margin: 20px 0; }
        .camera-image { max-width: 100%; height: auto; border: 2px solid #333; border-radius: 10px; }
        .controls { margin: 20px 0; }
        .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .status { margin: 10px 0; padding: 10px; background: #1a1a1a; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 XIAO ESP32S3 SENSE Camera</h1>
        
        <div class="camera-view">
            <img id="camera-stream" class="camera-image" src="/api/camera/capture" alt="Camera Stream">
        </div>
        
        <div class="controls">
            <button class="btn" onclick="refreshImage()">Refresh Image</button>
            <button class="btn" onclick="toggleAutoRefresh()">Toggle Auto Refresh</button>
            <button class="btn" onclick="captureImage()">Capture & Save</button>
        </div>
        
        <div class="status" id="status">
            Camera stream active
        </div>
    </div>

    <script>
        let autoRefresh = true;
        let refreshInterval;
        
        function refreshImage() {
            const img = document.getElementById('camera-stream');
            img.src = '/api/camera/capture?' + new Date().getTime();
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const status = document.getElementById('status');
            
            if (autoRefresh) {
                refreshInterval = setInterval(refreshImage, 1000); // Refresh every second
                status.textContent = 'Auto refresh ON (1 sec interval)';
            } else {
                clearInterval(refreshInterval);
                status.textContent = 'Auto refresh OFF';
            }
        }
        
        function captureImage() {
            refreshImage();
            document.getElementById('status').textContent = 'Image captured!';
        }
        
        // Start auto refresh
        refreshInterval = setInterval(refreshImage, 1000);
        
        // Refresh image every second
        setInterval(refreshImage, 1000);
    </script>
</body>
</html>
)rawliteral";
  
  request->send(200, "text/html", html);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Blink LED every second
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState);
    
    // Print status information
    Serial.printf("Uptime: %lu ms | ", currentMillis);
    Serial.printf("Free Heap: %d bytes | ", ESP.getFreeHeap());
    Serial.printf("LED: %s | ", ledState ? "ON" : "OFF");
    
    if (wifiConnected && WiFi.status() == WL_CONNECTED) {
      Serial.printf("WiFi RSSI: %d dBm", WiFi.RSSI());
    } else if (apMode) {
      Serial.printf("AP Mode | Connected clients: %d", WiFi.softAPgetStationNum());
    } else {
      Serial.print("WiFi: Disconnected");
      wifiConnected = false;
    }
    Serial.println();
  }
  
  // Periodic WiFi scan every 30 seconds
  if (currentMillis - previousScanMillis >= scanInterval) {
    previousScanMillis = currentMillis;
    Serial.println("\n=== WiFi Network Scan ===");
    
    int n = WiFi.scanNetworks(false, false, false, 300);
    Serial.printf("Found %d networks:\n", n);
    
    if (n == 0) {
      Serial.println("No WiFi networks found!");
    } else {
      for (int i = 0; i < n; ++i) {
        String encryption;
        switch (WiFi.encryptionType(i)) {
          case WIFI_AUTH_OPEN: encryption = "Open"; break;
          case WIFI_AUTH_WEP: encryption = "WEP"; break;
          case WIFI_AUTH_WPA_PSK: encryption = "WPA"; break;
          case WIFI_AUTH_WPA2_PSK: encryption = "WPA2"; break;
          case WIFI_AUTH_WPA_WPA2_PSK: encryption = "WPA/WPA2"; break;
          case WIFI_AUTH_WPA2_ENTERPRISE: encryption = "WPA2-ENT"; break;
          case WIFI_AUTH_WPA3_PSK: encryption = "WPA3"; break;
          default: encryption = "Unknown"; break;
        }
        
        Serial.printf("%2d: %-20s %3d dBm [%s] Ch:%d\n", 
                      i + 1, 
                      WiFi.SSID(i).c_str(), 
                      WiFi.RSSI(i),
                      encryption.c_str(),
                      WiFi.channel(i));
        
        // Highlight our target SSID
        if (WiFi.SSID(i) == ssid) {
          Serial.printf("    *** TARGET SSID FOUND! Signal: %d dBm ***\n", WiFi.RSSI(i));
        }
      }
    }
    Serial.println("========================\n");
  }
  
  // Check button press (active low)
  static bool lastButtonState = HIGH;
  bool currentButtonState = digitalRead(BUTTON_PIN);
  
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    Serial.println("Button pressed! Performing WiFi scan now...");
    previousScanMillis = 0; // Force immediate scan
    delay(100);
  }
  lastButtonState = currentButtonState;
  
  // Small delay to prevent overwhelming the serial output
  delay(10);
}

// Debug functions implementation
void debugSystemInfo() {
  DEBUG_PRINTLN("=== System Information ===");
  DEBUG_PRINTF("Chip Model: %s\n", ESP.getChipModel());
  DEBUG_PRINTF("Chip Revision: %d\n", ESP.getChipRevision());
  DEBUG_PRINTF("CPU Frequency: %d MHz\n", ESP.getCpuFreqMHz());
  DEBUG_PRINTF("Flash Size: %d bytes\n", ESP.getFlashChipSize());
  DEBUG_PRINTF("Free Heap: %d bytes\n", ESP.getFreeHeap());
  DEBUG_PRINTF("PSRAM Found: %s\n", psramFound() ? "YES" : "NO");
  if (psramFound()) {
    DEBUG_PRINTF("PSRAM Size: %d bytes\n", ESP.getPsramSize());
    DEBUG_PRINTF("Free PSRAM: %d bytes\n", ESP.getFreePsram());
  }
  DEBUG_PRINTLN("==========================");
}

void debugWiFiInfo() {
  DEBUG_PRINTLN("=== WiFi Information ===");
  DEBUG_PRINTF("WiFi MAC Address: %s\n", WiFi.macAddress().c_str());
  DEBUG_PRINTF("WiFi Mode: %d\n", WiFi.getMode());
  DEBUG_PRINTF("WiFi Status: %d\n", WiFi.status());
  DEBUG_PRINTLN("========================");
}

void debugCameraInfo() {
  DEBUG_PRINTLN("=== Camera Information ===");
  DEBUG_PRINTF("Camera Pin Configuration:\n");
  DEBUG_PRINTF("  XCLK: %d, PCLK: %d\n", XCLK_GPIO_NUM, PCLK_GPIO_NUM);
  DEBUG_PRINTF("  VSYNC: %d, HREF: %d\n", VSYNC_GPIO_NUM, HREF_GPIO_NUM);
  DEBUG_PRINTF("  SDA: %d, SCL: %d\n", SIOD_GPIO_NUM, SIOC_GPIO_NUM);
  DEBUG_PRINTF("  Data: %d,%d,%d,%d,%d,%d,%d,%d\n", 
               Y2_GPIO_NUM, Y3_GPIO_NUM, Y4_GPIO_NUM, Y5_GPIO_NUM,
               Y6_GPIO_NUM, Y7_GPIO_NUM, Y8_GPIO_NUM, Y9_GPIO_NUM);
  DEBUG_PRINTLN("==========================");
}