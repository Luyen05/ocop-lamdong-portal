-- Apply this once to databases created before the subject application workflow.
BEGIN;

ALTER TABLE subjects
  ADD COLUMN IF NOT EXISTS moderation_note TEXT;

COMMIT;
