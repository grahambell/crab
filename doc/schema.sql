CREATE TABLE job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255) NOT NULL,
    user VARCHAR(255) NOT NULL,
    command VARCHAR(255) NOT NULL,
    crabid VARCHAR(255),
    time VARCHAR(255),
    timezone VARCHAR(255),
    installed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP NULL,

    UNIQUE (host, user, crabid)
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX job_crabid ON job (crabid);
CREATE INDEX job_host ON job (host);
CREATE INDEX job_user ON job (user);
CREATE INDEX job_command ON job (command);
CREATE INDEX job_installed ON job (installed);
CREATE INDEX job_deleted ON job (deleted);

CREATE TABLE jobstart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jobid INTEGER NOT NULL,
    command VARCHAR(255) NOT NULL,
    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (jobid) REFERENCES job(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX jobstart_jobid ON jobstart (jobid);
CREATE INDEX jobstart_datetime ON jobstart (datetime);

CREATE TABLE jobfinish (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jobid INTEGER NOT NULL,
    command VARCHAR(255) NOT NULL,
    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER NOT NULL,

    FOREIGN KEY (jobid) REFERENCES job(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX jobfinish_jobid ON jobfinish (jobid);
CREATE INDEX jobfinish_datetime ON jobfinish (datetime);

CREATE TABLE jobalarm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jobid INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status INTEGER NOT NULL,

    FOREIGN KEY (jobid) REFERENCES job(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX jobalarm_jobid ON jobalarm (jobid);
CREATE INDEX jobalarm_datetime ON jobalarm (datetime);

CREATE TABLE joboutput (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finishid INTEGER NOT NULL,
    stdout TEXT DEFAULT "" NOT NULL,
    stderr TEXT DEFAULT "" NOT NULL,

    UNIQUE (finishid),
    FOREIGN KEY (finishid) REFERENCES jobfinish(id)
        ON DELETE CASCADE ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE TABLE jobconfig (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jobid INTEGER NOT NULL,
    graceperiod INTEGER,
    timeout INTEGER,
    success_pattern VARCHAR(255) DEFAULT NULL,
    warning_pattern VARCHAR(255) DEFAULT NULL,
    fail_pattern VARCHAR(255) DEFAULT NULL,
    note TEXT DEFAULT NULL,
    inhibit BOOLEAN NOT NULL DEFAULT 0,

    UNIQUE (jobid),
    FOREIGN KEY (jobid) REFERENCES job(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE TABLE jobnotify (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configid INTEGER,
    host VARCHAR(255) DEFAULT NULL,
    user VARCHAR(255) DEFAULT NULL,
    method VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    time VARCHAR(255) DEFAULT NULL,
    timezone VARCHAR(255) DEFAULT NULL,
    skip_ok BOOLEAN NOT NULL DEFAULT 0,
    skip_warning BOOLEAN NOT NULL DEFAULT 0,
    skip_error BOOLEAN NOT NULL DEFAULT 0,
    include_output BOOLEAN NOT NULL DEFAULT 0,

    FOREIGN KEY (configid) REFERENCES jobconfig(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX jobnotify_host ON jobnotify (host);
CREATE INDEX jobnotify_user ON jobnotify (user);

CREATE TABLE rawcrontab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host VARCHAR(255) NOT NULL,
    user VARCHAR(255) NOT NULL,
    crontab TEXT NOT NULL,

    UNIQUE (host, user)
)
-- MySQL: ENGINE=InnoDB
;

CREATE INDEX rawcrontab_host ON rawcrontab (host);
CREATE INDEX rawcrontab_user ON rawcrontab (user);
