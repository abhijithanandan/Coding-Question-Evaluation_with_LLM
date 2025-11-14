# Generic Coding Evaluation (LLM-Agnostic)

This repository provides a provider-agnostic evaluator for coding questions (HPC course). It keeps original scripts untouched and adds a flexible adapter layer so you can choose among OpenAI, Anthropic, Google Gemini, HuggingFace Inference API, or any local OpenAI-compatible endpoint (for example, vLLM or a local llama.cpp server exposing an OpenAI-compatible endpoint).

## Features

- Unified `LLMClient` abstraction with pluggable providers.
- Structured JSON parsing with fallback extraction.
- Dry-run mode that prints a representative payload without calling the API.
- Reuses the existing question spec/template directory layout under `data/`.

## Project layout

- `src/` - Python package with evaluator code, providers and utils.
  - `core/` - provider configuration and manager
  - `providers/` - provider implementations (OpenAI, Google, Anthropic, HuggingFace, local adapters)
  - `utils/` - prompt builders and parse helpers
  - `clients.py` - facade exporting `LLMClient` and `ProviderConfig`
  - `tests/` - unit tests
- `data/` - question specs, starter templates and `submissions_*` directories

## Installation

Install in editable mode from the repository root:

```bash
pip install -e .
```

## Environment variables

Set the relevant keys for the provider you plan to use:

| Provider    | Required variable(s)                | Notes / optional                            |
| ----------- | ----------------------------------- | ------------------------------------------- |
| openai      | `OPENAI_API_KEY`                    | `OPENAI_BASE_URL` for Azure or custom       |
| anthropic   | `ANTHROPIC_API_KEY`                 |                                             |
| google      | `GEMINI_API_KEY`                    |                                             |
| huggingface | `HF_API_KEY`                        |                                             |
| local       | `LOCAL_LLM_BASE_URL` (OpenAI-style) | `LOCAL_LLM_API_KEY` if your server needs it |

## Usage

Run the CLI evaluator for a specific question number (15, 24, 29):

```bash
# Example: run question 15 with Google Gemini (dry-run)
python -m evaluate_coding 15 --provider google --model gemini-2.5-flash --dry-run

# Other examples:
python -m evaluate_coding 24 --provider openai --model gpt-5-2025-08-07
python -m evaluate_coding 29 --provider anthropic --model claude-sonnet-4-5-20250929
```

If you're running a local OpenAI-compatible server (vLLM, etc.):

```bash
export LOCAL_LLM_BASE_URL="http://localhost:8000/v1"
python -m evaluate_coding 15 --provider local --model your-model-name
```

## Output

The evaluator writes a CSV `results_coding_question_<NUM>_generic.csv` with columns:

- `roll_number`
- `marks_cq<NUM>`
- `breakdown_cq<NUM>`

## Notes

- If model responses include extra text, the parser attempts to extract the JSON object (see `src/utils/parse.py`).
- Prompt/system prompt builder is in `src/utils/helpers.py`.
- To change inference settings (temperature, max tokens) edit the `ProviderConfig` passed to `LLMClient` (see `src/core/config.py`).

## Extending providers

Add new provider wiring in `src/core/manager.py` and a provider implementation under `src/providers/`. Keep the facade `clients.py` unchanged so callers continue to import `LLMClient` and `ProviderConfig` the same way.

## Troubleshooting

- If you see parsing errors, inspect the raw model output snippet included in logs and refine the system prompt.
- Ensure you run the CLI from the repository root so `data/` paths resolve correctly.
