# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `multiply`

The `multiply` multiplies two lightcurves together, for transit injection purposes. If the second lightcurve is sampled on a different raster from the first, it is resampled before multiplication.

### Example usage

```
{
  "task": "multiply",
  "name": "my_task",
  "inputs": {
    "lightcurve_1": "first_lc.dat",
    "lightcurve_2": "second_lc.dat"
  },
  "outputs": {
    "lightcurve": "output_lc.dat"
  }
}
```

### Input files

|Name        |Type      |Description      |
|------------|----------|-----------------|
|lightcurve_1|obligatory|First lightcurve |
|lightcurve_2|obligatory|Second lightcurve|


### Output files

|Name      |Type      |Description       |
|----------|----------|------------------|
|lightcurve|obligatory|Output lightcurve |

### Additional input settings

None

### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.