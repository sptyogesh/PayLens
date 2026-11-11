# Data model: 003-ask-your-money

## New table `chat_messages`
| Column | Type | Rules |
|---|---|---|
| id | UUID PK | |
| role | enum `chat_role` (`user`, `assistant`) | |
| content | TEXT | ≤ 4000 chars stored |
| outcome | VARCHAR(16) NULL | assistant only: answered / no_data / fallback |
| created_at | TIMESTAMPTZ | server default now() |

Write-only log (FR-011). No reads in Phase 1A.

## Named periods (`app/common/periods.py`)
`this_month`, `last_month`, `last_3_months`, `this_quarter`, `last_quarter`, `this_financial_year`,
`last_financial_year`, `all_time`; or explicit `start`/`end` dates (IST, inclusive). Half-open UTC
ranges; label includes the dates, e.g. "Last quarter (1 Jul 2026 – 30 Sep 2026)".
