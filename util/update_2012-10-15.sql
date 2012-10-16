-- This SQL script updates the SQLite database
-- to the new schema, on the assumption that
-- no job records have been deleted from the job
-- table.  (Crab would not have done so.)
-- Backing up the database is recommended before
-- running this script.

BEGIN TRANSACTION;

ALTER TABLE jobwarn RENAME TO jobalarm;

ALTER TABLE job RENAME TO job_old;

CREATE TABLE job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255) NOT NULL,
    user VARCHAR(255) NOT NULL,
    command VARCHAR(255) NOT NULL,
    crabid VARCHAR(255),
    time VARCHAR(255),
    timezone VARCHAR(255),
    installed VARCHAR(255) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted VARCHAR(255),
    UNIQUE (host, user, crabid)
);

INSERT INTO job
    (host, user, command, crabid, time, timezone, installed, deleted)
    SELECT host, user, command, jobid, time, timezone, installed, deleted
    FROM job_old
    ORDER BY id ASC;

DROP TABLE job_old;

CREATE INDEX job_crabid ON job (crabid);
CREATE INDEX job_host ON job (host);
CREATE INDEX job_user ON job (user);
CREATE INDEX job_command ON job (command);
CREATE INDEX job_installed ON job (installed);
CREATE INDEX job_deleted ON job (deleted);

COMMIT;
