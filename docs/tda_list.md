# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## List of transit-detection codes

The following transit-detection codes are currently supported by the pipeline prototype:

#### BLS - Boxed Least Squares.

Two implementations are supported: the [original FORTRAN implementation](https://github.com/dfm/python-bls) of [Kovacs et al. (2002)](https://ui.adsabs.harvard.edu/abs/2002A%26A...391..369K/abstract), and an [optimised Python implementation](https://github.com/dfm/bls.py) by Dan Forman-Mackey.


#### QATS - Quasiperiodic Automated Transit Search ([Carter & Agol 2018](https://ui.adsabs.harvard.edu/abs/2013ApJ...765..132C/abstract))

This code is publicly available from [Eric Agol's website](https://faculty.washington.edu/agol/QATS/).

#### TLS - Transit Least Squares ([Hippke & Heller 2019](https://ui.adsabs.harvard.edu/abs/2019A%26A...623A..39H/abstract))

This code is publicly available from [GitHub](https://github.com/hippke/tls)

## Codes that are not yet implemented

The following codes were previously investigated as part of the EAS Baseline Algorithm testbench, but have not yet been ported to work in the new EAS pipeline prototype:

#### DST - Détection Spécialisée de Transits ([Cabrera et al. 2018](https://ui.adsabs.harvard.edu/abs/2012A%26A...548A..44C/abstract))

This code is not publicly available, and must be obtained from teh author as a tar archive, which is placed in the `private_code` directory.

Two implementations are supported: versions 26 (C) and version 29 (C++).

#### EXOTRANS ([Grziwa et al. 2012](https://ui.adsabs.harvard.edu/abs/2012MNRAS.420.1045G/abstract))

This code is not publicly available, and must be obtained from the author. We are awaiting permission from the authors to use it within PLATO.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
