import os
import google.generativeai as genai
from typing import Optional, List
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT, FEW_SHOT_INSTRUCTION
from .db import get_relevant_examples

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the strongest free vision model currently available
MODEL_NAME = "gemini-2.0-flash"   # or "gemini-1.5-flash" / "gemini-2.5-flash" depending on availability


def build_prompt(user_text: str, examples: List[dict]) -> str:
    parts = [SYSTEM_PROMPT, "\n\n", FEW_SHOT_INSTRUCTION, "\n\n"]

    for i, ex in enumerate(examples, 1):
        parts.append(f"=== GOLDEN EXAMPLE {i} ({ex.get('domain', 'General')}) ===\n")
        parts.append(f"Prompt:\n{ex.get('prompt', '')}\n\n")
        parts.append(f"Step-by-step solution:\n{ex.get('step_by_step', '')}\n\n")
        parts.append(f"Final Answer: {ex.get('final_answer', '')}\n\n")

    parts.append("=== NEW USER QUESTION ===\n")
    parts.append(user_text or "(Image only – please analyse the attached image carefully)")
    return "".join(parts)


async def ask_gemini(
    user_text: Optional[str],
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
) -> str:
    examples = get_relevant_examples(limit=2)
    prompt = build_prompt(user_text or "", examples)

    model = genai.GenerativeModel(MODEL_NAME)

    content = [prompt]

    if image_bytes:
        content.append({
            "mime_type": mime_type,
            "data": image_bytes
        })

    response = model.generate_content(
        content,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,          # low temperature for precise technical answers
            max_output_tokens=4096,
        )
    )

    return response.text
