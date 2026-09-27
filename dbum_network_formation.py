import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

from utils.project_utils import utility_dbum, delta_u_add, delta_u_remove, one_step, classify_network_from_degrees, labels_to_str

# A baseline model for network formation via ABM
# It's going to use a distance-based utility function as benefit function
# Agents will form links based on maximizing their utility
# It introduces myopic behavior via a radius parameter, decay parameter delta, and link cost c
# At each step it will pick a node, and with some probability try to add a link, otherwise try to remove a link
# If randomly chosen candidate for link addition/removal increases utility for both parties, the action is taken

# --- Parameters setup ---
n = 10 # number of nodes
delta = 0.5 # decay parameter
c = 0.2 # link cost
add_prob = 0.6 # probability of trying to add a link 
# radius = 10 # the myopic radius
frames = 200 # how many frames are generated

# Parameter grid for delta and c
param_grid = []

param_grid_delta = [0.95, 0.65, 0.35]
param_grid_cost = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
param_grid_radius = [3, 5, 8, 10]

# # param_grid_delta = [0.95]
# param_grid_cost = [1, 0.9, 0.8]
# # param_grid_radius = [3]

for r in param_grid_radius:
    for d in param_grid_delta:
        for c in param_grid_cost:
            param_grid.append((d, c, r))

VIEW_MODE = "network" # choose betwee two view modes - "network" or "bars"

steps_per_setting = 200 # frames per (delta,c) setting
pause_frames = 100 # small pause when switching settings
total_frames = len(param_grid) * (steps_per_setting + pause_frames)

random.seed(1)
G = nx.Graph()
G.add_nodes_from(range(n))
current_param_idx = 0 # we use this to assign index to each combination of paremeters (delta, c)
step_in_setting = 0 # step counter for a particular combination of (delta, c)
in_pause = False
pause_left = 0

records = [] 
recorded_this_setting = False

# --- Animation ---
fig, ax = plt.subplots(figsize=(9, 5))

bars = ax.bar(range(n), [0]*n)
ax.set_ylim(0, n - 1)
ax.set_xlabel("Node id")
ax.set_ylabel("Degree")
ax.set_title("Degree evolution under DBUM dynamics")

pos = None # layout for drawing network


def visualizer_bars(degs, title: str):
    '''function that visualizes network structure via bar charts of node degress'''

    for b, h in zip(bars, degs):
        b.set_height(h)
    ax.set_ylim(0, n-1)
    ax.set_xlabel("Node id")
    ax.set_ylabel("Degree")
    ax.set_title(title)
    return bars


def visualizer_network(delta, c, radius, step_in_setting, action_text="", pause=False):
    '''function that visualizes network structure via networkx drawing (at a signle step, for given parameters)'''

    ax.clear()
    ax.set_axis_off()

    utilities = [utility_dbum(i, G, radius, delta, c) for i in range(n)] # Assign utility value for all agents, in network G, for parameters (delta, c)
    degs = [G.degree[i] for i in range(n)] # Store their degrees here
    _, labels = classify_network_from_degrees(degs, n) # Classify the network structure based on degree distribution
    struct_str = labels_to_str(labels) # Convert the list of structure labels into a string for display

    prefix = "(PAUSE) " if pause else ""
    ax.set_title(f"{prefix}δ={delta:.2f}, c={c:.2f}, R={radius} | step={step_in_setting}/{steps_per_setting}\n"
                 f"{struct_str} | {action_text}")
    
    nx.draw(
        G,
        pos=pos,
        with_labels=True,
        node_size=900,
        node_color=utilities,
        cmap=plt.cm.viridis,
        edge_color="gray",
        font_size=10
    )
    return []


def reset_graph_for_setting(seed_offset: int = 0):
    global G, recorded_this_setting, pos
    G = nx.Graph()
    G.add_nodes_from(range(n))
    random.seed(1 + seed_offset)
    recorded_this_setting = False

    if VIEW_MODE == "network":
        pos = nx.spring_layout(G, seed=42 + seed_offset) # stable per setting


def update(frame):

    '''The following function is responsible for iterating through all steps within a single setting (parameter combination)'''

    global current_param_idx, step_in_setting, in_pause, pause_left, recorded_this_setting

    delta, c, radius = param_grid[current_param_idx]

    if step_in_setting == 0 and not recorded_this_setting:
        reset_graph_for_setting(seed_offset=current_param_idx)

    if delta <= c and not recorded_this_setting:

        recorded_this_setting = True

        records.append({
            "delta": delta,
            "c": c,
            "radius": radius,
            "steps": 0,
            "edges": 0,
            "mean_degree": 0,
            "deg_max": 0,
            "deg_min": 0,
            "deg_range": 0,
            "deg_median": 0,
            "labels": "empty",
            "is_empty": True,
        })

        in_pause = True
        pause_left = pause_frames

        if VIEW_MODE == "bars":
            return visualizer_bars([0]*n,
                f"(ANALYTIC EMPTY) δ={delta:.2f}, c={c:.2f}, R={radius}")
        else:
            visualizer_network(delta, c, radius, 0,
                            action_text="analytic empty",
                            pause=True)
            return []

    if in_pause:
        pause_left -= 1
        if pause_left <= 0:
            in_pause = False
            step_in_setting = 0
            current_param_idx += 1
            if current_param_idx >= len(param_grid):
                
                df_results = pd.DataFrame(records)\
                    .sort_values(["delta", "c", "radius"])\
                    .reset_index(drop=True)

                dbum_param_grid_results_path = os.path.join(
                    script_dir,
                    "dbum_param_grid_results.csv"
                )

                df_results.to_csv(dbum_param_grid_results_path, index=False)

                print("\nSaved: dbum_param_grid_results.csv")
                print("Rows recorded:", len(df_results))

                # ---- STOP ANIMATION CLEANLY ----
                ani.event_source.stop()
                plt.close(fig)

                return []
            else:
                reset_graph_for_setting(seed_offset=current_param_idx)
        # update bars even during pause (graph is static)
        degs = [G.degree[i] for i in range(n)]
        flags, labels = classify_network_from_degrees(degs, n)
        struct_str = labels_to_str(labels)

        if VIEW_MODE == "bars":
            title = f"(PAUSE) δ={delta:.2f}, c={c:.2f}, R={radius} | {struct_str}"
            return visualizer_bars(degs, title)
        else:
            visualizer_network(delta, c, radius, step_in_setting, action_text="pause", pause=True)
            return []

    # If we're at the beginning of a setting, ensure we reset (only once)
    if step_in_setting == 0:
        reset_graph_for_setting(seed_offset=current_param_idx)

    # Perform one ABM step
    action = one_step(G, n, radius, delta, c, add_prob=add_prob)
    step_in_setting += 1

    # Update the chosen chart type
    degs = [G.degree[i] for i in range(n)]
    flags, labels = classify_network_from_degrees(degs, n)
    struct_str = labels_to_str(labels)

    if step_in_setting >= steps_per_setting and not recorded_this_setting:

        recorded_this_setting = True

        degs = [G.degree[i] for i in range(n)]
        dmax, dmin = max(degs), min(degs)
        med = float(pd.Series(degs).median())
        mean_deg = sum(degs) / n
        m_edges = G.number_of_edges()

        flags, labels = classify_network_from_degrees(
            degs=degs,
            n=n,
            near_regular_eps=2,
            weak_ratio=1.5,
            strong_ratio=3.3,
        )

        records.append({
            "delta": delta,
            "c": c,
            "radius": radius,
            "steps": steps_per_setting,
            "edges": m_edges,
            "mean_degree": mean_deg,
            "deg_max": dmax,
            "deg_min": dmin,
            "deg_range": dmax - dmin,
            "deg_median": med,
            "labels": "|".join(labels),  # easy to read/filter later
            **flags,                   # expands boolean columns
        })

        in_pause = True
        pause_left = pause_frames

    if VIEW_MODE == "bars":
        title = f"δ={delta:.2f}, c={c:.2f}, R={radius} | step={step_in_setting}/{steps_per_setting} | {struct_str}"
        return visualizer_bars(degs, title)
    else:
        visualizer_network(delta, c, radius, step_in_setting, action_text=action, pause=False)
        return []


ani = FuncAnimation(fig, update, frames=total_frames, interval=100, blit=False, repeat=False)
plt.tight_layout()
plt.show()

df_results = pd.DataFrame(records).sort_values(["delta", "c", "radius"]).reset_index(drop=True)

print(df_results)
print("\nRows recorded:", len(df_results), " (expected:", len(param_grid), "for one radius)")

flag_cols = [c for c in df_results.columns if c.startswith("is_")]
if flag_cols:
    print("\nFlag counts:")
    print(df_results[flag_cols].sum().sort_values(ascending=False))

dbum_param_grid_results_path = os.path.join(script_dir, "dbum_param_grid_results.csv")

df_results.to_csv(dbum_param_grid_results_path, index=False)
print("\nSaved: dbum_param_grid_results.csv")