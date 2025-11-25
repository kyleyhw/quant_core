import os
import glob

def cleanup_reports():
    reports_dir = r"c:\Users\Kyle\PycharmProjects\ibkr_quant_core\strategies\private\reports"
    files = glob.glob(os.path.join(reports_dir, "*.md"))
    
    count = 0
    for file in files:
        with open(file, 'r') as f:
            content = f.read()
            
        # Check for 0 trades in the table
        # Pattern: | # Trades               | 0                     |
        # We'll just look for the row content loosely
        if "| # Trades" in content and "| 0 " in content:
            # Verify it's on the same line or close enough context
            lines = content.split('\n')
            for line in lines:
                if "| # Trades" in line and "| 0 " in line:
                    print(f"Deleting {file}")
                    f.close() # Ensure closed before delete
                    os.remove(file)
                    # Also delete the html if it exists
                    html_file = file.replace(".md", ".html")
                    if os.path.exists(html_file):
                        os.remove(html_file)
                    count += 1
                    break
    
    print(f"Deleted {count} reports.")

if __name__ == "__main__":
    cleanup_reports()
