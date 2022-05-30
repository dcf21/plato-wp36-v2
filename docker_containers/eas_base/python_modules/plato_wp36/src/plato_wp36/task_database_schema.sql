-- initschema.sql

BEGIN;

-- Table of worker Docker containers and their resource requirements
CREATE TABLE eas_worker_containers
(
    containerId   INTEGER PRIMARY KEY AUTO_INCREMENT,
    containerName VARCHAR(64) UNIQUE NOT NULL,
    requiredCpus  REAL               NOT NULL,
    requiredGpus  INTEGER            NOT NULL,
    requiredRam   REAL               NOT NULL
);

-- Table of types of named tasks the EAS can run (e.g. synthesis_psls)
CREATE TABLE eas_task_types
(
    taskTypeId   INTEGER PRIMARY KEY AUTO_INCREMENT,
    taskTypeName VARCHAR(64) UNIQUE NOT NULL
);

-- Table of the containers that tasks can run within
CREATE TABLE eas_task_containers
(
    taskTypeId  INTEGER NOT NULL,
    containerId INTEGER NOT NULL,
    FOREIGN KEY (taskTypeId) REFERENCES eas_task_types (taskTypeId),
    FOREIGN KEY (containerId) REFERENCES eas_worker_containers (containerId)
);

CREATE UNIQUE INDEX eas_task_containers_1 ON eas_task_containers (taskTypeId, containerId);

-- Table of specific tasks EAS is scheduled to run (e.g. run tool X on lightcurve Y)
CREATE TABLE eas_task
(
    taskId           INTEGER PRIMARY KEY AUTO_INCREMENT,
    parentTask       INTEGER,
    createdTime      REAL,
    taskTypeId       INTEGER       NOT NULL,
    jobName          VARCHAR(256),
    taskName         VARCHAR(256),
    workingDirectory VARCHAR(1024) NOT NULL,
    FOREIGN KEY (parentTask) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (taskTypeId) REFERENCES eas_task_types (taskTypeId) ON DELETE CASCADE
);

CREATE INDEX eas_task_parent ON eas_task (parentTask);
CREATE INDEX eas_task_job ON eas_task (jobName);

-- Table of all the hosts which have run jobs
CREATE TABLE eas_worker_host
(
    hostId   INTEGER PRIMARY KEY AUTO_INCREMENT,
    hostname VARCHAR(256) DEFAULT NULL
);

-- Table of each time a task is scheduled on the cluster (a task may execute more than once if it fails)
CREATE TABLE eas_scheduling_attempt
(
    schedulingAttemptId   INTEGER PRIMARY KEY AUTO_INCREMENT,
    taskId                INTEGER NOT NULL,
    queuedTime            REAL             DEFAULT NULL,
    isQueued              BOOLEAN          DEFAULT FALSE,
    isRunning             BOOLEAN          DEFAULT FALSE,
    isFinished            BOOLEAN          DEFAULT FALSE,
    hostId                INTEGER          DEFAULT NULL,
    startTime             REAL             DEFAULT NULL,
    latestHeartbeat       REAL             DEFAULT NULL,
    endTime               REAL             DEFAULT NULL,
    allProductsPassedQc   BOOLEAN          DEFAULT NULL,
    errorFail             BOOLEAN NOT NULL DEFAULT FALSE,
    errorText             TEXT             DEFAULT NULL,
    runTimeWallClock      REAL             DEFAULT NULL,
    runTimeCpu            REAL             DEFAULT NULL,
    runTimeCpuIncChildren REAL             DEFAULT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (hostId) REFERENCES eas_worker_host (hostId) ON DELETE CASCADE
);

-- Log messages associated with each attempt to run a task
CREATE TABLE eas_log_messages
(
    generatedByTaskExecution INTEGER,
    timestamp                REAL    NOT NULL,
    severity                 INTEGER NOT NULL,
    message                  VARCHAR(4096),
    FOREIGN KEY (generatedByTaskExecution) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE
);

CREATE INDEX eas_log_1 ON eas_log_messages (severity, generatedByTaskExecution, timestamp);
CREATE INDEX eas_log_2 ON eas_log_messages (generatedByTaskExecution, severity, timestamp);
CREATE INDEX eas_log_3 ON eas_log_messages (generatedByTaskExecution, timestamp);

-- Table of semantic types of intermediate file products (e.g. lightcurve, periodogram, etc)
CREATE TABLE eas_semantic_type
(
    semanticTypeId INTEGER PRIMARY KEY AUTO_INCREMENT,
    name           VARCHAR(256) UNIQUE NOT NULL
);

CREATE INDEX eas_semantic_type_name ON eas_semantic_type (name);

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
    FOREIGN KEY (semanticType) REFERENCES eas_semantic_type (semanticTypeId) ON DELETE CASCADE
);

CREATE UNIQUE INDEX eas_product_1 ON eas_product (directoryName, filename);
CREATE UNIQUE INDEX eas_product_2 ON eas_product (generatorTask, semanticType);

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
    FOREIGN KEY (generatedByTaskExecution) REFERENCES eas_scheduling_attempt (schedulingAttemptId) ON DELETE CASCADE
);

CREATE UNIQUE INDEX eas_product_version_1 ON eas_product_version (productId, generatedByTaskExecution);

-- Table of metadata association with tasks or scheduling attempts, or file products
CREATE TABLE eas_metadata_keys
(
    keyId INTEGER PRIMARY KEY AUTO_INCREMENT,
    name  VARCHAR(64) UNIQUE NOT NULL
);

CREATE INDEX eas_metadata_keys_1 ON eas_metadata_keys (name);

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
    FOREIGN KEY (metadataKey) REFERENCES eas_metadata_keys (keyId) ON DELETE CASCADE
);

CREATE UNIQUE INDEX eas_metadata_item_1 ON eas_metadata_item (taskId, metadataKey);
CREATE UNIQUE INDEX eas_metadata_item_2 ON eas_metadata_item (schedulingAttemptId, metadataKey);
CREATE UNIQUE INDEX eas_metadata_item_3 ON eas_metadata_item (productId, metadataKey);
CREATE UNIQUE INDEX eas_metadata_item_4 ON eas_metadata_item (productVersionId, metadataKey);

-- Table of intermediate file products required by each task
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

CREATE UNIQUE INDEX eas_task_input_1 ON eas_task_input (taskId, semanticType);

-- Table of metadata from siblings required by each task
CREATE TABLE eas_task_metadata_input
(
    taskId  INTEGER NOT NULL,
    inputId INTEGER NOT NULL,
    FOREIGN KEY (taskId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    FOREIGN KEY (inputId) REFERENCES eas_task (taskId) ON DELETE CASCADE,
    UNIQUE (taskId, inputId)
);

CREATE UNIQUE INDEX eas_task_metadata_input_1 ON eas_task_metadata_input (taskId, inputId);

COMMIT;
