from typing import List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path

from data_loader import DataLoader
from model import Issue,Event
import config

_TOP_K_STATUSES = 10
class StatusAnalysis:
    """
    Implements an example analysis of GitHub
    issues and outputs the result of that analysis.
    """
    
    def __init__(self):
        """
        Constructor
        """
        # Parameter is passed in via command line (--user)
        self.USER:str = config.get_parameter('user')
        self.states: List[str] = []
        self.open_status_labels: List[str] = []
    
    def run(self):
        """
        Starting point for this analysis.
        
        Note: this is just an example analysis. You should replace the code here
        with your own implementation and then implement two more such analyses.
        """
        issues:List[Issue] = DataLoader().get_issues()
        
        ### BASIC STATISTICS
        # Calculate the total number of events for a specific user (if specified in command line args)
        total_events:int = 0
        for issue in issues:
            state = issue.state
            self.states.append(state)

            if state == "open":
                labels = issue.labels

                status_found = False
                for label in labels:
                    if isinstance(label, str) and label.startswith("status/"):
                        self.open_status_labels.append(label[len("status/"):])
                        status_found = True
                if not status_found:
                    self.open_status_labels.append("unassigned")

        # for state analysis
        state_counts = Counter(self.states)
        state_labels = list(state_counts.keys())
        state_sizes = [state_counts[k] for k in state_labels]

        # for open state label analysis
        status_counts_all = Counter(self.open_status_labels)
        status_counts = Counter(dict(status_counts_all.most_common(_TOP_K_STATUSES)))
        status_items = sorted(status_counts.items(), key=lambda kv: kv[1], reverse=True)
        status_keys = [k for k, _ in status_items]
        status_vals = [v for _, v in status_items]

        # print summary
        print("\n\n")
        print("Issue status counts:")
        for label in state_labels:
            print(f"  {label}: {state_counts[label]}")
        print("\nOpen issue status labels:")
        for label, cnt in status_items:
            print(f"  {label}: {cnt}")
        print("\n\n")
        # plot
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        # Left: Pie for open vs closed
        axes[0].pie(state_sizes, labels=state_labels, autopct="%1.1f%%", startangle=90)
        axes[0].set_title("Issue Status Distribution (Open vs Closed)")
        axes[0].axis("equal")

        # Right: Horizontal bar for open issue statuses
        ax = axes[1]
        if status_items:
            y = np.arange(len(status_keys))
            ax.barh(y, status_vals)
            ax.set_yticks(y, labels=status_keys)
            ax.invert_yaxis()  # largest on top
            ax.set_xlabel("Count")
            ax.set_title("Open Issues by Status Type")

            # Add value labels at the end of each bar
            for i, v in enumerate(status_vals):
                ax.text(v, i, f" {v}", va="center", ha="left")
        else:
            ax.axis("off")
            ax.text(0.5, 0.5, "No open issues (or no matching status labels)",
                    ha="center", va="center", transform=ax.transAxes)

        # plt.tight_layout()
        # plt.savefig(OUTPUT_PNG, dpi=200)
        # print(f"\nSaved figure to: {OUTPUT_PNG.resolve()}")
        plt.show()

if __name__ == '__main__':
    # Invoke run method when running this module directly
    StatusAnalysis().run()