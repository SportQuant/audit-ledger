# Changelog

All notable changes to the SportQuant Cryptographic Audit Ledger specification and data schema are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.0] - 2026-11-24 (Matchweek 12 Veritas v2.0 Cutover)

### Added
* **Sport-Agnostic `schema_version: "2.0"` Envelope**: Standardized canonical WORM payload with explicit `schema_version` (`"2.0"`), `sport`, `league`, `commit_window` (`"T-48h"` / `"T-45m"`), and `lineup_confirmed` (`bool`).
* **Cryptographic Model Provenance (`model_provenance`)**: Every commitment and reveal binds `model_version` (`"veritas-v2.0"`), `bundle_id`, and `artifact_sha256` directly into the SHA-256 preimage.
* **Multi-Market Coherent Derivative Locking (`markets`)**: Locks `1x2` (`home_win`, `draw`, `away_win`), `ou_2_5` (`over`, `under`), and `btts` (`yes`, `no`) probability vectors inside the `T-48h` SHA-256 commitment hash, each summing strictly to `1.0000` at 4 decimal places.
* **Structural & Final Intensity Diagnostics (`model_diagnostics`)**: Publishes `distribution_family` (`"dixon_coles_poisson"`), `entropy_score`, and `parameters` (`lambda_home_struct`, `lambda_away_struct`, `lambda_home_final`, `lambda_away_final`, `rho`).

### Changed
* **Upstream Poisson Intensity Residual Stacking**: Replaced v1 post-grid linear probability blending with Stage 2 log-residual intensity stacking ($\hat{\lambda} = \lambda^{\text{struct}} \cdot \exp(\delta^{\text{ML}})$) prior to $10 \times 10$ Dixon-Coles matrix integration.
* **Dual-Schema Verification (`verify_ledger.py`)**: Updated zero-dependency verifier to auto-detect `schema_version` (`"1.0"` vs `"2.0"`), preserving 100% backward-compatible verification across all 110 historical MW1–MW11 commitments.

### Removed
* Dropped deprecated v1 blending keys (`dynamic_alpha`, `physics_anchor`, `ml_ensemble`, `model_telemetry`) from all `schema_version: "2.0"` ledger payloads.

---

## [v1.1.0] - 2026-09-18 (Matchweek 5 Genesis)

### Added
* **Matchweek Subdirectory Partitioning**: Ledger files are organized into matchweek-specific directories (`[league_slug]/[season_year]/mw[XX]/[YYYY-MM-DD]-[home]-vs-[away].json`) for scalable filesystem navigation and deterministic historical batching.
* **Canonical Match ID Format**: Standardized `match_id` internal slug structure `[league_slug]_[year]_[home_team]_[away_team]` (e.g. `epl_2026_brentford_chelsea`) across API payloads and ledger documents.
* **Pure Math Settlement Verification**: Revealed settlements include mathematical grading metrics (`actual_result`, `brier_score`) directly bound to pre-match locked distributions.

### Changed
* **Strict Zero-Knowledge Pre-Match Commitments**: Blind commitment documents contain only cryptographic proof metadata (`status`, `commit_utc`, `sha256_hash`), preventing any pre-match probability or telemetry leakage.
* **Pure Math Baseline Canonical Preimage ($P_{\text{true}}$)**: All external sportsbook reference lines and third-party market contexts are completely purged from the SHA-256 canonical hash preimage. The preimage strictly encapsulates pure quantitative engine outputs and physical model telemetry.
* **Settlement Schema Sanitization**: Post-match public reveal documents strictly isolate pure math grading. External market closing odds and CLV calculations remain exclusively in internal PostgreSQL ledger databases.

### Removed
* External data vendor IDs (`api_...`) purged from public ledger documents.
* Deprecated root-level `market_context`, `reference_odds`, and `market_implied_probabilities` from public ledger JSON structures.

---

## [v1.0.0] - 2026-08-15 (Initial Release - MW1–MW4)
* Initial implementation of the single-file Write Once, Read Many (WORM) cryptographic audit ledger with SHA-256 commitments.
