# Security and Data Boundaries

## Security Baseline

- Never commit credentials, keys, or secret tokens.
- Never expose secrets in logs, reports, screenshots, or PR text.
- Keep sensitive values in secure environment mechanisms when runtime services are introduced.

## Repository-Level Safety

- Run secret-pattern scans before merge.
- Keep `.dwp/` runtime state untracked except approved tracked files.
- Use least-privilege decisions for automation and CI.

## Data Boundaries

Authoritative source: `docs/data/data-policy.md`

- Large datasets are external (Kaggle/local/Colab).
- Sensitive health data must be treated as restricted by default.
- Tiny synthetic fixtures are the preferred repository test data.

## Vulnerability and Incident Handling

- Record material security decisions in versioned docs/ADRs.
- Escalate suspected vulnerabilities through private channels before disclosure.
