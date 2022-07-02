# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `transit_search_qats`

The `transit_search_qats` searches for transit signals in a lightcurve using QATS ([Carter & Agol 2012](https://arxiv.org/abs/1210.5136)).

### Example usage

```
{
  "task": "transit_search_qats",
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
|transit_count|int  |Number of transits detected |
|period_span  |int  |Number of transits - 1      |
|first_transit|float|Time of first transit (days)|
|last_transit |float|Time of last transit (days  |

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.