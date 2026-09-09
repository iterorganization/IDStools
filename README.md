
# IDStools - IMAS IDS Python Tools

A comprehensive Python toolset for working with IMAS (Integrated Modelling and Analysis Suite) Interface Data Structures (IDS) in fusion research.

## Overview

IDStools provides a collection of command-line utilities and Python libraries for:
- **Database Operations**: List, copy, compare, and manipulate IDS data entries
- **Data Analysis**: Extract, validate, and analyze fusion plasma data
- **Visualization**: Plot equilibrium, profiles, and other physics quantities
- **Format Conversion**: Convert GEQDSK files to IDS equilibrium format

## Key Features

### Database Tools
- `idslist` - List available IDSs and their time slices
- `idscp` - Copy IDSs between data entries
- `idsdiff` - Compare IDSs and highlight differences
- `idsperf` - Profile IDS access performance
- `dblist` - List database entries and pulses

### Analysis Tools
- `eqdsk2ids` - Convert GEQDSK equilibrium files to IDS format
- `idsprint` - Print IDS data values and structures
- `idsresample` - Resample IDS data in time
- `plotequilibrium` - Plot equilibrium data
- `plotkineticprofiles` - Visualize kinetic profiles

### Data Validation
- Built-in COCOS (Coordinate Conventions) validation
- IDS structure and physics consistency checks
- Data quality assessment tools

## Installation

### From PyPI
```bash
pip install imas-idstools
```

### From Source
```bash
git clone https://github.com/iter-organization/IDStools.git
cd IDStools
pip install .
```

## Quick Start

### List IDSs in a pulse
```bash
idslist --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"
```

### Plot equilibrium
```bash
plotequilibrium --uri "imas:mdsplus?user=public;pulse=134174;run=117;database=ITER;version=3"
```

## Requirements

- Python ≥ 3.10

### Installed automatically via pip
- NumPy, Matplotlib, Pandas
- Rich (for enhanced terminal output)

### Requires separate installation
- **Tkinter** — usually bundled with Python but may require system packages:
  - Linux (Debian/Ubuntu): `sudo apt install python3-tk`
  - Linux (RHEL/CentOS/Rocky): `sudo dnf install python3-tkinter`
  - Windows: included in the [python.org](https://www.python.org/downloads/) installer ("tcl/tk and IDLE" component, enabled by default)
  - macOS (python.org installer): included by default
  - macOS (Homebrew): `brew install python-tk` (or `brew install python-tk@3.x` for a specific version)

## Documentation

Full documentation is available at the project repository. Each tool includes built-in help:
```bash
<tool-name> --help
```

## Contributing

We welcome contributions from the fusion community! Please see `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the terms specified in `LICENSE.md`.

## Support

For questions and support, contact: imas-support@iter.org