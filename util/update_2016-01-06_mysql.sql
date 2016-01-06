-- This SQL script updates a MySQL database to alter the foreign
-- key constraint on joboutput.finishid to allow deletions to
-- cascade.  You will need to apply this update if you wish to use
-- the automated cleaning service with an existing MySQL-based
-- installation which has been run without a separate output store.
-- You may wish to check the name of the existing foreign key
-- constraint using "SHOW CREATE TABLE joboutput" and update the name
-- used in this script if necessary.
--
-- Backing up the database is recommended before running this script.

ALTER TABLE joboutput
    DROP FOREIGN KEY `joboutput_ibfk_1`;

ALTER TABLE joboutput
    ADD FOREIGN KEY (finishid) REFERENCES jobfinish(id)
        ON DELETE CASCADE ON UPDATE RESTRICT;
