-- This SQL script updates the SQLite database to add
-- new columns to the job configuration table.
-- Backing up the database is recommended before
-- running this script.

BEGIN TRANSACTION;

ALTER TABLE jobconfig ADD COLUMN success_pattern VARCHAR(255) DEFAULT NULL;
ALTER TABLE jobconfig ADD COLUMN warning_pattern VARCHAR(255) DEFAULT NULL;
ALTER TABLE jobconfig ADD COLUMN fail_pattern VARCHAR(255) DEFAULT NULL;
ALTER TABLE jobconfig ADD COLUMN note TEXT DEFAULT NULL;

COMMIT;
