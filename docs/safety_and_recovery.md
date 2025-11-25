# Safety & Recovery Protocols

This document outlines the safety mechanisms built into the IBKR Open-Core Trading Bot and the protocols for recovering from system failures.

## 1. In-Program Safety (The "Fat Finger" Layer)

The `src/execution.py` module acts as a final gatekeeper before any order is submitted to Interactive Brokers.

### Hard Limits
These limits are hard-coded in `ExecutionManager` and **cannot** be overridden by strategy logic.

| Limit | Value | Description |
| :--- | :--- | :--- |
| `MAX_SHARES_PER_ORDER` | **100** | Maximum number of shares for a single order. |
| `MAX_DOLLAR_VALUE` | **$5,000** | Maximum notional value (Price * Quantity) per order. |
| `MAX_PRICE_DEVIATION` | **5%** | Limit orders cannot deviate more than 5% from the current market price. |

**Action on Violation:**
- The order is **rejected** immediately.
- A `CRITICAL` log is generated.
- A notification is sent to the user (Discord/Telegram).
- The strategy execution is halted for that specific tick.

### Strategy-Level Risk Management
Implemented in `strategies/base_strategy.py`.

- **Trailing Stop-Loss**: Defaults to **2%**. If the price drops 2% from the highest point since entry, the position is closed.
- **Take-Profit**: Defaults to **5%**. If the price rises 5% from the entry price, the position is closed.
- **Position Sizing**: Dynamically calculated based on account equity (default **1% risk per trade**).

---

## 2. System Safety & Crash Recovery

### Scenario: Unexpected Shutdown
If the bot crashes, loses power, or is terminated unexpectedly:

1.  **Open Orders**: IBKR (TWS/Gateway) may still have open orders active.
2.  **Open Positions**: You may still hold positions that the bot is no longer managing.
3.  **State Mismatch**: The bot's internal database (if any) or memory is lost.

### Recovery Protocol

**Step 1: Immediate Manual Check**
- Log in to TWS or IBKR Mobile.
- **Cancel all open orders** manually to prevent unwanted fills.
- Verify current positions.

**Step 2: Restart the Bot**
- Relaunch the application.
- The bot is designed to be **stateless** regarding positions on startup. It queries IBKR for the *actual* portfolio state (`ib.positions()`).

**Step 3: State Reconciliation (Automatic)**
- On startup, the bot fetches all open positions from IBKR.
- **Rule**: The IBKR portfolio is the "Source of Truth".
- If the bot detects a position it didn't originate (or lost track of), it will:
    1.  Log a `WARNING`.
    2.  (Configurable) Attempt to manage it using default risk parameters OR ignore it and require manual intervention.
    *Current Default*: The bot will **NOT** automatically close unknown positions to avoid accidental losses. It will alert the user.

### System Health Monitoring (Heartbeat)

To ensure the bot is running:
- **Logs**: Check `logs/trading.log` for recent activity (timestamps within the last minute).
- **Notifications**: The bot sends a "Startup" message on launch and a "Daily Summary" at market close.

### Automated Process Supervisor
We provide a supervisor script `tools/supervisor.py` that launches the bot and watches for crashes.

**Usage:**
```bash
python tools/supervisor.py python your_script.py
```

**Features:**
- Launches the target script as a subprocess.
- Sends an **INFO** notification on startup and normal exit.
- Sends a **CRITICAL** notification if the process crashes (non-zero exit code).
- Handles `Ctrl+C` to gracefully terminate the child process.

### "Who Watches the Watchmen?" (Monitoring the Supervisor)
If `supervisor.py` itself crashes (e.g., server power loss), it cannot send an alert. To mitigate this:

1.  **External Heartbeat (Dead Man's Switch)**: Use a service like [Healthchecks.io](https://healthchecks.io) or [Dead Man's Snitch](https://deadmanssnitch.com). Configure the bot to send a "ping" (HTTP request) every minute. If the service stops receiving pings, *it* emails/alerts you.
2.  **OS-Level Restart**:
    -   **Windows**: Use **Task Scheduler** to run the supervisor on startup and restart it if it fails.
    -   **Linux**: Use `systemd` with `Restart=always`.
