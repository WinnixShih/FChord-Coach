import json
import glob
from pathlib import Path
from torch_geometric.data import InMemoryDataset
from .graph import nodes_to_graph, LABEL_MAP


class FChordDataset(InMemoryDataset):
    """
    Loads all JSON samples under data_dir/<label>/*.json.

    Expected JSON format:
        { "label": "correct", "nodes": [[x,y,z], ...] }  # 21 nodes
    """

    def __init__(self, data_dir: str = "data"):
        super().__init__(root=None)
        graphs = []
        skipped = 0

        for path in glob.glob(f"{data_dir}/**/*.json", recursive=True):
            try:
                d = json.load(open(path))
                label = d.get("label")
                nodes = d.get("nodes")

                if label not in LABEL_MAP:
                    skipped += 1
                    continue
                if not nodes or len(nodes) != 21:
                    skipped += 1
                    continue

                graphs.append(nodes_to_graph(nodes, label=label))
            except Exception as e:
                print(f"[WARN] {path}: {e}")
                skipped += 1

        if skipped:
            print(f"[INFO] Skipped {skipped} invalid samples")

        self.data, self.slices = self.collate(graphs)

    def __repr__(self):
        from collections import Counter
        labels = [self.get(i).y.item() for i in range(len(self))]
        dist   = dict(Counter(labels))
        return f"FChordDataset({len(self)} samples, dist={dist})"
