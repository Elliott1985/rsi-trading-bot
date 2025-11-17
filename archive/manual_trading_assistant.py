#!/usr/bin/env python3
"""
MANUAL TRADING ASSISTANT
Smart bot gives you trade signals to execute manually
Perfect for testing the bot's performance before going automated
"""

import asyncio
import sys
import time
import json
from datetime import datetime
import os

sys.path.append('src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('api_keys.env')

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ManualTradingAssistant:
    """Smart trading assistant that gives manual trade signals"""
    
    def __init__(self, balance=50.00):
        self.account_balance = balance
        self.buying_power = balance
        self.current_positions = {}
        
        # Trading parameters optimized for $50 options account
        self.max_positions = 1  # Only 1 position with $50 budget
        self.max_position_pct = 0.80  # Use 80% of budget per trade
        self.max_daily_trades = 2
        self.daily_trade_count = 0
        
        # Stock filtering - focus on stocks with cheap options
        self.min_stock_price = 5.00   # Minimum $5 for liquid options
        self.max_stock_price = 200.00  # Higher max since we're buying options, not shares
        
        # Dynamic stock universe
        self.stock_universe = []
        
        # Risk management
        self.stop_loss_pct = 0.05   # 5% stop loss
        self.take_profit_pct = 0.12  # 12% take profit
        
        # Manual tracking
        self.manual_orders = []
        self.orders_file = "manual_trading_log.json"
        self.load_manual_orders()
        
        print("🎯 MANUAL OPTIONS TRADING ASSISTANT (\$50 BUDGET)")
        print(f"💰 Account Balance: ${self.account_balance:,.2f}")
        print(f"📊 Max Positions: {self.max_positions} (focused approach)")
        print(f"💸 Max Per Trade: ${self.buying_power * self.max_position_pct:,.2f} (80% of budget)")
        print("📞 Bot will find CHEAP options plays for small budget")
        print("⚡ Optimized for high-leverage, low-cost options")
        print()

    def load_manual_orders(self):
        """Load manual order history"""
        try:
            with open(self.orders_file, 'r') as f:
                self.manual_orders = json.load(f)
        except FileNotFoundError:
            self.manual_orders = []
    
    def save_manual_orders(self):
        """Save manual orders"""
        try:
            with open(self.orders_file, 'w') as f:
                json.dump(self.manual_orders, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save orders error: {e}")

    async def get_current_price(self, symbol):
        """Get current stock price using Finnhub"""
        try:
            import finnhub
            
            # Use working API key
            finnhub_key = 'd3neu6pr01qo7510pnpgd3neu6pr01qo7510pnq0'
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            quote = finnhub_client.quote(symbol)
            
            if quote and 'c' in quote and quote['c'] > 0:
                current_price = float(quote['c'])
                print(f"      📊 {symbol}: ${current_price:.2f} (Finnhub)")
                return current_price
            else:
                print(f"      ⚠️  No price data for {symbol}")
                return None
                
        except Exception as e:
            print(f"      ❌ Price fetch error for {symbol}: {e}")
            return None

    async def get_price_momentum(self, symbol):
        """Get price momentum"""
        try:
            import finnhub
            
            finnhub_key = 'd3neu6pr01qo7510pnpgd3neu6pr01qo7510pnq0'
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            quote = finnhub_client.quote(symbol)
            
            if quote and 'c' in quote and 'pc' in quote:
                current_price = float(quote['c'])
                previous_close = float(quote['pc'])
                
                momentum = (current_price - previous_close) / previous_close * 100
                
                return {
                    'current_price': current_price,
                    'momentum': momentum,
                    'previous_close': previous_close
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Momentum error for {symbol}: {e}")
            return None

    async def build_stock_universe(self):
        """Build universe of affordable stocks"""
        print("🔍 Building stock universe...")
        
        # Expanded list of liquid stocks for options trading
        candidates = [
            # Large Cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'AMD', 'INTC', 'ORCL', 'CRM',
            # Finance
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'USB', 'PNC', 'TFC', 'COF', 'AXP', 'V', 'MA',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'MRK', 'ABBV', 'TMO', 'ABT', 'LLY', 'BMY', 'AMGN',
            # Consumer
            'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'COST', 'KO', 'PEP', 'PG',
            # Energy/Industrials  
            'XOM', 'CVX', 'SLB', 'HAL', 'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'FDX',
            # Telecom/Utilities
            'T', 'VZ', 'CMCSA', 'DIS', 'NFLX', 'SO', 'NEE', 'DUK',
            # ETFs (very liquid for options)
            'SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'XLK', 'GLD', 'SLV',
            # Meme/Popular stocks
            'GME', 'AMC', 'PLTR', 'HOOD', 'RIVN', 'LCID', 'SOFI', 'BB', 'NOK'
        ]
        
        print(f"  Testing {len(candidates)} stocks for affordability...")
        
        affordable_stocks = []
        for symbol in candidates[:20]:  # Test first 20 stocks for more options
            price = await self.get_current_price(symbol)
            if price and self.min_stock_price <= price <= self.max_stock_price:
                affordable_stocks.append(symbol)
                print(f"    ✅ {symbol}: ${price:.2f} - ADDED")
            elif price:
                print(f"    ❌ {symbol}: ${price:.2f} - Out of range")
        
        self.stock_universe = affordable_stocks
        print(f"\n✅ Stock universe: {len(self.stock_universe)} symbols")
        print(f"   Symbols: {', '.join(self.stock_universe)}")

    async def scan_for_signals(self):
        """Scan for trade signals"""
        print("\n🔍 SCANNING FOR TRADE SIGNALS...")
        
        signals = []
        
        for symbol in self.stock_universe:
            print(f"  🧠 Analyzing {symbol}...")
            
            momentum_data = await self.get_price_momentum(symbol)
            if not momentum_data:
                continue
            
            current_price = momentum_data['current_price']
            momentum = momentum_data['momentum']
            
            print(f"     💰 Current: ${current_price:.2f} | Momentum: {momentum:+.2f}%")
            
            # Trading criteria
            buy_signal = False
            confidence = 0
            
            # Strong momentum signals
            if abs(momentum) > 2.0:  # Strong move
                if momentum > 0:  # Upward momentum
                    buy_signal = True
                    confidence = min(95, 80 + abs(momentum) * 3)
                elif momentum < -3.0:  # Strong dip - contrarian play
                    buy_signal = True  
                    confidence = min(95, 70 + abs(momentum) * 2)
            
            # Moderate signals
            elif 1.0 < abs(momentum) < 2.0:
                if momentum > 0:
                    buy_signal = True
                    confidence = 70 + abs(momentum) * 5
            
            if buy_signal and confidence > 75:
                # Determine options strategy based on momentum
                option_type, strike_price, expiration = self.calculate_options_strategy(current_price, momentum)
                
                # Calculate position size for $50 budget (options contracts)
                max_investment = self.buying_power * self.max_position_pct
                estimated_option_price = self.estimate_option_price(current_price, strike_price, option_type)
                
                # Skip if option is too expensive for budget
                cost_per_contract = estimated_option_price * 100  # Each contract = 100 shares
                if cost_per_contract > max_investment:
                    print(f"     ❌ {symbol}: Option too expensive (${estimated_option_price:.2f}/contract = ${cost_per_contract:.0f})")
                    continue
                    
                contracts = max(1, int(max_investment / cost_per_contract))
                cost = contracts * cost_per_contract
                
                # Only include if affordable and worthwhile
                if cost <= max_investment and cost >= 10:  # Minimum $10 position
                    signal = {
                        'symbol': symbol,
                        'action': 'BUY',
                        'option_type': option_type,
                        'strike_price': strike_price,
                        'expiration': expiration,
                        'stock_price': current_price,
                        'estimated_option_price': estimated_option_price,
                        'contracts': contracts,
                        'cost': cost,
                        'momentum': momentum,
                        'confidence': confidence,
                        'stop_loss_pct': 50,  # 50% loss on options
                        'take_profit_pct': 100,  # 100% gain target
                        'timestamp': datetime.now()
                    }
                    signals.append(signal)
                    
                    print(f"     ✅ {symbol}: OPTIONS SIGNAL! {option_type} ${strike_price} | Est. ${estimated_option_price:.2f} | {contracts} contracts")
        
        return signals

    def calculate_options_strategy(self, stock_price, momentum):
        """Calculate options strategy optimized for $50 budget"""
        from datetime import datetime, timedelta
        
        # Shorter expirations for $50 budget (cheaper options)
        if abs(momentum) > 3.0:  # Strong momentum - very short expiration
            days_to_expiry = 3  # 3 days for max leverage
        elif abs(momentum) > 2.0:  # Moderate momentum 
            days_to_expiry = 7  # 1 week
        else:
            days_to_expiry = 14  # 2 weeks max
            
        expiration_date = datetime.now() + timedelta(days=days_to_expiry)
        expiration = expiration_date.strftime('%m/%d/%Y')
        
        # Determine option type and strike for $50 budget
        if momentum > 0:  # Bullish momentum - CALL options
            option_type = "CALL"
            # Strike price more out of the money for cheaper options
            strike_price = round(stock_price * 1.03, 2)  # 3% OTM for cheaper premium
        else:  # Bearish momentum - PUT options  
            option_type = "PUT"
            # Strike price more out of the money for cheaper options
            strike_price = round(stock_price * 0.97, 2)  # 3% OTM for cheaper premium
            
        return option_type, strike_price, expiration
    
    def estimate_option_price(self, stock_price, strike_price, option_type):
        """Budget-optimized option pricing for micro-budgets ($50)"""
        
        # Calculate intrinsic value
        intrinsic_value = 0
        if option_type == "CALL" and stock_price > strike_price:
            intrinsic_value = stock_price - strike_price
        elif option_type == "PUT" and stock_price < strike_price:
            intrinsic_value = strike_price - stock_price
        
        # For micro-budgets, focus on very cheap options with aggressive time value estimates
        # This targets options that brokers often offer for $0.05-$1.00
        
        # Base time value on stock price with budget-friendly multipliers
        if stock_price < 5:  # Very cheap stocks
            time_value = stock_price * 0.02  # 2% time value
        elif stock_price < 10:
            time_value = stock_price * 0.015  # 1.5% time value  
        elif stock_price < 20:
            time_value = stock_price * 0.01   # 1% time value
        elif stock_price < 50:
            time_value = stock_price * 0.008  # 0.8% time value
        else:
            time_value = stock_price * 0.005  # 0.5% time value
        
        # Reduce time value for out-of-the-money options (they're cheaper)
        if option_type == "CALL" and stock_price < strike_price:
            time_value *= 0.6  # 40% discount for OTM calls
        elif option_type == "PUT" and stock_price > strike_price:
            time_value *= 0.6  # 40% discount for OTM puts
            
        # Total option price
        estimated_price = max(0.05, intrinsic_value + time_value)  # Minimum $0.05
        
        # Aggressive caps for micro-budget compatibility
        if stock_price < 5:
            estimated_price = min(estimated_price, 0.25)   # Max $0.25 for very cheap stocks
        elif stock_price < 10:
            estimated_price = min(estimated_price, 0.50)   # Max $0.50 for cheap stocks
        elif stock_price < 20:
            estimated_price = min(estimated_price, 1.00)   # Max $1.00 for low-price stocks
        elif stock_price < 50:
            estimated_price = min(estimated_price, 2.00)   # Max $2.00 for mid-price stocks
        else:
            estimated_price = min(estimated_price, 4.00)   # Max $4.00 for expensive stocks
        
        return round(estimated_price, 2)

    def display_signals_dashboard(self, signals):
        """Display multiple signals in a clean dashboard format"""
        if not signals:
            return
            
        print("\n" + "="*100)
        print("🎯 OPTIONS TRADING DASHBOARD")
        print("="*100)
        
        # Sort by confidence
        sorted_signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)
        
        print(f"{'#':<2} {'SYMBOL':<6} {'TYPE':<4} {'STRIKE':<8} {'EXP':<10} {'MOMENTUM':<10} {'CONF%':<6} {'CONTRACTS':<9} {'COST':<8}")
        print("-"*100)
        
        for i, signal in enumerate(sorted_signals[:5], 1):  # Show top 5
            momentum_str = f"{signal['momentum']:+.1f}%"
            conf_str = f"{signal['confidence']:.0f}%"
            cost_str = f"${signal['cost']:.0f}"
            
            print(f"{i:<2} {signal['symbol']:<6} {signal['option_type']:<4} ${signal['strike_price']:<7.2f} {signal['expiration']:<10} {momentum_str:<10} {conf_str:<6} {signal['contracts']:<9} {cost_str:<8}")
        
        print("="*100)
        
        if len(sorted_signals) > 5:
            print(f"📊 Showing top 5 of {len(sorted_signals)} total signals")
            
        return sorted_signals

    def display_trade_signal(self, signal):
        """Display options trade signal for manual execution"""
        print("\n" + "="*80)
        print("🚨 MANUAL OPTIONS TRADE SIGNAL")
        print("="*80)
        print(f"📊 UNDERLYING: {signal['symbol']}")
        print(f"💰 STOCK PRICE: ${signal['stock_price']:.2f}")
        print(f"🚀 MOMENTUM: {signal['momentum']:+.2f}%")
        print(f"🎯 CONFIDENCE: {signal['confidence']:.1f}%")
        print()
        print("📞 OPTIONS DETAILS:")
        print(f"   🎯 OPTION TYPE: {signal['option_type']}")
        print(f"   💎 STRIKE PRICE: ${signal['strike_price']:.2f}")
        print(f"   📅 EXPIRATION: {signal['expiration']}")
        print(f"   💰 EST. OPTION PRICE: ${signal['estimated_option_price']:.2f}")
        print(f"   📈 CONTRACTS: {signal['contracts']} contracts")
        print(f"   💸 TOTAL COST: ${signal['cost']:.2f}")
        print()
        print("🎯 MANUAL EXECUTION:")
        print(f"   1. Open your options trading app")
        print(f"   2. Search for {signal['symbol']} options")
        print(f"   3. Find {signal['expiration']} expiration")
        print(f"   4. BUY {signal['contracts']} contracts of ${signal['strike_price']} {signal['option_type']}")
        print(f"   5. Use LIMIT ORDER at ~${signal['estimated_option_price']:.2f} or better")
        print()
        print("🛡️ RISK MANAGEMENT:")
        print(f"   📉 STOP LOSS: -50% (cut losses quickly on options)")
        print(f"   📈 TAKE PROFIT: +100% (double your money target)")
        print(f"   ⚠️  Options can expire worthless - manage risk carefully!")
        print("="*80)
        
        # Log the signal
        self.manual_orders.append(signal)
        self.save_manual_orders()

    async def check_exit_signals(self):
        """Check if any positions should be sold"""
        if not self.current_positions:
            return
        
        print("\n🔍 Checking exit signals for current positions...")
        
        for symbol, position in list(self.current_positions.items()):
            current_price = await self.get_current_price(symbol)
            if not current_price:
                continue
            
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price * 100
            
            print(f"  📊 {symbol}: Entry ${entry_price:.2f} → Current ${current_price:.2f} ({pnl_pct:+.1f}%)")
            
            sell_signal = False
            reason = ""
            
            # Stop loss
            if current_price <= position['stop_loss']:
                sell_signal = True
                reason = f"STOP LOSS triggered at ${position['stop_loss']:.2f}"
            
            # Take profit
            elif current_price >= position['take_profit']:
                sell_signal = True
                reason = f"TAKE PROFIT triggered at ${position['take_profit']:.2f}"
            
            if sell_signal:
                self.display_exit_signal(symbol, position, current_price, reason, pnl_pct)

    def display_exit_signal(self, symbol, position, current_price, reason, pnl_pct):
        """Display exit signal"""
        print("\n" + "="*70)
        print("🚨 MANUAL EXIT SIGNAL")
        print("="*70)
        print(f"📊 SYMBOL: {symbol}")
        print(f"🎯 ACTION: SELL")
        print(f"💰 CURRENT PRICE: ${current_price:.2f}")
        print(f"📈 QUANTITY: {position['quantity']} shares")
        print(f"📊 P&L: {pnl_pct:+.1f}%")
        print(f"🔔 REASON: {reason}")
        print()
        print("🎯 MANUAL EXECUTION:")
        print(f"   1. Open your trading app")  
        print(f"   2. SELL {position['quantity']} shares of {symbol}")
        print(f"   3. Use MARKET ORDER (current price: ${current_price:.2f})")
        print("="*70)

    def add_manual_position(self, symbol, entry_price, quantity):
        """Manually add a position that was executed"""
        position = {
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'cost': entry_price * quantity,
            'stop_loss': entry_price * (1 - self.stop_loss_pct),
            'take_profit': entry_price * (1 + self.take_profit_pct),
            'timestamp': datetime.now()
        }
        
        self.current_positions[symbol] = position
        self.buying_power -= position['cost']
        
        print(f"✅ Added position: {quantity} shares of {symbol} @ ${entry_price:.2f}")

    async def run_assistant(self):
        """Run the manual trading assistant"""
        print("🚀 MANUAL TRADING ASSISTANT STARTING")
        print("="*60)
        
        # Build stock universe
        await self.build_stock_universe()
        
        if not self.stock_universe:
            print("❌ No affordable stocks found!")
            return
        
        print(f"\n🎯 STARTING TRADE SIGNAL SCANNING...")
        print(f"💰 Available Balance: ${self.buying_power:.2f}")
        print(f"📊 Scanning {len(self.stock_universe)} stocks")
        print("Press Ctrl+C to stop\n")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                print(f"\n[CYCLE {cycle}] {datetime.now().strftime('%H:%M:%S')}")
                
                # Check for exit signals first
                await self.check_exit_signals()
                
                # Look for new entry signals (if we have capacity)
                if len(self.current_positions) < self.max_positions:
                    signals = await self.scan_for_signals()
                    
                    if signals:
                        # Show dashboard of all signals
                        sorted_signals = self.display_signals_dashboard(signals)
                        
                        # Let user pick which signal to see details for
                        if len(signals) > 1:
                            choice = input(f"\n📋 Enter signal # for details (1-{min(5, len(signals))}), or press Enter for #1: ").strip()
                            try:
                                idx = int(choice) - 1 if choice else 0
                                selected_signal = sorted_signals[idx] if 0 <= idx < len(sorted_signals) else sorted_signals[0]
                            except (ValueError, IndexError):
                                selected_signal = sorted_signals[0]
                        else:
                            selected_signal = signals[0]
                            
                        # Show detailed signal
                        self.display_trade_signal(selected_signal)
                        
                        # Ask if they executed it
                        executed = input("\n📝 Did you execute this options trade? (y/n): ").lower()
                        if executed == 'y':
                            actual_price = float(input(f"💰 What price did you pay per option? (est. ${selected_signal['estimated_option_price']:.2f}): ") or selected_signal['estimated_option_price'])
                            self.add_manual_position(
                                selected_signal['symbol'],
                                selected_signal['option_type'],
                                selected_signal['strike_price'],
                                selected_signal['expiration'],
                                actual_price,
                                selected_signal['contracts']
                            )
                    else:
                        print("   📊 No strong signals found this cycle")
                else:
                    print(f"   📋 Position limit reached ({len(self.current_positions)}/{self.max_positions})")
                
                print(f"\n⏳ Waiting 60 seconds before next scan...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Manual Trading Assistant stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main function"""
    print("🎯 MANUAL OPTIONS TRADING ASSISTANT")
    print("="*60)
    print("📞 Bot will give you CALL/PUT options signals to execute manually")
    print("💡 Perfect for testing options strategies before automation")
    print("⚡ High-leverage plays with defined risk management")
    print()
    
    balance = float(input("💰 Enter your options trading balance ($): ") or "50")
    
    assistant = ManualTradingAssistant(balance=balance)
    await assistant.run_assistant()

if __name__ == "__main__":
    asyncio.run(main())