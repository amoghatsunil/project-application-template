import json
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

class LabelResolutionAnalysis:
    def __init__(self, data_path='data/poetry_issues_all.json'):
        self.data_path = data_path
        self.issues = []

    def load_data(self):
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.issues = json.load(f)

    def parse_date(self, date_str):
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def run(self):
        self.load_data()

        # Label frequency calculation
        label_count = Counter()
        for issue in self.issues:
            labels = issue.get('labels', [])
            for label in labels:
                label_name = label if isinstance(label, str) else label.get('name', '')
                if label_name:
                    label_count[label_name] += 1

        top_labels = [l for l, _ in label_count.most_common(15)]
        top_label_counts = [label_count[l] for l in top_labels]

        # Average resolution time computation (closed issues only, in months)
        label_resolution_sum = defaultdict(float)
        label_resolution_count = defaultdict(int)

        for issue in self.issues:
            if issue.get('state') != 'closed':
                continue

            created = self.parse_date(issue.get('created_date'))
            updated = self.parse_date(issue.get('updated_date'))
            if not created or not updated:
                continue

            resolution_days = (updated - created).total_seconds() / (24 * 3600)
            resolution_months = resolution_days / 30.44

            for label in issue.get('labels', []):
                label_resolution_sum[label] += resolution_months
                label_resolution_count[label] += 1

        avg_resolution_time = {
            label: label_resolution_sum[label] / label_resolution_count[label]
            for label in label_resolution_sum
        }

        avg_times_top_labels = [avg_resolution_time.get(label, 0) for label in top_labels]

        # Plotting
        fig, axs = plt.subplots(1, 2, figsize=(16, 6))

        axs[0].bar(top_labels, top_label_counts, color='skyblue')
        axs[0].set_title('Label Frequency (Top 15)')
        axs[0].set_xlabel('Labels')
        axs[0].set_ylabel('Count')
        axs[0].tick_params(axis='x', rotation=60)

        axs[1].bar(top_labels, avg_times_top_labels, color='coral')
        axs[1].set_title('Average Resolution Time (months) Per Label (Closed issues only)')
        axs[1].set_xlabel('Labels')
        axs[1].set_ylabel('Avg Resolution Time (months)')
        axs[1].tick_params(axis='x', rotation=60)
        axs[1].yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

        plt.tight_layout()
        plt.show()
