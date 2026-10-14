# Security

## Baseline Posture

- Never commit secrets, credentials, or private keys.
- Never include tokens in logs, reports, or screenshots.
- Keep sensitive values in environment variables or secret stores once runtime components are introduced.

## Agent Rules

- Do not print secret values in command outputs.
- Do not create credential files in repository paths.
- Do not bypass validation or security review gates.

## Data Governance

- Treat dataset-level personally identifiable information as sensitive by default.
- Document anonymization and access controls before ingesting production datasets.

## Vulnerability Handling

- Use private disclosure channels for third-party skill vulnerabilities.
- Record security-relevant decisions in versioned documentation.
