#!/usr/bin/env python3
"""
DrainSentinel: Alert System Module

Handles sending alerts via multiple channels:
- Console logging
- File logging
- SMS (via Twilio)
- Email
- WhatsApp (via Twilio)
- Push notifications

Alerts are rate-limited to prevent spam.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger('DrainSentinel.Alerts')


class AlertSystem:
    """Multi-channel alert system with rate limiting."""
    
    # Alert messages by level
    MESSAGES = {
        'GREEN': 'Drainage system operating normally.',
        'YELLOW': 'Monitor closely: Slight blockage or elevated water detected.',
        'ORANGE': 'WARNING: Significant blockage or high water level. Take action.',
        'RED': 'CRITICAL: Flood imminent! Evacuate low-lying areas immediately.',
    }
    
    def __init__(self, config=None, test_mode=False):
        """
        Initialize the alert system.
        
        Args:
            config: Configuration dictionary (optional)
            test_mode: If True, don't actually send external alerts
        """
        self.test_mode = test_mode
        
        # Default configuration
        self.config = {
            'enabled_channels': ['console', 'file'],
            'rate_limit_minutes': {
                'GREEN': 60,   # Only log green every hour
                'YELLOW': 15,  # Yellow every 15 mins max
                'ORANGE': 5,   # Orange every 5 mins max
                'RED': 1,      # Red every minute max
            },
            'sms': {
                'enabled': False,
                'twilio_sid': os.environ.get('TWILIO_SID', ''),
                'twilio_token': os.environ.get('TWILIO_TOKEN', ''),
                'from_number': os.environ.get('TWILIO_FROM', ''),
                'to_numbers': [],
            },
            'email': {
                'enabled': False,
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': '',
                'to_emails': [],
            },
            'webhook': {
                'enabled': False,
                'url': '',
            },
        }
        
        if config:
            self.config.update(config)
        
        # Track last alert times for rate limiting
        self.last_alerts = {}
        
        # Alert log file
        self.log_file = Path('data/logs/alerts.json')
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("AlertSystem initialized")
    
    def send_alert(self, level, state):
        """
        Send an alert based on the current state.
        
        Args:
            level: Alert level ('GREEN', 'YELLOW', 'ORANGE', 'RED')
            state: Current system state dictionary
        """
        # Check rate limiting
        if not self._should_send(level):
            logger.debug(f"Alert rate limited: {level}")
            return
        
        # Build alert message
        message = self._build_message(level, state)
        
        # Send to all enabled channels
        self._send_console(level, message)
        self._log_to_file(level, message, state)
        
        if not self.test_mode:
            if 'sms' in self.config['enabled_channels']:
                self._send_sms(level, message)
            
            if 'email' in self.config['enabled_channels']:
                self._send_email(level, message)
            
            if 'webhook' in self.config['enabled_channels']:
                self._send_webhook(level, message, state)
        
        # Update last alert time
        self.last_alerts[level] = datetime.now()
    
    def _should_send(self, level):
        """Check if we should send an alert (rate limiting)."""
        if level not in self.last_alerts:
            return True
        
        last_time = self.last_alerts[level]
        limit_minutes = self.config['rate_limit_minutes'].get(level, 5)
        
        if datetime.now() - last_time > timedelta(minutes=limit_minutes):
            return True
        
        return False
    
    def _build_message(self, level, state):
        """Build the alert message."""
        base_message = self.MESSAGES.get(level, 'Unknown alert level')
        
        details = (
            f"\n"
            f"Water Level: {state.get('water_level_percent', 0):.1f}%\n"
            f"Blockage: {'Yes' if state.get('blockage_detected') else 'No'} "
            f"({state.get('blockage_confidence', 0)*100:.0f}% confidence)\n"
            f"Rate of Rise: {state.get('rate_of_rise', 0):.1f} cm/min\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return f"[DrainSentinel {level}] {base_message}{details}"
    
    def _send_console(self, level, message):
        """Send alert to console."""
        # Use appropriate log level
        if level == 'RED':
            logger.critical(message)
        elif level == 'ORANGE':
            logger.warning(message)
        elif level == 'YELLOW':
            logger.info(message)
        else:
            logger.debug(message)
    
    def _log_to_file(self, level, message, state):
        """Log alert to JSON file."""
        try:
            # Load existing alerts
            alerts = []
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    try:
                        alerts = json.load(f)
                    except json.JSONDecodeError:
                        alerts = []
            
            # Add new alert
            alerts.append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'state': state,
            })
            
            # Keep only last 1000 alerts
            alerts = alerts[-1000:]
            
            # Save
            with open(self.log_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
    
    def _send_sms(self, level, message):
        """Send SMS via Twilio."""
        if not self.config['sms']['enabled']:
            return
        
        try:
            from twilio.rest import Client
            
            client = Client(
                self.config['sms']['twilio_sid'],
                self.config['sms']['twilio_token']
            )
            
            for to_number in self.config['sms']['to_numbers']:
                client.messages.create(
                    body=message[:1600],  # SMS limit
                    from_=self.config['sms']['from_number'],
                    to=to_number
                )
                logger.info(f"SMS sent to {to_number}")
                
        except ImportError:
            logger.warning("Twilio library not installed: pip install twilio")
        except Exception as e:
            logger.error(f"SMS failed: {e}")
    
    def _send_email(self, level, message):
        """Send email alert."""
        if not self.config['email']['enabled']:
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['Subject'] = f"[DrainSentinel {level}] Drainage Alert"
            msg['From'] = self.config['email']['from_email']
            msg['To'] = ', '.join(self.config['email']['to_emails'])
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(
                self.config['email']['smtp_host'],
                self.config['email']['smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.config['email']['username'],
                    self.config['email']['password']
                )
                server.send_message(msg)
            
            logger.info("Email sent")
            
        except Exception as e:
            logger.error(f"Email failed: {e}")
    
    def _send_webhook(self, level, message, state):
        """Send webhook notification."""
        if not self.config['webhook']['enabled']:
            return
        
        try:
            import requests
            
            payload = {
                'level': level,
                'message': message,
                'state': state,
                'timestamp': datetime.now().isoformat(),
            }
            
            response = requests.post(
                self.config['webhook']['url'],
                json=payload,
                timeout=10
            )
            
            if response.ok:
                logger.info(f"Webhook sent: {response.status_code}")
            else:
                logger.warning(f"Webhook failed: {response.status_code}")
                
        except ImportError:
            logger.warning("Requests library not installed: pip install requests")
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
    
    def get_recent_alerts(self, limit=50):
        """Get recent alerts from the log file."""
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            return alerts[-limit:]
            
        except Exception as e:
            logger.error(f"Failed to read alerts: {e}")
            return []
    
    def clear_alerts(self):
        """Clear the alerts log."""
        try:
            if self.log_file.exists():
                self.log_file.unlink()
            logger.info("Alerts cleared")
        except Exception as e:
            logger.error(f"Failed to clear alerts: {e}")


def test_alerts():
    """Test the alert system."""
    print("Testing alert system...")
    
    alerts = AlertSystem(test_mode=True)
    
    # Test each alert level
    test_state = {
        'water_level_percent': 75,
        'blockage_detected': True,
        'blockage_confidence': 0.85,
        'rate_of_rise': 2.5,
    }
    
    for level in ['GREEN', 'YELLOW', 'ORANGE', 'RED']:
        print(f"\n--- Testing {level} alert ---")
        alerts.send_alert(level, test_state)
    
    # Show recent alerts
    print("\n--- Recent Alerts ---")
    for alert in alerts.get_recent_alerts(5):
        print(f"{alert['timestamp']}: [{alert['level']}]")
    
    print("\nTest complete")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_alerts()
