# -*- coding: utf-8 -*-
# task_status.py

from datetime import datetime
from plato_wp36 import task_database

from .log_messages import fetch_log_messages


def render_time(timestamp):
    if timestamp is None:
        return "&ndash;"
    else:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def render_run_time(input):
    if input is None:
        return "&ndash;"
    else:
        return "{:.2f} sec".format(input)


def metadata_list_from_dict(input_metadata):
    input_metadata_list_keys = sorted(input_metadata.keys())
    input_metadata_list_values = [input_metadata[key].value for key in input_metadata_list_keys]
    input_metadata_list = zip(input_metadata_list_keys, input_metadata_list_values)
    return input_metadata_list


def task_status(task_id: int):
    """
    Show the status of a task

    :param task_id:
        The task to show the status for

    :return:
        Dict
    """

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Fetch task information
        task_info = task_db.task_lookup(task_id=task_id)

        # Start building output data structure
        output = {
            'runs': [],
            'task_type_name': task_info.task_type,
            'task_name': task_info.task_name
        }

        # Search for input metadata for this task
        input_metadata = task_db.metadata_fetch_all(task_id=task_id)
        output['input_metadata_list'] = metadata_list_from_dict(input_metadata=input_metadata)

        # Search for input files for this task
        file_inputs = task_db.task_fetch_file_inputs(task_id=task_id)
        file_input_info = []
        for semantic_type in sorted(file_inputs.keys()):
            item_parent = file_inputs[semantic_type]

            # Find out which version of this file we should use
            version_ids = task_db.file_version_by_product(product_id=item_parent.product_id,
                                                          must_have_passed_qc=True)
            if len(version_ids) == 0:
                repository_id = "-- Not generated yet --"
                item_metadata = item_parent.metadata
            else:
                item = task_db.file_version_lookup(product_version_id=version_ids[-1])
                repository_id = item.repository_id
                item_metadata = item.metadata
            file_input_info.append({
                'name': semantic_type,
                'filename': item_parent.filename,
                'directory': item_parent.directory,
                'id': repository_id,
                'metadata': metadata_list_from_dict(item_metadata)
            })
        output['file_input_info'] = file_input_info

        # Search for all attempts to execute this task
        task_db.db_handle.parameterised_query("""
SELECT schedulingAttemptId, queuedTime, startTime, endTime, latestHeartbeat, h.hostname,
       runTimeWallClock, runTimeCpu, runTimeCpuIncChildren, errorFail, isQueued, isRunning, isFinished
FROM eas_scheduling_attempt s
LEFT OUTER JOIN eas_worker_host h ON h.hostId = s.hostId
WHERE taskId=%s
ORDER BY queuedTime;
""", (task_id,))

        run_list = task_db.db_handle.fetchall()

        for task_run in run_list:
            # Fetch output metadata from this scheduling attempt
            output_metadata = task_db.metadata_fetch_all(scheduling_attempt_id=task_run['schedulingAttemptId'])
            output_metadata_list = metadata_list_from_dict(input_metadata=output_metadata)

            # Fetch file outputs from this scheduling attempt
            file_outputs = task_db.execution_attempt_fetch_output_files(attempt_id=task_run['schedulingAttemptId'])
            file_output_info = []
            for semantic_type in sorted(file_outputs.keys()):
                item = file_outputs[semantic_type]
                item_parent = task_db.file_product_lookup(product_id=item.product_id)
                file_output_info.append({
                    'name': semantic_type,
                    'filename': item_parent.filename,
                    'directory': item_parent.directory,
                    'passed_qc': item.passed_qc,
                    'id': item.repository_id,
                    'metadata': metadata_list_from_dict(item.metadata)
                })

            # Create a dictionary of data about this scheduling attempt
            run_info = {
                'run_id': task_run['schedulingAttemptId'],
                'queuedTime': render_time(timestamp=task_run['queuedTime']),
                'startTime': render_time(timestamp=task_run['startTime']),
                'endTime': render_time(timestamp=task_run['endTime']),
                'latestHeartbeat': render_time(timestamp=task_run['latestHeartbeat']),
                'hostname': task_run['hostname'],
                'runTimeWallClock': render_run_time(input=task_run['runTimeWallClock']),
                'runTimeCpu': render_run_time(input=task_run['runTimeCpu']),
                'runTimeCpuIncChildren': render_run_time(input=task_run['runTimeCpuIncChildren']),
                'isQueued': task_run['isQueued'],
                'isRunning': task_run['isRunning'],
                'isFinished': task_run['isFinished'],
                'errorFail': task_run['errorFail'],
                'output_metadata': output_metadata_list,
                'file_output_info': file_output_info,
                'log_table': fetch_log_messages(attempt_id=task_run['schedulingAttemptId'])
            }

        # Append this item to the list of results
        output['runs'].append(run_info)

    # Return results
    return output
