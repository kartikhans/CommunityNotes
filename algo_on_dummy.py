import pandas as pd
from dummy_data import DummyData


def interpret_score(val):
    if val > 1.5:
        return "Strong positive bridging contributor"
    elif val < 0:
        return "Consistently biased or low-quality contributor"
    else:
        return "Helpful, balanced participant"

# Functions to compute scores
def compute_beta_rating(row):
    if row['participantId_note'] == row['participantId_rating']:
        return 1
    if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful']:
        if row['agree'] == 1:
            return 1
        if row['agree'] == 0 and row['helpfulnessLevel'] in ['helpful', 'somewhat helpful']:
            return 1.5
        if row['agree'] == 0 and row['helpfulnessLevel'] == 'not helpful':
            return -1.5
    if row['lockedStatusNorm'] == 'not helpful':
        if row['agree'] == 0:
            return 1
        if row['agree'] == 1 and row['helpfulnessLevel'] == 'not helpful':
            return 1.5
        if row['agree'] == 1 and row['helpfulnessLevel'] in ['helpful', 'somewhat helpful']:
            return -1.5
    return 0

def compute_lambda_rating(row):
    if row['participantId_note'] == row['participantId_rating']:
        return 1
    return 1.5 if row['lockedStatusNorm'] == row['helpfulnessLevel'] else 1

def compute_beta_note(row):
    if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful']:
        if row['disagree'] > row['agree']:
            return 1.5
        else:
            return 1
    if row['lockedStatusNorm'] == 'not helpful':
        return -1.5

def compute_lambda_note(row):
    return 1.5 if row['lockedStatusNorm'] in ['helpful', 'somewhat helpful'] else 0.5

class ReputationAlgo:
    def __init__(self, data):
        self.df = pd.DataFrame(data)

    def apply_algo(self, user_id=None):

        self.df['lockedStatusNorm'] = self.df['lockedStatus'].map({
            'currently rated helpful': 'helpful',
            'currently rated somewhat helpful': 'somewhat helpful',
            'currently rated not helpful': 'not helpful'
        })

        self.df['beta_rating'] = self.df.apply(compute_beta_rating, axis=1)
        self.df['lambda_rating'] = self.df.apply(compute_lambda_rating, axis=1)
        self.df['beta_note'] = self.df.apply(compute_beta_note, axis=1)
        self.df['lambda_note'] = self.df.apply(compute_lambda_note, axis=1)

        # Filter for a single participant (here we have user 1)
        if user_id is not None:
            df_user = self.df[self.df['participantId_note'] == user_id].copy()

        # Compute contribution for each note
        df_user['contribution'] = (
                df_user['beta_rating'] * df_user['lambda_rating'] * df_user['beta_note'] * df_user['lambda_note']
        )

        # Compute R_alpha_d per domain
        R_alpha_d = df_user.groupby('domain')['contribution'].mean().reset_index()
        R_alpha_d.rename(columns={'contribution': 'R_alpha_d'}, inplace=True)
        R_alpha_d['Interpretation'] = R_alpha_d['R_alpha_d'].apply(interpret_score)

        return R_alpha_d

if __name__ == '__main__':
    k = DummyData()
    k.get_data_ready()
    m = ReputationAlgo(k.data)
    print("The reputation score of User 1 for 15 different domains")
    print(m.apply_algo("user_1"))
