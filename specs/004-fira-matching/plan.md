# Implementation Plan: FIRA Matching

**Branch**: `001-paypal-sync` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Summary
Upload → validate file (type, size, hash) → LLM extraction (PDF document input, strict JSON schema) →
Pydantic + code validation → store → global rematch with a pure engine (`engine/fira_match/`) →
`fira_status` on transactions. FIRA page + grid badge column + `fira_status` chat tool. ReportLab script
generates sample FIRAs; fake LLM reads their embedded truth.

## Technical Context
No new dependency beyond the approved `reportlab` (generator only). Tables `fira_documents`,
`fira_matches`. Upload is a raw `application/pdf` body per file (python-multipart is not installed; no new install).

## Constitution Check
| # | Principle | Compliance | ✓ |
|---|---|---|---|
| I | Scope | S1, after M1–M3 | ✓ |
| II | Code computes | Scores, statuses, counts from the pure engine; LLM only extracts | ✓ |
| III | Money | Decimals; 1% tolerance in Decimal; currency on every amount | ✓ |
| IV | Types | Strict extraction schema + Pydantic; invalid output rejected/needs review | ✓ |
| V | Verify | F1–F14, E1–E6, E7/E8 E2E, U6, U10 | ✓ |
| VI | Security | PDF-only, 5 MB, hash dedupe, no file kept, document text is data (E5), rate limit | ✓ |
| VII | Honest | Sample FIRAs labelled "Demo sample" in the PDF; badges | ✓ |
| IX | AI | Same wrapper, timeout, fallback; prompt file `prompts/fira_extract.md` | ✓ |
| X–XIX | Simplicity, reuse, size, constants, changelog, hooks, approvals | per plan, no commits in run | ✓ |

## Reusable Parts
Used: LLM wrapper, `rate_limit`, `Badge` (has fira variants), `DataGrid`, `MoneyText`, `StatCard`,
`ErrorState`, `useApi`, chat tool registry, `leakage_query` eligibility, seed rows. New: `components/ui/FileUpload`
(constitution building block; U10), `engine/fira_match/` (score, match, weekly).

## File Split Plan
| Parent | Children | Entry |
|---|---|---|
| `engine/fira_match/__init__.py` | `types.py`, `score.py`, `match.py`, `weekly.py` | `__init__` |
| `services/fira_service.py` (upload coordinator) | `ai/fira_extract.py`, `services/fira_rematch.py` | module |
| `frontend/features/fira/FiraView.tsx` | `FiraUpload.tsx`, `FiraList/{FiraList,FiraRow}`, `FiraSummary.tsx`, `useFira.ts` | `index.ts` |

Parallel subagents: A engine + tests; B backend extraction/upload/routes/model/generator/fake; C frontend.
New constants: FIRA scores 60/25/15, thresholds 80/50, tolerance 1%, window 7 days, `FIRA_MAX_BYTES` 5 MB,
`FIRA_MAX_FILES` 10, `RATE_LIMIT_FIRA`, samples dir.
