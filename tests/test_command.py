import unittest
from pathlib import Path
from unittest.mock import patch

from publishing_qa import cli
from unittest.mock import patch

from publishing_qa.command import main


class CommandTests(unittest.TestCase):
    def test_unknown_command_returns_usage_error(self):
        with patch("sys.argv",["ploos-qa","nope"]):
            self.assertEqual(main(),2)

    def test_release_is_dispatched(self):
        with patch("sys.argv",["ploos-qa","release","--x"]), patch("publishing_qa.command.release_main",return_value=7) as release:
            self.assertEqual(main(),7)
            release.assert_called_once_with(["--x"])


if __name__=="__main__":
    unittest.main()
