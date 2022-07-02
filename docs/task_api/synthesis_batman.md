# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `synthesis_batman`

The `synthesis_batman` synthesises a lightcurve using Batman.

### Example usage

```
{
  "task": "synthesis_batman",
  "name": "my_task",
  "outputs": {
    "lightcurve": "output_lightcurve.dat"
  },
  "specs": {
    "duration": 240,
    "planet_radius": 1,
    "orbital_period": 50,
    "semi_major_axis": 0.4,
    "orbital_angle": 0,
    "sampling_cadence": 900
  }
}
```

### Input files

None

### Output files

|Name      |Type      |Description       |
|----------|----------|------------------|
|lightcurve|obligatory|Output lightcurve |

### Additional input settings

|Name                    |Type |Description                                                             |
|------------------------|-----|------------------------------------------------------------------------|
|specs / duration        |float|Duration of lightcurve (days)                                           |
|specs / planet_radius   |float|Radius of planet (Jupiter radii)                                        |
|specs / orbital_period  |float|Orbital period of planet (days)                                         |
|specs / semi_major_axis |float|Semi-major axis of orbit (days)                                         |
|specs / orbital_angle   |float|Orbital inclination of planet (degrees)                                 |
|specs / sampling_cadence|float|Sampling cadence of lightcurve (sec)                                    |
|specs / eccentricity    |float|Eccentricity of planet's orbit                                          |
|specs / t0              |float|Time of first transit (days)                                            |
|specs / star_radius     |float|Radius of host star (solar radii)                                       |
|specs / impact_parameter|float|Impact parameter of planet (0-1); if set, this overrides `orbital_angle`|


### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.