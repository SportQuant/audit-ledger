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
│  Full Payload       Brier & CLV          Same File Overwrite│
│  + Salt Revealed──► Performance     ───► (Mathematically    │
│                     Scoring              Verifiable)        │
└─────────────────────────────────────────────────────────────┘
```

1. **Phase 1: T-48h Blind Commitment (`COMMITTED`)**
   * Exactly 48 hours prior to match kickoff, our predictive engine formats a canonical JSON payload, injects a 32-byte cryptographic salt, and computes a SHA-256 hash.
   * **Only the SHA-256 hash and match metadata are committed to this repository.** The predicted probabilities and salt remain secret to prevent market leakage.

2. **Phase 2: Post-Match Settlement & Reveal (`REVEALED`)**
   * After the match concludes and scores are finalized, the settlement pipeline rewrites the same file in place.
   * The file is updated to `REVEALED` status, revealing the `salt`, `revealed_probabilities`, full `canonical_payload`, and institutional benchmark metrics (Brier score, closing lines, and Closing Line Value / CLV beat).

---

## 📁 Repository Directory Structure

Ledger records follow a deterministic, single-file pathing structure partitioned by sport/league, season year, and match date:

```plaintext
audit-ledger/
├── epl/
│   └── 2026/
│       ├── 2026-08-21-arsenal-vs-coventry.json
│       ├── 2026-08-22-aston-villa-vs-chelsea.json
│       └── ...
├── ufc/
│   └── 2026/
│       └── ...
└── verify_ledger.py
```

---

## 📄 Ledger Record Schemas

### Phase 1: Pre-Kickoff Blind Commitment (`COMMITTED`)

Pushed to GitHub at **T-48h**. Notice that probabilities are completely hidden:

```json
{
  "status": "COMMITTED",
  "fixture": "Arsenal vs Coventry",
  "match_id": "epl_2026_ars_cov_4f8a12bc",
  "league": "Premier League",
  "kickoff_utc": "2026-08-21T19:00:00+00:00",
  "commit_utc": "2026-08-19T19:00:00.104291+00:00",
  "model_version": "Veritas-v1.0",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Phase 2: Post-Match Settlement & Reveal (`REVEALED`)

Rewritten to the exact same file path post-match:

```json
{
  "status": "REVEALED",
  "fixture": "Arsenal vs Coventry",
  "match_id": "epl_2026_ars_cov_4f8a12bc",
  "league": "Premier League",
  "kickoff_utc": "2026-08-21T19:00:00+00:00",
  "commit_utc": "2026-08-19T19:00:00.104291+00:00",
  "revealed_utc": "2026-08-21T21:05:14.882103+00:00",
  "model_version": "Veritas-v1.0",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "revealed_probabilities": {
    "home_win": 0.6840,
    "draw": 0.1920,
    "away_win": 0.1240
  },
  "salt": "a8f5f167f44f4964e6c998dee827110c",
  "canonical_payload": {
    "away_team": "Coventry",
    "home_team": "Arsenal",
    "kickoff_time": "2026-08-21T19:00:00+00:00",
    "market": "1X2",
    "match_id": "epl_2026_ars_cov_4f8a12bc",
    "model_version": "Veritas-v1.0",
    "probabilities": {
      "away_win": "0.1240",
      "draw": "0.1920",
      "home_win": "0.6840"
    },
    "salt": "a8f5f167f44f4964e6c998dee827110c"
  },
  "settlement": {
    "actual_result": "HOME",
    "brier_score": 0.1521,
    "closing_lines": {
      "away": 7.50,
      "draw": 4.80,
      "home": 1.45
    },
    "clv_beat": true
  }
}
```

---

## 🔍 Independent Cryptographic Verification

Anyone can independently verify the authenticity and timestamp of any prediction without trust assumptions:

1. **Verify Timestamp Integrity (Zero Hindsight Bias)**
   * Click **History** on any ledger file on GitHub or inspect the Git log. The initial `[COMMIT]` commit timestamp on GitHub's immutable servers will be verified &ge; 48 hours before `kickoff_utc`.

2. **Verify Cryptographic Hash (Zero Tampering)**
   * To verify that the revealed probability distribution was truly the one locked in at **T-48h**:
     1. Extract the `canonical_payload` dictionary from the `REVEALED` JSON.
     2. Sort all keys lexicographically and format with compact JSON separators (`separators=(",", ":")`).
     3. Compute the SHA-256 hash. The result will match `sha256_hash` character-for-character.

3. **Automated Single-Command Verification**
   * Run the zero-dependency verification script to audit all entries in the repository:
   ```bash
   python3 verify_ledger.py
   ```

---

## 🛡️ Mathematical Standards

* **Brier Score Calculation**: Multi-class mean squared error:

$$ \text{Brier} = (p_{\text{home}} - y_{\text{home}})^2 + (p_{\text{draw}} - y_{\text{draw}})^2 + (p_{\text{away}} - y_{\text{away}})^2 $$

* **CLV Beat Determination**: Measured against the sharpest market closing odds at kickoff.

---

© 2026 SportQuant. All rights reserved. Cryptographic Audit Protocol.
