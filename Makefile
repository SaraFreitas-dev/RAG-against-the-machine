export PATH := $(HOME)/.local/bin:$(PATH)

# Store cache
GOINFRE := $(firstword $(wildcard /goinfre/$(USER) $(HOME)/goinfre))

ifneq ($(GOINFRE),)
export UV_CACHE_DIR := $(GOINFRE)/.cache/uv
export HF_HOME := $(GOINFRE)/.cache/huggingface
endif

VENV := .venv
ifneq ($(filter /mnt/%,$(CURDIR)),)
VENV := $(HOME)/.venvs/$(notdir $(CURDIR))
export UV_PROJECT_ENVIRONMENT := $(VENV)
endif

all: install run

# INSTALL ALL REQUIREMENTS
install:
	@if command -v uv >/dev/null 2>&1; then \
		echo "✅ uv is already installed ($$(uv --version))"; \
	else \
		echo "📦 uv not found. Installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	@echo "📦 Syncing dependencies..."
	@uv sync
	@echo "✅ Dependencies ready"

# RUN THE PROGRAM
run:
	uv run python -m src


# DEBUG
debug:
	uv run python -m pdb -m src

# CHECK FOR NORM ERRORS
lint:
	@echo "🔍 Running flake8 and mypy..."
	uv run flake8 .
	uv run mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs
	@echo "✅ Lint completed"

lint-strict:
	@echo "🧠 Running strict checks..."
	uv run flake8 .
	uv run mypy . --strict
	@echo "✅ Strict lint completed"

# CLEANERS
reset-index:
	@echo "🗑️ Removing generated index..."
	@rm -rf data/processed/*

clean:
	@echo "\n🧹 Cleaning cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@rm -rf .mypy_cache .pytest_cache .ruff_cache
	@echo "\n✅ Cache cleaning complete\n"

fclean: clean
	@echo "\n🧹 Cleaning generated output..."
	@rm -rf data/output/*
	@echo "💣 Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "\n✅ Full clean complete\n"

# HELP - LIST OF COMMANDS
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║                      RAG — Help                      ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  1) ⚙️  Project commands"
	@echo "  2) 🔎 RAG CLI commands"
	@echo "  3) 🚀 Quick start"
	@echo "  q) ❌ Exit"
	@echo ""
	@printf "Choose an option: "; \
	read choice; \
	case $$choice in \
		1) \
			echo ""; \
			echo "╔════════════════════════════════════════════════════════════════════╗"; \
			echo "║                       RAG — Make Commands                          ║"; \
			echo "╚════════════════════════════════════════════════════════════════════╝"; \
			echo ""; \
			echo "⚙️  PROJECT SETUP"; \
			echo ""; \
			echo "📦 make install"; \
			echo "   Install uv and sync project dependencies."; \
			echo ""; \
			echo "▶️  make run"; \
			echo "   Run the RAG application."; \
			echo ""; \
			echo "🐞 make debug"; \
			echo "   Run with Python's pdb debugger."; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "🧪 CODE QUALITY"; \
			echo ""; \
			echo "✅ make lint"; \
			echo "   Run flake8 and mypy."; \
			echo ""; \
			echo "🧠 make lint-strict"; \
			echo "   Run strict code checks."; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "🧹 CLEANING"; \
			echo ""; \
			echo "🧹 make clean"; \
			echo "   Remove cache files."; \
			echo ""; \
			echo "🗑️  make reset-index"; \
			echo "   Remove the generated retrieval index."; \
			echo ""; \
			echo "💣 make fclean"; \
			echo "   Remove caches, outputs and virtual environment."; \
			echo ""; \
			echo "🔁 make re"; \
			echo "   Clean and reinstall the project."; \
			echo ""; \
			;; \
		2) \
			echo ""; \
			echo "╔════════════════════════════════════════════════════════════════════╗"; \
			echo "║                         RAG CLI Commands                           ║"; \
			echo "╚════════════════════════════════════════════════════════════════════╝"; \
			echo ""; \
			echo "All CLI commands follow:"; \
			echo ""; \
			echo "  uv run python -m src <command> [options]"; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "📚 INDEX — Build the searchable codebase index"; \
			echo ""; \
			echo "  index --max_chunk_size <int>"; \
			echo ""; \
			echo "  Reads the corpus under data/raw/, splits files into chunks,"; \
			echo "  builds the retrieval index and saves it under data/processed/."; \
			echo ""; \
			echo "  Example:"; \
			echo "    uv run python -m src index --max_chunk_size 2000"; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "🔎 SEARCH — Search a single question"; \
			echo ""; \
			echo "  search <query> --k <int>"; \
			echo ""; \
			echo "  Retrieves the top-k most relevant source chunks for one query."; \
			echo ""; \
			echo "  Example:"; \
			echo '    uv run python -m src search "How is LoRA configured?" --k 5'; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "📋 SEARCH DATASET — Search multiple questions"; \
			echo ""; \
			echo "  search_dataset --dataset_path <path> --k <int>"; \
			echo "                 --save_directory <dir>"; \
			echo ""; \
			echo "  Runs retrieval over every question in a JSON dataset"; \
			echo "  and saves the generated search results."; \
			echo ""; \
			echo "  Example:"; \
			echo "    uv run python -m src search_dataset"; \
			echo "      --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json"; \
			echo "      --k 10"; \
			echo "      --save_directory data/output/search_results/UnansweredQuestions"; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "💬 ANSWER — Answer a single question"; \
			echo ""; \
			echo "  answer <query> --k <int>"; \
			echo ""; \
			echo "  Retrieves relevant sources and uses Qwen to generate"; \
			echo "  a grounded natural-language answer."; \
			echo ""; \
			echo "  Example:"; \
			echo '    uv run python -m src answer "How is LoRA configured?" --k 5'; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "🤖 ANSWER DATASET — Generate answers for a dataset"; \
			echo ""; \
			echo "  answer_dataset --student_search_results_path <path>"; \
			echo "                 --save_directory <dir>"; \
			echo ""; \
			echo "  Generates answers from a previously created search-results file"; \
			echo "  and saves the resulting dataset."; \
			echo ""; \
			echo "  Example:"; \
			echo "    uv run python -m src answer_dataset"; \
			echo "      --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json"; \
			echo "      --save_directory data/output/search_results_and_answer/UnansweredQuestions"; \
			echo ""; \
			echo "────────────────────────────────────────────────────────────────────"; \
			echo ""; \
			echo "📊 EVALUATE — Measure retrieval quality"; \
			echo ""; \
			echo "  evaluate --student_search_results_path <path>"; \
			echo "           --dataset_path <path>"; \
			echo ""; \
			echo "  Calculates recall@k against a ground-truth dataset"; \
			echo "  for local testing."; \
			echo ""; \
			echo "  Example:"; \
			echo "    uv run python -m src evaluate"; \
			echo "      --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json"; \
			echo "      --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json"; \
			echo ""; \
			;; \
		3) \
			echo ""; \
			echo "╔══════════════════════════════════════════════════════╗"; \
			echo "║                      Quick Start                     ║"; \
			echo "╚══════════════════════════════════════════════════════╝"; \
			echo ""; \
			echo "1. Install dependencies:"; \
			echo "   make install"; \
			echo ""; \
			echo "2. Build the index:"; \
			echo "   uv run python -m src index --max_chunk_size 2000"; \
			echo ""; \
			echo "3. Search the codebase:"; \
			echo '   uv run python -m src search "your question" --k 5'; \
			echo ""; \
			echo "4. Generate an answer:"; \
			echo '   uv run python -m src answer "your question" --k 5'; \
			echo ""; \
			;; \
		q|Q) \
			echo ""; \
			echo "Bye!"; \
			;; \
		*) \
			echo ""; \
			echo "❌ Invalid option."; \
			;; \
	esac

re: fclean install

.PHONY: all install run debug help lint lint-strict reset-index clean fclean re