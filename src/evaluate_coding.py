import os
import argparse
import pandas as pd
import json
import logging
from pydantic import ValidationError
from schemas import CodingEvaluation
from tqdm import tqdm
import concurrent.futures
from dotenv import load_dotenv

from clients import LLMClient, ProviderConfig

logger = logging.getLogger(__name__)
from utils.helpers import (
    generate_student_roll_numbers,
    get_coding_system_prompt,
)

# Load .env if present
load_dotenv()

_module_dir = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(_module_dir, "..", "data"))

# Load question map from data/question_map.json (no fallback)
_question_map_path = os.path.join(DATA_DIR, "question_map.json")
if not os.path.exists(_question_map_path):
    logger.error("Question map file not found at '%s'", _question_map_path)
    raise FileNotFoundError(f"Question map file not found: {_question_map_path}")
with open(_question_map_path, "r", encoding="utf-8") as _f:
    _raw_map = json.load(_f)
# JSON keys are strings; convert to ints for code expectations
QUESTION_MAP = {int(k): v for k, v in _raw_map.items()}


def main():
    parser = argparse.ArgumentParser(description="Generic LLM coding evaluator")
    parser.add_argument(
        "question_number", type=int, help="Question number (e.g., 15, 24, 29)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="google",
        choices=["openai", "anthropic", "google", "huggingface", "local"],
        help="LLM provider",
    )
    parser.add_argument(
        "--model", type=str, default="gemini-2.5-flash", help="Model name"
    )
    parser.add_argument("--max-score", type=float, default=10.0)
    parser.add_argument("--dry-run", action="store_true", help="Print payload and exit")
    parser.add_argument(
        "--single-file", type=str, default=None, help="Path to a single submission file"
    )
    parser.add_argument(
        "--out", type=str, default=None, help="Output CSV path (optional)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker threads to evaluate students in parallel (default: 4)",
    )
    args = parser.parse_args()

    qnum = args.question_number
    if qnum not in QUESTION_MAP:
        logger.error(
            "Unsupported question number %s. Supported: %s",
            qnum,
            list(QUESTION_MAP.keys()),
        )
        return
    cfgq = QUESTION_MAP[qnum]

    spec_file = cfgq["spec_file"]
    template_file = cfgq["template_file"]
    submissions_dir = cfgq["submissions_dir"]
    file_ext = cfgq["ext"].lower()
    tech_hint = cfgq["tech_hint"]
    output_csv = args.out or f"results_coding_question_{qnum}_generic.csv"

    # Resolve spec/template/submissions under DATA_DIR when relative
    if not os.path.isabs(spec_file):
        spec_file = os.path.join(DATA_DIR, spec_file)
    if not os.path.isabs(template_file):
        template_file = os.path.join(DATA_DIR, template_file)
    if not os.path.isabs(submissions_dir):
        submissions_dir = os.path.join(DATA_DIR, submissions_dir)

    if not os.path.exists(spec_file):
        logger.error("Question spec not found at '%s'", spec_file)
        return
    if not os.path.exists(template_file):
        logger.error("Starter template not found at '%s'", template_file)
        return
    if args.single_file is None and not os.path.isdir(submissions_dir):
        logger.error("Submissions directory not found at '%s'", submissions_dir)
        return

    with open(spec_file, "r", encoding="utf-8") as f:
        question_text = f.read()
    with open(template_file, "r", encoding="utf-8") as f:
        template_text = f.read()

    system_prompt = get_coding_system_prompt(
        question_text, template_text, args.max_score, tech_hint
    )

    provider_cfg = ProviderConfig(
        provider=args.provider,
        model=args.model,
        temperature=0.0,
        max_output_tokens=1024,
        # Pass the Pydantic class itself so the client can use it
        # with SDK parse helpers (structured outputs / text_format).
        json_schema=CodingEvaluation,
    )
    try:
        client = LLMClient.from_env(provider_cfg)
    except Exception as e:
        logger.error("Error initializing provider '%s': %s", args.provider, e)
        return

    # If the client discovered a requests-per-minute limit, print an advisory
    rpm = getattr(client, "_rpm", 0)
    if rpm:
        est_lat = float(os.getenv("LLM_ESTIMATED_LATENCY_SEC", "30"))
        recommended_workers = max(1, int((rpm / 60.0) * est_lat))
        logger.info(
            "Provider RPM limit detected: %s RPM. Estimated latency: %ss.", rpm, est_lat
        )
        logger.info(
            "Recommended workers to approach full utilization: %s. You set --workers=%s.",
            recommended_workers,
            args.workers,
        )

    results = []

    def evaluate_student_code(student_code: str):
        if not student_code.strip():
            return {"score": 0.0, "breakdown": "Submission was empty."}
        if args.dry_run:
            payload_preview = {
                "provider": args.provider,
                "model": args.model,
                "system_prompt": system_prompt[:400]
                + ("..." if len(system_prompt) > 400 else ""),
                "student_code_sample": student_code[:400]
                + ("..." if len(student_code) > 400 else ""),
            }
            logger.info(json.dumps(payload_preview, indent=2, ensure_ascii=False))
            return None
        data = client.generate_json(
            system_prompt,
            f"Student Submission:\n---\n{student_code}\n---",
            schema=CodingEvaluation,
        )
        try:
            if isinstance(data, dict) and "score" in data and "breakdown" in data:
                parsed = CodingEvaluation.model_validate(data)
                return {"score": float(parsed.score), "breakdown": parsed.breakdown}
        except ValidationError:
            pass
        return {
            "score": 0.0,
            "breakdown": f"Could not parse model output. Raw: {str(data)[:300]}",
        }

    if args.single_file:
        file_path = args.single_file
        # If single-file provided as a relative name, prefer DATA_DIR first
        if not os.path.isabs(file_path):
            candidate = os.path.join(DATA_DIR, file_path)
            if os.path.exists(candidate):
                file_path = candidate
        if not os.path.exists(file_path):
            logger.error("single-file path '%s' does not exist.", file_path)
            return
        with open(file_path, "r", encoding="utf-8") as f:
            student_code = f.read()
        evaluation = evaluate_student_code(student_code)
        if evaluation is None:
            return
        results.append(
            {
                "roll_number": os.path.basename(file_path),
                f"marks_cq{qnum}": evaluation["score"],
                f"breakdown_cq{qnum}": evaluation["breakdown"],
            }
        )
    else:
        all_roll_numbers = generate_student_roll_numbers()
        logger.info(
            "Processing %d students with %d workers...",
            len(all_roll_numbers),
            args.workers,
        )

        # Per-student processing: evaluate all submissions for a student sequentially
        def process_student(roll_no: str):
            try:
                submission_files = [
                    f
                    for f in os.listdir(submissions_dir)
                    if f.lower().startswith(roll_no.lower())
                    and f.lower().endswith(file_ext)
                ]
            except FileNotFoundError:
                submission_files = []
            best_score = -1.0
            best_eval = {"score": 0.0, "breakdown": "Not Attempted"}
            for submission_file in submission_files:
                file_path = os.path.join(submissions_dir, submission_file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        student_code = f.read()
                except Exception as e:
                    logger.warning(
                        "Could not read file %s. Skipping. Error: %s", file_path, e
                    )
                    continue
                evaluation = evaluate_student_code(student_code)
                if evaluation is None:
                    # dry-run prints one preview and exits early
                    return None
                try:
                    score_val = float(evaluation.get("score", 0.0))
                except Exception:
                    score_val = 0.0
                if score_val > best_score:
                    best_score = score_val
                    best_eval = evaluation

            return {
                "roll_number": roll_no,
                f"marks_cq{qnum}": best_eval["score"],
                f"breakdown_cq{qnum}": best_eval["breakdown"],
            }

        # Use ThreadPoolExecutor to evaluate multiple students concurrently.
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_student, rn): rn for rn in all_roll_numbers}
            with tqdm(total=len(all_roll_numbers), desc="Evaluating Students") as pbar:
                for fut in concurrent.futures.as_completed(futures):
                    rn = futures[fut]
                    try:
                        item = fut.result()
                    except Exception as e:
                        logger.exception("Error evaluating student %s: %s", rn, e)
                        item = {
                            "roll_number": rn,
                            f"marks_cq{qnum}": 0.0,
                            f"breakdown_cq{qnum}": f"Error: {e}",
                        }
                    if item is None:
                        # dry-run; process exited early
                        return
                    results.append(item)
                    pbar.update(1)

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    logger.info("Evaluation complete for Question %s.", qnum)
    logger.info("Results saved to '%s'.", output_csv)


if __name__ == "__main__":
    # Configure logging for CLI usage
    import logging as _logging

    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s: %(message)s")
    main()
