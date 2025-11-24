import unittest
import json
from unittest.mock import patch, mock_open
import data_loader
from model import Issue

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # We have to clear the cache before every test, otherwise
        # the tests will interfere with each other.
        data_loader._ISSUES = None

    @patch('config.get_parameter')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"title": "fresh", "state": "open"}]')
    def test_loading_fresh(self, mock_file, mock_conf):
        # First time calling get_issues(), it should actually read the file.
        mock_conf.return_value = "dummy.json"
        
        dl = data_loader.DataLoader()
        results = dl.get_issues()
        
        # Verify we got the data we mocked above
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "fresh")
        
        # Make sure it actually opened the file
        mock_file.assert_called_with("dummy.json", "r")

    @patch('config.get_parameter')
    @patch('builtins.open', new_callable=mock_open)
    def test_loading_cached(self, mock_file, mock_conf):
        # If data is already loaded, we shouldn't touch the file system again.
        
        # FIX: Added "state": "open" because model.py requires it!
        existing_issue = Issue({"title": "cached_issue", "state": "open"})
        data_loader._ISSUES = [existing_issue]
        
        dl = data_loader.DataLoader()
        results = dl.get_issues()
        
        self.assertEqual(results[0].title, "cached_issue")
        
        # This is the important part: verify open() was NEVER called
        mock_file.assert_not_called()

    @patch('config.get_parameter')
    def test_path_setup(self, mock_conf):
        # Just checking that the init grabs the path from config correctly
        mock_conf.return_value = "test_data.json"
        dl = data_loader.DataLoader()
        self.assertEqual(dl.data_path, "test_data.json")

if __name__ == '__main__':
    unittest.main()