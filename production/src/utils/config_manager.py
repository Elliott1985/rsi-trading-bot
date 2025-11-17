#!/usr/bin/env python3
"""
Configuration Management System
Handles loading, validation, and updates of trading bot configuration.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class TradingConfig:
    """Trading configuration data class"""
    capital_use_percentage: float
    max_position_size: float
    min_trade_amount: float
    stop_loss_percent: float
    take_profit_percent: float
    trailing_stop_percent: float
    max_daily_loss: float
    max_positions: int
    crypto_stop_loss_percent: float
    crypto_take_profit_percent: float
    crypto_trailing_stop_percent: float
    rsi_oversold: int
    rsi_overbought: int
    volume_threshold: float
    momentum_lookback: int
    min_price: float
    max_price: float
    sentiment_weight: float
    sentiment_skip_threshold: float
    sentiment_bias_threshold: float
    min_confidence: float
    scan_universe: list
    
class ConfigManager:
    """Manages trading bot configuration"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to production config
            self.config_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'config', 'trading_config.json'
            )
        else:
            self.config_path = config_path
        
        self.config = {}
        self.trading_config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Extract trading parameters into dataclass
            trading = self.config['trading']
            capital = trading['capital_allocation']
            risk = trading['risk_management']
            strategy = trading['strategy']
            sentiment = trading['sentiment']
            market = self.config['market']
            
            self.trading_config = TradingConfig(
                capital_use_percentage=capital['use_percentage'],
                max_position_size=capital['max_position_size'],
                min_trade_amount=capital['min_trade_amount'],
                stop_loss_percent=risk['stop_loss_percent'],
                take_profit_percent=risk['take_profit_percent'],
                trailing_stop_percent=risk['trailing_stop_percent'],
                max_daily_loss=risk['max_daily_loss'],
                max_positions=risk['max_positions'],
                crypto_stop_loss_percent=risk.get('crypto_stop_loss_percent', risk['stop_loss_percent']),
                crypto_take_profit_percent=risk.get('crypto_take_profit_percent', risk['take_profit_percent']),
                crypto_trailing_stop_percent=risk.get('crypto_trailing_stop_percent', risk['trailing_stop_percent']),
                rsi_oversold=strategy['rsi_oversold'],
                rsi_overbought=strategy['rsi_overbought'],
                volume_threshold=strategy['volume_threshold'],
                momentum_lookback=strategy['momentum_lookback'],
                min_price=strategy['min_price'],
                max_price=strategy['max_price'],
                sentiment_weight=sentiment['weight'],
                sentiment_skip_threshold=sentiment['skip_threshold'],
                sentiment_bias_threshold=sentiment['bias_threshold'],
                min_confidence=strategy.get('min_confidence', 0.6),
                scan_universe=market['scan_universe']
            )
            
            logging.info(f"Configuration loaded from {self.config_path}")
            return self.config
            
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            raise
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False
    
    def update_trading_param(self, section: str, param: str, value: Any) -> bool:
        """Update a specific trading parameter"""
        try:
            if section in self.config['trading']:
                self.config['trading'][section][param] = value
                self.load_config()  # Reload to update dataclass
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to update parameter {section}.{param}: {e}")
            return False
    
    def get_api_credentials(self) -> Dict[str, str]:
        """Get API credentials from environment variables"""
        credentials = {}
        
        # Try to load from the archived api_keys.env file
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'api_keys.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('ALPACA_') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key] = value
        
        # Override with environment variables if set
        credentials.update({
            'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY', credentials.get('ALPACA_LIVE_KEY_ID', '')),
            'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY', credentials.get('ALPACA_LIVE_SECRET_KEY', '')),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', credentials.get('NEWSAPI_KEY', '')),
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', credentials.get('FINNHUB_API_KEY', ''))
        })
        
        return credentials
    
    def validate_config(self) -> bool:
        """Validate configuration parameters"""
        try:
            # Check required sections
            required_sections = ['trading', 'market', 'apis', 'logging']
            for section in required_sections:
                if section not in self.config:
                    logging.error(f"Missing required config section: {section}")
                    return False
            
            # Validate trading parameters
            tc = self.trading_config
            if not (0 < tc.capital_use_percentage <= 100):
                logging.error("Capital use percentage must be between 0 and 100")
                return False
            
            if not (0 < tc.max_position_size <= 1):
                logging.error("Max position size must be between 0 and 1")
                return False
            
            if tc.stop_loss_percent <= 0 or tc.take_profit_percent <= 0:
                logging.error("Stop loss and take profit must be positive")
                return False
            
            # Check API credentials
            creds = self.get_api_credentials()
            if not creds.get('ALPACA_API_KEY') or not creds.get('ALPACA_SECRET_KEY'):
                logging.error("Missing Alpaca API credentials")
                return False
            
            logging.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            return False
    
    def get_log_paths(self) -> Dict[str, str]:
        """Get absolute paths for log files"""
        base_path = os.path.dirname(self.config_path)
        log_config = self.config['logging']
        
        return {
            'trade_log': os.path.join(base_path, '..', log_config['trade_log_file']),
            'performance_log': os.path.join(base_path, '..', log_config['performance_log_file']),
            'debug_log': os.path.join(base_path, '..', log_config['debug_log_file'])
        }

# Global config instance
_config_manager = None

def get_config() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def reload_config():
    """Reload configuration from file"""
    global _config_manager
    if _config_manager:
        _config_manager.load_config()