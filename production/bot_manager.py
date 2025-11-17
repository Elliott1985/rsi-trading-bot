#!/usr/bin/env python3
"""
Safe Bot Manager - Ensures only one bot instance runs at a time
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

class BotManager:
    def __init__(self):
        self.bot_script = "src/main_bot.py"
        self.log_file = "bot_live_trading.log"
        self.pid_file = "bot.pid"
        
    def is_bot_running(self):
        """Check if bot is currently running"""
        if not os.path.exists(self.pid_file):
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)  # Sends no signal, just checks if process exists
            return True
            
        except (OSError, ValueError, ProcessLookupError):
            # PID file exists but process is dead - clean up
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            return False
    
    def stop_bot(self):
        """Safely stop the bot"""
        if not os.path.exists(self.pid_file):
            print("No PID file found - checking for running processes...")
            return self.force_stop_all()
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"Stopping bot with PID {pid}...")
            
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            
            # Wait up to 10 seconds for graceful shutdown
            for i in range(10):
                try:
                    os.kill(pid, 0)  # Check if still alive
                    time.sleep(1)
                except ProcessLookupError:
                    break
            else:
                # Force kill if still alive
                print("Graceful shutdown failed, force killing...")
                os.kill(pid, signal.SIGKILL)
            
            # Clean up PID file
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            print("✅ Bot stopped successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping bot: {e}")
            return self.force_stop_all()
    
    def force_stop_all(self):
        """Force stop all bot processes"""
        print("Force stopping all bot processes...")
        
        try:
            # Find all bot processes
            result = subprocess.run([
                'pgrep', '-f', 'python.*main_bot.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"Killing PID {pid}")
                        os.kill(int(pid), signal.SIGKILL)
                
                print(f"✅ Killed {len(pids)} bot processes")
            else:
                print("No bot processes found")
            
            # Also check for enhanced_bot
            result = subprocess.run([
                'pgrep', '-f', 'python.*enhanced_bot.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"Killing enhanced bot PID {pid}")
                        os.kill(int(pid), signal.SIGKILL)
            
            # Clean up PID file
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Error force stopping: {e}")
            return False
    
    def start_bot(self):
        """Start the bot safely"""
        if self.is_bot_running():
            print("❌ Bot is already running! Use 'stop' first.")
            return False
        
        print("Starting bot...")
        
        # Start bot process
        process = subprocess.Popen([
            sys.executable, self.bot_script
        ], stdout=open(self.log_file, 'a'), 
           stderr=subprocess.STDOUT,
           preexec_fn=os.setsid  # Start new process group
        )
        
        # Save PID
        with open(self.pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # Wait a moment to check if it started successfully
        time.sleep(2)
        
        if self.is_bot_running():
            print(f"✅ Bot started successfully with PID {process.pid}")
            print(f"📝 Logs: tail -f {self.log_file}")
            return True
        else:
            print("❌ Bot failed to start")
            return False
    
    def restart_bot(self):
        """Restart the bot safely"""
        print("Restarting bot...")
        self.stop_bot()
        time.sleep(3)  # Wait for cleanup
        return self.start_bot()
    
    def status(self):
        """Check bot status"""
        if self.is_bot_running():
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            print(f"✅ Bot is running with PID {pid}")
        else:
            print("❌ Bot is not running")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bot_manager.py {start|stop|restart|status}")
        sys.exit(1)
    
    manager = BotManager()
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_bot()
    elif command == "stop":
        manager.stop_bot()
    elif command == "restart":
        manager.restart_bot()
    elif command == "status":
        manager.status()
    else:
        print("❌ Unknown command. Use: start, stop, restart, or status")

if __name__ == "__main__":
    main()