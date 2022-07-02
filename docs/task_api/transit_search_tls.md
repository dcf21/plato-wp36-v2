# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `transit_search_tls`

The `transit_search_tls` searches for transit signals in a lightcurve using TLS ([Hippke & Heller 2019](https://github.com/hippke/tls)).

### Example usage

```
{
  "task": "transit_search_tls",
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
|depth        |float|Depth of transit signal     |
|duration     |float|Duration of transit signal  |
|sde          |float|Signal detection efficiency |


---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.