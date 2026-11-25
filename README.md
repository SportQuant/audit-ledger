# SportQuant Cryptographic Audit Ledger

[![Ledger Status: Active](https://img.shields.io/badge/Ledger-Active-00E599?style=flat-square)](https://sportquant.ai)
[![Protocol: Zero--Knowledge Commit--Reveal](https://img.shields.io/badge/Protocol-Commit--Reveal-0070F3?style=flat-square)](https://sportquant.ai)
[![Integrity: SHA--256 Immutable](https://img.shields.io/badge/Integrity-SHA--256-7928CA?style=flat-square)](https://sportquant.ai)

This repository serves as the official, public audit ledger for **[SportQuant](https://sportquant.ai)**. It provides cryptographic, mathematically irrefutable proof that our quantitative predictions and probability distributions are generated and locked prior to kickoff—guaranteeing **zero hindsight bias**, **zero retroactive tampering**, and **zero pre-match market leakage**.

---

## 🏛️ The Zero-Knowledge Commit-Reveal Protocol

To protect live trading alpha for active institutional subscribers while offering total transparency to historical auditors, SportQuant operates a strict two-stage **Commit-Reveal Protocol**:

```
┌─────────────────────────────────────────────────────────────┐
│                PHASE 1: T-48h BLIND COMMIT                  │
│                                                             │
│  Proprietary        Deterministic        Public Git Commit  │
│  Model Output  ───► SHA-256 Hash    ───► (Probabilities     │
│  + 32-byte Salt     Computation          REDACTED)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ Kickoff & Match Settlement
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PHASE 2: POST-MATCH REVEAL                  │
│                                                             │
│  Full Payload       Pure-Math Brier      Same File Overwrite│
│  + Salt Revealed──► Performance     ───► (Mathematically    │
│                     Scoring              Verifiable)        │
└─────────────────────────────────────────────────────────────┘
```

1. **Phase 1: T-48h Blind Commitment (`COMMITTED`)**
   * Exactly 48 hours prior to match kickoff, our predictive engine formats a canonical JSON payload, injects a 32-byte cryptographic salt, and computes a SHA-256 hash.
   * **Only the SHA-256 hash and commit timestamp are committed to this repository.** The predicted probabilities, derivative markets, and salt remain secret to prevent market leakage.

2. **Phase 2: Post-Match Settlement & Reveal (`REVEALED`)**
   * After the match concludes and scores are finalized, the settlement pipeline rewrites the same file in place.
   * The file is updated to `REVEALED` status, revealing the `salt`, full `canonical_payload` (`model_provenance`, multi-market `1x2` / `ou_2_5` / `btts` probabilities, and `model_diagnostics`), and pure math grading metrics (`actual_result`, `brier_score`).

---

## 📁 Repository Directory Structure

Ledger records follow a deterministic, matchweek-partitioned structure by sport/league, season year, and matchweek:

```plaintext
audit-ledger/
├── epl/
│   └── 2026/
│       ├── mw05/
│       │   ├── 2026-09-18-brentford-vs-chelsea.json
│       │   └── ...
│       ├── mw12/
│       │   ├── 2026-11-26-arsenal-vs-chelsea.json
│       │   └── ...
│       └── ...
├── CHANGELOG.md
├── LEDGER_README.md
└── verify_ledger.py
```

---

## 📄 Ledger Record Schemas (`schema_version: "2.0"` — Veritas v2.0)

### Phase 1: Pre-Kickoff Blind Commitment (`COMMITTED`)

Pushed to GitHub at **T-48h**. Contains strictly zero model probabilities or market data:

```json
{
  "status": "COMMITTED",
  "commit_utc": "2026-11-24T20:00:00Z",
  "sha256_hash": "9c41f27d8b53a04917e649c0e83a1120f729d8b4c63a159f02d18e447109ab32"
}
```

### Phase 2: Post-Match Settlement & Reveal (`REVEALED`)

Rewritten to the exact same file path post-match:

```json
{
  "status": "REVEALED",
  "commit_utc": "2026-11-24T20:00:00Z",
  "revealed_utc": "2026-11-26T22:05:14Z",
  "sha256_hash": "9c41f27d8b53a04917e649c0e83a1120f729d8b4c63a159f02d18e447109ab32",
  "canonical_payload": {
    "schema_version": "2.0",
    "sport": "soccer",
    "league": "epl",
    "match_id": "epl_2026_arsenal_chelsea",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "kickoff_utc": "2026-11-26T20:00:00Z",
    "commit_window": "T-48h",
    "lineup_confirmed": false,
    "model_provenance": {
      "model_version": "veritas-v2.0",
      "bundle_id": "v20261124_0044-VERITAS-V2-SOCCER-EN_EPL",
      "artifact_sha256": "18eb6bd4dbba186d7f743cd3f465478e9804f9891f6f11d2f08dd8211f747d6f"
    },
    "markets": {
      "1x2": {
        "home_win": 0.4820,
        "draw": 0.2590,
        "away_win": 0.2590
      },
      "ou_2_5": {
        "over": 0.5410,
        "under": 0.4590
      },
      "btts": {
        "yes": 0.5680,
        "no": 0.4320
      }
    },
    "model_diagnostics": {
      "distribution_family": "dixon_coles_poisson",
      "entropy_score": 0.9614,
      "parameters": {
        "lambda_home_struct": 1.5200,
        "lambda_away_struct": 1.1400,
        "lambda_home_final": 1.5840,
        "lambda_away_final": 1.1120,
        "rho": -0.0405
      }
    },
    "salt": "a8f5f167f44f4964e6c998dee827110c9b120e4a87d63190f45c82e1093ab412"
  },
  "settlement": {
    "actual_result": "HOME",
    "brier_score": 0.4025
  }
}
```

> **Post-Match Auditability vs. Live API Tier Gating:** The canonical `"2.0"` WORM ledger payload hashes the complete `model_diagnostics` block (`distribution_family: "dixon_coles_poisson"`, `entropy_score`, and `parameters`: `lambda_home_struct`, `lambda_away_struct`, `lambda_home_final`, `lambda_away_final`, `rho`) at `T-48h`—publishing only the blind `sha256_hash` pre-kickoff—and reveals the full `parameters` dictionary post-match at Full-Time (`REVEALED`) for complete mathematical verification. On the live pre-match B2B API (`/v1/predictions`), `model_diagnostics.parameters` is gated to **Pro (`$499/mo`)** and **Desk (`$999/mo`)** tiers and omitted on the **Starter (`$149/mo`)** tier (which returns `markets` alongside `distribution_family` and `entropy_score`).
>
> **Backward Compatibility (`schema_version: "1.0"`):** Historical MW1–MW11 ledger records generated under `veritas-v1.0` and `veritas-v1.1` remain permanently locked in their original `schema_version: "1.0"` format (`probabilities` + `model_telemetry`) and are automatically detected and verified by `verify_ledger.py`.

---

## 🔍 Independent Cryptographic Verification

Anyone can independently verify the authenticity and timestamp of any prediction without trust assumptions:

1. **Verify Timestamp Integrity (Zero Hindsight Bias)**
   * Click **History** on any ledger file on GitHub or inspect the Git log. The initial `[COMMIT]` commit timestamp on GitHub's immutable servers will be verified &ge; 48 hours before `kickoff_utc`.

2. **Verify Cryptographic Hash (Zero Tampering)**
   * To verify that the revealed probability distribution was truly the one locked in at **T-48h**:
     1. Extract the `canonical_payload` dictionary from the `REVEALED` JSON.
     2. Format all floating-point numbers to 4 decimal places (`"{:.4f}"`), sort all keys lexicographically, and serialize with compact JSON separators (`separators=(",", ":")`).
     3. Compute the SHA-256 hash. The result will match `sha256_hash` character-for-character.

3. **Automated Single-Command Verification**
   * Run the zero-dependency verification script (auto-detecting `schema_version: "1.0"` and `"2.0"`) to audit all entries in the repository:
   ```bash
   python3 verify_ledger.py
   ```

---

## 🛡️ Mathematical Standards

* **Upstream Poisson Intensity Residual Stacking (Veritas v2.0)**:
  Stage 1 structural club latent ratings produce baseline goal intensities $(\lambda_H^{\text{struct}}, \lambda_A^{\text{struct}})$. Stage 2 out-of-fold continuous Poisson ensembles apply bounded second-order log-residual refinements ($\delta^{\text{ML}} \in [-0.35, +0.35]$):

$$ \hat{\lambda}_H = \lambda_H^{\text{struct}} \cdot \exp(\delta_H^{\text{ML}}), \quad \hat{\lambda}_A = \lambda_A^{\text{struct}} \cdot \exp(\delta_A^{\text{ML}}) $$

* **Coherent $10 \times 10$ Dixon-Coles Derivative Slicing**:
  All locked markets (`1x2`, `ou_2_5`, `btts`) are analytically integrated from the single normalized $10 \times 10$ bivariate Dixon-Coles joint score matrix $M(\hat{\lambda}_H, \hat{\lambda}_A, \rho)$ with zero post-grid probability blending.

* **Brier Score Calculation**: Multi-class mean squared error:

$$ \text{Brier} = (p_{\text{home}} - y_{\text{home}})^2 + (p_{\text{draw}} - y_{\text{draw}})^2 + (p_{\text{away}} - y_{\text{away}})^2 $$

---

© 2026 SportQuant. All rights reserved. Cryptographic Audit Protocol.
