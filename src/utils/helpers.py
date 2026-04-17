from __future__ import annotations
import os
import re
from typing import List


def discover_roll_numbers(submissions_dir: str, file_ext: str) -> List[str]:
    """Scan the submissions directory and extract unique roll-number
    prefixes from filenames.

    This is course-agnostic: it derives roll numbers from whatever
    files are present rather than relying on hardcoded patterns.
    """
    if not os.path.isdir(submissions_dir):
        return []
    roll_numbers = set()
    for fname in os.listdir(submissions_dir):
        if not fname.lower().endswith(file_ext):
            continue
        # Strip the file extension to get the roll number identifier
        roll = os.path.splitext(fname)[0]
        roll_numbers.add(roll.lower())
    return sorted(roll_numbers)


def get_coding_system_prompt(
    question_text: str, template_text: str, max_score: float, tech_hint: str
) -> str:
    """Construct the system prompt used to instruct the model for a
    coding evaluation.

    Keeping it here makes the large multiline template easier to test
    and reuse.
    """
    return f"""
You are an expert AI examiner for a university-level coding exam. Evaluate a student's code submission against the problem specification.

Specification (authoritative):
---
{question_text}
---

Starter template (structure and mark allocation guidance):
---
{template_text}
---

Important context:
- Target technology: {tech_hint}.
- There is no execution environment. Judge by reading code: intent, structure, correctness vs. spec, API usage, and reasoned plausibility.
- Be generous with partial credit. Do not penalize style, grammar, or minor formatting. Minor errors or small omissions should not zero-out marks.
- The template contains TODO comments with mark allocations (e.g., "TODO 1: ... (3 Marks)"). Use these as the primary rubric to distribute marks.

Evaluation guidelines (out of {max_score} total):
- Award marks for each TODO section based on the marks indicated in the template comments.
- For each TODO, evaluate whether the student's code correctly addresses the requirement.
- If the student's approach is partially correct or shows understanding of the concept, award proportional partial credit.
- If the template does not contain explicit per-TODO mark allocations, distribute {max_score} marks holistically across: correctness, API usage, completeness, and code structure.

Instructions:
- Carefully read the student's submission.
- Compare against the spec and template.
- Provide a final score and a concise, point-by-point breakdown referencing each TODO or requirement.
- Your response MUST be a single, valid JSON object. Do not include any other text or code fences.
- Be generous. Award partial credit where intent/structure is correct, even if incomplete.

JSON Output Format:
{{
  "score": <float between 0 and {max_score}>,
  "breakdown": "<string explanation>"
}}

Evaluate the following student's code:
"""
