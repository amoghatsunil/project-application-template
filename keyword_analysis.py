# keyword_analysis.py
from typing import List
from data_loader import DataLoader
from model import Issue
import config
import os
import sys

class KeywordAnalysis:
    """
    Searches all issues for a given keyword (case-insensitive)
    and prints the titles of issues that contain that keyword.
    """

    def __init__(self):
        # Get keyword parameter from command line (populated via config.overwrite_from_args in run.py)
        self.KEYWORD: str = config.get_parameter('keyword')

        # Gracefully handle missing keyword argument
        if not self.KEYWORD:
            print("❗ Error: The '--keyword' parameter is required for this analysis.")
            print("Usage: python run.py --feature 1 --keyword <word>")
            sys.exit(1)  # exit cleanly, not crash

        # normalize
        self.keyword_normalized = self.KEYWORD.strip().lower()

    def run(self):
        """
        Executes the keyword search and prints results.
        """
        # Load all issues using DataLoader
        issues: List[Issue] = DataLoader().get_issues()

        # Filter issues where keyword appears in title or text (case-insensitive)
        matching_issues = []
        for issue in issues:
            title = issue.title or ""
            text = issue.text or ""
            if self.keyword_normalized in title.lower() or self.keyword_normalized in text.lower():
                matching_issues.append(issue)

        # Print result summary and details
        print(f"\nSearching for keyword: '{self.KEYWORD}' (case-insensitive)")
        if matching_issues:
            print(f"Found {len(matching_issues)} matching issue(s):\n")
            for issue in matching_issues:
                print(f"- {issue.title}")
        else:
            print("No issues found that match the given keyword.\n")

        # Write results file (overwrite existing)
        out_path = "keyword_results.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            if matching_issues:
                for issue in matching_issues:
                    f.write(f"{issue.title}\n")
            else:
                f.write(f"No issues found for keyword: {self.KEYWORD}\n")

        print(f"\nResults saved to '{os.path.abspath(out_path)}'\n")


if __name__ == '__main__':
    KeywordAnalysis().run()