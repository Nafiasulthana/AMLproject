import numpy as np
import pandas as pd


def generate_synthetic_aml_dataset(n_samples: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic AML transactions for training.

    Design note: earlier versions of this generator sampled the suspicious/
    normal label FIRST and then drew every feature from a label-conditional
    distribution. That makes the label mathematically recoverable from the
    generator's own lookup tables, so a classifier trained on it is really
    just learning to reconstruct the generator rather than a genuine
    feature -> risk relationship (this is why the old model reported a
    suspiciously perfect ROC-AUC of ~0.996 with zero false positives).

    This version reverses the causality to match how labels would actually
    be produced in the real world:
      1. Every raw feature is sampled from a distribution that does NOT know
         the label (amount, network position, retention ratio, etc. are all
         drawn independently of `is_aml_suspicious`).
      2. The rule-trigger flags (structuring, smurfing, layering, round-trip)
         are derived deterministically FROM those features, the same way a
         real rules engine would compute them from a transaction/graph
         snapshot -- not sampled independently of the numbers they claim to
         describe.
      3. The label is drawn from Bernoulli(sigmoid(weighted risk score +
         noise)), i.e. suspicious activity is *likely* when several signals
         line up but is never a deterministic function of them. This keeps
         real classes overlapping (irreducible Bayes error) so metrics can't
         hit 100% and a model has to actually learn feature importance
         instead of memorizing the generator.
    """
    rng = np.random.default_rng(seed)

    # ---- 1. Label-agnostic feature sampling --------------------------------
    # Heavy-tailed transaction amount shared by every transaction (no label lookahead).
    amount = rng.lognormal(mean=9.9, sigma=1.45, size=n_samples) + 400.0
    amount = np.clip(amount, 100.0, 2_000_000.0)

    # Simulated per-customer historical baseline -> a genuinely *derived* z-score,
    # rather than an independently sampled number.
    cust_avg = rng.lognormal(mean=9.3, sigma=0.8, size=n_samples) + 300.0
    cust_std = np.maximum(cust_avg * rng.uniform(0.15, 0.6, size=n_samples), 1.0)
    z_score_amount = np.clip((amount - cust_avg) / cust_std, -3.0, 8.0)

    degree_centrality = rng.poisson(lam=4.2, size=n_samples)
    hop_count = rng.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.42, 0.28, 0.16, 0.09, 0.05])

    # Betweenness centrality is structurally correlated with degree/hop depth in a
    # real transaction graph, plus noise -- not an independent random draw.
    structural = (degree_centrality / 12.0) + (hop_count / 8.0)
    betweenness_centrality = np.clip(
        rng.beta(a=2.0, b=5.0, size=n_samples) * 0.6
        + structural * 0.4
        + rng.normal(0, 0.03, n_samples),
        0.0, 1.0,
    )

    money_retention_ratio = np.clip(rng.beta(a=3.0, b=3.0, size=n_samples), 0.0, 1.0)

    # ---- 2. Rule-trigger flags derived FROM the sampled features -----------
    # CTR-evasion band: amounts deliberately kept just under a reporting threshold.
    structuring_flag = ((amount >= 400_000) & (amount < 500_000)).astype(int)
    # Funds cycle back quickly with little retained -> round-tripping.
    round_trip_flag = (
        (money_retention_ratio < 0.22) & (hop_count <= 2) & (rng.random(n_samples) < 0.75)
    ).astype(int)
    # Many counterparties, individually small amounts -> smurfing.
    smurfing_flag = (
        (degree_centrality >= 7) & (amount < 60_000) & (rng.random(n_samples) < 0.7)
    ).astype(int)
    # Long, high-betweenness pass-through chains -> layering.
    layering_flag = (
        (hop_count >= 3) & (betweenness_centrality > 0.35) & (rng.random(n_samples) < 0.7)
    ).astype(int)
    # Dormant-account reactivation is an independent real-world signal (not derivable
    # from the other simulated features here), so it stays a weak base-rate draw.
    dormant_flag = (rng.random(n_samples) < 0.05).astype(int)

    # ---- 3. Latent risk score -> noisy Bernoulli label ----------------------
    # Weights are deliberately imperfect predictors (irreducible overlap between
    # classes) so the resulting dataset is learnable but not trivially separable.
    logit = (
        1.55 * (z_score_amount / 3.0)
        + 1.35 * (1.0 - money_retention_ratio)
        + 1.30 * betweenness_centrality
        + 0.55 * (hop_count / 5.0)
        + 0.35 * (degree_centrality / 10.0)
        + 1.9 * structuring_flag
        + 1.7 * layering_flag
        + 2.1 * round_trip_flag
        + 1.4 * dormant_flag
        + 1.6 * smurfing_flag
        - 7.0  # bias tuned so ~15% of transactions end up suspicious, matching real AML base rates
        + rng.normal(0, 0.65, n_samples)  # irreducible label noise
    )
    p_suspicious = 1.0 / (1.0 + np.exp(-logit))
    is_suspicious = (rng.random(n_samples) < p_suspicious).astype(int)

    df = pd.DataFrame({
        "amount": np.round(amount, 2),
        "z_score_amount": np.round(z_score_amount, 2),
        "degree_centrality": degree_centrality.astype(int),
        "betweenness_centrality": np.round(betweenness_centrality, 3),
        "money_retention_ratio": np.round(money_retention_ratio, 2),
        "hop_count": hop_count.astype(int),
        "structuring_flag": structuring_flag,
        "layering_flag": layering_flag,
        "round_trip_flag": round_trip_flag,
        "dormant_flag": dormant_flag,
        "smurfing_flag": smurfing_flag,
        "is_aml_suspicious": is_suspicious,
    })

    return df


if __name__ == "__main__":
    df = generate_synthetic_aml_dataset()
    df.to_csv("ml/synthetic_aml_transactions.csv", index=False)
    print(f"Generated {len(df)} synthetic AML transactions with realistic noise.")
