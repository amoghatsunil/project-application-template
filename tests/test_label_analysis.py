import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import matplotlib
# Force non-interactive backend during tests to avoid GUI windows
matplotlib.use('Agg')
from label_analysis import LabelAnalysis


class TestLabelAnalysis(unittest.TestCase):
    @patch('label_analysis.plt.show')
    @patch('label_analysis.plt.subplots')
    def test_label_frequency_and_avg_resolution(self, mock_subplots, mock_show):
        """Label frequency and average resolution time plotting inputs."""
        ax0 = MagicMock()
        ax1 = MagicMock()
        mock_subplots.return_value = (MagicMock(), [ax0, ax1])

        issues = [
            {'labels': ['bug', 'enhancement'], 'state': 'open', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-01-02T00:00:00Z'},
            {'labels': ['bug'], 'state': 'closed', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-02-01T00:00:00Z'},
            {'labels': ['task', 'bug'], 'state': 'closed', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-01-16T00:00:00Z'},
        ]

        la = LabelAnalysis()
        la.load_data = lambda: setattr(la, 'issues', issues)
        la.run()

        ax0.bar.assert_called_once()
        labels_arg = list(ax0.bar.call_args[0][0])
        counts_arg = list(ax0.bar.call_args[0][1])
        self.assertIn('bug', labels_arg)
        self.assertEqual(counts_arg[labels_arg.index('bug')], 3)

        ax1.bar.assert_called_once()
        avg_labels = list(ax1.bar.call_args[0][0])
        avg_values = list(ax1.bar.call_args[0][1])
        self.assertEqual(len(avg_labels), len(avg_values))

    @patch('label_analysis.plt.show')
    @patch('label_analysis.plt.subplots')
    def test_ignores_non_closed_and_missing_dates(self, mock_subplots, mock_show):
        """Only closed issues with valid dates are used for resolution times."""
        ax0 = MagicMock()
        ax1 = MagicMock()
        mock_subplots.return_value = (MagicMock(), [ax0, ax1])

        issues = [
            {'labels': ['a'], 'state': 'closed', 'created_date': None, 'updated_date': '2020-01-10T00:00:00Z'},
            {'labels': ['a'], 'state': 'open', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': None},
            {'labels': ['a'], 'state': 'closed', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-01-11T00:00:00Z'},
        ]

        la = LabelAnalysis()
        la.load_data = lambda: setattr(la, 'issues', issues)
        la.run()

        ax0.bar.assert_called_once()
        ax1.bar.assert_called_once()
        avg_vals = list(ax1.bar.call_args[0][1])
        self.assertEqual(len(avg_vals), 1)

    @patch('label_analysis.plt.show')
    @patch('label_analysis.plt.subplots')
    def test_dict_labels_as_open_issues(self, mock_subplots, mock_show):
        """Dict-format labels on open issues are counted and do not cause errors."""
        ax0 = MagicMock()
        ax1 = MagicMock()
        mock_subplots.return_value = (MagicMock(), [ax0, ax1])

        issues = [
            {'labels': [{'name': 'bug'}], 'state': 'open', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-01-02T00:00:00Z'},
            {'labels': ['bug'], 'state': 'closed', 'created_date': '2020-01-01T00:00:00Z', 'updated_date': '2020-01-16T00:00:00Z'},
        ]

        la = LabelAnalysis()
        la.load_data = lambda: setattr(la, 'issues', issues)
        la.run()

        ax0.bar.assert_called_once()
        labels_arg = list(ax0.bar.call_args[0][0])
        self.assertIn('bug', labels_arg)


if __name__ == '__main__':
    unittest.main()
