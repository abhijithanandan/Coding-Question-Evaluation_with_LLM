from __future__ import annotations
from typing import List


def generate_student_roll_numbers() -> List[str]:
    """Generate expected student roll-number identifiers used by the
    dataset. Kept as a helper so the evaluator remains focused on
    orchestration.
    """
    batch1 = [f"cb.ai.u4aid23{str(i).zfill(3)}" for i in range(1, 70)]
    batch2 = [f"cb.ai.u4aid23{str(i).zfill(3)}" for i in range(101, 168)]
    return sorted(batch1 + batch2)


def get_coding_system_prompt(
    question_text: str, template_text: str, max_score: float, tech_hint: str
) -> str:
    """Construct the system prompt used to instruct the model for a
    coding evaluation.

    Keeping it here makes the large multiline template easier to test
    and reuse.
    """
    return f"""
You are an expert AI examiner for a university-level HPC/systems course. Evaluate a student's code submission against the problem specification.

Specification (authoritative):
---
{question_text}
---

Starter template (function signatures/structure guidance):
---
{template_text}
---

Important context:
- Target technology: {tech_hint}.
- There is no execution. Judge by reading code: intent, structure, correctness vs. spec, parallelism usage, and reasoned plausibility.
- Be generous with partial credit. Do not penalize style/grammar. Minor errors or small omissions should not zero-out marks.

Evaluation rubric (out of {max_score} total):
1. Problem correctness and core logic: 0–4
   - Implements the required algorithm aligned with the spec; reasonable handling of inputs/outputs.
2. Parallel/concurrency construct usage and correctness: 0–2
   - Appropriate API usage (e.g., {tech_hint}); plausible synchronization/reduction; avoids common pitfalls.
3. Completeness and edge cases: 0–1
   - Handles typical edge cases or mentions assumptions; basic error checks (headers, main/signatures).
4. Efficiency and complexity: 0–1
   - Reasonable complexity; uses parallel constructs efficiently (e.g., avoiding obvious bottlenecks).
5. Code structure and readability: 0–1
   - Clear structure, meaningful variable names, comments where non-trivial.
6. Compilability and API correctness by inspection: 0–1
   - Includes required headers, signatures, pragma/launch/configuration plausibility; no fatal API misuse.

Instructions:
- Carefully read the student's submission.
- Compare against the spec and template.
- Provide a final score and a concise, point-by-point breakdown referencing the rubric.
- Your response MUST be a single, valid JSON object. Do not include any other text or code fences.
- Be generous. Award partial credit where intent/structure is correct, even if incomplete.

JSON Output Format:
{{
  "score": <float between 0 and {max_score}>,
  "breakdown": "<string explanation>"
}}

Evaluate the following student's code:
"""
