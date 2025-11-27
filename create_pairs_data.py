import pandas as pd
import os

data_dir = "data/benchmark"
pep = pd.read_csv(os.path.join(data_dir, "PEP_2024-10-01_2025-11-25.csv"), index_col="Date", parse_dates=True)
ko = pd.read_csv(os.path.join(data_dir, "KO_2024-10-01_2025-11-25.csv"), index_col="Date", parse_dates=True)

# Rename columns
pep.columns = [f"{col}_1" for col in pep.columns]
ko.columns = [f"{col}_2" for col in ko.columns]

# Merge
pair_data = pd.concat([pep, ko], axis=1).dropna()

# Save
# Save
# pair_data.to_csv(os.path.join(data_dir, "PEP-KO_2024-10-01_2025-11-25.csv"))
# print("Created PEP-KO_2024-10-01_2025-11-25.csv")
print("Aggregation is now done in memory during backtest execution. This script is deprecated.")
