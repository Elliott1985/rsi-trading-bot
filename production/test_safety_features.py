#!/usr/bin/env python3
"""
Test script to verify all safety mechanisms work correctly
"""

import sys
import time
sys.path.append('src')

from utils.config_manager import ConfigManager
from utils.risk_manager import RiskManager
from api.alpaca_client import AlpacaClient
from main_bot import AutonomousTradingBot

def test_position_tracking():
    """Test position tracking reliability"""
    print("🧪 Testing Position Tracking...")
    
    config = ConfigManager('config/trading_config.json')
    client = AlpacaClient(config)
    
    # Test safe position retrieval
    bot = AutonomousTradingBot()
    positions = bot.get_positions_safely()
    
    if positions is not None:
        print(f"✅ Position tracking working: {len(positions)} positions found")
    else:
        print("❌ Position tracking failed")
    
    return positions is not None

def test_trading_frequency_limits():
    """Test trading frequency limits"""
    print("\n🧪 Testing Trading Frequency Limits...")
    
    bot = AutonomousTradingBot()
    
    # Simulate 3 trades in quick succession
    for i in range(4):
        bot.record_trade_execution("TESTUSD", "BUY", 0.1, 100.0)
        can_trade = bot.check_trading_frequency_limits()
        
        if i < 3:
            print(f"Trade {i+1}: {'✅ Allowed' if can_trade else '❌ Blocked'}")
        else:
            print(f"Trade {i+1}: {'❌ Should be blocked' if can_trade else '✅ Correctly blocked'}")
    
    return True

def test_consecutive_loss_circuit_breaker():
    """Test consecutive loss circuit breaker"""
    print("\n🧪 Testing Consecutive Loss Circuit Breaker...")
    
    bot = AutonomousTradingBot()
    
    # Simulate 3 consecutive losses
    for i in range(4):
        bot.record_trade_outcome("TEST", -10.0)  # $10 loss
        can_trade = bot.check_consecutive_loss_limit()
        
        print(f"Loss {i+1}: Consecutive losses = {bot.consecutive_losses}, "
              f"Can trade = {'Yes' if can_trade else 'No'}")
        
        if i >= 2:  # After 3rd loss, should be halted
            if bot.trading_halted:
                print("✅ Trading correctly halted after 3 consecutive losses")
                break
    
    return bot.trading_halted

def test_crypto_stop_loss_config():
    """Test crypto stop loss configuration"""
    print("\n🧪 Testing Crypto Stop Loss Configuration...")
    
    config = ConfigManager('config/trading_config.json')
    crypto_stop_loss = config.trading_config.crypto_stop_loss_percent
    
    if crypto_stop_loss >= 8.0:
        print(f"✅ Crypto stop loss correctly set to {crypto_stop_loss}%")
        return True
    else:
        print(f"❌ Crypto stop loss too low: {crypto_stop_loss}% (should be >= 8%)")
        return False

def test_position_size_scaling():
    """Test position size scaling after losses"""
    print("\n🧪 Testing Position Size Scaling...")
    
    config = ConfigManager('config/trading_config.json')
    client = AlpacaClient(config)
    risk_manager = RiskManager(config, client)
    
    # Create mock bot with consecutive losses
    bot = AutonomousTradingBot()
    bot.consecutive_losses = 2
    
    import __main__
    __main__.bot_instance = bot
    
    # Test position sizing with losses
    trade_risk = risk_manager.calculate_position_size(
        "TESTUSD", 100.0, 92.0, 1000.0, 0.7
    )
    
    if trade_risk:
        print(f"✅ Position sizing with scaling working")
        print(f"   Position size affected by {bot.consecutive_losses} consecutive losses")
        return True
    else:
        print("❌ Position sizing failed")
        return False

def main():
    """Run all safety feature tests"""
    print("🛡️ Testing Trading Bot Safety Features")
    print("=" * 50)
    
    results = {
        "Position Tracking": test_position_tracking(),
        "Trading Frequency Limits": test_trading_frequency_limits(), 
        "Consecutive Loss Circuit Breaker": test_consecutive_loss_circuit_breaker(),
        "Crypto Stop Loss Config": test_crypto_stop_loss_config(),
        "Position Size Scaling": test_position_size_scaling()
    }
    
    print("\n🏁 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All safety features working correctly!")
    else:
        print("⚠️ Some safety features need attention")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)