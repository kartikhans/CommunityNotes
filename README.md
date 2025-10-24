# CommunityNotes

# Reputation Algorithm

This project implements a **reputation scoring algorithm** for evaluating participants' contributions based on their interactions with community notes and ratings.  
Each participant is scored per domain using weighted parameters that capture agreement, helpfulness, and bias tendencies.

---

## 🔍 Overview

The algorithm computes a **reputation score (`R_alpha_d`)** for each participant and domain.  
It uses four key intermediate factors:

- **β_rating (Beta Rating):** Measures the consistency and quality of a participant’s ratings.
- **λ_rating (Lambda Rating):** Reflects how closely a participant’s ratings align with community consensus.
- **β_note (Beta Note):** Evaluates how helpful a participant’s note was, based on community votes.
- **λ_note (Lambda Note):** Measures reliability of a participant’s notes.

The final **contribution score** for each note is:

*Equation to calculate reputation score:*

$$
R_{\alpha,d} = \frac{\sum_{n \in N_d} \beta_{\text{rating}} \, \lambda_{\text{rating}} \, \beta_{\text{note}} \, \lambda_{\text{note}}}{|N_d|}
$$

Calculating $\beta_{\text{rating}}$:

This term denotes the bridging score of the user when rating a note in a domain.
$$
\beta_{\text{rating}} =
\begin{cases}
1, & \text{if user authored the note} \\[6pt]
1, & \text{if lockedStatus} \in \{\text{helpful, somewhat helpful}\} \text{ and rating} = \text{agree} \\[6pt]
1.5, & \text{if lockedStatus} \in \{\text{helpful, somewhat helpful}\} \text{ and rating} = \text{disagree and helpfulnessLevel} \in \{\text{helpful, somewhat helpful}\} \\[6pt]
-1.5, & \text{if lockedStatus} \in \{\text{helpful, somewhat helpful}\} \text{ and rating} = \text{disagree and helpfulnessLevel} = \text{not helpful} \\[6pt]
1, & \text{if lockedStatus} = \text{not helpful and rating} = \text{disagree} \\[6pt]
1.5, & \text{if lockedStatus} = \text{not helpful and rating} = \text{agree and helpfulnessLevel} = \text{not helpful} \\[6pt]
-1.5, & \text{if lockedStatus} = \text{not helpful and rating} = \text{agree and helpfulnessLevel} \in \{\text{helpful, somewhat helpful}\}
\end{cases}
$$

Calculating $\lambda_{\text{rating}}$:

This term denotes the success of the user when rating a note in a domain:

$$
\lambda_{\text{rating}} =
\begin{cases}
1, & \text{if user authored the note} \\[6pt]
1.5, & \text{if } \text{lockedStatus} = \text{helpfulnessLevel} \\[6pt]
1, & \text{otherwise}
\end{cases}
$$

Calculating $\beta_{\text{note}}$:

This term denotes the bridging score of the user when writing a note in a domain.

$$
\beta_{\text{note}} =
\begin{cases}
1.5, & \text{if } \text{lockedStatus} \in \{\text{helpful}, \text{somewhat helpful}\}
\text{ and } \sum(\text{disagree}) > \sum(\text{agree}) \\[2pt]
1, & \text{if } \text{lockedStatus} \in \{\text{helpful}, \text{somewhat helpful}\}
\text{ and } \sum(\text{agree}) \ge \sum(\text{disagree}) \\[2pt]
-1.5, & \text{if } \text{lockedStatus} = \text{not helpful}
\end{cases}
$$

Calculating $\lambda_{\text{note}}$:

This term denotes the success of the user when authoring a note in a domain:

$$
\lambda_{\text{note}} =
\begin{cases}
1.5, & \text{if } \text{lockedStatus} \in \{\text{helpful}, \text{somewhat helpful}\} \\[2pt]
0.5, & \text{if } \text{lockedStatus} = \text{not helpful}
\end{cases}
$$

***EXPLANATION OF LOGIC:***

The proposed reputation model quantifies how effectively a user contributes to informational quality and ideological balance within specific topical domains. Each user’s reputation score by domain captures both their performance when writing notes and their behavior when rating others’ notes, weighted by measures of accuracy, consensus alignment, and bridging quality.

**Scores for rating:**

The Bridging Score for Rating, denoted $\beta_{\text{rating}}$, measures a user’s ideological bridging or bias when rating others’ notes. Positive values of $\beta_{\text{rating}}$ indicate cross-ideological agreement or fair evaluation, whereas negative values reflect biased or ideologically predictable behavior. If the user authored the note, $\beta_{\text{rating}}$ defaults to 1, reflecting the inherent contribution of the note’s author to their own reputation score.

The Correctness Score for Rating, denoted $\lambda_{\text{rating}}$, captures whether the user’s judgment aligns with the final community consensus. If the note’s locked status matches the user’s helpfulness evaluation (i.e., $\text{lockedStatus} = \text{helpfulnessLevel}$), then $\lambda_{\text{rating}} = 1.5$, rewarding accurate evaluation. Otherwise, $\lambda_{\text{rating}} = 1$, ensuring that incorrect ratings do not overly penalize users who may still demonstrate positive bridging behavior. Importantly, when $\beta_{\text{rating}}$ is negative, this value is not attenuated, naturally amplifying penalties for biased or ideologically extreme ratings.



**Scores for writing:**

The choice of these values creates a balance between bridging impact, outcome quality, and penalization for low-quality contributions. For
$\beta_{\text{note}}$, helpful notes that attract more disagree ratings than agree ratings receive a stronger bridging score (1.5) because they demonstrate the author’s capacity to challenge existing viewpoints constructively, fostering cross-ideological dialogue. Helpful notes with majority agreement are assigned a normal bridging score (1), reflecting their alignment with the general consensus but still providing positive contribution. Notes that are ultimately deemed not helpful receive a strongly negative bridging score (-1.5), penalizing content that fails to provide value or introduces bias.

For
$\lambda_{\text{note}}$, helpful notes are amplified with a score of 1.5, reinforcing the positive influence of contributions that successfully guide or inform the community. Notes rated as not helpful are assigned a lower outcome weight (0.5) to reduce their impact and ensure that low-quality or misleading contributions do not distort the user’s reputation. Together, these terms ensure that the overall reputation score
$R_{\alpha,d}$ captures both the quality and bridging nature of contributions in a domain, rewarding users who consistently provide high-value, cross-perspective content while penalizing those whose notes fail to meet community standards.


The **reputation per domain (`R_alpha_d`)** is computed as the average contribution value.

---

## 🧠 Interpretation of Scores

| Score Range | Interpretation |
|--------------|----------------|
| > 1.5 | **Strong positive bridging contributor** |
| 0 ≤ Score ≤ 1.5 | **Helpful, balanced participant** |
| < 0 | **Consistently biased or low-quality contributor** |

---
