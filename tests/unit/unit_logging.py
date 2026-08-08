import logging
from unittest.mock import patch

from copilot_app.utils.logging_setup import init_logging


def unit_init_logging_configures_basic_config():
    with patch("logging.basicConfig") as mock_basic:
        init_logging()
        mock_basic.assert_called_once()
        _, kwargs = mock_basic.call_args
        assert kwargs["level"] == logging.INFO
        assert "%(asctime)s" in kwargs["format"]
        assert "%(levelname)s" in kwargs["format"]
        assert "%(name)s" in kwargs["format"]


def unit_init_logging_idempotent():
    with patch("logging.basicConfig") as mock_basic:
        init_logging()
        init_logging()
        assert mock_basic.call_count == 2