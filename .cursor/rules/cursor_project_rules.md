# Project Development Rules & Guidelines

## 1. Version Control (Git)

- **Branching:** Feature branches (`feat/`, `fix/`, `refactor/`)
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`)
- **PRs:** Required for `main` merges

## 2. Code Style

- **Python:** PEP 8 + `black` + `flake8`
- **JavaScript:** ESLint + Prettier
- **Comments:** Explain "why" not "what"

## 3. Testing

- **Python:** Pytest (80%+ coverage)
- **React:** Jest + React Testing Library

## 4. Security

- **Secrets:** Never commit `.env`
- **API:** Validate all inputs
- **Auth:** Use CSRF + CORS restrictions

## 5. Documentation

- Update `README.md` for setup changes
- Keep `ARCHITECTURE.md` current
- Document complex logic in code

## 6. Dependencies

- **Python:** Pin in `requirements.txt`
- **NPM:** Use `package-lock.json`
- **Audit:** Run `pip-audit`/`npm audit` monthly

## 7. Error Handling

- Log errors with context
- Return user-friendly messages
- **Monitoring:** (Future) Set up logging pipeline
