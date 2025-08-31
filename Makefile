.PHONY: install dev build test lint clean help dashboard

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development server"
	@echo "  build       - Build for production"
	@echo "  test        - Run all tests"
	@echo "  lint        - Run linter"
	@echo "  clean       - Clean build artifacts"
	@echo "  setup       - Initial project setup"
	@echo "  dashboard   - Start Streamlit dashboard"

# Install dependencies
install:
	poetry install

setup:
	poetry install

# Start development server
dev:
	npm run dev

# Build for production
build:
	npm run build

# Run tests
test:
	poetry run pytest tests/ -m "not integration and not e2e"

# All tests (fast)
ci:
	poetry run pytest tests/ -m "not e2e"

# E2E validation (dry-run with Google Ads)
e2e-validate:
	ENABLE_REAL_MUTATES=0 poetry run pytest tests/ -m e2e

# Run linter
lint:
	poetry run ruff check src/ tests/

# Lint and typecheck
check:
	poetry run ruff check src/ tests/
	poetry run black --check src/ tests/
	poetry run mypy src/

# Clean build artifacts
clean:
	rm -rf dist/
	rm -rf node_modules/
	rm -rf coverage/

# Initial setup
setup: install
	@echo "Setting up Google Ads AI application..."
	@echo "1. Copy .env.example to .env and fill in your API credentials"
	@echo "2. Set up PostgreSQL database"
	@echo "3. Run 'make db-setup' to initialize database"
	@echo "4. Run 'make dev' to start development server"

# Database operations
db-setup:
	npm run db:migrate
	npm run db:seed

db-reset:
	npm run db:reset
	npm run db:migrate
	npm run db:seed

# Testing variants
test-watch:
	npm run test:watch

test-coverage:
	npm run test:coverage

test-integration:
	npm run test:integration

# Linting variants
lint-fix:
	npm run lint:fix

type-check:
	npm run type-check

# Development utilities
logs:
	tail -f logs/app.log

# Docker operations
docker-build:
	docker build -t ai-adwords .

docker-run:
	docker run -p 3000:3000 ai-adwords

# Production deployment
deploy:
	npm run build
	npm run db:migrate
	npm start

# Start Streamlit dashboard
dashboard:
	PYTHONPATH=/Users/joelhorwitz/dev/ai-adwords poetry run streamlit run src/dashboard/app.py
