# Data model: 004-fira-matching

## `fira_documents`
| Column | Type | Rules |
|---|---|---|
| id | UUID PK | |
| file_name | VARCHAR(255) | sanitised base name |
| file_hash | CHAR(64) UNIQUE | SHA-256 hex (F14) |
| extracted_json | JSONB | validated extraction (or the raw invalid output summary) |
| foreign_amount | NUMERIC(14,2) NULL | > 0 |
| currency | CHAR(3) NULL | |
| inr_amount | NUMERIC(14,2) NULL | |
| rate | NUMERIC(14,6) NULL | |
| remittance_date | DATE NULL | |
| reference_no | VARCHAR(64) NULL | |
| remitter | VARCHAR(200) NULL | data only |
| purpose_code | VARCHAR(8) NULL | |
| status | enum `fira_doc_status`: matched, needs_review, no_match | recomputed |
| score | INT NULL | 0–100 |
| reason | VARCHAR(200) NULL | why needs review / no match |
| validation_reason | VARCHAR(200) NULL | code validation failure (E2/E3); kept across rematches |
| uploaded_at | TIMESTAMPTZ | set by the app; upload order for tie-breaks |
| created_at/updated_at | TIMESTAMPTZ | |

## `fira_matches`
| id | fira_id FK (ON DELETE CASCADE) | transaction_id FK UNIQUE (one FIRA per payment, ON DELETE CASCADE) | match_score INT | kind enum `fira_match_kind` direct/weekly |
Recomputed (delete + insert) on every rematch. `transactions.fira_status` (existing column) is set for
eligible rows and cleared for others.
