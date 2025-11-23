# tests/test_keyword_analysis.py
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import matplotlib

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use non-GUI backend for matplotlib during tests
matplotlib.use("Agg")

from keyword_analysis import KeywordAnalysis


class TestKeywordAnalysis(unittest.TestCase):
    # ------------------------------------------------------------------ #
    #  __init__ / configuration
    # ------------------------------------------------------------------ #
    @patch("keyword_analysis.config.get_parameter", return_value=None)
    def test_init_without_keyword_exits(self, mock_get_param):
        """If no --keyword is provided, the analysis should exit with error."""
        with self.assertRaises(SystemExit):
            KeywordAnalysis()
        mock_get_param.assert_called_once_with("keyword")

    # ------------------------------------------------------------------ #
    #  _find_sentences_with_keyword / noise filtering
    # ------------------------------------------------------------------ #
    @patch("keyword_analysis.config.get_parameter", return_value="error")
    def test_find_sentences_filters_noise_and_keeps_keyword(self, mock_get_param):
        """_find_sentences_with_keyword keeps meaningful sentences and drops noise."""
        ka = KeywordAnalysis()

        text = (
            "Error occurred when connecting to the database. "
            "Traceback (most recent call last):\n"
            '  File "/usr/lib/python3.10/site-packages/foo.py", line 10, in <module>\n'
            "    raise ValueError('boom')\n"
            "Some additional context without the keyword."
        )

        matches = ka._find_sentences_with_keyword(text)

        # We should keep the human-readable sentence that contains the keyword
        self.assertTrue(any("Error occurred" in s for s in matches))

        # Lines that look like pure traceback / noise and don't contain the keyword
        # should be filtered out.
        self.assertFalse(any("Traceback" in s for s in matches))

        # All returned sentences should be non-empty and not exceed the truncation length
        self.assertTrue(all(len(s) > 0 for s in matches))
        self.assertTrue(all(len(s) <= 253 for s in matches))  # 250 + "..."

    # ------------------------------------------------------------------ #
    #  run() – branch with no results
    # ------------------------------------------------------------------ #
    @patch("keyword_analysis.config.get_parameter", return_value="keyword")
    def test_run_no_matching_issues_skips_plot_and_file(self, mock_get_param):
        """If no issue contains the keyword, no file is written and no chart is shown."""
        # Issues that do NOT contain the keyword "keyword"
        issues = [
            MagicMock(title="First issue", text="Nothing interesting here."),
            MagicMock(title="Second", text="Another description."),
        ]

        with patch("keyword_analysis.DataLoader") as mock_loader_cls, \
             patch("keyword_analysis.plt.show") as mock_show, \
             patch("keyword_analysis.open", mock_open(), create=True) as m_open:
            mock_loader = mock_loader_cls.return_value
            mock_loader.get_issues.return_value = issues

            ka = KeywordAnalysis()
            ka.run()

            # No chart and no file when there are no results
            mock_show.assert_not_called()
            m_open.assert_not_called()

    # ------------------------------------------------------------------ #
    #  run() – branch with results, file write and bar chart
    # ------------------------------------------------------------------ #
    @patch("keyword_analysis.config.get_parameter", return_value="error")
    def test_run_writes_results_and_plots_for_matches(self, mock_get_param):
        """When matches are found, results are written and a bar chart is produced."""
        # One issue with three matches of "error"
        issue1 = MagicMock()
        issue1.title = "Database error"
        issue1.text = "Error connecting to DB. Another error occurred."

        # One issue with two matches
        issue2 = MagicMock()
        issue2.title = "Minor error in UI"
        issue2.text = "An error is shown when clicking the button."

        issues = [issue1, issue2]

        with patch("keyword_analysis.DataLoader") as mock_loader_cls, \
             patch("keyword_analysis.plt.show") as mock_show, \
             patch("keyword_analysis.plt.barh") as mock_barh, \
             patch("keyword_analysis.open", mock_open(), create=True) as m_open:

            mock_loader = mock_loader_cls.return_value
            mock_loader.get_issues.return_value = issues

            ka = KeywordAnalysis()
            ka.run()

            # File should be written
            self.assertTrue(m_open.called)
            open_call_args = m_open.call_args[0]
            self.assertIn("keyword_results.txt", open_call_args[0])

            # Bar chart should be drawn with counts matching the number of matches
            self.assertTrue(mock_barh.called)
            counts_arg = list(mock_barh.call_args[0][1])
            # issue1 has 3 matches, issue2 has 2 matches
            self.assertEqual(sorted(counts_arg), [2, 3])

            # Chart shown once
            mock_show.assert_called_once()

    # ------------------------------------------------------------------ #
    #  _find_sentences_with_keyword – fallback snippet path
    # ------------------------------------------------------------------ #
    @patch("keyword_analysis.config.get_parameter", return_value="keyword")
    def test_run_uses_snippet_when_no_sentences_found(self, mock_get_param):
        """If no sentences are returned, run() should fall back to a snippet."""
        issue = MagicMock()
        issue.title = "Keyword issue"
        issue.text = "Prefix text " + ("keyword " * 5) + "suffix"

        with patch("keyword_analysis.DataLoader") as mock_loader_cls, \
             patch.object(KeywordAnalysis, "_find_sentences_with_keyword", return_value=[]), \
             patch("keyword_analysis.open", mock_open(), create=True) as m_open, \
             patch("keyword_analysis.plt.barh") as mock_barh, \
             patch("keyword_analysis.plt.show"):

            mock_loader = mock_loader_cls.return_value
            mock_loader.get_issues.return_value = [issue]

            ka = KeywordAnalysis()
            ka.run()

            # A file should still be written even when we rely on the snippet fallback
            self.assertTrue(m_open.called)

            # And we should still produce a bar chart entry for that issue
            self.assertTrue(mock_barh.called)


if __name__ == "__main__":
    unittest.main()
