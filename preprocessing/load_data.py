import pandas as pd
from pathlib import Path

DATA_DIR = Path(r"C:\Users\nyafe\Data\community_notes_data\extracted")

def load_all_tsv(pattern: str, usecols=None, max_rows=None) -> pd.DataFrame:
    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    dfs = []
    for f in files:
        print(f"Loading {f.name} ...")
        # Use chunksize to read big files in manageable pieces
        chunk_iter = pd.read_csv(
            f,
            sep="\t",
            usecols=usecols,
            chunksize=500_000,  # adjust chunk size depending on your RAM
            low_memory=False
        )
        for chunk in chunk_iter:
            if max_rows is not None and len(dfs) * 500_000 >= max_rows:
                break
            dfs.append(chunk)

    return pd.concat(dfs, ignore_index=True)

if __name__ == "__main__":
    notes = load_all_tsv(
    "notes-*.tsv",
    usecols=["noteId", "noteAuthorParticipantId", "createdAtMillis", "summary"]
    )
    notes = notes.rename(columns={"noteAuthorParticipantId": "participantId_note"})


    ratings = load_all_tsv(
    "ratings-*.tsv",
    usecols=["noteId", "raterParticipantId", "helpfulnessLevel", "agree", "disagree"],
    max_rows=2_000_000
    )
    ratings = ratings.rename(columns={"raterParticipantId": "participantId_rating"})


    note_status = load_all_tsv(
        "noteStatusHistory-*.tsv",
        usecols=["noteId", "lockedStatus", "noteAuthorParticipantId", "timestampMillisOfStatusLock"]
    )
    note_status = note_status.rename(columns={"noteAuthorParticipantId": "participantId_note"})

    enrollment = load_all_tsv(
        "userEnrollment-*.tsv",
        usecols=["participantId", "enrollmentState"]
    )
    enrollment = enrollment.rename(columns={"participantId": "participantId"})

    print("Loaded data:")
    print("Notes:", notes.shape)
    print("Ratings (sampled):", ratings.shape)
    print("Note status:", note_status.shape)
    print("Enrollment:", enrollment.shape)
