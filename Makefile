# Egypt Chatbot - Development Makefile
# This Makefile provides convenient shortcuts for common development tasks

.PHONY: help setup setup-dev clean test test-unit test-integration test-load
.PHONY: lint format type-check security-check
.PHONY: dev run build deploy-local
.PHONY: docs docs-diagrams docs-serve
.PHONY: profile profile-cpu profile-memory trace-requests
.PHONY: db-setup db-migrate db-seed db-backup db-restore
.PHONY: logs logs-follow logs-errors
.PHONY: coverage coverage-html coverage-report

# Default target
help: ## Show this help message
	@echo "Egypt Chatbot - Development Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup-dev    # Set up development environment"
	@echo "  make dev          # Start development server"
	@echo "  make test         # Run all tests"
	@echo ""

# Environment setup
setup: ## Set up basic environment
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # On macOS/Linux"
	@echo "  venv\\Scripts\\activate     # On Windows"

setup-dev: ## Set up development environment with all dependencies
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "✅ Development environment set up!"
	@echo "Run 'make dev' to start the development server"

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "✅ Cleaned up temporary files"

# Development server
dev: ## Start development server with hot reload
	@echo "🚀 Starting development server..."
	@echo "Access the application at: http://localhost:8000"
	@echo "API docs available at: http://localhost:8000/docs"
	python run_chatbot.py --debug --reload

run: ## Start production server
	@echo "🚀 Starting production server..."
	python run_chatbot.py

# Docker operations
build: ## Build Docker image
	docker-compose build

deploy-local: ## Deploy locally with Docker Compose
	docker-compose up --build -d
	@echo "✅ Application deployed locally"
	@echo "Access at: http://localhost:8000"

stop: ## Stop local deployment
	docker-compose down
	@echo "✅ Local deployment stopped"

# Testing
test: ## Run all tests
	@echo "🧪 Running all tests..."
	pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	pytest tests/integration/ -v

test-load: ## Run load tests
	@echo "🧪 Running load tests..."
	@echo "Make sure the application is running (make dev or make deploy-local)"
	locust -f tests/load/locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 30s

test-watch: ## Run tests in watch mode
	@echo "🧪 Running tests in watch mode..."
	pytest-watch tests/ -- -v

# Code quality
lint: ## Run all linting tools
	@echo "🔍 Running linting tools..."
	flake8 src/ tests/
	pylint src/ tests/
	@echo "✅ Linting complete"

format: ## Format code with Black and isort
	@echo "🎨 Formatting code..."
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "✅ Code formatted"

type-check: ## Run type checking with mypy
	@echo "🔍 Running type checking..."
	mypy src/
	@echo "✅ Type checking complete"

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r src/
	safety check
	@echo "✅ Security checks complete"

quality: lint type-check security-check ## Run all code quality checks

# Coverage
coverage: ## Run tests with coverage
	@echo "📊 Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=term-missing

coverage-html: ## Generate HTML coverage report
	@echo "📊 Generating HTML coverage report..."
	pytest tests/ --cov=src --cov-report=html
	@echo "✅ Coverage report generated: htmlcov/index.html"

coverage-report: coverage-html ## Generate and open coverage report
	@if command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	else \
		echo "Coverage report generated: htmlcov/index.html"; \
	fi

# Performance profiling
profile: profile-cpu profile-memory ## Run all performance profiling

profile-cpu: ## Run CPU profiling
	@echo "⚡ Running CPU profiling..."
	python scripts/cpu_profiler.py --message-count 100
	@echo "✅ CPU profiling complete"

profile-memory: ## Run memory profiling
	@echo "💾 Running memory profiling..."
	python scripts/memory_profiler.py --iterations 200
	@echo "✅ Memory profiling complete"

trace-requests: ## Trace request flow (demo mode)
	@echo "🔍 Tracing request flow..."
	python scripts/request_tracer.py --demo-mode --output-dir traces/$(shell date +%Y%m%d_%H%M%S)
	@echo "✅ Request tracing complete - check traces/ directory"

# Database operations
db-setup: ## Set up database with Docker
	@echo "🗄️  Setting up database..."
	docker-compose up postgres -d
	sleep 5
	@echo "✅ Database is running"

db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	python scripts/run_migrations.py
	@echo "✅ Migrations complete"

db-seed: ## Seed database with sample data
	@echo "🗄️  Seeding database..."
	python scripts/seed_database.py
	@echo "✅ Database seeded"

db-backup: ## Backup database
	@echo "🗄️  Creating database backup..."
	mkdir -p backups
	docker-compose exec postgres pg_dump -U postgres chatbot > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

db-restore: ## Restore database from backup (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify BACKUP_FILE=path/to/backup.sql"; \
		exit 1; \
	fi
	@echo "🗄️  Restoring database from $(BACKUP_FILE)..."
	docker-compose exec postgres psql -U postgres chatbot < $(BACKUP_FILE)
	@echo "✅ Database restored"

db-shell: ## Open database shell
	docker-compose exec postgres psql -U postgres chatbot

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "⚠️  This will destroy all database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down postgres; \
		docker-compose rm -f postgres; \
		docker volume rm egypt-chatbot-wind-cursor_postgres_data 2>/dev/null || true; \
		docker-compose up postgres -d; \
		echo "✅ Database reset complete"; \
	else \
		echo "Database reset cancelled"; \
	fi

# Documentation
docs: ## Generate all documentation
	@echo "📚 Generating documentation..."
	python scripts/generate_diagrams.py --output-dir docs/diagrams
	@echo "✅ Documentation generated"

docs-diagrams: ## Generate architectural diagrams
	@echo "🎨 Generating architectural diagrams..."
	python scripts/generate_diagrams.py --output-dir docs/diagrams --format png
	@echo "✅ Diagrams generated in docs/diagrams/"

docs-serve: ## Serve documentation locally
	@echo "📚 Starting documentation server..."
	@if command -v python3 >/dev/null 2>&1; then \
		cd docs && python3 -m http.server 8080; \
	else \
		cd docs && python -m http.server 8080; \
	fi

# Logging and monitoring
logs: ## View application logs
	docker-compose logs chatbot

logs-follow: ## Follow application logs in real-time
	docker-compose logs -f chatbot

logs-errors: ## View only error logs
	docker-compose logs chatbot | grep ERROR

logs-tail: ## View last 100 log entries
	docker-compose logs --tail=100 chatbot

# Debugging
debug: ## Start application in debug mode
	@echo "🐛 Starting application in debug mode..."
	@echo "Debugger will be available on port 5678"
	python run_chatbot.py --debug --debugger

debug-test: ## Run specific test in debug mode
	@if [ -z "$(TEST)" ]; then \
		echo "❌ Please specify TEST=path/to/test.py::test_function"; \
		exit 1; \
	fi
	@echo "🐛 Running test in debug mode: $(TEST)"
	pytest $(TEST) -v -s --pdb

# Deployment helpers
check-deps: ## Check for outdated dependencies
	@echo "📦 Checking for outdated dependencies..."
	pip list --outdated

update-deps: ## Update dependencies (be careful!)
	@echo "📦 Updating dependencies..."
	pip-review --auto
	@echo "⚠️  Don't forget to test after updating dependencies!"

freeze-deps: ## Freeze current dependencies
	@echo "📦 Freezing dependencies..."
	pip freeze > requirements.txt
	@echo "✅ Dependencies frozen to requirements.txt"

# Installation verification
verify-install: ## Verify installation is working
	@echo "✅ Verifying installation..."
	@python -c "import src.main; print('✅ Main module imports successfully')" 2>/dev/null || echo "❌ Failed to import main module"
	@python -c "import src.chatbot; print('✅ Chatbot module imports successfully')" 2>/dev/null || echo "❌ Failed to import chatbot module"
	@python -c "import pytest; print('✅ Pytest is available')" 2>/dev/null || echo "❌ Pytest not available"
	@python -c "import black; print('✅ Black is available')" 2>/dev/null || echo "❌ Black not available"
	@docker --version >/dev/null 2>&1 && echo "✅ Docker is available" || echo "❌ Docker not available"
	@docker-compose --version >/dev/null 2>&1 && echo "✅ Docker Compose is available" || echo "❌ Docker Compose not available"

# CI/CD helpers
ci-test: ## Run tests as they would run in CI
	@echo "🚀 Running CI-style tests..."
	pytest tests/ -v --tb=short --cov=src --cov-report=xml --cov-report=term

ci-quality: ## Run quality checks as they would run in CI
	@echo "🚀 Running CI-style quality checks..."
	black --check src/ tests/ scripts/
	isort --check-only src/ tests/ scripts/
	flake8 src/ tests/
	mypy src/
	bandit -r src/

# Examples and demos
demo: ## Run interactive demo
	@echo "🎭 Starting interactive demo..."
	python scripts/demo.py

example-request: ## Send example request to running server
	@echo "📡 Sending example request..."
	curl -X POST "http://localhost:8000/api/v1/chat" \
		-H "Content-Type: application/json" \
		-d '{"message": "What are the best restaurants in Cairo?", "session_id": "demo_session"}' \
		| python -m json.tool

# Development workflow helpers
start: setup-dev db-setup dev ## Complete setup and start development (one command)

reset: clean db-reset ## Clean everything and reset database

status: ## Show status of all services
	@echo "📊 Service Status:"
	@echo "=================="
	@docker-compose ps 2>/dev/null || echo "Docker Compose not running"
	@echo ""
	@echo "🌐 Application:"
	@curl -s http://localhost:8000/health 2>/dev/null | python -m json.tool 2>/dev/null || echo "Application not responding"

# Full workflow commands
full-test: clean test coverage-html lint type-check security-check ## Run complete test suite with quality checks

full-profile: profile trace-requests docs-diagrams ## Run complete performance analysis

# Help for specific workflows
help-setup: ## Show setup help
	@echo "🏗️  Setup Workflow:"
	@echo "=================="
	@echo "1. make setup          # Create virtual environment"
	@echo "2. source venv/bin/activate  # Activate environment (Linux/macOS)"
	@echo "3. make setup-dev      # Install development dependencies"
	@echo "4. make db-setup       # Start database"
	@echo "5. make dev            # Start development server"
	@echo ""
	@echo "Or use the shortcut: make start"

help-testing: ## Show testing help
	@echo "🧪 Testing Workflow:"
	@echo "==================="
	@echo "make test              # Run all tests"
	@echo "make test-unit         # Run only unit tests"
	@echo "make test-integration  # Run only integration tests"
	@echo "make test-load         # Run load tests"
	@echo "make coverage-html     # Generate coverage report"
	@echo "make test-watch        # Run tests in watch mode"

help-debugging: ## Show debugging help
	@echo "🐛 Debugging Workflow:"
	@echo "======================"
	@echo "make debug             # Start with debugger"
	@echo "make logs-follow       # Follow logs in real-time"
	@echo "make logs-errors       # View error logs"
	@echo "make trace-requests    # Trace request flow"
	@echo "make profile           # Profile performance"
