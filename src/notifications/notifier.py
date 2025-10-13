"""
Notification Management Module
Handles alerts, notifications, and communications for trading events
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    TRADE_SIGNAL = "trade_signal"
    ENTRY_ALERT = "entry_alert"
    EXIT_ALERT = "exit_alert"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    PORTFOLIO_RISK = "portfolio_risk"
    MARKET_NEWS = "market_news"
    ERROR = "error"

@dataclass
class Notification:
    """Notification data structure"""
    type: NotificationType
    title: str
    message: str
    symbol: Optional[str] = None
    price: Optional[float] = None
    timestamp: datetime = datetime.now()
    priority: str = "normal"  # low, normal, high, critical
    metadata: Dict[str, Any] = None

class NotificationManager:
    """Main notification management system"""
    
    def __init__(self):
        self.enabled_channels = ['console']  # Default to console logging
        self.notification_queue = asyncio.Queue()
        self.processing_task = None
        
    async def initialize(self):
        """Initialize the notification manager"""
        logger.info("Initializing Notification Manager...")
        
        # Start notification processing task
        self.processing_task = asyncio.create_task(self._process_notifications())
        logger.info("Notification processing task started")
    
    async def shutdown(self):
        """Shutdown the notification manager"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
    
    async def send_notification(self, notification: Notification):
        """Send a notification through all enabled channels"""
        await self.notification_queue.put(notification)
    
    async def notify_trade_signal(self, symbol: str, signal_type: str, 
                                confidence: float, price: float, strategy: str):
        """Send trade signal notification"""
        notification = Notification(
            type=NotificationType.TRADE_SIGNAL,
            title=f"Trade Signal: {symbol}",
            message=f"{signal_type.upper()} signal for {symbol} at ${price:.2f} "
                   f"(Confidence: {confidence:.1%}) - {strategy}",
            symbol=symbol,
            price=price,
            priority="high" if confidence > 0.7 else "normal",
            metadata={
                'signal_type': signal_type,
                'confidence': confidence,
                'strategy': strategy
            }
        )
        await self.send_notification(notification)
    
    async def notify_entry_alert(self, symbol: str, entry_price: float, 
                               trade_type: str, position_size: float):
        """Send entry alert notification"""
        notification = Notification(
            type=NotificationType.ENTRY_ALERT,
            title=f"Entry Alert: {symbol}",
            message=f"Consider {trade_type} {symbol} at ${entry_price:.2f} "
                   f"(Position: ${position_size:.2f})",
            symbol=symbol,
            price=entry_price,
            priority="high",
            metadata={
                'trade_type': trade_type,
                'position_size': position_size
            }
        )
        await self.send_notification(notification)
    
    async def notify_exit_alert(self, symbol: str, current_price: float, 
                              target_price: float, reason: str):
        """Send exit alert notification"""
        notification = Notification(
            type=NotificationType.EXIT_ALERT,
            title=f"Exit Alert: {symbol}",
            message=f"Consider exiting {symbol} at ${current_price:.2f} "
                   f"(Target: ${target_price:.2f}) - {reason}",
            symbol=symbol,
            price=current_price,
            priority="high",
            metadata={
                'target_price': target_price,
                'reason': reason
            }
        )
        await self.send_notification(notification)
    
    async def notify_stop_loss(self, symbol: str, current_price: float, 
                             stop_price: float, loss_amount: float):
        """Send stop loss notification"""
        notification = Notification(
            type=NotificationType.STOP_LOSS,
            title=f"STOP LOSS: {symbol}",
            message=f"STOP LOSS triggered for {symbol} at ${current_price:.2f} "
                   f"(Stop: ${stop_price:.2f}) - Loss: ${loss_amount:.2f}",
            symbol=symbol,
            price=current_price,
            priority="critical",
            metadata={
                'stop_price': stop_price,
                'loss_amount': loss_amount
            }
        )
        await self.send_notification(notification)
    
    async def notify_take_profit(self, symbol: str, current_price: float, 
                               profit_amount: float):
        """Send take profit notification"""
        notification = Notification(
            type=NotificationType.TAKE_PROFIT,
            title=f"PROFIT TARGET: {symbol}",
            message=f"Profit target reached for {symbol} at ${current_price:.2f} "
                   f"- Profit: ${profit_amount:.2f}",
            symbol=symbol,
            price=current_price,
            priority="high",
            metadata={
                'profit_amount': profit_amount
            }
        )
        await self.send_notification(notification)
    
    async def notify_portfolio_risk(self, risk_percentage: float, 
                                  max_risk: float, message: str):
        """Send portfolio risk notification"""
        priority = "critical" if risk_percentage > 5 else "high" if risk_percentage > 3 else "normal"
        
        notification = Notification(
            type=NotificationType.PORTFOLIO_RISK,
            title="Portfolio Risk Alert",
            message=f"Portfolio risk: {risk_percentage:.2f}% (Max risk: ${max_risk:.2f}) - {message}",
            priority=priority,
            metadata={
                'risk_percentage': risk_percentage,
                'max_risk': max_risk
            }
        )
        await self.send_notification(notification)
    
    async def notify_error(self, error_message: str, context: str = ""):
        """Send error notification"""
        notification = Notification(
            type=NotificationType.ERROR,
            title="Trading Bot Error",
            message=f"Error in {context}: {error_message}",
            priority="high",
            metadata={
                'context': context,
                'error': error_message
            }
        )
        await self.send_notification(notification)
    
    async def _process_notifications(self):
        """Process notifications from the queue"""
        logger.info("Starting notification processing loop")
        
        while True:
            try:
                # Get notification from queue
                notification = await self.notification_queue.get()
                
                # Process through all enabled channels
                await self._send_to_console(notification)
                
                # Future: Add other channels like Slack, email, SMS, etc.
                if 'slack' in self.enabled_channels:
                    await self._send_to_slack(notification)
                
                if 'sms' in self.enabled_channels and notification.priority in ['high', 'critical']:
                    await self._send_sms(notification)
                
                # Mark task as done
                self.notification_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Notification processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
                continue
    
    async def _send_to_console(self, notification: Notification):
        """Send notification to console/logs"""
        timestamp = notification.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format message based on priority
        if notification.priority == "critical":
            log_func = logger.critical
            prefix = "🚨 CRITICAL"
        elif notification.priority == "high":
            log_func = logger.warning
            prefix = "⚠️  HIGH"
        elif notification.priority == "low":
            log_func = logger.debug
            prefix = "💬 INFO"
        else:
            log_func = logger.info
            prefix = "📢 ALERT"
        
        message = f"{prefix} [{timestamp}] {notification.title}: {notification.message}"
        log_func(message)
    
    async def _send_to_slack(self, notification: Notification):
        """Send notification to Slack (placeholder for future implementation)"""
        # TODO: Implement Slack webhook integration
        logger.debug(f"Would send to Slack: {notification.title}")
        pass
    
    async def _send_sms(self, notification: Notification):
        """Send SMS notification (placeholder for future implementation)"""
        # TODO: Implement Twilio SMS integration
        logger.debug(f"Would send SMS: {notification.title}")
        pass
    
    def enable_channel(self, channel: str):
        """Enable a notification channel"""
        if channel not in self.enabled_channels:
            self.enabled_channels.append(channel)
            logger.info(f"Enabled notification channel: {channel}")
    
    def disable_channel(self, channel: str):
        """Disable a notification channel"""
        if channel in self.enabled_channels:
            self.enabled_channels.remove(channel)
            logger.info(f"Disabled notification channel: {channel}")
    
    async def send_market_summary(self, opportunities_count: int, 
                                total_budget: float, suggestions_count: int):
        """Send market summary notification"""
        notification = Notification(
            type=NotificationType.MARKET_NEWS,
            title="Market Scan Complete",
            message=f"Found {opportunities_count} opportunities, generated {suggestions_count} "
                   f"trade suggestions for ${total_budget:.2f} budget",
            priority="normal",
            metadata={
                'opportunities': opportunities_count,
                'suggestions': suggestions_count,
                'budget': total_budget
            }
        )
        await self.send_notification(notification)