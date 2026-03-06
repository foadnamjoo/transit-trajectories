# Transit Ops IQ — one-command demo and pipeline
PYTHON ?= python3
PIP = $(PYTHON) -m pip
PORT ?= 8080

.PHONY: demo pipeline serve install test lint

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Run full pipeline only (no server)
pipeline:
	$(PYTHON) python/run_pipeline.py

# Run pipeline then start local static server
demo: pipeline
	@echo "Serving dashboard at http://localhost:$(PORT)"
	$(PYTHON) -m http.server $(PORT)

# Serve only (use prebuilt data/serving for GitHub Pages)
serve:
	@echo "Serving at http://localhost:$(PORT)"
	$(PYTHON) -m http.server $(PORT)

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Lint
lint:
	$(PYTHON) -m py_compile python/*.py 2>/dev/null || true
	$(PYTHON) -m pytest tests/ -v --tb=short
