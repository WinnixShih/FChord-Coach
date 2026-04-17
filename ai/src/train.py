import os
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from sklearn.model_selection import train_test_split

from .dataset import FChordDataset
from .model   import FChordGNN


def train(
    data_dir:   str   = "data",
    epochs:     int   = 100,
    batch_size: int   = 32,
    lr:         float = 1e-3,
    save_path:  str   = "models/fchord_gnn.pt",
):
    dataset = FChordDataset(data_dir)
    print(dataset)

    idx = list(range(len(dataset)))
    train_idx, val_idx = train_test_split(idx, test_size=0.2, random_state=42)

    train_loader = DataLoader(dataset[train_idx], batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(dataset[val_idx],   batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = FChordGNN().to(device)
    opt   = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        # ── train ──────────────────────────────────
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = batch.to(device)
            opt.zero_grad()
            out  = model(batch.x, batch.edge_index, batch.batch)
            loss = F.cross_entropy(out, batch.y)
            loss.backward()
            opt.step()
            total_loss += loss.item()

        # ── validate ────────────────────────────────
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for batch in val_loader:
                batch   = batch.to(device)
                pred    = model(batch.x, batch.edge_index, batch.batch).argmax(dim=-1)
                correct += (pred == batch.y).sum().item()
                total   += batch.num_graphs

        val_acc = correct / total

        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d} | loss {total_loss/len(train_loader):.4f} | val_acc {val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(model.state_dict(), save_path)

    print(f"\nBest val acc: {best_val_acc:.3f} → {save_path}")
    return best_val_acc


if __name__ == "__main__":
    train()
