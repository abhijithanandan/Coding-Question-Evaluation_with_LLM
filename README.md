# Generic Coding Evaluation (LLM-Agnostic)

This repository provides a course-agnostic, provider-agnostic evaluator for coding questions. It uses LLMs to read student code submissions and award partial marks based on the question specification and template-defined rubric. You can choose among OpenAI, Anthropic, Google Gemini, HuggingFace Inference API, or any local OpenAI-compatible endpoint.

## Features

- Unified `LLMClient` abstraction with pluggable providers.
- Structured JSON parsing with fallback extraction.
- Dry-run mode that prints a representative payload without calling the API.
- Per-question `max_score` defined in `question_map.json`; mark allocations derived from template TODO comments.
- Auto-discovers student roll numbers from submission filenames (no hardcoding needed).
- Reuses the existing question spec/template directory layout under `data/`.

## Project layout

- `src/` - Python package with evaluator code, providers and utils.
  - `core/` - provider configuration and manager
  - `providers/` - provider implementations (OpenAI, Google, Anthropic, HuggingFace, local adapters)
  - `utils/` - prompt builders and parse helpers
  - `clients.py` - facade exporting `LLMClient` and `ProviderConfig`
  - `tests/` - unit tests
- `data/` - question specs, starter templates, `question_map.json`, and `Submissions_*` directories

## Installation

Install in editable mode from the repository root:

```bash
pip install -e .
```

## Environment variables

Copy `.env.example` to `.env` and set the relevant keys for the provider you plan to use:

| Provider    | Required variable(s)                | Notes / optional                            |
| ----------- | ----------------------------------- | ------------------------------------------- |
| openai      | `OPENAI_API_KEY`                    | `OPENAI_BASE_URL` for Azure or custom       |
| anthropic   | `ANTHROPIC_API_KEY`                 |                                             |
| google      | `GEMINI_API_KEY`                    |                                             |
| huggingface | `HF_API_KEY`                        |                                             |
| local       | `LOCAL_LLM_BASE_URL` (OpenAI-style) | `LOCAL_LLM_API_KEY` if your server needs it |

## Preparing data for a new course

1. Create `Question_<N>.md` files with the problem specification.
2. Create `Template_<N>.py` (or other extension) with starter code including `# TODO` comments and mark allocations (e.g., `(3 Marks)`).
3. Place student submissions in `Submissions_<N>/` directories, named by roll number (e.g., `student001.py`).
4. Edit `data/question_map.json` to register each question with its spec, template, submissions directory, file extension, technology hint, and `max_score`.

## Usage

Run the CLI evaluator for a question number defined in `question_map.json`:

```bash
# Dry-run to preview the prompt (no API call)
python -m evaluate_coding 17 --provider google --model gemini-2.5-flash --dry-run

# Run evaluation with OpenAI
python -m evaluate_coding 17 --provider openai --model gpt-5.4
python -m evaluate_coding 18 --provider openai --model gpt-5.4-mini

# Run evaluation with Google Gemini
python -m evaluate_coding 17 --provider google --model gemini-2.5-flash

# Run evaluation with Anthropic
python -m evaluate_coding 18 --provider anthropic --model claude-sonnet-4-5-20250929
```

If you're running a local OpenAI-compatible server (vLLM, etc.):

```bash
export LOCAL_LLM_BASE_URL="http://localhost:8000/v1"
python -m evaluate_coding 17 --provider local --model your-model-name
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
