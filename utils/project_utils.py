import networkx as nx
import random
import pandas as pd


def utility_dbum(i: int,
                G: nx.Graph,
                radius: int,
                delta: float,
                c: float) -> float:
    """Distance-based utility function for agent i in graph G with decay parameter delta, link cost c, and myopic radius"""
    lengths = nx.single_source_shortest_path_length(G, i, cutoff=radius)
    benefit = 0.0
    for j, d in lengths.items():
        if i == j:
            continue

        benefit += delta ** d
    return benefit - c * G.degree[i]


def delta_u_add(i: int,
                j: int,
                G: nx.Graph,
                radius: int,
                delta: float,
                c: float) -> float:
    """Marginal utility of adding edge (i, j)"""
    if G.has_edge(i, j):
        return 0.0

    u_before = utility_dbum(i, G, radius, delta, c)
    G.add_edge(i, j)
    u_after = utility_dbum(i, G, radius, delta, c)
    G.remove_edge(i, j)
    return u_after - u_before


def delta_u_remove(i: int,
                   j: int,
                   G: nx.Graph,
                   radius: int,
                   delta: float,
                   c: float) -> float:
    """Marginal utility of removing edge (i, j)"""
    if not G.has_edge(i, j):
        return 0.0

    u_before = utility_dbum(i, G, radius, delta, c)
    G.remove_edge(i, j)
    u_after = utility_dbum(i, G, radius, delta, c)
    G.add_edge(i, j)
    return u_after - u_before


def one_step(G: nx.Graph,
             n: int,
             radius:int,
             delta: float,
             c: float,
             add_prob: float = 0.6) -> str:
    """Perform one update step in the DBUM network formation process"""

    i = random.randrange(n)
    
    if random.random() < add_prob:
        candidates = [j for j in range(n) if j != i and not G.has_edge(i, j)]
        if not candidates:
            return "add skipped (i = {i})"
        
        j = random.choice(candidates)
        if delta_u_add(i, j, G, radius, delta, c) > 0 and delta_u_add(j, i, G, radius, delta, c) > 0:
            G.add_edge(i, j)
            return f"added edge ({i}, {j})"
        return f"add rejected (i = {i}, j = {j})"
    else:
        neighborhood = list(G.neighbors(i))
        if not neighborhood:
            return "remove skipped (i = {i})"
        
        j = random.choice(neighborhood)
        if delta_u_remove(i, j, G, radius, delta, c) > 0:
            G.remove_edge(i, j)
            return f"removed edge ({i}, {j})"
        return f"remove rejected (i = {i}, j = {j})"


def classify_network_from_degrees(degs: list, 
                                  n: int, 
                                  near_regular_eps=2, 
                                  weak_ratio=1.5, 
                                  strong_ratio=2.0) -> tuple[dict, list]:
    """
    This function classifies a network based on its degree distribution in the following categories:
    1) empty
    2) complete
    3) regular (uniform)
    4) nearly-regular (max-min <= near_regular_eps)
    5) star
    6) weakly star-like (dmax >= weak_ratio * median)
    7) star-like (dmax >= strong_ratio * median)
    8) other

    If median degree == 0, ratio-based classes are undefined -> return "other" (or "sparse-other").

    Returns:
      flags: dict[str,bool] -> which flags were triggered (e.g. "is_empty": True, "is_star": False, etc.)
      labels: list[str] -> list of labels that apply to this network (e.g. ["empty"], ["nearly_regular"], ["weakly_star_like", "star_like"], etc.)

    Notes:
      - Overlap is allowed (multi-label).
    """

    m_edges = sum(degs) // 2
    dmax = max(degs)
    dmin = min(degs)
    med = float(pd.Series(degs).median())

    degs_sorted = sorted(degs, reverse=True)
    is_star = (degs_sorted[0] == n - 1 and all(d == 1 for d in degs_sorted[1:]))

    # Condition checks for each structure type (e.g. 'is_empty': True, 'is_complete': False, etc.)
    flags = {
        "is_empty": (m_edges == 0),
        "is_complete": (m_edges == n * (n - 1) // 2),
        "is_regular": (dmax - dmin == 0),                 # regular
        "is_nearly_regular": (dmax - dmin <= near_regular_eps),
        "is_star": is_star,
        "is_weakly_star_like": False,
        "is_star_like": False,
    }

    # Hub dominance ratio rules (only for non-zero median)
    if med > 0:
        ratio = dmax / med
        flags["is_weakly_star_like"] = (ratio >= weak_ratio)
        flags["is_star_like"] = (ratio >= strong_ratio)

    # labels list - which strcuture types apply to this network?
    labels = []

    if flags["is_empty"]:
        labels.append("empty")
    if flags["is_complete"]:
        labels.append("complete")
    if flags["is_star"]:
        labels.append("star")
    if flags["is_regular"]:
        labels.append("regular")
    if flags["is_nearly_regular"]:
        labels.append("nearly_regular")
    if flags["is_star_like"]:
        labels.append("star_like")
    elif flags["is_weakly_star_like"]:
        labels.append("weakly_star_like")

    # if none matched, mark as other
    if len(labels) == 0:
        labels = ["other"]

    return flags, labels


def labels_to_str(labels):
    return "; ".join(labels)