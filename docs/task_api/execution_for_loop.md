# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `execution_for_loop`

The `execution_for_loop` conditionally executes a sequence of pipeline steps if some metadata criterion tests true. If the criterion tests false, then an alternative sequence of pipeline steps is executed.

### Example usage

The example below runs a dummy task three times, for three different explicit values of the metadata parameter `tda`:

```
{
  "task": "execution_for_loop",
  "parameter": "tda",
  "values": ["tls", "bls", "qats"],
  "task_list": [
    {
      "task": "null",
      "name": "dummy_task"
    }
  ]
}
```

The example below runs a dummy task eight times, for eight different logarithmically-spaced value of the metadata parameter `size`. The limits could have been specified numerically, but here they are specified as a string expression which is evaluated:

```
{
  "task": "execution_for_loop",
  "parameter": "size",
  "log_range": ["(constants.Rearth / 8)", "(constants.Rearth * 8)", 8],
  "task_list": [
    {
      "task": "null",
      "name": "dummy_task"
    }
  ]
}
```

The example below runs a dummy task eight times, for eight different uniformly-spaced value of the metadata parameter `size`. The limits could have been specified numerically, but here they are specified as a string expression which is evaluated:

```
{
  "task": "execution_for_loop",
  "parameter": "size",
  "linear_range": ["(constants.Rearth / 8)", "(constants.Rearth * 8)", 8],
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

|Name        |Type |Description                                                                                      |
|------------|-----|-------------------------------------------------------------------------------------------------|
|parameter   |str  |The name of the metadata variable we are to loop over                                            |
|values      |list |Optional: An explicit list of parameter values to loop over                                      |
|linear_range|list |Optional: [start, end, number of samples] to iterate over uniformly-spaced parameter values      |
|log_range   |list |Optional: [start, end, number of samples] to iterate over logarithmically-spaced parameter values|

You must specify one, and only one, out of `values`, `linear_range` and `log_range`.

### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.