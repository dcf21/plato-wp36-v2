# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](../contents.md)
* [<< Pipeline task list](../task_list.md)

## Pipeline module: `ingest_external_lcs`

The `ingest_external_lcs` ingests externally-generated lightcurves into the pipeline's filing system. Currently it only supports ingestion of lightcurves generated from the lightcurve stitching working group.

### Example usage

```
{
  "task": "ingest_external_lcs",
  "lc_type": "lcsg",
  "input_path": "lightcurves_v2/csvs/bright/plato_bright*"
}
```

### Input files

None

### Output files

None

### Additional input settings

|Name      |Type |Description                                      |
|----------|-----|-------------------------------------------------|
|lc_type   |str  |Data format of input LCs. Must be set to 'lcsg'. |
|input_path|str  |Path to input lightcurves within `datadir_input`.|


### Output metadata

None

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.