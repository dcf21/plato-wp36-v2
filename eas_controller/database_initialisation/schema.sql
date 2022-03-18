# initschema.sql

BEGIN;

# Table of types of tasks the testbench can run
CREATE TABLE eas_task_types
(
    taskTypeId INTEGER PRIMARY KEY AUTO_INCREMENT,
    taskName   VARCHAR(64) UNIQUE NOT NULL,
    queueName  VARCHAR(64) UNIQUE NOT NULL,
    workerName VARCHAR(64)        NOT NULL
);

# Table of tasks EAS is scheduled to run
CREATE TABLE eas_task
(
    taskId     INTEGER PRIMARY KEY,
    parentTask INTEGER,
    taskTypeId INTEGER NOT NULL,
    FOREIGN KEY (parentTask) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (taskTypeId) REFERENCES eas_task_types (taskTypeId) ON DELETE CASCADE
);

# Table of each time a task is scheduled on the cluster
CREATE TABLE eas_scheduling_attempt
(
    schedulingAttemptId   INTEGER PRIMARY KEY,
    taskId                INTEGER NOT NULL,
    startTime             REAL             DEFAULT NULL,
    endTime               REAL             DEFAULT NULL,
    allProductsPassedQc   BOOLEAN          DEFAULT NULL,
    errorFail             BOOLEAN NOT NULL DEFAULT FALSE,
    errorText             TEXT             DEFAULT NULL,
    runTimeWallClock      REAL             DEFAULT NULL,
    runTimeCpu            REAL             DEFAULT NULL,
    runTimeCpuIncChildren REAL             DEFAULT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE
);

# Table of metadata association with each time a task runs
CREATE TABLE eas_metadata_keys
(
    keyId INTEGER PRIMARY KEY,
    name  VARCHAR(64) UNIQUE NOT NULL,
    INDEX (name)
);

CREATE TABLE eas_scheduling_attempt_metadata
(
    schedulingAttemptId INTEGER,
    metadataKey         INTEGER,
    valueFloat          REAL,
    valueString         TEXT,
    FOREIGN KEY (schedulingAttemptId) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE,
    FOREIGN KEY (metadataKey) REFERENCES eas_metadata_keys (keyId) ON DELETE CASCADE
);

# Table of all intermediate file products
CREATE TABLE eas_product
(
    productId     INTEGER PRIMARY KEY,
    generatorTask INTEGER             NOT NULL,
    filename      VARCHAR(255) UNIQUE NOT NULL,
    created       BOOLEAN DEFAULT FALSE,
    passedQc      BOOLEAN,
    FOREIGN KEY (generatorTask) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE
);

# Table of intermediate products required by each task
CREATE TABLE eas_task_input
(
    taskId  INTEGER NOT NULL,
    inputId INTEGER NOT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (inputId) REFERENCES eas_product (productId) ON DELETE CASCADE
);

# Trigger to propagate QC from individual file products to the tasks that created them
DELIMITER //
CREATE TRIGGER qc_propagation
    AFTER UPDATE
    ON eas_product
    FOR EACH ROW
BEGIN
    UPDATE eas_scheduling_attempt s
    SET s.allProductsPassedQc = NOT EXISTS(SELECT 1
                                           FROM eas_product p
                                           WHERE p.generatorTask = new = s.schedulingAttemptId
                                             AND NOT p.passedQc)
    WHERE s.schedulingAttemptId = new.generatorTask;
END;
//

COMMIT;

