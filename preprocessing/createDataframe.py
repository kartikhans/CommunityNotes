import pandas as pd
from load_data import load_all_tsv
from pathlib import Path

DATA_DIR = Path(r"C:/Users/nyafe\Data/community_notes_data/extracted")

# ============================
# 1. Load raw tables
# ============================
notes = load_all_tsv("notes-*.tsv", usecols=["noteId", "noteAuthorParticipantId", "createdAtMillis", "summary"])
ratings = load_all_tsv(
    "ratings-*.tsv",
    usecols=["noteId", "raterParticipantId", "helpfulnessLevel", "agree", "disagree"],
    max_rows=2_000_000
)
note_status_df = load_all_tsv(
    "noteStatusHistory-*.tsv",
    usecols=["noteId", "lockedStatus", "noteAuthorParticipantId", "timestampMillisOfStatusLock"]
)
enrollment = load_all_tsv("userEnrollment-*.tsv", usecols=["participantId", "enrollmentState"])

# ============================
# 2. Rename columns for clarity
# ============================
notes = notes.rename(columns={"noteAuthorParticipantId": "noteAuthorId"})
ratings = ratings.rename(columns={"raterParticipantId": "raterId"})
note_status_df = note_status_df.rename(columns={"noteAuthorParticipantId": "noteAuthorId"})
# Keep enrollment as general participant table
enrollment = enrollment.rename(columns={"participantId": "participantId_global"})

# ============================
# 3. Merge notes + status
# ============================
merged = notes.merge(
    note_status_df,
    on="noteId",
    how="inner",
    suffixes=("", "_status")  # keep notes version as 'noteAuthorId'
)

# ============================
# 4. Merge with ratings
# ============================
merged = merged.merge(ratings, on="noteId", how="inner")

# ============================
# 5. Merge enrollment for rater
# ============================
merged = merged.merge(
    enrollment,
    left_on="raterId",
    right_on="participantId_global",
    how="left"
).rename(columns={"enrollmentState": "raterEnrollmentState"}).drop(columns=["participantId_global"])

# ============================
# 6. (Optional) Merge enrollment for note author if needed
# ============================
merged = merged.merge(
     enrollment,
     left_on="noteAuthorId",
     right_on="participantId_global",
     how="left"
 ).rename(columns={"enrollmentState": "authorEnrollmentState"}).drop(columns=["participantId_global"])

# ============================
# 7. Convert timestamps
# ============================
merged["createdAtMillis"] = pd.to_datetime(merged["createdAtMillis"], unit="ms")
merged["timestampMillisOfStatusLock"] = pd.to_datetime(merged["timestampMillisOfStatusLock"], unit="ms")

# ============================
# 8. Final column order
# ============================
merged = merged[[
    "noteId",
    "noteAuthorId",
    "createdAtMillis",
    "summary",
    "lockedStatus",
    "timestampMillisOfStatusLock",
    "raterId",
    "agree",
    "disagree",
    "helpfulnessLevel",
    "raterEnrollmentState",
    "authorEnrollmentState"
]]

# ============================
# 9. Save merged dataset
# ============================
merged.to_parquet(DATA_DIR / "merged_notes_dataset.parquet", index=False)
print(f"Merged dataset saved to: {DATA_DIR / 'merged_notes_dataset.parquet'}")
print(f"Shape: {merged.shape}")
print(merged.head())
