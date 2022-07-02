# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `execution_do_while_loop`

The `execution_do_while_loop` conditionally executes a sequence of pipeline steps repeatedly until some criterion tests false. The do loop always executes at least once.

### Example usage

The example below runs a dummy task in a do-while loop. To determine whether to repeat, it inspects the metadata output from a task named `transit_detection` within the while loop, and it repeats if that task produced a metadata item `outcome` which had the value `PASS`. Additionally, it exits if it has already looped three times, since `my_while_loop_index` keeps count of the number of loop iterations:

```
{
  "task": "execution_do_while_loop",
  "iteration_name": "my_while_loop",
  "requires_metadata_from_child": ["transit_detection"],
  "repeat_criterion": "(requested_metadata['transit_detection']['outcome'] == 'PASS') and (metadata['my_while_loop_index'] < 3)",
  "task_list": [
    {
      "task": "null",
      "name": "dummy_task"
    }
  ]
}
```

### Input files

None

### Output files

None

### Additional input settings

|Name                        |Type |Description                                                                                                         |
|----------------------------|-----|--------------------------------------------------------------------------------------------------------------------|
|requires_metadata_from_child|list |List of child tasks whose metadata we require metadata from in order to decide whether to repeat the loop           |
|repeat_criterion            |bool |Boolean expression we evaluate at the end of each iteration to decide whether to repeat the loop                    |
|iteration_name              |str  |The name of the iteration. Within the loop, a metadata value `{name}_index` keeps count of the number of iterations.|

You must specify one, and only one, out of `values`, `linear_range` and `log_range`.

### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.