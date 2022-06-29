# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Task chain definition files

Currently, pipeline jobs are specified via JSON descriptions, of which there are several examples in the `demo_jobs`
directory. This may or may not be a good format to continue using - JSON editors are plentiful, but the format is rather
verbose and full of punctuation. Perhaps YAML would be a better choice (we're not tied to any particular format...)

For example, a request to synthesise a lightcurve for the Earth using PSLS would look as follows:

```
{
  "task": "synthesis_psls",
  "outputs": {
    "lightcurve": "earth.lc"
  },
  "specs": {
    "duration": 730,
    "planet_radius": "(constants.Rearth)",
    "orbital_period": 365,
    "semi_major_axis": 1,
    "orbital_angle": 0,
  }
```

More complex chains of tasks can easily be built by sequencing operations together into an execution chain (
see. `demo_jobs` for some examples). Loops, such as for loops and while loops, can be executed using special tasks which
perform iterations just like any other task.
