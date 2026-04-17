import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, global_mean_pool
from .graph import NUM_CLASSES


class FChordGNN(torch.nn.Module):
    """
    3-layer GraphSAGE for F chord posture classification.

    Input:
        x          : [N, 3]   node features (x, y, z per keypoint)
        edge_index : [2, E]   graph connectivity
        batch      : [N]      batch assignment vector

    Output:
        logits : [B, NUM_CLASSES]
    """

    def __init__(self, in_channels: int = 3, hidden: int = 64):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.conv3 = SAGEConv(hidden, hidden)
        self.head  = torch.nn.Linear(hidden, NUM_CLASSES)

    def forward(self, x, edge_index, batch):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        x = F.relu(self.conv2(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        x = F.relu(self.conv3(x, edge_index))
        x = global_mean_pool(x, batch)
        return self.head(x)

    def predict(self, x, edge_index, batch):
        """Returns (label_idx, confidence) without gradient."""
        self.eval()
        with torch.no_grad():
            logits = self(x, edge_index, batch)
            probs  = F.softmax(logits, dim=-1)
            conf, idx = probs.max(dim=-1)
        return idx.item(), round(conf.item(), 3)
