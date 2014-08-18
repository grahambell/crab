-- This SQL script updates the SQLite database to add
-- a new column to the job configuration table.
-- Backing up the database is recommended before
-- running this script.

BEGIN TRANSACTION;

ALTER TABLE jobconfig ADD COLUMN inhibit BOOLEAN NOT NULL DEFAULT 0;

COMMIT;
