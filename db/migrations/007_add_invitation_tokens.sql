-- Add invitation token fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS invitation_token VARCHAR,
ADD COLUMN IF NOT EXISTS invitation_expires TIMESTAMP WITH TIME ZONE;

-- Add index for faster token lookups
CREATE INDEX IF NOT EXISTS idx_users_invitation_token ON users(invitation_token);
