# -*- coding: utf-8 -*-
# pass_fail_table.py

from operator import itemgetter
from typing import Optional

from plato_wp36 import task_database


def fetch_pass_fail_table(job_name: Optional[str] = None, task_type: Optional[str] = None):
    """
    List pass/fail verdicts stored in the task database.

    :param job_name:
        Filter results by job name.
    :type job_name:
        str
    :param task_type:
        Filter results by type of task.
    :type task_type:
        str
    """
    output_table_list = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Fetch list of jobs
        task_db.db_handle.parameterised_query("SELECT DISTINCT jobName FROM eas_task ORDER BY jobName;")
        job_list = [item['jobName'] for item in task_db.db_handle.fetchall()]

        if job_name is not None:
            job_list = [item for item in job_list if item == job_name]

        # Fetch list of task types (but to save space, don't show internal execution_ task types)
        task_db.db_handle.parameterised_query("SELECT taskTypeName FROM eas_task_types ORDER BY taskTypeName;")
        task_list = [item['taskTypeName']
                     for item in task_db.db_handle.fetchall()
                     if not item['taskTypeName'].startswith('execution_')]

        if task_type is not None:
            task_list = [item for item in task_list if item == task_type]

        # Loop over job names
        for job_name in job_list:

            # Loop over task types
            for task_type in task_list:
                # Fetch all the results we are to display
                task_db.db_handle.parameterised_query("""
SELECT et.taskId, s.schedulingAttemptId
FROM eas_scheduling_attempt s
INNER JOIN eas_task et on et.taskId = s.taskId
INNER JOIN eas_task_types ett on ett.taskTypeId = et.taskTypeId
WHERE et.jobName=%s AND ett.taskTypeName=%s
ORDER BY schedulingAttemptId;
""", (job_name, task_type)
                                                      )
                results = list(task_db.db_handle.fetchall())

                # Abort if no database entries matched this search
                if len(results) < 1:
                    continue

                # Fetch numerical input parameters to each task
                metadata_per_item = []
                all_parameter_names = []
                for result in results:
                    metadata_in = task_db.metadata_fetch_all(task_id=result['taskId'])
                    metadata_per_item.append(metadata_in)

                    for keyword in tuple(metadata_in.keys()):
                        # Purge very long values
                        if len(str(metadata_in[keyword].value)) > 25:
                            del metadata_in[keyword]
                            continue
                        # Keep track of all metadata field names
                        if keyword not in all_parameter_names:
                            all_parameter_names.append(keyword)

                # Sort parameter names alphabetically
                all_parameter_names.sort()

                # Display heading for this job
                output_table_item = {
                    'title': "{}  --  {}".format(job_name, task_type),
                    'column_headings': [],
                    'data_rows': []
                }
                output_table_list.append(output_table_item)

                # Display column headings
                for item in all_parameter_names + ["outcome"]:
                    output_table_item['column_headings'].append(item)

                # Display results
                for metadata_in, result in zip(metadata_per_item, results):
                    output_row = {
                        'row_values': [],
                        'row_str': []
                    }

                    # Fetch output metadata
                    metadata_out = task_db.metadata_fetch_all(scheduling_attempt_id=result['schedulingAttemptId'])

                    # Only display items with a pass/fail outcome
                    if 'outcome' not in metadata_out:
                        continue

                    # Display parameter values
                    for item in all_parameter_names:
                        if item in metadata_in:
                            value_string = metadata_in[item].value
                        else:
                            value_string = "--"
                        try:
                            value_float = float(value_string)
                            output_row['row_values'].append(value_float)
                            output_row['row_str'].append("{:12.8f}".format(value_float))
                        except ValueError:
                            output_row['row_values'].append(value_string)
                            output_row['row_str'].append("{:12.12s}".format(str(value_string)))

                    # Display result
                    outcome = int(metadata_out['outcome'] == 'PASS')
                    output_row['row_values'].append(outcome)
                    output_row['row_str'].append("{:d} ".format(outcome))

                    # New line
                    output_table_item['data_rows'].append(output_row)

                # Sort table rows
                output_table_item['data_rows'].sort(key=itemgetter('row_values'))

    # Return data table
    return output_table_list
