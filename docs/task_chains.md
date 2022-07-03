# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Task chain definition files

Work is submitted to the pipeline prototype by means of *task chains*, which are currently defined by files in JSON format. There are several examples of varying complexity in the `demo_jobs` directory.

At its simplest, a task chain is a list of *tasks* which needs to be performed. Each task is represented by an associative array of properties which define that task. Some tasks rely on inputs from previous tasks - either file products or metadata values - and the pipeline controller automatically works out which preceeding tasks need to complete before a task can be scheduled to begin.

For example, the following task chain description would run three null tasks:

```
{
  "job_name": "an_example_job",
  "working_directory": "my_example",
  "task_list": [
    {
      "task": "null"
    },
    {
      "task": "null"
    },
    {
      "task": "null"
    }
  ]
}
```

The JSON format follows the same syntax convention as Python: lists are represented by [], while associative arrays (aka. dictionaries) are represented by {}.

### Task chain descriptions

The above example shows an associative array which defines a *task chain*. The fields within that associative array are as follows:

|Name             |Type|Required|Description                                                                                                                |
|-----------------|----|--------|---------------------------------------------------------------------------------------------------------------------------|
|job_name         |str |no      |A label to describe this task chain, used to distinguish it from other task chains when querying results from the database.|
|working_directory|str |no      |The directory within the `datadir_output` in which tasks in this task chain should place their output file products.       |
|task_list        |list|yes     |The list of tasks to be run, each specified as an associative array.                                                       |

In this example, the pipeline will automatically identify that the three `null` tasks which make up the job have no inter-dependencies, and hence can be run in parallel. However, in the more complicated example below, which synthesises a lightcurve and then runs it through a transit-detection algorithm, the pipeline will automatically identify that the first task needs to run before the second, since the second uses a file which is created by the synthesis task:

```
{
  "job_name": "a_second_example_job",
  "working_directory": "my_example_2",
  "task_list": [
    {
      "task": "synthesis_psls",
      "name": "synthesis_step",
      "outputs": {
        "lightcurve": "my_lightcurve.lc"
      },
      "specs": {
        "duration": 730,
        "planet_radius": "(constants.Rearth)",
        "orbital_period": 365,
        "semi_major_axis": 1,
        "orbital_angle": 0,
      }
    },
    {
      "task": "transit_search_tls",
      "name": "transit_detection_step",
      "inputs": {
        "lightcurve": "my_lightcurve.lc"
      },
      "lc_duration": 720
    }
  ]
}
```

The next section describes the meaning of each of the attributes that is used to define the tasks within a task chain:

### Task descriptors

Each task within a task chain is defined by an associative array of attributes. Some of these attributes are specific to individual tasks; these are [listed in full here](task_list.md).

The table below lists the attributes that are common to all tasks:

|Name                        |Type |Required      |Description                                                                                                                                                                                                                     |
|----------------------------|-----|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|task                        |str  |yes           |The name of the task to be performed. This must be one of the task types [listed here](task_list.md).                                                                                                                           |
|name                        |str  |no            |A user-defined label for this task. These labels are used to define when a task uses metadata output from a preceeding task.                                                                                                    |
|inputs                      |dict |for some tasks|An associative array [input name -> filename] of file products that this task takes as inputs.                                                                                                                                  |
|outputs                     |dict |for some tasks|An associative array [output name -> filename] of file products that this task produces as outputs.                                                                                                                             |
|job_name                    |str  |no            |Optionally, the `job_name` set in the task chain descriptor can be overridden for individual tasks. This propagates to all child tasks.                                                                                         |
|working_directory           |str  |no            |Optionally, the `working_directory` set in the task chain descriptor can be overridden for individual tasks. This propagates to all child tasks.                                                                                |
|requires_metadata_from      |list |no            |A list of the `name`s of previous tasks within this task chain whose output metadata is needed to calculate the settings for this task. See the following section for a description of how this is used.                        |
|requires_metadata_from_child|list |no            |A special attribute, currently only used by `do`/`while` loops, specifying the `name`s of the **child** tasks (within the loop) whose output metadata is needed to evaluate whether the loop should repeat after each iteration.|

### Evaluating expressions

Each of the attributes in a task description can be specified either as an immediate value - either a number or a string - or as a mathematical expression, to be evaluated by the Python interpretter.

Expressions are identified by the pipeline because they are strings, and they are enclosed in brackets, e.g. `"(2 + 2)"` or `"('%.3f' % pi)"`.

Within these Python expressions, the following dictionaries of values are available:

|Name              |Description                                                                                                                          |
|------------------|-------------------------------------------------------------------------------------------------------------------------------------|
|constants         |Numerical constants, as defined in the module `plato_wp36.constants`. These include physical constants, and PLATO mission parameters.|
|metadata          |Output metadata values produced by parent tasks. This includes, for example, the values of any `for` loop iterations.                |
|requested_metadata|Output metadata values produced by any sibling tasks listed in the `requires_metadata_from` field described in the previous section. |


---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
