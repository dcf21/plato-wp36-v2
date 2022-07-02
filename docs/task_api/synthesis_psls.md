# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `synthesis_psls`

The `synthesis_psls` synthesises a lightcurve using PSLS.

### Example usage

```
{
  "task": "synthesis_psls",
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

|Name                            |Type |Description                                                             |
|--------------------------------|-----|------------------------------------------------------------------------|
|specs / mode                    |str  |PSLS mode (either `main_sequence` or `red_giant`)                       |
|specs / enable_transits         |bool |Boolean flag indicating whether PSLS should inject any transits         |
|specs / duration                |float|Duration of lightcurve (days)                                           |
|specs / planet_radius           |float|Radius of planet (Jupiter radii)                                        |
|specs / orbital_period          |float|Orbital period of planet (days)                                         |
|specs / semi_major_axis         |float|Semi-major axis of orbit (days)                                         |
|specs / orbital_angle           |float|Orbital inclination of planet (degrees)                                 |
|specs / sampling_cadence        |float|Sampling cadence of lightcurve (sec)                                    |
|specs / eccentricity            |float|Eccentricity of planet's orbit                                          |
|specs / t0                      |float|Time of first transit (days)                                            |
|specs / star_radius             |float|Radius of host star (solar radii)                                       |
|specs / impact_parameter        |float|Impact parameter of planet (0-1); if set, this overrides `orbital_angle`|
|specs / nsr                     |float|Noise-to-signal ratio. Default: 73 (PLATO nominal performance)          |
|specs / mask_updates            |bool |Boolean flag indicating whether mask updates should be included         |
|specs / enable_systematics      |bool |Boolean flag indicating whether systematics should be included          |
|specs / enable_random_noise     |bool |Boolean flag indicating whether random noise should be included         |
|specs / number_camera_groups    |int  |Number of camera groups. Default 4.                                     |
|specs / number_cameras_per_group|int  |Number of cameras in each group. Default 6.                             |


### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.