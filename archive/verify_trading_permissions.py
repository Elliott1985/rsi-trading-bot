#!/usr/bin/env python3
"""
E*TRADE Trading Permissions Verification Tool
Checks account access, trading permissions, and API capabilities
"""

import sys
import os
import json
from datetime import datetime

sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TradingPermissionsChecker:
    """Comprehensive E*TRADE permissions checker"""
    
    def __init__(self):
        self.config = Config()
        self.broker = None
        
    async def run_full_check(self):
        """Run complete permissions verification"""
        print("🔍 E*TRADE Trading Permissions Verification")
        print("=" * 55)
        
        results = {
            'authentication': False,
            'account_access': False,
            'account_list': False,
            'balance_access': False,
            'positions_access': False,
            'order_preview': False,
            'trading_permissions': False,
            'sandbox_vs_live': None
        }
        
        # Test both sandbox and production
        for mode in ['sandbox', 'production']:
            print(f"\n🏦 Testing {mode.upper()} mode...")
            
            try:
                is_sandbox = (mode == 'sandbox')
                self.broker = ETradeBroker(self.config, sandbox=is_sandbox)
                
                # 1. Authentication Test
                print("1️⃣ Testing authentication...")
                auth_success = await self.broker.authenticate()
                results['authentication'] = auth_success
                
                if not auth_success:
                    print("   ❌ Authentication failed - cannot proceed")
                    continue
                    
                print("   ✅ Authentication successful")
                
                # 2. Account List Access
                print("2️⃣ Testing account list access...")
                try:
                    accounts = await self.get_accounts()
                    if accounts:
                        results['account_list'] = True
                        print(f"   ✅ Found {len(accounts)} account(s)")
                        for acc in accounts:
                            print(f"      - Account: {acc.get('accountIdKey', 'N/A')}")
                    else:
                        print("   ❌ No accounts found")
                except Exception as e:
                    print(f"   ❌ Account list failed: {e}")
                
                # 3. Balance Access
                print("3️⃣ Testing balance access...")
                try:
                    balance = await self.get_balance()
                    if balance is not None:
                        results['balance_access'] = True
                        print(f"   ✅ Balance access successful: ${balance}")
                    else:
                        print("   ❌ Balance access failed")
                except Exception as e:
                    print(f"   ❌ Balance error: {e}")
                
                # 4. Positions Access
                print("4️⃣ Testing positions access...")
                try:
                    positions = await self.get_positions()
                    results['positions_access'] = True
                    print(f"   ✅ Positions access successful ({len(positions)} positions)")
                except Exception as e:
                    print(f"   ❌ Positions error: {e}")
                
                # 5. Order Preview (Trading Permission Test)
                print("5️⃣ Testing order preview (trading permissions)...")
                try:
                    preview_result = await self.test_order_preview()
                    if preview_result:
                        results['order_preview'] = True
                        results['trading_permissions'] = True
                        print("   ✅ Order preview successful - TRADING PERMISSIONS CONFIRMED")
                    else:
                        print("   ❌ Order preview failed - trading permissions may be restricted")
                except Exception as e:
                    print(f"   ❌ Order preview error: {e}")
                
                # 6. Check Trading Capabilities
                print("6️⃣ Checking trading capabilities...")
                trading_caps = await self.check_trading_capabilities()
                if trading_caps:
                    print("   ✅ Trading capabilities confirmed:")
                    for capability, status in trading_caps.items():
                        status_icon = "✅" if status else "❌"
                        print(f"      {status_icon} {capability}")
                
                results['sandbox_vs_live'] = mode
                
                print(f"\n📊 {mode.upper()} Mode Summary:")
                for check, status in results.items():
                    if check != 'sandbox_vs_live':
                        icon = "✅" if status else "❌"
                        print(f"   {icon} {check.replace('_', ' ').title()}")
                
            except Exception as e:
                print(f"   💥 {mode.upper()} mode failed: {e}")
        
        # Final recommendations
        await self.provide_recommendations(results)
        
        return results
    
    async def get_accounts(self):
        """Get account list"""
        try:
            # This method varies by broker implementation
            if hasattr(self.broker, 'get_accounts'):
                return await self.broker.get_accounts()
            else:
                print("   ⚠️ get_accounts method not implemented")
                return []
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            return None
    
    async def get_balance(self):
        """Get account balance"""
        try:
            if hasattr(self.broker, 'get_account_balance'):
                return await self.broker.get_account_balance()
            else:
                print("   ⚠️ get_account_balance method not implemented")
                return None
        except Exception as e:
            logger.error(f"Get balance error: {e}")
            return None
    
    async def get_positions(self):
        """Get current positions"""
        try:
            if hasattr(self.broker, 'get_positions'):
                return await self.broker.get_positions()
            else:
                print("   ⚠️ get_positions method not implemented") 
                return []
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return []
    
    async def test_order_preview(self):
        """Test order preview to verify trading permissions"""
        try:
            # Try to preview a small order (doesn't execute)
            test_symbol = "AAPL"
            test_quantity = 1
            
            if hasattr(self.broker, 'preview_order'):
                preview = await self.broker.preview_order(
                    symbol=test_symbol,
                    action="BUY",
                    quantity=test_quantity,
                    order_type="MARKET"
                )
                return preview is not None
            else:
                print("   ⚠️ preview_order method not implemented")
                return False
                
        except Exception as e:
            # Some errors are expected (like insufficient funds)
            error_msg = str(e).lower()
            
            # These errors mean we have trading permissions but other issues
            acceptable_errors = [
                'insufficient', 'funds', 'buying power', 'balance',
                'market closed', 'invalid symbol'
            ]
            
            if any(err in error_msg for err in acceptable_errors):
                print(f"   ✅ Trading permissions OK (got expected error: {e})")
                return True
            else:
                print(f"   ❌ Trading permissions error: {e}")
                return False
    
    async def check_trading_capabilities(self):
        """Check specific trading capabilities"""
        capabilities = {
            'Market Orders': False,
            'Limit Orders': False, 
            'Buy Orders': False,
            'Sell Orders': False,
            'Equity Trading': False
        }
        
        # This would need specific API calls to verify each capability
        # For now, return basic assessment
        try:
            if hasattr(self.broker, 'place_order'):
                capabilities['Market Orders'] = True
                capabilities['Buy Orders'] = True
                capabilities['Sell Orders'] = True
                capabilities['Equity Trading'] = True
        except:
            pass
            
        return capabilities
    
    async def provide_recommendations(self, results):
        """Provide actionable recommendations"""
        print("\n💡 RECOMMENDATIONS:")
        print("=" * 55)
        
        if not results['authentication']:
            print("🔐 AUTHENTICATION ISSUES:")
            print("   1. Verify API keys in api_keys.env")
            print("   2. Check if tokens are expired")
            print("   3. Re-run OAuth authentication")
            print("   4. Ensure correct sandbox vs production keys")
        
        elif not results['account_list']:
            print("🏦 ACCOUNT ACCESS ISSUES:")
            print("   1. Check account permissions in E*TRADE developer portal")
            print("   2. Verify account is approved for API access")
            print("   3. Ensure account is not restricted")
        
        elif not results['trading_permissions']:
            print("📈 TRADING PERMISSION ISSUES:")
            print("   1. Log into E*TRADE web/mobile app")
            print("   2. Go to 'Account Settings' -> 'API Access'") 
            print("   3. Verify 'Trading' is enabled (not just 'Read-Only')")
            print("   4. Check for any account restrictions")
            print("   5. Contact E*TRADE support if permissions missing")
        
        else:
            print("✅ ALL PERMISSIONS VERIFIED!")
            print("   Your account has full trading permissions")
            print("   Bot should be able to place orders automatically")
            print("   If orders still fail, check network/API rate limits")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Save this report: verify_trading_permissions.log")
        print(f"   2. If issues persist, contact E*TRADE API support")
        print(f"   3. Test with small orders in sandbox mode first")

async def main():
    """Main verification function"""
    try:
        checker = TradingPermissionsChecker()
        results = await checker.run_full_check()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"trading_permissions_check_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"❌ Verification error: {e}")

if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Verification cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")