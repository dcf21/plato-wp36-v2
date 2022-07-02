# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `verify`

The `verify` checks whether a lightcurve is sampled on a (roughly) fixed timestep.

### Example usage

```
{
  "task": "verify",
  "name": "my_task",
  "inputs": {
    "lightcurve": "input_lightcurve.lc"
  }
}
```

### Input files

|Name      |Type      |Description         |
|----------|----------|--------------------|
|lightcurve|obligatory|Lightcurve to verify|


### Output files

None

### Additional input settings

None

### Output metadata

|Name                 |Type |Description                                               |
|---------------------|-----|----------------------------------------------------------|
|verification_time_min|float|Lowest time value in lightcurve                           |
|verification_time_max|float|Largest time value in lightcurve                          |
|verification_flux_min|float|Lowest flux value in lightcurve                           |
|verification_flux_max|float|Largest flux value in lightcurve                          |
|verification         |bool |Flag indicating whether lightcurve is on a fixed time step|


---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.