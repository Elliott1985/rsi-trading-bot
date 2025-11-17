#!/usr/bin/env python3

import sys
sys.path.append('src')
from utils.config_manager import ConfigManager
from utils.risk_manager import RiskManager
from api.alpaca_client import AlpacaClient

def test_position_size():
    # Initialize components
    config = ConfigManager('config/trading_config.json')
    client = AlpacaClient(config)
    risk_manager = RiskManager(config, client)
    
    # Test with SOLUSD
    symbol = "SOLUSD"
    entry_price = 186.05
    stop_loss_price = 176.75
    account_balance = 1.55  # Current buying power
    confidence = 0.68
    
    print(f"\nTesting position size calculation:")
    print(f"Symbol: {symbol}")
    print(f"Entry Price: ${entry_price}")
    print(f"Stop Loss: ${stop_loss_price}")
    print(f"Account Balance: ${account_balance}")
    print(f"Confidence: {confidence}")
    
    # Calculate position size
    trade_risk = risk_manager.calculate_position_size(
        symbol, entry_price, stop_loss_price, account_balance, confidence
    )
    
    if trade_risk:
        notional_value = trade_risk.position_size * trade_risk.entry_price
        print(f"\nResults:")
        print(f"Position Size: {trade_risk.position_size}")
        print(f"Notional Value: ${notional_value:.2f}")
        print(f"Risk Amount: ${trade_risk.risk_amount:.2f}")
        print(f"Risk/Reward Ratio: {trade_risk.risk_reward_ratio:.2f}")
        
        # Test validation
        is_valid, reason = risk_manager.validate_trade(trade_risk, account_balance)
        print(f"\nValidation:")
        print(f"Valid: {is_valid}")
        print(f"Reason: {reason}")
        
        if notional_value >= 1.0:
            print("✅ Order meets $1 minimum requirement")
        else:
            print("❌ Order below $1 minimum requirement")
    else:
        print("❌ Failed to calculate trade risk")

if __name__ == "__main__":
    test_position_size()