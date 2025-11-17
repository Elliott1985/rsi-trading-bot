#!/usr/bin/env python3
"""
SMS Notification System
Handles trade alerts and notifications via Twilio SMS.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TradeNotification:
    """Trade notification data"""
    symbol: str
    action: str  # BUY, SELL
    price: float
    quantity: float
    stop_loss: float
    take_profit: float
    estimated_roi: float
    reason: str
    timestamp: str

class NotificationManager:
    """Manages SMS and other notifications"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize Twilio if enabled
        self.twilio_client = None
        if self.is_sms_enabled():
            self._init_twilio()
    
    def _init_twilio(self):
        """Initialize Twilio client"""
        try:
            from twilio.rest import Client
            
            credentials = self.config.get_api_credentials()
            sms_config = self.config.config['notifications']['sms']
            
            account_sid = sms_config.get('account_sid') or credentials.get('TWILIO_ACCOUNT_SID', '')
            auth_token = sms_config.get('auth_token') or credentials.get('TWILIO_AUTH_TOKEN', '')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                self.logger.info("✅ Twilio SMS client initialized")
            else:
                self.logger.warning("⚠️ Twilio credentials not found")
                
        except ImportError:
            self.logger.error("❌ Twilio package not installed. Run: pip install twilio")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Twilio: {e}")
    
    def is_sms_enabled(self) -> bool:
        """Check if SMS notifications are enabled"""
        try:
            return self.config.config['notifications']['sms']['enabled']
        except KeyError:
            return False
    
    def send_trade_entry_alert(self, trade_data: Dict):
        """Send SMS alert for trade entry"""
        try:
            if not self.is_sms_enabled() or not self.twilio_client:
                return
            
            symbol = trade_data['symbol']
            action = trade_data['action']
            price = trade_data['price']
            quantity = trade_data['quantity']
            stop_loss = trade_data.get('stop_loss', 0)
            take_profit = trade_data.get('take_profit', 0)
            estimated_roi = trade_data.get('estimated_roi', 0)
            reason = trade_data.get('reason', 'Technical signal')
            
            # Format message
            asset_type = "CRYPTO" if "/" in symbol else "STOCK"
            message = f"""
🚀 TRADE ENTRY ALERT

{asset_type}: {symbol}
Action: {action}
Entry: ${price:.2f}
Quantity: {quantity}
Stop Loss: ${stop_loss:.2f}
Take Profit: ${take_profit:.2f}
Est. ROI: {estimated_roi:.1f}%

Reason: {reason}
Time: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            self._send_sms(message)
            
        except Exception as e:
            self.logger.error(f"Failed to send trade entry alert: {e}")
    
    def send_trade_exit_alert(self, trade_data: Dict):
        """Send SMS alert for trade exit"""
        try:
            if not self.is_sms_enabled() or not self.twilio_client:
                return
            
            symbol = trade_data['symbol']
            action = "SOLD" if trade_data['original_action'] == "BUY" else "COVERED"
            entry_price = trade_data['entry_price']
            exit_price = trade_data['exit_price']
            quantity = trade_data['quantity']
            pnl = trade_data['pnl']
            pnl_percent = trade_data['pnl_percent']
            exit_reason = trade_data.get('exit_reason', 'Manual')
            duration = trade_data.get('duration_minutes', 0)
            
            # Determine profit/loss status
            status = "✅ PROFIT" if pnl > 0 else "❌ LOSS"
            asset_type = "CRYPTO" if "/" in symbol else "STOCK"
            
            message = f"""
{status} TRADE CLOSED

{asset_type}: {symbol}
Action: {action}
Entry: ${entry_price:.2f}
Exit: ${exit_price:.2f}
Quantity: {quantity}

P&L: ${pnl:.2f} ({pnl_percent:.1f}%)
Duration: {duration}m
Reason: {exit_reason}
Time: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            self._send_sms(message)
            
        except Exception as e:
            self.logger.error(f"Failed to send trade exit alert: {e}")
    
    def send_system_alert(self, message: str, alert_type: str = "INFO"):
        """Send system status alert"""
        try:
            if not self.is_sms_enabled() or not self.twilio_client:
                return
            
            emoji = {
                "INFO": "ℹ️",
                "WARNING": "⚠️", 
                "ERROR": "❌",
                "SUCCESS": "✅"
            }.get(alert_type, "📢")
            
            formatted_message = f"""
{emoji} SYSTEM ALERT

{message}

Time: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            self._send_sms(formatted_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send system alert: {e}")
    
    def _send_sms(self, message: str):
        """Send SMS via Twilio"""
        try:
            sms_config = self.config.config['notifications']['sms']
            from_phone = sms_config.get('from_phone', '')
            to_phone = sms_config.get('to_phone', '')
            
            if not from_phone or not to_phone:
                self.logger.error("❌ SMS phone numbers not configured")
                return
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=from_phone,
                to=to_phone
            )
            
            self.logger.info(f"📱 SMS sent successfully: {message_obj.sid}")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS: {e}")
    
    def test_sms(self):
        """Test SMS functionality"""
        try:
            if not self.is_sms_enabled():
                return False, "SMS notifications are disabled"
            
            if not self.twilio_client:
                return False, "Twilio client not initialized"
            
            test_message = f"""
🤖 TEST MESSAGE

Your trading bot SMS alerts are working!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            self._send_sms(test_message)
            return True, "Test SMS sent successfully"
            
        except Exception as e:
            return False, f"Test SMS failed: {e}"