# Security Vulnerabilities Report

This document tracks known security vulnerabilities in our dependencies and the plan to address them.

## Current Vulnerabilities

As of the latest `pip-audit` scan on the refactoring process:

| Package          | Version | Vulnerability ID                     | Fix Version  | Priority | Status                                      |
| ---------------- | ------- | ------------------------------------ | ------------ | -------- | ------------------------------------------- |
| flask            | 2.2.3   | PYSEC-2023-62                        | 2.2.5, 2.3.2 | High     | To be removed (replacing with FastAPI)      |
| flask-cors       | 3.0.10  | Multiple (PYSEC-2024-71, etc.)       | 4.0.2        | High     | To be removed (replacing with FastAPI CORS) |
| werkzeug         | 2.2.3   | Multiple                             | 3.0.6        | High     | To be removed (Flask dependency)            |
| jinja2           | 3.1.4   | Multiple (GHSA-q2x7-8rv6-6q7h, etc.) | 3.1.6        | Medium   | Will upgrade in requirements.txt            |
| python-multipart | 0.0.9   | GHSA-59g5-xgcq-4qw3                  | 0.0.18       | Medium   | Will upgrade in requirements.txt            |
| requests         | 2.31.0  | GHSA-9wx4-h78v-vm56                  | 2.32.0       | Medium   | Will upgrade in requirements.txt            |
| gunicorn         | 22.0.0  | GHSA-hc5x-x2vx-497g                  | 23.0.0       | Medium   | Will upgrade in requirements.txt            |
| transformers     | 4.41.0  | Multiple                             | 4.48.0       | Low      | Will upgrade in Phase 4 (NLU enhancements)  |
| torch            | 2.6.0   | Multiple                             | -            | Low      | To be evaluated (no fix version available)  |
| scikit-learn     | 1.3.0   | PYSEC-2024-110                       | 1.5.0        | Low      | Will upgrade in conda environment           |
| starlette        | 0.37.2  | GHSA-f96h-pmfr-66vw                  | 0.40.0       | Low      | Will upgrade in requirements.txt            |

## Remediation Plan

1. **High Priority (Phase 1-2)**:

   - ✅ Flask and related packages will be removed as part of the architecture consolidation
   - ✅ FastAPI and its dependencies will replace them

2. **Medium Priority (Phase 0-1)**:

   - Update remaining vulnerable packages in requirements.txt (jinja2, python-multipart, requests, gunicorn)

3. **Low Priority (Future Phases)**:
   - Update ML-related packages (transformers, torch) during Phase 4 implementation
   - Investigate mitigations for packages without fix versions

## Notes

- Vulnerabilities in Flask ecosystem will be automatically resolved by switching to FastAPI
- We're primarily using scikit-learn from conda, so it will be upgraded in the environment.yml
- Some dependencies with vulnerabilities are deeply nested and may require careful testing after upgrading

Last Updated: Upon initialization of refactoring project
