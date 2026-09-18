"""Load a Graphify graph.json and collapse it to a file-level dependency graph."""

import json
from pathlib import Path

import networkx as nx

DEPENDENCY_RELATIONS = {
    "calls",
    "references",
    "imports",
    "imports_from",
    "inherits",
    "implements",
    "indirect_call",
    "dispatches_to",
    "re_exports",
    "dynamic_import",
}


def load_graph(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)


def build_file_graph(raw_graph: dict) -> nx.DiGraph:
    """Collapse a symbol-level Graphify graph to a file-level dependency graph.

    Only nodes with file_type == "code" and a non-empty source_file are part
    of the codebase (unresolved/external symbols, e.g. framework types, have
    no source_file and are dropped). Only relations in DEPENDENCY_RELATIONS
    count as coupling; containment/declaration relations (contains, method,
    defines) and documentation links (rationale_for, cites, case_of) are
    excluded. Edge weight is the number of symbol-level references between
    the two files.
    """
    symbol_to_file = {
        n["id"]: n["source_file"]
        for n in raw_graph["nodes"]
        if n.get("file_type") == "code" and n.get("source_file")
    }

    file_graph = nx.DiGraph()
    file_graph.add_nodes_from(set(symbol_to_file.values()))

    for link in raw_graph["links"]:
        if link.get("relation") not in DEPENDENCY_RELATIONS:
            continue
        src_file = symbol_to_file.get(link["source"])
        tgt_file = symbol_to_file.get(link["target"])
        if src_file is None or tgt_file is None or src_file == tgt_file:
            continue
        if file_graph.has_edge(src_file, tgt_file):
            file_graph[src_file][tgt_file]["weight"] += 1
        else:
            file_graph.add_edge(src_file, tgt_file, weight=1)

    return file_graph


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _find_cycles(g: nx.DiGraph) -> list[list[str]]:
    """One representative cycle per strongly-connected component of size > 1.

    Enumerating every elementary cycle (nx.simple_cycles) is combinatorial
    and can blow up on real codebases; a representative cycle per SCC is
    enough to flag the problem and point at where it lives.
    """
    cycles = []
    for scc in nx.strongly_connected_components(g):
        if len(scc) < 2:
            continue
        sub = g.subgraph(scc)
        edges = nx.find_cycle(sub)
        nodes = [u for u, _ in edges] + [edges[-1][1]]
        cycles.append(nodes)
    return cycles


def compute_graph_metrics(g: nx.DiGraph) -> dict:
    """Compute the graph_metrics fields defined in docs/design/structure-scoring.md."""
    fan_in = [d for _, d in g.in_degree()]
    fan_out = [d for _, d in g.out_degree()]

    condensation = nx.condensation(g)
    longest_dependency_path = (
        nx.dag_longest_path_length(condensation) if condensation.number_of_nodes() else 0
    )

    undirected = g.to_undirected()
    if g.number_of_edges():
        communities = nx.community.greedy_modularity_communities(undirected, weight="weight")
        modularity_score = nx.community.modularity(undirected, communities, weight="weight")
    else:
        modularity_score = 0.0

    betweenness = nx.betweenness_centrality(g, weight=None)
    betweenness_values = list(betweenness.values())
    top_betweenness_nodes = sorted(betweenness.items(), key=lambda kv: -kv[1])[:5]

    return {
        "node_count": g.number_of_nodes(),
        "avg_fan_in": _mean(fan_in),
        "max_fan_in": max(fan_in, default=0),
        "avg_fan_out": _mean(fan_out),
        "max_fan_out": max(fan_out, default=0),
        "longest_dependency_path": longest_dependency_path,
        "circular_dependencies": _find_cycles(g),
        "modularity_score": modularity_score,
        "avg_betweenness_centrality": _mean(betweenness_values),
        "max_betweenness_centrality": max(betweenness_values, default=0.0),
        "top_betweenness_nodes": [
            {"node": n, "betweenness": b} for n, b in top_betweenness_nodes
        ],
    }
