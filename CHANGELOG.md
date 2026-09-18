# Changelog

All notable changes to the SportQuant Cryptographic Audit Ledger specification and data schema are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
