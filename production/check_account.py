#!/usr/bin/env python3

import sys
sys.path.append('src')
from api.alpaca_client import AlpacaClient
from utils.config_manager import ConfigManager

def main():
    config = ConfigManager('config/trading_config.json')
    client = AlpacaClient(config)

    # Check account
    account = client.get_account()
    print(f'Portfolio Value: ${account.portfolio_value:.2f}')
    print(f'Buying Power: ${account.buying_power:.2f}')
    print(f'Cash: ${account.cash:.2f}')

    # Check positions
    positions = client.get_positions()
    print(f'\nActive Positions: {len(positions)}')
    for pos in positions:
        print(f'  {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price:.2f} = ${pos.market_value:.2f}')
        print(f'    P&L: ${pos.unrealized_pl:.2f} ({pos.unrealized_plpc*100:.2f}%)')

if __name__ == "__main__":
    main()