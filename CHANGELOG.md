# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project tooling: root check scripts, Husky hooks (lint-staged, commitlint, secretlint), file size check, Vitest + MSW, Playwright setup (specs/001-paypal-sync)
- Backend foundation: typed settings with sandbox-only guard, money/date/error/HTTP-retry/rate-limit helpers, `clients` and `transactions` tables, `GET /health` (specs/001-paypal-sync)
- Frontend foundation: shared UI components (Button, Card, Badge, MoneyText, DataGrid, Spinner, EmptyState, ErrorState, Disclaimer), app shell with demo-mode banner, typed API client with zod validation (specs/001-paypal-sync)

### Changed

- `.gitignore`: anchor Python `lib/` rules to the repo root so `frontend/lib/` is tracked; add Node/Next.js patterns
