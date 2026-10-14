-- Project Lumiere Telegram Bot – Supabase Schema

-- 1. Golden examples (from the original PDF + future verified answers)
CREATE TABLE IF NOT EXISTS golden_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT NOT NULL,                     -- e.g. "Computer Science", "Microelectronics"
    subdomain TEXT,
    title TEXT,
    prompt TEXT NOT NULL,
    step_by_step TEXT NOT NULL,
    final_answer TEXT NOT NULL,
    image_description TEXT,
    failure_type TEXT,
    failure_reason TEXT,
    distractors TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Conversations (every user interaction)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT NOT NULL,
    telegram_chat_id BIGINT NOT NULL,
    message_id BIGINT,
    user_text TEXT,
    has_image BOOLEAN DEFAULT FALSE,
    image_url TEXT,                           -- temporary or permanent storage URL
    bot_reply TEXT,
    model_used TEXT,
    is_verified BOOLEAN DEFAULT FALSE,        -- human marked as correct
    promoted_to_golden BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Simple index for retrieval later
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_golden_domain ON golden_examples(domain);

-- Optional: enable RLS later if you want public read access
-- ALTER TABLE golden_examples ENABLE ROW LEVEL SECURITY;
