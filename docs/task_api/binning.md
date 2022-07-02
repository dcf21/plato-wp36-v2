# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `binning`

The `binning` resamples a lightcurve onto a new, fixed timestep.

### Example usage

```
{
  "task": "binning",
  "name": "my_task",
  "inputs": {
    "lightcurve": "input_lightcurve.lc"
  },
  "outputs": {
    "lightcurve": "output_lightcurve.lc"
  },
  "cadence": 900
}
```

### Input files

|Name      |Type      |Description           |
|----------|----------|----------------------|
|lightcurve|obligatory|Lightcurve to resample|


### Output files

|Name      |Type      |Description      |
|----------|----------|-----------------|
|lightcurve|obligatory|Output lightcurve|

### Additional input settings

|Name   |Type      |Description                             |
|-------|----------|----------------------------------------|
|cadence|obligatory|Time step for resampled lightcurve (sec)|

### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.