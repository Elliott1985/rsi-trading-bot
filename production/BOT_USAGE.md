# Safe Bot Management Guide

## The Problem We Fixed

During testing, multiple bot instances were accidentally started simultaneously, leading to:
- 27 trades executed in 14 minutes
- $5.64 loss (11.4% of portfolio)
- Catastrophic trading loop

## Root Cause

The `pkill` command wasn't reliably stopping bot processes, so each restart attempt created additional running instances.

## Solutions Implemented

### 1. Bot Manager Script ✅
Use the `bot_manager.py` script for all bot operations:

```bash
# Check bot status
python3 bot_manager.py status

# Start bot (only if not already running)
python3 bot_manager.py start

# Stop bot safely
python3 bot_manager.py stop

# Restart bot (stop + start)
python3 bot_manager.py restart
```

### 2. Singleton Protection ✅
The bot now includes built-in protection against multiple instances:
- Creates a `bot.lock` file when starting
- Prevents multiple instances from running
- Automatically cleans up on shutdown

### 3. Process Isolation ✅
- Each bot starts in its own process group
- PID tracking for reliable shutdown
- Graceful shutdown with fallback to force kill

## Safe Operating Procedures

### Starting the Bot
```bash
# ALWAYS check status first
python3 bot_manager.py status

# If not running, start it
python3 bot_manager.py start

# Monitor logs
tail -f bot_live_trading.log
```

### Stopping the Bot
```bash
# Stop gracefully
python3 bot_manager.py stop

# Verify it stopped
python3 bot_manager.py status

# Check account status
python3 check_account.py
```

### Emergency Stop
If the bot manager fails to stop the bot:
```bash
# Force stop all processes
python3 bot_manager.py stop

# Double-check no processes remain
ps aux | grep -i "python.*bot"

# Force kill any remaining processes
kill -9 [PID]

# Close any open positions manually
python3 close_position.py
```

## What NOT to Do

❌ **Never** use direct commands like:
- `nohup python3 src/main_bot.py &`
- `pkill -f python`
- Starting multiple terminals with bot commands

❌ **Never** restart without checking status first

❌ **Never** ignore error messages about existing instances

## Monitoring Checklist

### Before Starting
- [ ] Check `python3 bot_manager.py status`
- [ ] Verify account balance with `python3 check_account.py`
- [ ] Review recent logs for any issues

### While Running
- [ ] Monitor logs: `tail -f bot_live_trading.log`
- [ ] Check positions periodically: `python3 check_account.py`
- [ ] Watch for excessive trading (more than 3 trades/hour)

### Before Stopping
- [ ] Let current positions complete if possible
- [ ] Check final account status
- [ ] Review trading performance

## Files Created by Bot Manager

- `bot.pid` - Contains process ID of running bot
- `bot.lock` - Singleton lock file (auto-cleaned)
- `bot_live_trading.log` - Main log file

## Troubleshooting

### "Bot is already running" Error
```bash
python3 bot_manager.py stop
python3 bot_manager.py status
python3 bot_manager.py start
```

### Multiple Processes Found
```bash
# Check for multiple processes
ps aux | grep -i "python.*bot"

# Force stop all
python3 bot_manager.py stop

# Clean up manually if needed
kill -9 [PID1] [PID2] [PID3]
rm -f bot.pid bot.lock
```

### Log File Issues
```bash
# Check log file size
ls -lh bot_live_trading.log

# Rotate if too large
mv bot_live_trading.log bot_live_trading_old.log
```

## Current Safety Features

1. ✅ Singleton protection (prevents multiple instances)
2. ✅ Process management (reliable start/stop)
3. ✅ Position closing fixes (crypto time-in-force)
4. ✅ Minimum order value fixes ($1 minimum)
5. ⚠️ Still needed: Trading frequency limits
6. ⚠️ Still needed: Position tracking error handling
7. ⚠️ Still needed: Dynamic stop loss adjustment

---

**Remember**: Always use `bot_manager.py` for all bot operations!