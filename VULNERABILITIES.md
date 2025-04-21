# Security Vulnerabilities Report

This document tracks known security vulnerabilities in our dependencies and the plan to address them.

## Package Vulnerabilities

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

## Code Security Issues

### CORS Misconfiguration

#### src/app.py (Flask)

- **Issue**: The Flask application uses wildcard ("_") origins for `/socket.io/_`and`/static/_` routes, and falls back to "_" if `FRONTEND_URL` environment variable is not set for `/api/*` routes.
- **Impact**: Allows any website to make cross-origin requests to these endpoints, potentially leading to Cross-Site Request Forgery (CSRF) attacks or data leakage.
- **Priority**: High
- **Planned Fix**: Will be addressed in Phase 2 when FastAPI fully replaces Flask.

#### src/main.py (FastAPI)

- **Issue**: The FastAPI application configures CORS with `allow_origins=["*"]` (wildcard) and `allow_methods=["*"]`, `allow_headers=["*"]`.
- **Impact**: Same as above, plus the `allow_credentials=True` setting with wildcard origins violates the CORS spec and can lead to serious security issues.
- **Priority**: High
- **Planned Fix**: Implement specific allowed origins in Phase 2 by:
  1. Reading from environment variables (`FRONTEND_URL`, etc.)
  2. Explicitly listing domains instead of using wildcards
  3. Setting appropriate restrictions on methods and headers

### Missing CSRF Protection

- **Issue**: CSRF protection is disabled in Flask app (`app.config['WTF_CSRF_ENABLED'] = False`) and not implemented in FastAPI.
- **Impact**: Without CSRF protection, attackers can potentially trick users into making unwanted state-changing requests.
- **Priority**: Medium
- **Planned Fix**: Implement `starlette-csrf` middleware in Phase 2.

### Input Validation

- **Issue**: Some endpoints do not properly validate input parameters (ad-hoc validation instead of schema-based validation).
- **Impact**: Potential for injection attacks or unexpected behavior.
- **Priority**: Medium
- **Planned Fix**: Implement Pydantic models for request validation in Phase 2.

### JWT Authentication Issues

- **Issue**: JWT authentication appears to be configured but not fully implemented or properly secured.
- **Impact**: Potential for authentication bypass or token vulnerabilities.
- **Priority**: Medium
- **Planned Fix**: Implement proper JWT authentication with secure secret key management in Phase 2.

## Remediation Plan

1. **High Priority (Phase 2)**:

   - Fix CORS configuration by listing specific allowed origins from environment variables
   - Enable CSRF protection using appropriate middleware
   - Implement proper Pydantic request validation

2. **Medium Priority (Phase 2)**:
   - Implement proper JWT authentication with secure key management
   - Ensure secure session handling

See the full implementation plan in Phase 2 (Architecture Unification) of the refactoring plan.

Last Updated: Upon initialization of refactoring project

# Project Vulnerabilities

This document tracks known vulnerabilities identified in the project's dependencies.

## pip-audit Findings (YYYY-MM-DD)

Date: 2024-07-27 (Replace with actual date if different)

Command: `pip-audit`

Found 24 known vulnerabilities in 11 packages:

| Name             | Version | ID                  | Fix Versions | Notes |
| ---------------- | ------- | ------------------- | ------------ | ----- |
| flask            | 2.2.3   | PYSEC-2023-62       | 2.2.5, 2.3.2 |       |
| flask-cors       | 3.0.10  | PYSEC-2024-71       | 4.0.2        |       |
| flask-cors       | 3.0.10  | GHSA-84pr-m4jr-85g5 | 4.0.1        |       |
| flask-cors       | 3.0.10  | GHSA-8vgw-p6qm-5gr7 |              |       |
| flask-cors       | 3.0.10  | GHSA-43qf-4rqw-9q2g |              |       |
| flask-cors       | 3.0.10  | GHSA-7rxf-gvfg-47g4 |              |       |
| gunicorn         | 22.0.0  | GHSA-hc5x-x2vx-497g | 23.0.0       |       |
| jinja2           | 3.1.4   | GHSA-q2x7-8rv6-6q7h | 3.1.5        |       |
| jinja2           | 3.1.4   | GHSA-gmj6-6f8f-6699 | 3.1.5        |       |
| jinja2           | 3.1.4   | GHSA-cpwx-vrp4-4pq7 | 3.1.6        |       |
| python-multipart | 0.0.9   | GHSA-59g5-xgcq-4qw3 | 0.0.18       |       |
| requests         | 2.31.0  | GHSA-9wx4-h78v-vm56 | 2.32.0       |       |
| scikit-learn     | 1.3.0   | PYSEC-2024-110      | 1.5.0        |       |
| starlette        | 0.37.2  | GHSA-f96h-pmfr-66vw | 0.40.0       |       |
| torch            | 2.6.0   | GHSA-3749-ghw9-m3mg |              |       |
| torch            | 2.6.0   | GHSA-887c-mr87-cxwp |              |       |
| transformers     | 4.41.0  | PYSEC-2024-227      | 4.48.0       |       |
| transformers     | 4.41.0  | PYSEC-2024-228      | 4.48.0       |       |
| transformers     | 4.41.0  | PYSEC-2024-229      | 4.48.0       |       |
| transformers     | 4.41.0  | GHSA-6rvg-6v2m-4j46 | 4.48.0       |       |
| werkzeug         | 2.2.3   | PYSEC-2023-221      | 2.3.8, 3.0.1 |       |
| werkzeug         | 2.2.3   | GHSA-2g68-c3qc-8985 | 3.0.3        |       |
| werkzeug         | 2.2.3   | GHSA-f9vj-2wh5-fj8j | 3.0.6        |       |
| werkzeug         | 2.2.3   | GHSA-q34m-jh98-gwm2 | 3.0.6        |       |

**Skipped Dependencies:**

| Name           | Skip Reason                                                                   |
| -------------- | ----------------------------------------------------------------------------- |
| en-core-web-md | Dependency not found on PyPI and could not be audited: en-core-web-md (3.7.1) |
| xx-ent-wiki-sm | Dependency not found on PyPI and could not be audited: xx-ent-wiki-sm (3.7.0) |

**Note:** Remediation of these vulnerabilities is planned for later phases as per `the-plan.mdc`, unless they block critical setup steps.
