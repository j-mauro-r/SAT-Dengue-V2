# DWP adoption record for SAT-Dengue-V2

Status: PASS (DWP v7 installed)
Verification date: 2026-10-14

## Scope

- Repository: SAT-Dengue-V2
- Adopted line: DWP v7
- Previous v6-only block resolved by explicit user decision to install v7.

## Official sources used

- https://deepworkplan.com/spec
- https://deepworkplan.com/changelog
- https://deepworkplan.com/.well-known/dwp-trust.json
- https://github.com/DailybotHQ/deepworkplan-skill/releases
- https://raw.githubusercontent.com/DailybotHQ/deepworkplan-skill/main/docs/INSTALLATION.md
- https://raw.githubusercontent.com/DailybotHQ/deepworkplan-skill/main/CHANGELOG.md

## Exact adopted version

- DWP standard line: v7 (DWP 7.0.0)
- Installed skill pack: v7.8.1
- Lockfile ref: v7.8.1

## Installation method executed

Official pinned command from trust manifest:

- npx --yes skills add https://github.com/DailybotHQ/deepworkplan-skill/tree/v7.8.1 --skill deepworkplan -y

Prerequisites validated before install:

- Node.js available
- npx available

## Verification commands and outcomes

Source/version checks:

- curl -fsSL https://deepworkplan.com/.well-known/dwp-trust.json
- curl -fsSL -H 'Accept: text/markdown' https://deepworkplan.com/spec
- curl -fsSL -H 'Accept: text/markdown' https://deepworkplan.com/changelog

Installed version checks:

- grep -n '^version:' .agents/skills/deepworkplan/SKILL.md
- cat skills-lock.json

Repository wiring checks:

- ls -la .agents/skills
- ls -la .claude/skills
- grep -n '^.dwp/$' .gitignore

Security hygiene checks:

- grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true

## Validation status

- DWP installed correctly: PASS
- Exact installed version is queryable: PASS
- Repository recognizes/configures DWP skill artifacts: PASS
- Initialization errors: UNVERIFIED (onboarding/init flow not executed in this step)
- Unexpected changes outside installation scope: PASS
- Secrets/credentials/temp files added: PASS

## Files that remain versioned

- .agents/skills/deepworkplan/**
- .claude/skills/deepworkplan (symlink to .agents copy)
- skills-lock.json
- docs/governance/dwp.md

## Files that remain ignored

- .dwp/

## Intentionally not executed in this step

- deepworkplan-onboard
- deepworkplan-create
- PITAGORAS-related setup