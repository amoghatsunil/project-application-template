import unittest
import os
import json
from unittest.mock import patch, MagicMock
import config

class TestConfig(unittest.TestCase):

    def setUp(self):
        # Reset the global config before every test so we start fresh
        config._config = None
        
    def test_convert_values(self):
        # Test the helper that converts strings to types
        self.assertEqual(config.convert_to_typed_value("123"), 123)
        self.assertEqual(config.convert_to_typed_value("true"), True)
        self.assertEqual(config.convert_to_typed_value('{"a": 1}'), {'a': 1})
        self.assertEqual(config.convert_to_typed_value("just text"), "just text")
        self.assertIsNone(config.convert_to_typed_value(None))
        self.assertEqual(config.convert_to_typed_value(100), 100)

    @patch.dict(os.environ, {"MY_VAR": "some_value", "JSON_VAR": "json:123"}, clear=True)
    def test_get_parameter_env(self):
        # Environment variables should take priority
        val = config.get_parameter("MY_VAR")
        self.assertEqual(val, "some_value")
        
        # Test the special "json:" prefix logic
        val_json = config.get_parameter("JSON_VAR")
        self.assertEqual(val_json, 123)

    def test_get_parameter_defaults(self):
        # Check fallback to default if not in config
        val = config.get_parameter("MISSING_KEY", default="my_default")
        self.assertEqual(val, "my_default")
        
        # Check returns None if no default provided
        val_none = config.get_parameter("REALLY_MISSING")
        self.assertIsNone(val_none)

    @patch('config._get_default_path')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"file_key": "file_value"}')
    def test_init_config_loads_file(self, mock_file, mock_path):
        # Pretend we found a config.json file
        mock_path.return_value = "/fake/path/config.json"
        
        # This should load the file content into _config
        val = config.get_parameter("file_key")
        self.assertEqual(val, "file_value")

    @patch('config._get_default_path')
    def test_init_config_no_file(self, mock_path):
        # Pretend no config file exists
        mock_path.return_value = None
        
        # Should initialize empty config and not crash
        config._init_config()
        self.assertEqual(config._config, {})

    @patch('config._get_default_path')
    def test_init_config_already_loaded(self, mock_path):
        # If config is already loaded, it shouldn't try to load again
        config._config = {'existing': 1}
        config._init_config()
        mock_path.assert_not_called()

    @patch('os.getcwd')
    @patch('os.path.isfile')
    def test_find_config_path(self, mock_isfile, mock_getcwd):
        # Scenario 1: Config is right here
        mock_getcwd.return_value = "/app"
        mock_isfile.return_value = True
        path = config._get_default_path()
        self.assertTrue(path.endswith("config.json"))

        # Scenario 2: Traverse up the tree (fail first, find second)
        mock_isfile.side_effect = [False, True] 
        path = config._get_default_path()
        self.assertIsNotNone(path)

    @patch('os.getcwd')
    @patch('os.path.isfile')
    def test_config_not_found(self, mock_isfile, mock_getcwd):
        # Scenario: Traverse all the way to root and find nothing
        mock_getcwd.return_value = "/" 
        mock_isfile.return_value = False
        
        path = config._get_default_path()
        self.assertIsNone(path)

    @patch.dict(os.environ, {}, clear=True)
    def test_set_parameter(self):
        # Test setting a simple string
        config.set_parameter("NEW_VAR", "test")
        self.assertEqual(os.environ["NEW_VAR"], "test")
        
        # Test setting a complex object (should get json prefix)
        config.set_parameter("COMPLEX_VAR", [1, 2])
        self.assertEqual(os.environ["COMPLEX_VAR"], "json:[1, 2]")

    def test_overwrite_args(self):
        # Mocking a class to act like argparse arguments
        class Args:
            def __init__(self):
                self.arg1 = "val1"
                self.arg2 = None 

        args = Args()
        
        with patch.dict(os.environ, {}, clear=True):
            config.overwrite_from_args(args)
            self.assertEqual(os.environ.get("arg1"), "val1")
            self.assertIsNone(os.environ.get("arg2"))

        # Test passing something broken to trigger the except blocks
        config.overwrite_from_args(None)

if __name__ == '__main__':
    unittest.main()