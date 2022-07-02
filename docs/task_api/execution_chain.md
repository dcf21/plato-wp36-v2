# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `execution_chain`

The `execution_chain` executes a sequence of pipeline steps. Although it is used internally by the pipeline to execute the contents of a chain of pipeline tasks specified in a JSON file, or to execute loop iterations, there is never normally any reason for a user to explicitly create an execution chain.

### Example usage

The example below executes two null tasks in an execution chain:

```
{
  "task": "execution_chain",
  "name": "my_task_chain",
  "task_list": [
    {
      "task": "null",
      "name": "first_task"
    },
    {
      "task": "null",
      "name": "second_task"
    }
  ]
}
```

### Input files

None

### Output files

None

### Additional input settings

None

### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.