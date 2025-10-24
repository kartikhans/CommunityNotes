import pandas as pd
from pathlib import Path

DATA_DIR = Path(r"C:\Users\nyafe\Data\community_notes_data\extracted")

# Inspect noteStatusHistory
f = next(DATA_DIR.glob("noteStatusHistory-*.tsv"))
df_status = pd.read_csv(f, sep="\t", nrows=5)
print("noteStatusHistory columns:", df_status.columns.tolist())

# Inspect userEnrollment
g = next(DATA_DIR.glob("userEnrollment-*.tsv"))
df_enroll = pd.read_csv(g, sep="\t", nrows=5)
print("userEnrollment columns:", df_enroll.columns.tolist())
