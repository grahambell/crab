-- This SQL script updates a SQLite database to alter the foreign
-- key constraint on joboutput.finishid to allow deletions to
-- cascade.  You will need to apply this update if you wish to use
-- the automated cleaning service with an existing SQLite-based
-- installation which has been run without a separate output store.
--
-- Backing up the database is recommended before running this script.

BEGIN TRANSACTION;

ALTER TABLE joboutput RENAME TO joboutput_old;

CREATE TABLE joboutput (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finishid INTEGER NOT NULL,
    stdout TEXT DEFAULT "" NOT NULL,
    stderr TEXT DEFAULT "" NOT NULL,

    UNIQUE (finishid),
    FOREIGN KEY (finishid) REFERENCES jobfinish(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
);

INSERT INTO joboutput
    (finishid, stdout, stderr)
    SELECT finishid, stdout, stderr
    FROM joboutput_old
    ORDER BY id ASC;

DROP TABLE joboutput_old;

COMMIT;
