#!/usr/bin/env python3

import sys
sys.path.append('src')
from api.alpaca_client import AlpacaClient
from utils.config_manager import ConfigManager

def close_solusd_position():
    config = ConfigManager('config/trading_config.json')
    client = AlpacaClient(config)
    
    print("Current positions:")
    positions = client.get_positions()
    for pos in positions:
        print(f"  {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price:.2f} = ${pos.market_value:.2f}")
        print(f"    P&L: ${pos.unrealized_pl:.2f} ({pos.unrealized_plpc*100:.2f}%)")
    
    if not positions:
        print("No positions to close.")
        return
    
    # Find SOLUSD position
    solusd_pos = None
    for pos in positions:
        if pos.symbol == "SOLUSD":
            solusd_pos = pos
            break
    
    if not solusd_pos:
        print("SOLUSD position not found.")
        return
    
    print(f"\nAttempting to close SOLUSD position...")
    print(f"Quantity to close: {solusd_pos.qty}")
    
    # Close the position
    result = client.close_position("SOLUSD")
    
    if result:
        print(f"✅ Successfully closed SOLUSD position. Order ID: {result}")
        
        # Wait a moment and check positions again
        import time
        time.sleep(2)
        
        print("\nUpdated positions:")
        new_positions = client.get_positions()
        for pos in new_positions:
            print(f"  {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price:.2f} = ${pos.market_value:.2f}")
    else:
        print("❌ Failed to close SOLUSD position.")

if __name__ == "__main__":
    close_solusd_position()