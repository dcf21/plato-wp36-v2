# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `execution_conditional`

The `execution_conditional` conditionally executes a sequence of pipeline steps if some metadata criterion tests true. If the criterion tests false, then an alternative sequence of pipeline steps is executed.

### Example usage

The example below inspects the output metadata from the previous pipeline step whose `name` attribute was set to `transit_detection`, and conditionally executes a sequence of code if the output metadata field `outcome` was set to `PASS`:

```
{
  "task": "execution_conditional",
  "name": "my_task",
  "requires_metadata_from": ["transit_detection"],
  "criterion": "(requested_metadata['transit_detection']['outcome'] == 'PASS')",
  "task_list": [
    {
      "task": "null",
      "name": "conditional_true"
    }
  ],
  "else_task_list": [
    {
      "task": "null",
      "name": "conditional_false"
    }
  ]
}
```

### Input files

None

### Output files

None

### Additional input settings

|Name     |Type |Description                                         |
|---------|-----|----------------------------------------------------|
|criterion|bool |Boolean flag choosing which execution path to follow|


### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.