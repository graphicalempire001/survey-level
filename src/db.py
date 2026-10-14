import os
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_conversation(
    telegram_user_id: int,
    telegram_chat_id: int,
    message_id: Optional[int],
    user_text: Optional[str],
    has_image: bool,
    image_url: Optional[str],
    bot_reply: str,
    model_used: str = "gemini-2.0-flash",
) -> None:
    data = {
        "telegram_user_id": telegram_user_id,
        "telegram_chat_id": telegram_chat_id,
        "message_id": message_id,
        "user_text": user_text,
        "has_image": has_image,
        "image_url": image_url,
        "bot_reply": bot_reply,
        "model_used": model_used,
    }
    supabase.table("conversations").insert(data).execute()


def get_relevant_examples(limit: int = 2) -> List[Dict[str, Any]]:
    """Simple retrieval for now. Later we can add embeddings."""
    response = (
        supabase.table("golden_examples")
        .select("domain, title, prompt, step_by_step, final_answer")
        .limit(limit)
        .execute()
    )
    return response.data or []


def promote_to_golden(conversation_id: str, domain: str, title: str) -> None:
    """Mark a conversation as verified and copy it into golden_examples."""
    # Implementation left for later expansion
    pass


def insert_golden_example(
    domain: str,
    subdomain: Optional[str],
    title: str,
    prompt: str,
    step_by_step: str,
    final_answer: str,
    image_description: Optional[str] = None,
) -> None:
    """Insert a new structured golden example into the knowledge base."""
    data = {
        "domain": domain,
        "subdomain": subdomain,
        "title": title,
        "prompt": prompt,
        "step_by_step": step_by_step,
        "final_answer": final_answer,
        "image_description": image_description,
    }
    supabase.table("golden_examples").insert(data).execute()
