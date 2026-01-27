from io import StringIO
import logging
from unittest import TestCase
from src.ftva_etl.metadata.utils import configure_logging


class TestLogging(TestCase):
    """Tests related to logging configuration and usage."""

    def setUp(self) -> None:
        """Reset logging configuration before each test."""
        # Reset to default state (disabled logging)
        configure_logging(enable_logging=False)

    def test_logging_disabled_by_default(self):
        """Test that logging is disabled by default."""
        # setUp() should reset logging to default state before each test
        logger = logging.getLogger("src.ftva_etl.metadata")

        # Should have NullHandler when disabled
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.NullHandler)
        self.assertEqual(logger.level, logging.CRITICAL)

    def test_logging_enabled_with_defaults(self):
        """Test that enabling logging uses INFO level and StreamHandler to stdout."""
        configure_logging(enable_logging=True)
        logger = logging.getLogger("src.ftva_etl.metadata")

        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        self.assertEqual(logger.level, logging.INFO)

    def test_log_messages_are_filtered_by_level(self):
        """Test that log messages are properly filtered by provided log level."""
        log_output = StringIO()
        handler = logging.StreamHandler(log_output)
        configure_logging(
            enable_logging=True, log_level=logging.WARNING, handler=handler
        )
        logger = logging.getLogger("src.ftva_etl.metadata")

        # INFO message should not be logged (level is WARNING)
        logger.info("This info message should not appear")
        self.assertEqual(log_output.getvalue(), "")

        # WARNING message should be logged
        logger.warning("This warning message should appear")
        self.assertIn("This warning message should appear", log_output.getvalue())

    def test_child_logger_inherits_parent_config(self):
        """Test that a child logger, such as that in a module,
        inherits the parent logger's configuration.
        """
        log_output = StringIO()
        handler = logging.StreamHandler(log_output)
        configure_logging(enable_logging=True, handler=handler)
        # Anything under `src.ftva_etl.metadata.*` should be recognized as a child logger
        logger = logging.getLogger("src.ftva_etl.metadata.test")
        parent_name = ""
        if logger.parent:
            parent_name = logger.parent.name

        self.assertEqual(parent_name, "src.ftva_etl.metadata")

        # Child should be able to log INFO messages via propagation to parent...
        logger.info("This info message should appear")
        self.assertIn("This info message should appear", log_output.getvalue())

        # ...but not DEBUG messages, which are below level set on parent
        logger.debug("This debug message should not appear")
        self.assertNotIn("This debug message should not appear", log_output.getvalue())
