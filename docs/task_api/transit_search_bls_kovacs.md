# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `transit_search_bls_kovacs`

The `transit_search_bls_kovacs` searches for transit signals in a lightcurve using BLS (original FORTRAN implementation).

### Example usage

```
{
  "task": "transit_search_bls_kovacs",
  "name": "my_task",
  "inputs": {
    "lightcurve": "input_lightcurve.lc"
  },
  "lc_duration": 720
}
```

### Input files

|Name      |Type      |Description         |
|----------|----------|--------------------|
|lightcurve|obligatory|Lightcurve to search|


### Output files

None

### Additional input settings


|Name       |Type      |Description                                               |
|-----------|----------|----------------------------------------------------------|
|lc_duration|float     |Only search for transits in first N days of the lightcurve|

### Output metadata

|Name         |Type |Description                 |
|-------------|-----|----------------------------|
|period       |float|Transit period (days)       |
|power        |float|Transit signal power        |

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.