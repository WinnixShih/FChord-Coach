"""
F Chord GNN Training Data — Visual QC Script
=============================================
Usage:
    python tools/qc.py                         # interactive browser
    python tools/qc.py --report                # export HTML report
    python tools/qc.py --label err_index_low   # filter one label
    python tools/qc.py --check                 # automated checks only
    python tools/qc.py --grid                  # skeleton grid view
    python tools/qc.py --dist                  # distribution plots
"""

import json
import glob
import os
import argparse
import collections
import math
from pathlib import Path

import cv2
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── MediaPipe finger connection topology ──────────────────────────────────────
FINGER_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

FINGER_NAMES = {
    0:"wrist",
    1:"thumb",2:"thumb",3:"thumb",4:"thumb",
    5:"index",6:"index",7:"index",8:"index",
    9:"middle",10:"middle",11:"middle",12:"middle",
    13:"ring",14:"ring",15:"ring",16:"ring",
    17:"pinky",18:"pinky",19:"pinky",20:"pinky",
}

# F chord reference angle ranges per joint (degrees)
FCHORD_ANGLE_REFS = {
    6:  (40, 70),   # index PIP
    7:  (20, 50),   # index DIP
    10: (50, 80),   # middle MCP
    14: (50, 80),   # ring MCP
    18: (40, 75),   # pinky MCP
}

LABEL_COLORS = {
    "correct":          "#1D9E75",
    "err_index_low":    "#E24B4A",
    "err_index_angle":  "#D85A30",
    "err_thumb_wrong":  "#BA7517",
    "err_wrist_far":    "#7F77DD",
    "not_fchord":       "#888780",
}

def label_color(label):
    return LABEL_COLORS.get(label, "#378ADD")


# ── Data loading ──────────────────────────────────────────────────────────────
def load_samples(data_dir="data", label_filter=None):
    samples = []
    for path in glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True):
        try:
            d = json.load(open(path))
            if label_filter and d.get("label") != label_filter:
                continue
            d["_path"] = path
            samples.append(d)
        except Exception as e:
            print(f"[WARN] Could not load {path}: {e}")
    return samples


# ── Geometry helpers ──────────────────────────────────────────────────────────
def angle_between(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cos_val = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return math.degrees(math.acos(np.clip(cos_val, -1, 1)))

def compute_joint_angles(nodes):
    parent_map = {
        1:0,2:1,3:2,4:3,
        5:0,6:5,7:6,8:7,
        9:0,10:9,11:10,12:11,
        13:0,14:13,15:14,16:15,
        17:0,18:17,19:18,20:19,
    }
    angles = {}
    for node_id, parent_id in parent_map.items():
        children = [k for k,v in parent_map.items() if v == node_id]
        for child_id in children:
            angles[node_id] = angle_between(
                nodes[parent_id], nodes[node_id], nodes[child_id]
            )
    return angles

def wrist_span(nodes):
    return float(np.linalg.norm(np.array(nodes[0]) - np.array(nodes[5])))


# ── Skeleton plot ─────────────────────────────────────────────────────────────
GHOST_NODES = [
    [0.50,0.85],[0.42,0.72],[0.38,0.58],[0.35,0.45],[0.33,0.35],
    [0.58,0.70],[0.56,0.52],[0.54,0.38],[0.53,0.28],
    [0.64,0.68],[0.63,0.48],[0.62,0.34],[0.61,0.24],
    [0.70,0.67],[0.70,0.47],[0.70,0.33],[0.70,0.23],
    [0.76,0.66],[0.77,0.49],[0.78,0.37],[0.79,0.28],
]

def plot_skeleton(ax, nodes, label, show_ghost=True, show_angles=False, title=""):
    xs = [n[0] for n in nodes]
    ys = [1 - n[1] for n in nodes]

    joint_angles = compute_joint_angles(nodes)
    node_ok = {}
    for nid in range(21):
        if nid in FCHORD_ANGLE_REFS:
            lo, hi = FCHORD_ANGLE_REFS[nid]
            node_ok[nid] = lo <= joint_angles.get(nid, 999) <= hi
        else:
            node_ok[nid] = True

    if show_ghost:
        gx = [g[0] for g in GHOST_NODES]
        gy = [g[1] for g in GHOST_NODES]
        for (a,b) in FINGER_CONNECTIONS:
            ax.plot([gx[a],gx[b]],[gy[a],gy[b]],
                    color="#EF9F27",linewidth=1.2,linestyle="--",alpha=0.55,zorder=1)
        ax.scatter(gx,gy,s=18,color="#EF9F27",alpha=0.5,zorder=2)

    for (a,b) in FINGER_CONNECTIONS:
        color = "#1D9E75" if (node_ok.get(a,True) and node_ok.get(b,True)) else "#E24B4A"
        ax.plot([xs[a],xs[b]],[ys[a],ys[b]],
                color=color,linewidth=2.0,solid_capstyle="round",zorder=3)

    for i,(x,y) in enumerate(zip(xs,ys)):
        color = "#1D9E75" if node_ok.get(i,True) else "#E24B4A"
        ax.scatter(x,y,s=40,color=color,zorder=4)
        if i in [4,8,12,16,20]:
            ax.annotate(["T","I","M","R","P"][[4,8,12,16,20].index(i)],
                        (x,y),textcoords="offset points",xytext=(5,4),
                        fontsize=7,color=color,fontweight="bold")

    if show_angles:
        for nid, angle in joint_angles.items():
            if nid in FCHORD_ANGLE_REFS:
                ok = node_ok.get(nid,True)
                ax.annotate(f"{angle:.0f}°",(xs[nid],ys[nid]),
                            textcoords="offset points",xytext=(6,-8),
                            fontsize=6.5,color="#1D9E75" if ok else "#E24B4A")

    ax.set_title(title or label,fontsize=9,color=label_color(label),pad=4,fontweight="bold")
    ax.set_xlim(0.2,0.9)
    ax.set_ylim(0.1,1.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("#F8F8F6")


# ── Automated QC checks ───────────────────────────────────────────────────────
def qc_check(sample):
    issues = []
    nodes  = sample["nodes"]

    if len(nodes) != 21:
        issues.append(("fail", f"Expected 21 nodes, got {len(nodes)}"))
        return issues

    for i, n in enumerate(nodes):
        if not (0 <= n[0] <= 1 and 0 <= n[1] <= 1):
            issues.append(("warn", f"Node {i} xy out of [0,1]: ({n[0]:.3f},{n[1]:.3f})"))

    span = wrist_span(nodes)
    if span < 0.05:
        issues.append(("fail", f"Hand span too small ({span:.3f}) — no hand detected?"))
    elif span > 0.5:
        issues.append(("warn", f"Hand span unusually large ({span:.3f})"))

    angles = compute_joint_angles(nodes)
    label  = sample.get("label","")

    if label == "correct":
        for nid,(lo,hi) in FCHORD_ANGLE_REFS.items():
            a = angles.get(nid)
            if a is not None and not (lo <= a <= hi):
                issues.append(("warn",
                    f"Node {nid} ({FINGER_NAMES[nid]}) angle {a:.1f}° outside ref [{lo},{hi}]"))

    pip = angles.get(6)
    if pip is not None:
        if label == "correct" and pip < 35:
            issues.append(("warn", f"Index PIP {pip:.1f}° very low — finger may be collapsed"))
        if label == "err_index_low" and pip > 60:
            issues.append(("warn", f"Label err_index_low but PIP {pip:.1f}° looks correct — mislabel?"))

    if not issues:
        issues.append(("ok","All checks passed"))
    return issues


# ── View 1: Distribution ──────────────────────────────────────────────────────
def plot_distribution(samples):
    counter = collections.Counter(s["label"] for s in samples)
    labels  = list(counter.keys())
    counts  = [counter[l] for l in labels]
    colors  = [label_color(l) for l in labels]

    fig, axes = plt.subplots(1,2,figsize=(13,4.5))
    fig.patch.set_facecolor("#FAFAF8")

    ax = axes[0]
    bars = ax.bar(labels,counts,color=colors,width=0.6,edgecolor="white",linewidth=0.8)
    ax.set_facecolor("#F4F4F2")
    ax.set_title("Sample count per label",fontsize=11,pad=8)
    ax.tick_params(axis="x",labelrotation=20,labelsize=8)
    ax.spines[["top","right"]].set_visible(False)
    for bar,count in zip(bars,counts):
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1,
                str(count),ha="center",va="bottom",fontsize=8,fontweight="bold")

    axes[1].pie(counts,labels=labels,colors=colors,autopct="%1.0f%%",startangle=140,
                textprops={"fontsize":8},wedgeprops={"linewidth":0.8,"edgecolor":"white"})
    axes[1].set_title("Class balance",fontsize=11,pad=8)

    fig.suptitle(f"Dataset overview — {sum(counts)} total samples",fontsize=13,y=1.01)
    plt.tight_layout()
    return fig


# ── View 2: Skeleton grid ─────────────────────────────────────────────────────
def plot_skeleton_grid(samples, n_cols=5, label_filter=None):
    if label_filter:
        samples = [s for s in samples if s["label"] == label_filter]

    n      = min(len(samples), 25)
    n_rows = math.ceil(n / n_cols)
    fig, axes = plt.subplots(n_rows,n_cols,figsize=(n_cols*2.2,n_rows*2.4))
    fig.patch.set_facecolor("#FAFAF8")
    axes = np.array(axes).flatten()

    for i, ax in enumerate(axes):
        if i < n:
            s      = samples[i]
            fname  = Path(s["_path"]).stem
            issues = qc_check(s)
            worst  = max(issues, key=lambda x: ["ok","warn","fail"].index(x[0]))
            border = {"ok":"#1D9E75","warn":"#EF9F27","fail":"#E24B4A"}[worst[0]]
            plot_skeleton(ax,s["nodes"],s["label"],
                          show_ghost=True,show_angles=True,
                          title=f"{s['label']}\n{fname}")
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_edgecolor(border)
                spine.set_linewidth(1.5)
        else:
            ax.axis("off")

    fig.suptitle(f"Skeleton grid — {label_filter or 'all'} ({n} samples)",
                 fontsize=11,y=1.01)
    plt.tight_layout()
    return fig


# ── View 3: Angle distributions ───────────────────────────────────────────────
def plot_angle_distributions(samples):
    nodes_of_interest = {
        6:"Index PIP", 7:"Index DIP",
        10:"Middle MCP", 14:"Ring MCP", 18:"Pinky MCP",
    }
    label_groups = collections.defaultdict(list)
    for s in samples:
        angles = compute_joint_angles(s["nodes"])
        for nid in nodes_of_interest:
            if nid in angles:
                label_groups[(s["label"],nid)].append(angles[nid])

    labels_present = list(set(s["label"] for s in samples))
    n = len(nodes_of_interest)
    fig, axes = plt.subplots(1,n,figsize=(n*2.8,4))
    fig.patch.set_facecolor("#FAFAF8")

    for ax,(nid,jname) in zip(axes,nodes_of_interest.items()):
        for label in labels_present:
            vals = label_groups.get((label,nid),[])
            if vals:
                ax.hist(vals,bins=15,alpha=0.55,label=label,
                        color=label_color(label),density=True)
        if nid in FCHORD_ANGLE_REFS:
            lo,hi = FCHORD_ANGLE_REFS[nid]
            ax.axvspan(lo,hi,alpha=0.12,color="#1D9E75")
            ax.axvline(lo,color="#1D9E75",linewidth=0.8,linestyle="--")
            ax.axvline(hi,color="#1D9E75",linewidth=0.8,linestyle="--")
        ax.set_title(f"Node {nid}\n{jname}",fontsize=9,pad=4)
        ax.set_xlabel("Angle (°)",fontsize=8)
        ax.spines[["top","right"]].set_visible(False)
        ax.set_facecolor("#F4F4F2")
        ax.tick_params(labelsize=7)

    handles = [mpatches.Patch(color=label_color(l),label=l,alpha=0.7) for l in labels_present]
    handles.append(mpatches.Patch(color="#1D9E75",alpha=0.3,label="F chord target"))
    fig.legend(handles=handles,loc="upper right",fontsize=7,framealpha=0.8)
    fig.suptitle("Joint angle distributions by label",fontsize=11,y=1.03)
    plt.tight_layout()
    return fig


# ── QC report (terminal) ──────────────────────────────────────────────────────
def print_qc_report(samples):
    print("\n" + "="*70)
    print("QC REPORT")
    print("="*70)

    by_sev = {"fail":[],"warn":[],"ok":[]}
    for s in samples:
        issues = qc_check(s)
        for sev,msg in issues:
            if sev != "ok":
                by_sev[sev].append((s["_path"],msg))
        if all(i[0]=="ok" for i in issues):
            by_sev["ok"].append(s["_path"])

    print(f"\n  PASS : {len(by_sev['ok'])}")
    print(f"  WARN : {len(by_sev['warn'])}")
    print(f"  FAIL : {len(by_sev['fail'])}")

    if by_sev["fail"]:
        print("\n── FAILURES ──────────────────────────────────────────────")
        for path,msg in by_sev["fail"]:
            print(f"  [FAIL] {Path(path).name}: {msg}")

    if by_sev["warn"]:
        print("\n── WARNINGS ──────────────────────────────────────────────")
        for path,msg in by_sev["warn"][:20]:
            print(f"  [WARN] {Path(path).name}: {msg}")
        if len(by_sev["warn"]) > 20:
            print(f"  ... and {len(by_sev['warn'])-20} more")

    counter = collections.Counter(s["label"] for s in samples)
    total   = sum(counter.values())
    print("\n── CLASS BALANCE ─────────────────────────────────────────")
    for label,count in sorted(counter.items(),key=lambda x:-x[1]):
        pct = count/total*100
        bar = "█" * int(pct/2)
        flag = "  [!] add more samples" if count < 80 else ""
        print(f"  {label:<22} {count:>4}  {pct:5.1f}%  {bar}{flag}")

    print("="*70 + "\n")
    return by_sev


# ── HTML report export ────────────────────────────────────────────────────────
def export_html_report(samples, output_path="models/qc_report.html"):
    import base64
    from io import BytesIO

    def fig_to_b64(fig):
        buf = BytesIO()
        fig.savefig(buf,format="png",dpi=120,bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        return base64.b64encode(buf.getvalue()).decode()

    figs = [
        ("Distribution",        plot_distribution(samples)),
        ("Angle distributions", plot_angle_distributions(samples)),
    ]
    for label in sorted(set(s["label"] for s in samples)):
        sub = [s for s in samples if s["label"]==label]
        figs.append((f"Skeletons — {label}", plot_skeleton_grid(sub,label_filter=label)))

    plt.close("all")

    html = ["<!DOCTYPE html><html><head><meta charset='utf-8'><style>",
            "body{font-family:sans-serif;background:#f8f8f6;padding:2rem}",
            "h2{font-size:1.1rem;font-weight:500;margin-top:2rem;color:#444}",
            "img{width:100%;border-radius:8px;border:1px solid #e0e0e0;margin-bottom:1.5rem}",
            f"</style></head><body><h1>F Chord QC Report — {len(samples)} samples</h1>"]

    for title,fig in figs:
        html.append(f"<h2>{title}</h2>")
        html.append(f"<img src='data:image/png;base64,{fig_to_b64(fig)}'>")
    html.append("</body></html>")

    os.makedirs(os.path.dirname(output_path),exist_ok=True)
    open(output_path,"w").write("".join(html))
    print(f"HTML report → {output_path}")


# ── Interactive browser ───────────────────────────────────────────────────────
def interactive_browser(samples):
    if not samples:
        print("No samples found.")
        return

    idx         = [0]
    show_ghost  = [True]
    show_angles = [True]

    fig, ax      = plt.subplots(figsize=(5,6))
    issue_ax     = fig.add_axes([0.05,0.02,0.9,0.12])
    fig.patch.set_facecolor("#FAFAF8")

    def draw():
        ax.cla(); issue_ax.cla(); issue_ax.axis("off")
        s      = samples[idx[0]]
        issues = qc_check(s)
        plot_skeleton(ax,s["nodes"],s["label"],
                      show_ghost=show_ghost[0],show_angles=show_angles[0],
                      title=f"[{idx[0]+1}/{len(samples)}] {s['label']}")
        y = 0.95
        for sev,msg in issues:
            color = {"ok":"#1D9E75","warn":"#BA7517","fail":"#E24B4A"}[sev]
            icon  = {"ok":"✓","warn":"⚠","fail":"✗"}[sev]
            issue_ax.text(0.02,y,f"{icon} {msg}",transform=issue_ax.transAxes,
                          fontsize=7.5,color=color,va="top")
            y -= 0.30
        fig.suptitle("← → navigate  |  Space: ghost  |  A: angles  |  Q: quit",
                     fontsize=7.5,color="#888",y=0.01)
        fig.canvas.draw_idle()

    def on_key(event):
        if   event.key == "right": idx[0] = (idx[0]+1) % len(samples)
        elif event.key == "left":  idx[0] = (idx[0]-1) % len(samples)
        elif event.key == " ":     show_ghost[0]  = not show_ghost[0]
        elif event.key == "a":     show_angles[0] = not show_angles[0]
        elif event.key == "q":     plt.close(fig); return
        draw()

    fig.canvas.mpl_connect("key_press_event", on_key)
    draw()
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="F Chord GNN Data QC")
    parser.add_argument("--data",   default="data")
    parser.add_argument("--label",  default=None)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check",  action="store_true")
    parser.add_argument("--grid",   action="store_true")
    parser.add_argument("--dist",   action="store_true")
    args = parser.parse_args()

    print(f"Loading from '{args.data}' ...")
    samples = load_samples(args.data, args.label)

    if not samples:
        print(f"[ERROR] No samples found in '{args.data}'.")
        return

    print(f"Loaded {len(samples)} samples.")
    print_qc_report(samples)

    if args.report:
        export_html_report(samples); return
    if args.check:
        return
    if args.dist:
        plot_distribution(samples); plot_angle_distributions(samples)
        plt.show(); return
    if args.grid:
        plot_skeleton_grid(samples, label_filter=args.label)
        plt.show(); return

    matplotlib.use("TkAgg")
    interactive_browser(samples)


if __name__ == "__main__":
    main()
