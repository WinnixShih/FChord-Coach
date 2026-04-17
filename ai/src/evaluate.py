import torch
import numpy as np
import matplotlib.pyplot as plt
from torch_geometric.loader import DataLoader
from sklearn.metrics import confusion_matrix, classification_report

from .dataset import FChordDataset
from .model   import FChordGNN
from .graph   import IDX_TO_LABEL, NUM_CLASSES


def evaluate(weights_path: str = "models/fchord_gnn.pt", data_dir: str = "data"):
    dataset = FChordDataset(data_dir)
    loader  = DataLoader(dataset, batch_size=64)

    model = FChordGNN()
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            pred = model(batch.x, batch.edge_index, batch.batch).argmax(dim=-1)
            all_preds.extend(pred.tolist())
            all_labels.extend(batch.y.tolist())

    labels = [IDX_TO_LABEL[i] for i in range(NUM_CLASSES)]
    print(classification_report(all_labels, all_preds, target_names=labels))

    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(NUM_CLASSES)); ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticks(range(NUM_CLASSES)); ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.tight_layout()
    plt.savefig("models/confusion_matrix.png", dpi=150)
    print("Saved → models/confusion_matrix.png")


if __name__ == "__main__":
    evaluate()
