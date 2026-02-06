# ftva-etl
Python package for UCLA FTVA MAMS ETL, for use in multiple projects.

# Testing
Tests for this package are organized under the `tests` directory, mirroring the structure of the `src` directory.

Tests can be auto-discovered and run using `python -m unittest` from within the project's dev container, or by running `docker compose exec ftva_etl python -m unittest` from outside the dev container.

# Logging
This package uses Python's standard `logging` library for handling logs. Consuming applications can enable logs within the package using the `configure_logging()` function in `ftva_etl.metadata.utils`. The function accepts several parameters that allow configuration of logging behavior:
- `enable_logging`: boolean. Defaults to False. Allows logging to be turned on or off.
- `log_level`: int. Defaults to `logging.INFO`, which has numeric value 20. Allows for the threshold at which log records will be logged to be set.
- `handler`: `logging.Handler` instance. Defaults to `StreamHandler` outputting to `stdout` if logging is enabled and this param is left out. Can be used to set a `FileHandler`, for example.
- `formatter`: `logging.Formatter` instance. Defaults to `"%(asctime)s - %(name)s - %(levelname)s: %(message)s"` if logging is enabled and this param is left out. Can be used to set a different format.

### Example logging usage
```python
# Main package imports as needed
from ftva_etl import (
    FilemakerClient,
    AlmaSRUClient,
    DigitalDataClient,
    get_mams_metadata,
)
# Then logging-specific imports
import logging
from ftva_etl.metadata.utils import configure_logging

# EXAMPLE: configure file-based logging at the WARNING level.
# DEBUG and INFO messages will be ignored, while WARNING and above will be captured.
custom_handler = logging.FileHandler("example.log")
configure_logging(enable_logging=True, log_level=logging.WARNING, handler=custom_handler)

# Continue using package as normal
# get_mams_metadata(), etc
```

### Developer notes
Modules under `ftva_etl.metadata` can connect to the package logger by creating a new logger using their `__name__` attribute. For example:

```python
# module.py
import logging

logger = logging.getLogger(__name__)

logger.info("Example info message")
```

Logger messages can then be added to code as needed. **Note**: under default configuration with `configure_logging(enable_logging=True)`, `logging.DEBUG` messages will be ignored.
