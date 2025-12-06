import subprocess
import sys
import time
import os
import signal
from pathlib import Path
import logging
from typing import List

# Add project root to path to import src
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.notifications import Notifier, Severity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [MONITOR] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def monitor_process(command: List[str]) -> None:
    """
    Runs and monitors a subprocess. Sends alerts on crash.
    """
    notifier = Notifier()
    
    logging.info(f"Starting monitored process: {' '.join(command)}")
    notifier.send(f"Bot started: `{' '.join(command)}`", Severity.INFO, "System Startup")

    process = subprocess.Popen(command)
    
    try:
        while True:
            ret_code = process.poll()
            
            if ret_code is not None:
                # Process has exited
                if ret_code == 0:
                    msg = f"Process exited normally (Code 0)."
                    logging.info(msg)
                    notifier.send(msg, Severity.INFO, "System Shutdown")
                else:
                    msg = f"Process CRASHED with exit code {ret_code}!"
                    logging.error(msg)
                    notifier.send(msg, Severity.CRITICAL, "System Crash Alert")
                break
            
            time.sleep(5) # Check every 5 seconds

    except KeyboardInterrupt:
        logging.info("Monitor stopping... Terminating child process.")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        logging.info("Child process stopped.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/monitor.py <command_to_run>")
        print("Example: python tools/monitor.py python run_backtesting/benchmark.py")
        sys.exit(1)
    
    target_command = sys.argv[1:]
    monitor_process(target_command)
