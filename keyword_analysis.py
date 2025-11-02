# keyword_analysis.py
from typing import List
from data_loader import DataLoader
from model import Issue
import config
import os
import sys
import re
import matplotlib.pyplot as plt


class KeywordAnalysis:
    """
    Searches all issues for a given keyword (case-insensitive),
    prints issue titles and relevant context sentences, and
    shows a bar chart of keyword frequency per issue.
    """

    def __init__(self):
        self.KEYWORD: str = config.get_parameter("keyword")
        if not self.KEYWORD:
            print("Error: The '--keyword' parameter is required for this analysis.")
            print("Usage: python run.py --feature 1 --keyword <word or phrase>")
            sys.exit(1)

        self.keyword_pattern = re.compile(re.escape(self.KEYWORD.strip()), re.IGNORECASE)

    def _is_noise(self, line: str) -> bool:
        """Determines if a line looks like code, logs, or trace output."""
        noise_patterns = [
            r"Traceback", r"File ", r"FAILED", r"test_", r"tests/",
            r"/usr/", r"\\", r"venv/", r"lib/python", r"site-packages",
            r"DeprecationWarning", r"assert ", r"=+ ", r"-{5,}", r"```"
        ]
        return any(re.search(p, line, re.IGNORECASE) for p in noise_patterns)

    def _find_sentences_with_keyword(self, text: str):
        """Finds meaningful sentences containing the keyword."""
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"\s{2,}", " ", text.strip())
        sentences = re.split(r"(?<=[.!?;:])\s+|\n+", text)

        matches = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if self.keyword_pattern.search(s):  # Always keep lines with keyword
                if len(s) > 250:
                    s = s[:250] + "..."
                matches.append(s)
            elif not self.keyword_pattern.search(s) and self._is_noise(s):
                continue
        return matches

    def run(self):
        """Executes the keyword analysis."""
        issues: List[Issue] = DataLoader().get_issues()
        results = []
        total_matches = 0

        for issue in issues:
            text = (issue.title or "") + ". " + (issue.text or "")
            all_matches = self.keyword_pattern.findall(text)

            if all_matches:
                sentences = self._find_sentences_with_keyword(text)
                if not sentences:
                    # fallback: at least show a snippet around the keyword
                    snippet_index = text.lower().find(self.KEYWORD.lower())
                    snippet_start = max(0, snippet_index - 80)
                    snippet_end = min(len(text), snippet_index + 80)
                    snippet = text[snippet_start:snippet_end].strip()
                    sentences = [snippet]
                total_matches += len(all_matches)
                results.append({
                    "issue": issue,
                    "count": len(all_matches),
                    "sentences": sentences
                })

        print(f"\nLoaded {len(issues)} issues from the dataset.")
        print(f"\nSearching for keyword: '{self.KEYWORD}' (case-insensitive)")

        if not results:
            print("\nNo issues found that match the given keyword.")
            print("No chart will be displayed.\n")
            return  # Exit early, skip plotting and file writing

        print(f"Found {len(results)} issue(s) containing '{self.KEYWORD}':\n")

        for r in results:
            issue = r["issue"]
            print(f"• {issue.title}")
            for s in r["sentences"]:
                print(f"   → {s}")
            print(f"   [Matches in this issue: {r['count']}]\n")

        # Save results
        out_path = "keyword_results.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(f"{r['issue'].title}\n")
                for s in r["sentences"]:
                    f.write(f"   → {s}\n")
                f.write(f"   [Matches in this issue: {r['count']}]\n\n")
        print(f"Results saved to '{os.path.abspath(out_path)}'")
        print(f"\nKeyword '{self.KEYWORD}' appeared {total_matches} times across {len(results)} issues.\n")

        # Visualization only if results exist
        if results:
            titles = [
                r["issue"].title[:60] + ("..." if len(r["issue"].title) > 60 else "")
                for r in results
            ]
            counts = [r["count"] for r in results]

            plt.figure(figsize=(10, 6))
            plt.barh(range(len(titles)), counts)
            plt.yticks(range(len(titles)), titles)
            plt.xlabel("Number of keyword matches")
            plt.title(f"Occurrences of '{self.KEYWORD}' in matched issues")
            plt.tight_layout()
            plt.show()


if __name__ == "__main__":
    KeywordAnalysis().run()