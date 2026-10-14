"""
Admin knowledge ingestion: PDF → structured golden example → Supabase
"""

import os
import io
from typing import Optional, Tuple
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
from .db import insert_golden_example

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.0-flash"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def structure_pdf_with_gemini(raw_text: str, topic: str) -> dict:
    """
    Ask Gemini to turn the raw PDF text into a clean golden-example structure.
    """
    prompt = f"""You are a knowledge curator for the Project Lumiere system.

The user uploaded a PDF belonging to the topic/domain: **{topic}**

Here is the extracted text from the PDF:

---
{raw_text[:120000]}
---

Your task:
1. Create a clear, self-contained **Prompt** (the question or problem statement).
2. Write a detailed **Step-by-step solution** in the same rigorous style used in Project Lumiere golden examples.
3. Extract or formulate the **Final Answer**.
4. If the document contains useful image descriptions, include them.
5. Give a short **Title**.

Return the result in exactly this JSON format (no markdown, no extra text):

{{
  "title": "...",
  "prompt": "...",
  "step_by_step": "...",
  "final_answer": "...",
  "image_description": "..." 
}}
"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )

    import json
    return json.loads(response.text)


def ingest_pdf(
    pdf_bytes: bytes,
    topic: str,
    subdomain: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Full pipeline: extract → structure → save to Supabase.
    Returns (success, message)
    """
    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
        if not raw_text.strip():
            return False, "Could not extract any text from the PDF."

        structured = structure_pdf_with_gemini(raw_text, topic)

        insert_golden_example(
            domain=topic,
            subdomain=subdomain,
            title=structured.get("title", "Untitled"),
            prompt=structured.get("prompt", ""),
            step_by_step=structured.get("step_by_step", ""),
            final_answer=structured.get("final_answer", ""),
            image_description=structured.get("image_description"),
        )

        return True, f"✅ Successfully added knowledge under topic **{topic}**\nTitle: {structured.get('title')}"

    except Exception as e:
        return False, f"❌ Failed to ingest PDF: {str(e)}"
