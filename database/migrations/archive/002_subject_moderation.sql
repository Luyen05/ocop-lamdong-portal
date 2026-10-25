-- Apply this once to databases created before the subject application workflow.
BEGIN;

ALTER TABLE subjects
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT REFERENCES users(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ck_subjects_review_state'
  ) THEN
    ALTER TABLE subjects ADD CONSTRAINT ck_subjects_review_state CHECK (
      (status = 'pending' AND reviewed_by IS NULL AND reviewed_at IS NULL AND rejection_reason IS NULL)
      OR (status = 'approved' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND rejection_reason IS NULL)
      OR (
        status = 'rejected'
        AND reviewed_by IS NOT NULL
        AND reviewed_at IS NOT NULL
        AND rejection_reason IS NOT NULL
        AND BTRIM(rejection_reason) <> ''
      )
    );
  END IF;
END $$;

COMMIT;
