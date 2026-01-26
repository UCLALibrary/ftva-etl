# Set up logging for the package during import.
# This ensures that loggers created by modules will be children of this logger,
# rather than the root logger.
import logging

package_logger = logging.getLogger(__name__)
package_logger.addHandler(logging.NullHandler())  # disable logging by default
package_logger.propagate = False  # stop package logs from propagating to root

# Expose these directly for convenience;
# ignore linter's complaints about not being used.

# Clients
from .clients.alma_sru_client import AlmaSRUClient  # noqa
from .clients.filemaker_client import FilemakerClient  # noqa
from .clients.digital_data_client import DigitalDataClient  # noqa

# Metadata generator
from .metadata.mams_metadata import get_mams_metadata  # noqa
