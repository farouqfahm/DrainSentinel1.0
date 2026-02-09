#!/usr/bin/env python3
"""
DrainSentinel: Web Dashboard Module

Provides a real-time web interface for monitoring the drainage system.
Uses Flask for the backend and Socket.IO for live updates.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, Response, send_from_directory

logger = logging.getLogger('DrainSentinel.Dashboard')

# Create Flask app
app = Flask(__name__,
            template_folder='../web/templates',
            static_folder='../web/static')

# Global reference to the DrainSentinel instance
sentinel = None


def start_dashboard(sentinel_instance, host='0.0.0.0', port=5000):
    """
    Start the web dashboard server.
    
    Args:
        sentinel_instance: The DrainSentinel instance to monitor
        host: Host address to bind to
        port: Port to run the server on
    """
    global sentinel
    sentinel = sentinel_instance
    
    logger.info(f"Starting dashboard on http://{host}:{port}")
    
    # Run Flask in production-like mode
    app.run(host=host, port=port, threaded=True, debug=False)


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """Get current system status."""
    if sentinel is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    status = sentinel.get_status()
    return jsonify(status)


@app.route('/api/alerts')
def api_alerts():
    """Get recent alerts."""
    alerts_file = Path('data/logs/alerts.json')
    
    if not alerts_file.exists():
        return jsonify([])
    
    try:
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        return jsonify(alerts[-50:])  # Last 50 alerts
    except Exception as e:
        logger.error(f"Failed to read alerts: {e}")
        return jsonify([])


@app.route('/api/history')
def api_history():
    """Get water level history."""
    if sentinel is None:
        return jsonify([])
    
    # Convert history to list of dicts for JSON
    history = [
        {'timestamp': t, 'level': l}
        for t, l in sentinel.water_history[-100:]  # Last 100 points
    ]
    
    return jsonify(history)


@app.route('/api/image/latest')
def api_latest_image():
    """Get the latest captured image."""
    image_path = Path('data/captures/latest.jpg')
    
    if image_path.exists():
        return send_from_directory(
            image_path.parent.absolute(),
            image_path.name,
            mimetype='image/jpeg'
        )
    
    # Return placeholder if no image
    return '', 204


@app.route('/video_feed')
def video_feed():
    """Stream video from camera (Motion JPEG)."""
    if sentinel is None or sentinel.camera is None:
        return '', 204
    
    def generate():
        while True:
            frame = sentinel.camera.get_stream_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Small delay if no frame
                import time
                time.sleep(0.1)
    
    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# Create the HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DrainSentinel Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1419;
            color: #e7e9ea;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #3b82f6;
        }
        
        .header h1 {
            font-size: 2rem;
            margin-bottom: 5px;
        }
        
        .header .subtitle {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: #1a1f2e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2d3748;
        }
        
        .card h2 {
            font-size: 1rem;
            color: #9ca3af;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-card {
            text-align: center;
        }
        
        .status-indicator {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .status-GREEN { background: linear-gradient(135deg, #059669, #10b981); }
        .status-YELLOW { background: linear-gradient(135deg, #d97706, #fbbf24); }
        .status-ORANGE { background: linear-gradient(135deg, #ea580c, #f97316); }
        .status-RED { background: linear-gradient(135deg, #dc2626, #ef4444); animation: pulse 0.5s infinite; }
        
        .status-label {
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-message {
            color: #9ca3af;
            margin-top: 5px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #2d3748;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #9ca3af;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .metric-value.danger {
            color: #ef4444;
        }
        
        .metric-value.warning {
            color: #fbbf24;
        }
        
        .metric-value.safe {
            color: #10b981;
        }
        
        .camera-feed {
            width: 100%;
            border-radius: 8px;
            background: #0f1419;
        }
        
        .camera-feed img {
            width: 100%;
            border-radius: 8px;
        }
        
        .progress-bar {
            background: #2d3748;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease, background 0.5s ease;
        }
        
        .alerts-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .alert-item {
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        .alert-GREEN { background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; }
        .alert-YELLOW { background: rgba(251, 191, 36, 0.1); border-left: 3px solid #fbbf24; }
        .alert-ORANGE { background: rgba(249, 115, 22, 0.1); border-left: 3px solid #f97316; }
        .alert-RED { background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; }
        
        .alert-time {
            color: #6b7280;
            font-size: 0.8rem;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 0.8rem;
        }
        
        #chart-container {
            height: 200px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌊 DrainSentinel</h1>
        <p class="subtitle">Real-time Drainage Monitoring System</p>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- Status Card -->
            <div class="card status-card">
                <h2>System Status</h2>
                <div class="status-indicator status-GREEN" id="status-indicator">
                    ✓
                </div>
                <div class="status-label" id="status-label">NORMAL</div>
                <div class="status-message" id="status-message">All systems operational</div>
            </div>
            
            <!-- Water Level Card -->
            <div class="card">
                <h2>Water Level</h2>
                <div class="metric">
                    <span class="metric-label">Current Level</span>
                    <span class="metric-value" id="water-level">--</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="water-progress" style="width: 0%; background: #10b981;"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Distance to Sensor</span>
                    <span class="metric-value" id="water-distance">-- cm</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Rate of Rise</span>
                    <span class="metric-value" id="rate-of-rise">-- cm/min</span>
                </div>
            </div>
            
            <!-- Blockage Detection Card -->
            <div class="card">
                <h2>Blockage Detection</h2>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value" id="blockage-status">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Confidence</span>
                    <span class="metric-value" id="blockage-confidence">--%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Analysis</span>
                    <span class="metric-value" id="last-update" style="font-size: 1rem;">--</span>
                </div>
            </div>
            
            <!-- Camera Feed Card -->
            <div class="card">
                <h2>Live Camera Feed</h2>
                <div class="camera-feed">
                    <img src="/api/image/latest" id="camera-image" alt="Drain Camera">
                </div>
            </div>
        </div>
        
        <!-- Alerts Section -->
        <div class="card">
            <h2>Recent Alerts</h2>
            <div class="alerts-list" id="alerts-list">
                <p style="color: #6b7280;">No alerts yet</p>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>DrainSentinel v2.0 | Last updated: <span id="update-time">--</span></p>
    </div>
    
    <script>
        // Update interval in milliseconds
        const UPDATE_INTERVAL = 2000;
        
        // Status messages
        const STATUS_MESSAGES = {
            'GREEN': 'All systems operational',
            'YELLOW': 'Monitor closely - minor issue detected',
            'ORANGE': 'Warning - action may be required',
            'RED': 'CRITICAL - Flood risk high!'
        };
        
        const STATUS_ICONS = {
            'GREEN': '✓',
            'YELLOW': '⚠',
            'ORANGE': '⚠',
            'RED': '!'
        };
        
        // Update status from API
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update status indicator
                const indicator = document.getElementById('status-indicator');
                const label = document.getElementById('status-label');
                const message = document.getElementById('status-message');
                
                indicator.className = 'status-indicator status-' + data.alert_level;
                indicator.textContent = STATUS_ICONS[data.alert_level] || '?';
                label.textContent = data.alert_level;
                message.textContent = STATUS_MESSAGES[data.alert_level] || '';
                
                // Update water level
                const waterLevel = document.getElementById('water-level');
                const waterProgress = document.getElementById('water-progress');
                const waterDistance = document.getElementById('water-distance');
                const rateOfRise = document.getElementById('rate-of-rise');
                
                const level = data.water_level_percent || 0;
                waterLevel.textContent = level.toFixed(1) + '%';
                waterProgress.style.width = level + '%';
                
                // Color based on level
                if (level > 80) {
                    waterLevel.className = 'metric-value danger';
                    waterProgress.style.background = '#ef4444';
                } else if (level > 50) {
                    waterLevel.className = 'metric-value warning';
                    waterProgress.style.background = '#fbbf24';
                } else {
                    waterLevel.className = 'metric-value safe';
                    waterProgress.style.background = '#10b981';
                }
                
                waterDistance.textContent = (data.water_level_cm || 0).toFixed(1) + ' cm';
                rateOfRise.textContent = (data.rate_of_rise || 0).toFixed(1) + ' cm/min';
                
                // Update blockage detection
                const blockageStatus = document.getElementById('blockage-status');
                const blockageConfidence = document.getElementById('blockage-confidence');
                
                if (data.blockage_detected) {
                    blockageStatus.textContent = 'BLOCKED';
                    blockageStatus.className = 'metric-value danger';
                } else {
                    blockageStatus.textContent = 'Clear';
                    blockageStatus.className = 'metric-value safe';
                }
                
                blockageConfidence.textContent = ((data.blockage_confidence || 0) * 100).toFixed(0) + '%';
                
                // Update last update time
                const lastUpdate = document.getElementById('last-update');
                const updateTime = document.getElementById('update-time');
                
                if (data.last_update) {
                    const date = new Date(data.last_update);
                    lastUpdate.textContent = date.toLocaleTimeString();
                    updateTime.textContent = date.toLocaleString();
                }
                
            } catch (error) {
                console.error('Failed to update status:', error);
            }
        }
        
        // Update alerts
        async function updateAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const alerts = await response.json();
                
                const container = document.getElementById('alerts-list');
                
                if (alerts.length === 0) {
                    container.innerHTML = '<p style="color: #6b7280;">No alerts yet</p>';
                    return;
                }
                
                // Show latest alerts first
                const reversed = alerts.slice().reverse().slice(0, 20);
                
                container.innerHTML = reversed.map(alert => `
                    <div class="alert-item alert-${alert.level}">
                        <strong>${alert.level}</strong> - ${alert.message.split('\\n')[0]}
                        <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Failed to update alerts:', error);
            }
        }
        
        // Update camera image
        function updateCamera() {
            const img = document.getElementById('camera-image');
            img.src = '/api/image/latest?' + Date.now();
        }
        
        // Start periodic updates
        setInterval(updateStatus, UPDATE_INTERVAL);
        setInterval(updateAlerts, 5000);
        setInterval(updateCamera, 3000);
        
        // Initial update
        updateStatus();
        updateAlerts();
    </script>
</body>
</html>
'''


def create_template_files():
    """Create the HTML template file."""
    template_dir = Path(__file__).parent.parent / 'web' / 'templates'
    template_dir.mkdir(parents=True, exist_ok=True)
    
    template_file = template_dir / 'dashboard.html'
    
    if not template_file.exists():
        with open(template_file, 'w') as f:
            f.write(DASHBOARD_HTML)
        logger.info(f"Created template: {template_file}")


# Create template on module load
create_template_files()


if __name__ == '__main__':
    # Run standalone for testing
    logging.basicConfig(level=logging.DEBUG)
    
    print("Starting test dashboard...")
    print("Open http://localhost:5000 in your browser")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
