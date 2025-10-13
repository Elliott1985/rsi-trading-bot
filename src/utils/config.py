"""
Configuration Management Module
Handles API keys, trading parameters, and system settings
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    max_position_size_pct: float = 0.10
    max_daily_risk_pct: float = 0.02
    min_risk_reward_ratio: float = 2.0
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    max_trades_per_day: int = 10
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15

@dataclass
class APIConfig:
    """API configuration"""
    alpha_vantage_key: Optional[str] = None
    finnhub_key: Optional[str] = None
    etrade_client_key: Optional[str] = None
    etrade_client_secret: Optional[str] = None
    crypto_com_api_key: Optional[str] = None
    crypto_com_secret: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    twilio_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None

class Config:
    """Main configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.trading = TradingConfig()
        self.api = APIConfig()
        
        # Load configurations
        self._load_env_variables()
        self._load_trading_config()
    
    def _load_env_variables(self):
        """Load environment variables from .env file"""
        env_file = self.config_dir / "api_keys.env"
        
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from api_keys.env")
        else:
            logger.warning(f"No api_keys.env file found at {env_file}")
        
        # Load API keys from environment
        self.api.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.api.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.api.etrade_client_key = os.getenv('ETRADE_CLIENT_KEY')
        self.api.etrade_client_secret = os.getenv('ETRADE_CLIENT_SECRET')
        self.api.crypto_com_api_key = os.getenv('CRYPTO_COM_API_KEY')
        self.api.crypto_com_secret = os.getenv('CRYPTO_COM_SECRET')
        self.api.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.api.twilio_sid = os.getenv('TWILIO_SID')
        self.api.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    def _load_trading_config(self):
        """Load trading configuration from YAML file"""
        config_file = self.config_dir / "trading_config.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Update trading config with values from file
                if config_data:
                    for key, value in config_data.get('trading', {}).items():
                        if hasattr(self.trading, key):
                            setattr(self.trading, key, value)
                            logger.debug(f"Set trading config {key} = {value}")
                
                logger.info("Loaded trading configuration from trading_config.yaml")
                
            except Exception as e:
                logger.error(f"Error loading trading config: {e}")
                logger.info("Using default trading configuration")
        else:
            logger.warning(f"No trading_config.yaml found at {config_file}")
            logger.info("Using default trading configuration")
            # Create default config file
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default trading configuration file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            
            default_config = {
                'trading': {
                    'max_position_size_pct': self.trading.max_position_size_pct,
                    'max_daily_risk_pct': self.trading.max_daily_risk_pct,
                    'min_risk_reward_ratio': self.trading.min_risk_reward_ratio,
                    'rsi_oversold': self.trading.rsi_oversold,
                    'rsi_overbought': self.trading.rsi_overbought,
                    'rsi_period': self.trading.rsi_period,
                    'macd_fast': self.trading.macd_fast,
                    'macd_slow': self.trading.macd_slow,
                    'macd_signal': self.trading.macd_signal,
                    'max_trades_per_day': self.trading.max_trades_per_day,
                    'stop_loss_pct': self.trading.stop_loss_pct,
                    'take_profit_pct': self.trading.take_profit_pct
                },
                'notifications': {
                    'enabled_channels': ['console'],
                    'high_priority_threshold': 0.7,
                    'send_entry_alerts': True,
                    'send_exit_alerts': True,
                    'send_risk_alerts': True
                },
                'market_data': {
                    'default_period': '3mo',
                    'update_frequency': 300,  # seconds
                    'cache_duration': 3600    # seconds
                }
            }
            
            config_file = self.config_dir / "trading_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Created default configuration file at {config_file}")
            
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
    
    def get_stock_symbols(self) -> list[str]:
        """Get list of stock symbols to scan"""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'AMD', 'INTC', 'CRM', 'UBER', 'ABNB', 'ROKU', 'PLTR', 'SNOW',
            'SPY', 'QQQ', 'IWM', 'DIA'  # Add some ETFs
        ]
    
    def get_crypto_symbols(self) -> list[str]:
        """Get list of crypto symbols to scan"""
        return [
            'BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD',
            'AVAX-USD', 'MATIC-USD', 'LINK-USD', 'UNI-USD', 'AAVE-USD',
            'BNB-USD', 'XRP-USD', 'DOGE-USD', 'SHIB-USD'
        ]
    
    def has_required_api_keys(self) -> bool:
        """Check if required API keys are available"""
        # For basic functionality, we only need market data
        # yfinance works without API key, so we can function with minimal setup
        return True  # For now, allow operation without API keys
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        key_mapping = {
            'alpha_vantage': self.api.alpha_vantage_key,
            'finnhub': self.api.finnhub_key,
            'etrade': self.api.etrade_client_key,
            'crypto_com': self.api.crypto_com_api_key,
            'slack': self.api.slack_webhook_url,
            'twilio': self.api.twilio_sid
        }
        
        return key_mapping.get(service.lower())
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        status = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check trading parameters
        if self.trading.max_position_size_pct > 0.5:
            status['warnings'].append("Max position size > 50% may be risky")
        
        if self.trading.max_daily_risk_pct > 0.1:
            status['warnings'].append("Max daily risk > 10% may be too high")
        
        if self.trading.min_risk_reward_ratio < 1.5:
            status['warnings'].append("Risk/reward ratio < 1.5 may not be profitable")
        
        # Check API keys (warnings only, not required for basic operation)
        if not self.api.alpha_vantage_key:
            status['warnings'].append("No Alpha Vantage API key - using yfinance only")
        
        return status
    
    def update_trading_param(self, param: str, value: Any) -> bool:
        """Update a trading parameter"""
        if hasattr(self.trading, param):
            setattr(self.trading, param, value)
            logger.info(f"Updated trading parameter {param} = {value}")
            return True
        else:
            logger.error(f"Unknown trading parameter: {param}")
            return False
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                'trading': {
                    'max_position_size_pct': self.trading.max_position_size_pct,
                    'max_daily_risk_pct': self.trading.max_daily_risk_pct,
                    'min_risk_reward_ratio': self.trading.min_risk_reward_ratio,
                    'rsi_oversold': self.trading.rsi_oversold,
                    'rsi_overbought': self.trading.rsi_overbought,
                    'rsi_period': self.trading.rsi_period,
                    'macd_fast': self.trading.macd_fast,
                    'macd_slow': self.trading.macd_slow,
                    'macd_signal': self.trading.macd_signal,
                    'max_trades_per_day': self.trading.max_trades_per_day,
                    'stop_loss_pct': self.trading.stop_loss_pct,
                    'take_profit_pct': self.trading.take_profit_pct
                }
            }
            
            config_file = self.config_dir / "trading_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved configuration to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False