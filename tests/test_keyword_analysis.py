import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import matplotlib

# Use non-interactive backend to prevent GUI windows during tests
matplotlib.use("Agg")

# Adjust path to find the parent directory modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from keyword_analysis import KeywordAnalysis
from model import Issue

class TestKeywordAnalysis(unittest.TestCase):

    # ------------------------------------------------------------------
    # 1. INIT & CONFIGURATION TESTS
    # ------------------------------------------------------------------
    @patch("keyword_analysis.config.get_parameter", return_value=None)
    def test_init_exits_without_keyword(self, mock_conf):
        """Test that the app calls sys.exit(1) if keyword is missing."""
        with self.assertRaises(SystemExit) as cm:
            KeywordAnalysis()
        self.assertEqual(cm.exception.code, 1)

    @patch("keyword_analysis.config.get_parameter", return_value="test")
    def test_init_success(self, mock_conf):
        """Test successful initialization."""
        ka = KeywordAnalysis()
        self.assertEqual(ka.KEYWORD, "test")

    # ------------------------------------------------------------------
    # 2. SENTENCE PARSING & LOGIC TESTS (CRITICAL FOR COVERAGE)
    # ------------------------------------------------------------------
    @patch("keyword_analysis.config.get_parameter", return_value="error")
    def test_find_sentences_comprehensive(self, mock_conf):
        """
        Hits EVERY branch in _find_sentences_with_keyword:
        1. Code Blocks (regex sub) -> stripped
        2. Whitespace cleanup -> stripped
        3. Keyword match -> kept
        4. Keyword match (Long) -> truncated
        5. Noise (Traceback) -> skipped
        6. Normal text (No keyword) -> skipped
        """
        ka = KeywordAnalysis()
        
        # This string is crafted to hit every single parsing logic line
        text = (
            "   \n"                              # Whitespace (Should be skipped)
            "```\ncode block with error\n```\n"  # Code block (Should be removed by regex)
            "Error occurred.\n"                  # Normal Match (Should be kept)
            + ("Big error " * 50) + ".\n"        # Long Match (Should be truncated)
            "Traceback (most recent call).\n"    # Noise (Should be skipped)
            "Just some normal text."             # Non-match (Should be skipped)
        )

        matches = ka._find_sentences_with_keyword(text)

        # 1. Verify Code Block was removed (regex sub check)
        self.assertFalse(any("code block" in s for s in matches))

        # 2. Verify Normal Match kept
        self.assertTrue(any("Error occurred" in s for s in matches))
        
        # 3. Verify Truncation logic (len > 250)
        long_matches = [s for s in matches if len(s) > 200]
        self.assertTrue(len(long_matches) > 0)
        self.assertTrue(long_matches[0].endswith("..."))
        self.assertLessEqual(len(long_matches[0]), 253)

        # 4. Verify Noise dropped (elif branch)
        self.assertFalse(any("Traceback" in s for s in matches))
        
        # 5. Verify Normal text dropped (implicit else)
        self.assertFalse(any("Just some normal text" in s for s in matches))

    @patch("keyword_analysis.config.get_parameter", return_value="C++")
    def test_regex_special_chars(self, mock_conf):
        """Test that regex characters in keywords don't break the search."""
        ka = KeywordAnalysis()
        text = "I use C++ daily."
        matches = ka._find_sentences_with_keyword(text)
        self.assertTrue(len(matches) > 0)
        self.assertIn("I use C++ daily", matches[0])

    # ------------------------------------------------------------------
    # 3. RUN() EXECUTION FLOWS
    # ------------------------------------------------------------------
    @patch("keyword_analysis.config.get_parameter", return_value="bug")
    def test_run_with_no_matches(self, mock_conf):
        """Test the 'if not results' branch (Early Exit)."""
        issue = Issue({"title": "Clean", "text": "Everything is fine.", "state": "open"})
        
        with patch("keyword_analysis.DataLoader") as mock_loader, \
             patch("keyword_analysis.plt.show") as mock_show, \
             patch("keyword_analysis.open", mock_open()) as mock_file:
            
            mock_loader.return_value.get_issues.return_value = [issue]
            
            ka = KeywordAnalysis()
            ka.run()
            
            # Should NOT plot or write file
            mock_show.assert_not_called()
            mock_file.assert_not_called()

    @patch("keyword_analysis.config.get_parameter", return_value="bug")
    def test_run_with_matches_normal(self, mock_conf):
        """Test the 'if results' branch (Plotting & File Write)."""
        issue = Issue({"title": "Bug Report", "text": "There is a bug here.", "state": "open"})
        
        with patch("keyword_analysis.DataLoader") as mock_loader, \
             patch("keyword_analysis.plt.show") as mock_show, \
             patch("keyword_analysis.plt.barh") as mock_barh, \
             patch("keyword_analysis.open", mock_open()) as mock_file:
            
            mock_loader.return_value.get_issues.return_value = [issue]
            
            ka = KeywordAnalysis()
            ka.run()
            
            # Should write file
            self.assertTrue(mock_file.called)
            # Should plot
            self.assertTrue(mock_show.called)
            # Verify bar chart was called
            self.assertTrue(mock_barh.called)

    @patch("keyword_analysis.config.get_parameter", return_value="security")
    def test_run_fallback_snippet_logic(self, mock_conf):
        """
        Test the 'if not sentences' branch inside the loop.
        This forces the code to use the string slicing fallback.
        """
        ka = KeywordAnalysis()
        
        # Mocking _find_sentences to return [] triggers the fallback logic
        with patch.object(ka, '_find_sentences_with_keyword', return_value=[]):
            
            issue = Issue({"title": "Alert", "text": "A security issue exists.", "state": "open"})
            
            with patch("keyword_analysis.DataLoader") as mock_loader, \
                 patch("keyword_analysis.plt.show"), \
                 patch("keyword_analysis.open", mock_open()) as mock_file:
                
                mock_loader.return_value.get_issues.return_value = [issue]
                ka.run()
                
                # Check that we still wrote to file
                self.assertTrue(mock_file.called)
                
                # Verify we captured the text via fallback slicing
                handle = mock_file()
                args, _ = handle.write.call_args_list[1]
                self.assertIn("security issue", args[0])

if __name__ == "__main__":
    unittest.main()