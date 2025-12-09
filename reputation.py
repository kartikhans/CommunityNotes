import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from transformers import pipeline
import math
from tqdm import tqdm
from collections import defaultdict
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
import torch

# # STEP 1: Import Dataset

from google.colab import drive
drive.mount('/content/drive')

path = "/content/drive/MyDrive/merged_notes_dataset.parquet"
df = pd.read_parquet(path)

# # STEP 2: Curate dataset: Top 20 contributing users --> All of their notes and ratings (Ensure that appropriate size)

users = pd.concat([df["noteAuthorId"], df["raterId"]], ignore_index=True)
topusers = users.value_counts().head(20)
topusers = topusers.index.tolist()


topuser_df = df[df["noteAuthorId"].isin(topusers) | df["raterId"].isin(topusers)]

print(topuser_df.shape)

# # Find the number of unique instances in the "summary" column (that is, unique notes)
# # This is just to check the number
unique_summaries = topuser_df["summary"].nunique()
print(unique_summaries)

import networkx as nx

G = nx.from_pandas_edgelist(
    topuser_df,
    source="noteAuthorId",
    target="raterId",
    create_using=nx.DiGraph()
)

subG = G.subgraph(topusers).copy()

import matplotlib.pyplot as plt

plt.figure(figsize=(12, 8))

pos = nx.spring_layout(subG, k=0.5, seed=42)

nx.draw_networkx_nodes(subG, pos, node_size=600)
nx.draw_networkx_edges(subG, pos, arrows=True, arrowstyle="-|>")
nx.draw_networkx_labels(subG, pos, font_size=10)

plt.title("Interaction Network Among Top Users")
plt.axis("off")
plt.show()

# # STEP 3: Use https://huggingface.co/cardiffnlp/tweet-topic-21-multi --> Already trained on pretty much what we need!
# # Actually... They have their own labels...
cardiff_labels = [
    "arts_&_culture",
    "business_&_entrepreneurs",
    "celebrity_&_pop_culture",
    "diaries_&_daily_life",
    "family",
    "fashion_&_style",
    "film_tv_&_video",
    "fitness_&_health",
    "food_&_dining",
    "gaming",
    "learning_&_educational",
    "music",
    "news_&_social_concern",
    "other_hobbies",
    "relationships",
    "science_&_technology",
    "sports",
    "travel_&_adventure",
    "youth_&_student_life",
    "automotive",
    "crafts_&_diy"
]

# # REASONING: These are from the paper! I put a link in our doc

# # Also, let's get the unique summaries for the sake of the model running quickly
unique_summaries = topuser_df["summary"].drop_duplicates().reset_index(drop=False)
unique_summaries.columns = ["orig_index", "summary"]

def get_topic_probs(text_list):
    inputs = tokenizer(
        text_list,
        padding=True,
        truncation=True,
        max_length=128,    # ensures tensor shape consistency
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1)

    return probs.cpu().numpy()

BATCH_SIZE = 128
results_list = []

num_batches = math.ceil(len(unique_summaries) / BATCH_SIZE)

for i in tqdm(range(num_batches), desc="Topic classification"):
    batch_df = unique_summaries.iloc[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
    texts = batch_df["summary"].tolist()

    batch_probs = get_topic_probs(texts)

    for j in range(len(batch_df)):
        row = batch_df.iloc[j].copy()
        probs = batch_probs[j]

        # sanity check – should be 19
        assert len(probs) == len(cardiff_labels)

        row["domain_probs"] = probs

        # add one column per probability
        for idx, label in enumerate(cardiff_labels):
            row[label] = probs[idx]

        results_list.append(row)

unique_results_df = pd.DataFrame(results_list)

df_with_probs = topuser_df.merge(
    unique_results_df.drop(columns=["orig_index"]),
    how="left",
    on="summary"
)

# # Save as CSV
df_with_probs["domain_probs"] = df_with_probs["domain_probs"].apply(lambda x: x.tolist())
final_path = "/content/drive/MyDrive/final_dataset_with_probs.csv"
df_with_probs.to_csv(final_path, index=False)

import pandas as pd

from google.colab import drive
drive.mount('/content/drive')
file_path = "/content/drive/MyDrive/final_dataset_with_probs.csv"

# Load into a DataFrame
df_with_probs = pd.read_csv(file_path)

# Quick check
print(df_with_probs.head())
print(df_with_probs.columns)

from sklearn.model_selection import train_test_split

train_df, validate_df = train_test_split(
    df_with_probs,
    test_size=0.2,
    random_state=42
)

validate_df.to_csv("/content/drive/MyDrive/validate_df.csv", index=False)
train_df.to_csv("/content/drive/MyDrive/train_df.csv", index=False)

from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "cardiffnlp/tweet-topic-21-multi"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

cardiff_labels = list(model.config.id2label.values())

# # Compute user scores!
df2 = train_df.copy()

# # Drop any leftover domain columns (safety)
df2 = df2.drop(columns=[c for c in train_df.columns if c in cardiff_labels], errors='ignore')

# # Merge in Cardiff domain probabilities
df2 = df2.merge(df_with_probs[['summary'] + cardiff_labels], on='summary', how='left')

# # Fill missing domain columns with 0
for col in cardiff_labels:
    if col not in df2.columns:
        df2[col] = 0.0
df2[cardiff_labels] = df2[cardiff_labels].fillna(0.0)

# # Normalize lockedStatus
df2['lockedStatusNorm'] = df2['lockedStatus'].map({
    'CURRENTLY_RATED_HELPFUL': 'HELPFUL',
    'NEEDS_MORE_RATINGS': 'NA',
    'CURRENTLY_RATED_NOT_HELPFUL': 'NOT_HELPFUL'
})


def compute_beta_rating(row):
    if row['noteAuthorId'] == row['raterId']:
        return 1
    if row['lockedStatusNorm'] in ['HELPFUL']:
        if row['agree'] == 1:
            return 1
        if row['agree'] == 0 and row['helpfulnessLevel'] in ['HELPFUL', 'SOMEWHAT_HELPFUL']:
            return 1.5
        if row['agree'] == 0 and row['helpfulnessLevel'] == 'NOT_HELPFUL':
            return -1.5
    if row['lockedStatusNorm'] == 'NOT_HELPFUL':
        if row['agree'] == 0:
            return 1
        if row['agree'] == 1 and row['helpfulnessLevel'] == 'NOT_HELPFUL':
            return 1.5
        if row['agree'] == 1 and row['helpfulnessLevel'] in ['HELPFUL', 'SOMEWHAT_HELPFUL']:
            return -1.5
    return 0

def compute_lambda_rating(row):
    if row['noteAuthorId'] == row['raterId']:
        return 1
    return 1.5 if row['lockedStatusNorm'] == row['helpfulnessLevel'] else 1

def compute_beta_note(row):
    if row['lockedStatusNorm'] in ['HELPFUL']:
        if row['disagree'] > row['agree']:
            return 1.5
        else:
            return 1
    if row['lockedStatusNorm'] == 'NOT_HELPFUL':
        return -1.5
    return 0

def compute_lambda_note(row):
    return 1.5 if row['lockedStatusNorm'] in ['HELPFUL', 'SOMEWHAT_HELPFUL'] else 0.5


df2['beta_rating'] = df2.apply(compute_beta_rating, axis=1)
df2['lambda_rating'] = df2.apply(compute_lambda_rating, axis=1)
df2['beta_note'] = df2.apply(compute_beta_note, axis=1)
df2['lambda_note'] = df2.apply(compute_lambda_note, axis=1)

# # Contribution per note
df2['contribution'] = df2['beta_rating'] * df2['lambda_rating'] * df2['beta_note'] * df2['lambda_note']


for domain in cardiff_labels:
    df2[f'weighted_{domain}'] = df2['contribution'] * df2[domain]


# # Stack author/rater contributions
author_cols = ['noteAuthorId'] + [f'weighted_{d}' for d in cardiff_labels]
rater_cols  = ['raterId']     + [f'weighted_{d}' for d in cardiff_labels]

df_author = df2[author_cols].rename(columns={'noteAuthorId':'user'})
df_rater  = df2[rater_cols].rename(columns={'raterId':'user'})

# # Combine all contributions
df_stack = pd.concat([df_author, df_rater], ignore_index=True)

# # Aggregate by user (average contribution per domain)
user_scores_df = df_stack.groupby('user').mean().reset_index()

user_scores_df.to_csv("/content/drive/MyDrive/user_scores.csv", index=False)

# @title
# # STEP 5: Compute Bayesian reputation vectors for all users
from collections import defaultdict
import pandas as pd

# # Copy train_df and merge in Cardiff domain probabilities
df2 = train_df.copy()
df2 = df2.drop(columns=[c for c in train_df.columns if c in cardiff_labels], errors='ignore')
df2 = df2.merge(df_with_probs[['summary'] + cardiff_labels], on='summary', how='left')
df2[cardiff_labels] = df2[cardiff_labels].fillna(0.0)

# # Normalize lockedStatus for simpler scoring
df2['lockedStatusNorm'] = df2['lockedStatus'].map({
    'currently rated helpful': 'helpful',
    'currently rated somewhat helpful': 'somewhat helpful',
    'currently rated not helpful': 'not helpful'
})

# # ---- Scoring functions ----
def compute_beta_rating(row):
    if row['noteAuthorId'] == row['raterId']:
        return 1
    if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful']:
        if row['agree'] == 1:
            return 1
        if row['agree'] == 0 and row['helpfulnessLevel'] in ['helpful', 'somewhat helpful']:
            return 1.5
        if row['agree'] == 0 and row['helpfulnessLevel'] == 'not helpful':
            return -1
    if row['lockedStatusNorm'] == 'not helpful':
        if row['agree'] == 0:
            return 1
        if row['agree'] == 1 and row['helpfulnessLevel'] == 'not helpful':
            return 1.5
        if row['agree'] == 1 and row['helpfulnessLevel'] in ['helpful', 'somewhat helpful']:
            return -1
    return 0.5  # baseline to avoid zero contribution

def compute_lambda_rating(row):
    if row['noteAuthorId'] == row['raterId']:
        return 1
    return 1.5 if row['lockedStatusNorm'] == row['helpfulnessLevel'] else 1

def compute_beta_note(row):
    if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful']:
        if row['disagree'] > row['agree']:
            return 1.5
        else:
            return 1
    if row['lockedStatusNorm'] == 'not helpful':
        return -1
    return 0.5  # baseline

def compute_lambda_note(row):
    return 1.5 if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful'] else 0.5

# # ---- Compute contribution per rating ----
df2['beta_rating'] = df2.apply(compute_beta_rating, axis=1)
df2['lambda_rating'] = df2.apply(compute_lambda_rating, axis=1)
df2['beta_note'] = df2.apply(compute_beta_note, axis=1)
df2['lambda_note'] = df2.apply(compute_lambda_note, axis=1)

# # Ensure contribution is never zero
df2['contribution'] = df2['beta_rating'] * df2['lambda_rating'] * df2['beta_note'] * df2['lambda_note']
df2['contribution'] = df2['contribution'].replace(0, 0.1)  # small positive floor

# # ---- Initialize Bayesian reputations ----
author_reputation = defaultdict(lambda: defaultdict(lambda: {"alpha":1.0, "beta":1.0}))
rater_reputation = defaultdict(lambda: defaultdict(lambda: {"alpha":1.0, "beta":1.0}))

# domain_list = cardiff_labels

# # ---- Bayesian update function ----
def bayesian_update(rep_dict, user, domain, score):
    #     # ensure entry exists
    _ = rep_dict[user][domain]
    if score > 0:
        rep_dict[user][domain]["alpha"] += abs(score)
    elif score < 0:
        rep_dict[user][domain]["beta"] += abs(score)
    # if score == 0, do nothing (already avoided by flooring contribution)

# # ---- Update reputations ----
for idx, row in df2.iterrows():
    for domain in domain_list:
        # Weighted score: contribution * domain probability
        score = row['contribution'] * row[domain]
        bayesian_update(author_reputation, row['noteAuthorId'], domain, score)
        bayesian_update(rater_reputation, row['raterId'], domain, score)

# # ---- Convert dicts to DataFrames ----
def reputation_dict_to_df(rep_dict, domain_list, role_name):
    records = []
    for user, domains in rep_dict.items():
        record = {"user": user}
        for domain in domain_list:
            alpha = domains[domain]["alpha"]
            beta = domains[domain]["beta"]
            record[f"{role_name}_{domain}"] = alpha / (alpha + beta)
        records.append(record)
    return pd.DataFrame(records)

author_rep_df = reputation_dict_to_df(author_reputation, domain_list, "author")
rater_rep_df = reputation_dict_to_df(rater_reputation, domain_list, "rater")

# # Merge author and rater reputations
user_reputation_df = pd.merge(author_rep_df, rater_rep_df, on="user", how="outer").fillna(1.0)

# # Quick sanity check
print(user_reputation_df.head())



from google.colab import drive
drive.mount('/content/drive')
file_path = "/content/drive/MyDrive/user_scores.csv"
# Also get out the validate_df
file_path2 = "/content/drive/MyDrive/validate_df.csv"
# Also get out the train_df
file_path3 = "/content/drive/MyDrive/train_df.csv"

# Load into a DataFrame
user_scores_df = pd.read_csv(file_path)
validate_df = pd.read_csv(file_path2)
train_df = pd.read_csv(file_path3)

user_scores_df = user_scores_df.rename(columns={
    col: col.replace("weighted_", "")
    for col in user_scores_df.columns
    if col.startswith("weighted_")
})

# -----------------------------------------
# STEP 6: Compute Trust Scores and Optimal Threshold
# HI KARTIK!! This actually JUST worked
# -----------------------------------------

import numpy as np
from sklearn.metrics import roc_curve

# -----------------------------------------
# 0. Ensure train_df has 'lockedStatusNorm' for threshold calculation
# -----------------------------------------
# Map train_df lockedStatus to normalized version (binary will be derived later)
train_df['lockedStatusNorm'] = train_df['lockedStatus'].map({
    'CURRENTLY_RATED_HELPFUL': 'HELPFUL',
    'NEEDS_MORE_RATINGS': 'NA',
    'CURRENTLY_RATED_NOT_HELPFUL': 'NOT_HELPFUL'
})

# -----------------------------------------
# 1. Normalize validate_df lockedStatus
# -----------------------------------------
validate_df['lockedStatusNorm'] = validate_df['lockedStatus'].map({
    'CURRENTLY_RATED_HELPFUL': 'HELPFUL',
    'NEEDS_MORE_RATINGS': 'NA',
    'CURRENTLY_RATED_NOT_HELPFUL': 'NOT_HELPFUL'
})

# -----------------------------------------
# 2. Normalize domain probabilities for each note
# -----------------------------------------
# Sum of domains may not equal 1, so we normalize per row
validate_df['prob_vec'] = validate_df[cardiff_labels].div(
    validate_df[cardiff_labels].sum(axis=1), axis=0
).fillna(0).values.tolist()  # fillna(0) handles rows that sum to 0

# -----------------------------------------
# 3. Prepare true labels (binary)
# -----------------------------------------
# 1 = helpful / somewhat helpful, 0 = not helpful
# This ensures a binary choice for ROC calculation
validate_df['label_true'] = validate_df['lockedStatusNorm'].isin(
    ['HELPFUL', 'SOMEWHAT_HELPFUL']
).astype(int)

# -----------------------------------------
# 4. Rebuild user reputation vectors from user_scores_df
# -----------------------------------------
author_vecs = {}
rater_vecs = {}

for idx, row in user_scores_df.iterrows():
    user = row['user']
    # Both author and rater use same user_scores_df columns
    author_vecs[user] = row[cardiff_labels].values.astype(float)
    rater_vecs[user]  = row[cardiff_labels].values.astype(float)

# -----------------------------------------
# 5. Compute trust scores for validation set
# -----------------------------------------
trust_scores = []

for idx, row in validate_df.iterrows():
    # Domain probability vector for this note
    p = np.array(row['prob_vec'], dtype=float)

    author = row['noteAuthorId']
    rater  = row['raterId']

    # Fallback to neutral vector (all 1s) if user not in training
    r_author = author_vecs.get(author, np.ones(len(p)))
    r_rater  = rater_vecs.get(rater,  np.ones(len(p)))

    # Combine author and rater reputations by averaging
    r_combined = (r_author + r_rater) / 2

    # Dot product → trust score
    trust_scores.append(float(np.dot(p, r_combined)))

validate_df['trust_score'] = trust_scores

# -----------------------------------------
# 6. Compute optimal threshold using train_df
# -----------------------------------------
# First, normalize train_df domain probabilities as well
train_df['prob_vec'] = train_df[cardiff_labels].div(
    train_df[cardiff_labels].sum(axis=1), axis=0
).fillna(0).values.tolist()

# Compute binary labels for train_df
y_train = train_df['lockedStatusNorm'].isin(
    ['HELPFUL', 'SOMEWHAT_HELPFUL']
).astype(int)

# Compute trust scores for train_df
scores_train = []
for idx, row in train_df.iterrows():
    p = np.array(row['prob_vec'], dtype=float)
    author = row['noteAuthorId']
    rater  = row['raterId']

    r_author = author_vecs.get(author, np.ones(len(p)))
    r_rater  = rater_vecs.get(rater, np.ones(len(p)))
    r_combined = (r_author + r_rater) / 2
    scores_train.append(float(np.dot(p, r_combined)))

# Compute ROC curve and Youden's J statistic
fpr, tpr, thresholds = roc_curve(y_train, scores_train)
J = tpr - fpr
best_idx = np.argmax(J)
best_threshold = thresholds[best_idx]

print("Optimal threshold (train):", best_threshold)

# Optimal threshold (train): 0.1580888048588657

# STEP 7: Now try on validation
# Apply threshold to predict on validation
# ------------------------------

threshold = 0.1580888048588657

# Apply threshold to compute predicted labels (vectorized)
validate_df["label_pred"] = (validate_df["trust_score"] >= threshold).astype(int)

# ------------------------------
# Compute validation metrics using sklearn (more concise and reliable)
# ------------------------------
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

y_true = validate_df["label_true"]
y_pred = validate_df["label_pred"]

accuracy  = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall    = recall_score(y_true, y_pred)
f1        = f1_score(y_true, y_pred)

print("Validation metrics:")
print(f"Accuracy:  {accuracy:.3f}")
print(f"Precision: {precision:.3f}")
print(f"Recall:    {recall:.3f}")
print(f"F1-score:  {f1:.3f}")
