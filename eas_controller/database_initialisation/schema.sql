-- initschema.sql

BEGIN;

-- Table of types of named tasks the testbench can run (e.g. synthesis_psls)
CREATE TABLE eas_task_types
(
    taskTypeId       INTEGER PRIMARY KEY AUTO_INCREMENT,
    taskName         VARCHAR(64) UNIQUE NOT NULL,
    workerContainers JSON               NOT NULL
);

-- Table of specific tasks EAS is scheduled to run (e.g. run tool X on lightcurve Y)
CREATE TABLE eas_task
(
    taskId           INTEGER PRIMARY KEY AUTO_INCREMENT,
    parentTask       INTEGER,
    createdTime      REAL,
    taskTypeId       INTEGER       NOT NULL,
    jobName          VARCHAR(256),
    workingDirectory VARCHAR(1024) NOT NULL,
    FOREIGN KEY (parentTask) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (taskTypeId) REFERENCES eas_task_types (taskTypeId) ON DELETE CASCADE,
    INDEX (parentTask),
    INDEX (jobName)
);

-- Table of each time a task is scheduled on the cluster (a task may execute more than once if it fails)
CREATE TABLE eas_scheduling_attempt
(
    schedulingAttemptId   INTEGER PRIMARY KEY AUTO_INCREMENT,
    taskId                INTEGER NOT NULL,
    queuedTime            REAL             DEFAULT NULL,
    hostname              VARCHAR(256)     DEFAULT NULL,
    startTime             REAL             DEFAULT NULL,
    latestHeartbeat       REAL             DEFAULT NULL,
    endTime               REAL             DEFAULT NULL,
    allProductsPassedQc   BOOLEAN          DEFAULT NULL,
    errorFail             BOOLEAN NOT NULL DEFAULT FALSE,
    errorText             TEXT             DEFAULT NULL,
    runTimeWallClock      REAL             DEFAULT NULL,
    runTimeCpu            REAL             DEFAULT NULL,
    runTimeCpuIncChildren REAL             DEFAULT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE
);

-- Log messages associated with each attempt to run a task
CREATE TABLE eas_log_messages
(
    generatedByTaskExecution INTEGER,
    timestamp                REAL    NOT NULL,
    severity                 INTEGER NOT NULL,
    message                  VARCHAR(4096),
    FOREIGN KEY (generatedByTaskExecution) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE,
    INDEX (severity, generatedByTaskExecution, timestamp),
    INDEX (generatedByTaskExecution, severity, timestamp),
    INDEX (generatedByTaskExecution, timestamp)
);

-- Table of semantic types of intermediate file products (e.g. lightcurve, periodogram, etc)
CREATE TABLE eas_semantic_type
(
    semanticTypeId INTEGER PRIMARY KEY AUTO_INCREMENT,
    name           VARCHAR(256) UNIQUE NOT NULL,
    INDEX (name)
);

-- Table of all intermediate file products, each associated with the task which generated / will generate them.
-- Note that multiple versions of the same file product may exist on disk, if a task runs multiple times.
CREATE TABLE eas_product
(
    productId     INTEGER PRIMARY KEY AUTO_INCREMENT,
    generatorTask INTEGER      NOT NULL,
    plannedTime   REAL,
    directoryName VARCHAR(512) NOT NULL,
    filename      VARCHAR(256) NOT NULL,
    semanticType  INTEGER      NOT NULL,
    mimeType      VARCHAR(64),
    FOREIGN KEY (generatorTask) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (semanticType) REFERENCES eas_semantic_type (semanticTypeId) ON DELETE CASCADE,
    UNIQUE (directoryName, filename),
    UNIQUE (generatorTask, semanticType)
);

-- Table of all intermediate file product versions stored on disk.
-- Note that multiple versions of the same file product may exist on disk, if a task runs multiple times.
CREATE TABLE eas_product_version
(
    productVersionId         INTEGER PRIMARY KEY AUTO_INCREMENT,
    productId                INTEGER            NOT NULL,
    generatedByTaskExecution INTEGER            NOT NULL,
    repositoryId             VARCHAR(64) UNIQUE NOT NULL,
    createdTime              REAL,
    modifiedTime             REAL,
    fileMD5                  VARCHAR(32),
    fileSize                 INTEGER,
    passedQc                 BOOLEAN,
    FOREIGN KEY (productId) REFERENCES eas_product (productId) ON DELETE CASCADE,
    FOREIGN KEY (generatedByTaskExecution) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE,
    UNIQUE (productId, generatedByTaskExecution)
);

-- Table of metadata association with tasks or scheduling attempts, or file products
CREATE TABLE eas_metadata_keys
(
    keyId INTEGER PRIMARY KEY AUTO_INCREMENT,
    name  VARCHAR(64) UNIQUE NOT NULL,
    INDEX (name)
);

CREATE TABLE eas_metadata_item
(
    taskId              INTEGER,
    schedulingAttemptId INTEGER,
    productId           INTEGER,
    productVersionId    INTEGER,
    setAtTime           REAL,
    metadataKey         INTEGER,
    valueFloat          REAL,
    valueString         TEXT,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (schedulingAttemptId) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE,
    FOREIGN KEY (productId) REFERENCES eas_product (productId) ON DELETE CASCADE,
    FOREIGN KEY (productVersionId) REFERENCES eas_product_version (productVersionId) ON DELETE CASCADE,
    FOREIGN KEY (metadataKey) REFERENCES eas_metadata_keys (keyId) ON DELETE CASCADE,
    UNIQUE (taskId, metadataKey),
    UNIQUE (schedulingAttemptId, metadataKey),
    UNIQUE (productId, metadataKey),
    UNIQUE (productVersionId, metadataKey)
);

-- Table of intermediate products required by each task
CREATE TABLE eas_task_input
(
    taskId       INTEGER NOT NULL,
    inputId      INTEGER NOT NULL,
    semanticType INTEGER NOT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (inputId) REFERENCES eas_product (productId) ON DELETE CASCADE,
    FOREIGN KEY (semanticType) REFERENCES eas_semantic_type (semanticTypeId) ON DELETE CASCADE,
    UNIQUE (taskId, semanticType)
);

-- Trigger to propagate QC from individual file products to the tasks that created them
DELIMITER //
CREATE TRIGGER qc_propagation
    AFTER UPDATE
    ON eas_product_version
    FOR EACH ROW
BEGIN
    UPDATE eas_scheduling_attempt s
    SET s.allProductsPassedQc = NOT EXISTS(
            SELECT 1
            FROM eas_product_version p
            WHERE p.generatedByTaskExecution = s.schedulingAttemptId
              AND NOT p.passedQc)
    WHERE s.schedulingAttemptId = new.generatedByTaskExecution;
END;
//

COMMIT;
