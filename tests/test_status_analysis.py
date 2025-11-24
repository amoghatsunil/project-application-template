import io
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import matplotlib

# Force a headless backend so plotting doesn't require a GUI during tests
matplotlib.use("Agg")

import status_analysis


class StatusAnalysisTests(unittest.TestCase):
    @patch("status_analysis.plt.show")  # prevent the real GUI from popping up
    def test_run_collects_states_and_labels(self, mock_show):
        # Synthetic issues to exercise the main run path: open with status labels,
        # open without status (becomes "unassigned"), and a closed issue.
        issues = [
            SimpleNamespace(state="open", labels=["status/in-review", "status/done"]),
            SimpleNamespace(state="open", labels=["priority/high"]),
            SimpleNamespace(state="closed", labels=["status/closed"]),
        ]

        # Patch dependencies: send output plot to a temp dir, mock DataLoader and config.
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "status_analysis.OUTPUT_PNG", Path(tmp_dir) / "status.png"
        ), patch(
            "status_analysis.DataLoader"
        ) as loader_mock, patch(
            "status_analysis.config.get_parameter",
            side_effect=lambda name, default=None: "tester" if name == "user" else None,
        ):
            loader_mock.return_value.get_issues.return_value = issues

            analysis = status_analysis.StatusAnalysis()
            analysis.run()

            # Verify collected states and parsed status labels cover open/closed and unassigned paths.
            self.assertEqual(analysis.states.count("open"), 2)
            self.assertEqual(analysis.states.count("closed"), 1)
            self.assertListEqual(
                analysis.open_status_labels, ["in-review", "done", "unassigned"]
            )
            # White-box check that plotting executed and wrote a file.
            self.assertTrue(
                Path(status_analysis.OUTPUT_PNG).exists(),
                "Expected analysis plot to be written",
            )

    @patch("status_analysis.plt.show")
    def test_plot_analysis_handles_no_status_items(self, mock_show):
        # Directly exercise the branch where there are no open status items.
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "status_analysis.OUTPUT_PNG", Path(tmp_dir) / "status_empty.png"
        ):
            analysis = status_analysis.StatusAnalysis()
            # Capture output to ensure method completes without errors
            buffer = io.StringIO()
            with patch("sys.stdout", buffer):
                analysis._plot_analysis(
                    state_sizes=[1, 1],
                    state_labels=["open", "closed"],
                    status_items=[],
                    status_keys=[],
                    status_vals=[],
                )

            # Even with no data, plot generation should still create a file.
            self.assertTrue(
                Path(status_analysis.OUTPUT_PNG).exists(),
                "Expected plot to be written even when no status items are present",
            )


if __name__ == "__main__":
    unittest.main()
