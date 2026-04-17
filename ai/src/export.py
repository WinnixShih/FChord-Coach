import torch
import numpy as np
from torch_geometric.data import Batch
from .graph import nodes_to_graph, EDGE_INDEX
from .model import FChordGNN


def export_onnx(
    weights_path: str = "models/fchord_gnn.pt",
    output_path:  str = "models/fchord.onnx",
):
    model = FChordGNN()
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    dummy = nodes_to_graph([[0.5, 0.5, 0.0]] * 21)
    batch = Batch.from_data_list([dummy])

    torch.onnx.export(
        model,
        (batch.x, batch.edge_index, batch.batch),
        output_path,
        input_names=["x", "edge_index", "batch"],
        output_names=["logits"],
        opset_version=17,
        dynamic_axes={
            "x":          {0: "num_nodes"},
            "edge_index": {1: "num_edges"},
            "batch":      {0: "num_nodes"},
        },
    )
    print(f"Exported → {output_path}")

    # ── quick sanity check ──
    import onnxruntime as ort
    sess    = ort.InferenceSession(output_path)
    x       = np.array([[0.5, 0.5, 0.0]] * 21, dtype=np.float32)
    ei      = EDGE_INDEX.numpy().astype(np.int64)
    b       = np.zeros(21, dtype=np.int64)
    logits  = sess.run(["logits"], {"x": x, "edge_index": ei, "batch": b})[0]
    print(f"Sanity check — logits shape: {logits.shape}")  # should be (1, 6)


if __name__ == "__main__":
    export_onnx()
