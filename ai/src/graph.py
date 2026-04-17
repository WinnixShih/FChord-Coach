import torch
from torch_geometric.data import Data

LABEL_MAP = {
    "correct":          0,
    "err_index_low":    1,
    "err_index_angle":  2,
    "err_thumb_wrong":  3,
    "err_wrist_far":    4,
    "not_fchord":       5,
}
IDX_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}
NUM_CLASSES = len(LABEL_MAP)

# MediaPipe 定義的手指骨架連線（雙向 → undirected graph）
CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

def nodes_to_graph(nodes: list[list[float]], label: str | None = None) -> Data:
    """
    nodes : list of 21 × [x, y, z], MediaPipe normalized 0–1
    label : string label key from LABEL_MAP, or None for inference
    """
    x = torch.tensor(nodes, dtype=torch.float)  # [21, 3]

    src = [a for a, b in CONNECTIONS] + [b for a, b in CONNECTIONS]
    dst = [b for a, b in CONNECTIONS] + [a for a, b in CONNECTIONS]
    edge_index = torch.tensor([src, dst], dtype=torch.long)  # [2, 46]

    data = Data(x=x, edge_index=edge_index)
    if label is not None:
        data.y = torch.tensor([LABEL_MAP[label]], dtype=torch.long)
    return data
