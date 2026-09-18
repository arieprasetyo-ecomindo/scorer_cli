from pathlib import Path

import networkx as nx

from app.metrics import (
    build_file_graph,
    compute_graph_metrics,
    extract_codebase_modules,
    load_graph,
)

SAMPLE_GRAPH = Path(__file__).parent.parent / "fixtures" / "sample_team_phoenix" / "graph.json"


def make_node(id_, source_file="", file_type="code"):
    return {"id": id_, "source_file": source_file, "file_type": file_type}


def make_link(source, target, relation):
    return {"source": source, "target": target, "relation": relation}


def test_cross_file_edge_is_counted():
    raw = {
        "nodes": [make_node("a", "fileA.py"), make_node("b", "fileB.py")],
        "links": [make_link("a", "b", "calls")],
    }
    g = build_file_graph(raw)
    assert set(g.nodes) == {"fileA.py", "fileB.py"}
    assert g.has_edge("fileA.py", "fileB.py")
    assert g["fileA.py"]["fileB.py"]["weight"] == 1


def test_same_file_edge_is_dropped():
    raw = {
        "nodes": [make_node("a", "fileA.py"), make_node("b", "fileA.py")],
        "links": [make_link("a", "b", "calls")],
    }
    g = build_file_graph(raw)
    assert g.number_of_edges() == 0


def test_edge_to_unresolved_symbol_is_dropped():
    raw = {
        "nodes": [make_node("a", "fileA.py"), make_node("b", "")],
        "links": [make_link("a", "b", "calls")],
    }
    g = build_file_graph(raw)
    assert g.number_of_edges() == 0


def test_non_dependency_relation_is_dropped():
    raw = {
        "nodes": [make_node("a", "fileA.py"), make_node("b", "fileB.py")],
        "links": [make_link("a", "b", "contains")],
    }
    g = build_file_graph(raw)
    assert g.number_of_edges() == 0


def test_repeated_edges_aggregate_weight():
    raw = {
        "nodes": [make_node("a", "fileA.py"), make_node("b", "fileB.py")],
        "links": [
            make_link("a", "b", "calls"),
            make_link("a", "b", "references"),
        ],
    }
    g = build_file_graph(raw)
    assert g["fileA.py"]["fileB.py"]["weight"] == 2


def test_non_code_node_is_dropped():
    raw = {
        "nodes": [
            make_node("a", "fileA.py"),
            make_node("b", "doc.md", file_type="rationale"),
        ],
        "links": [make_link("a", "b", "calls")],
    }
    g = build_file_graph(raw)
    assert "doc.md" not in g.nodes


def test_smoke_on_real_sample_graph():
    raw = load_graph(SAMPLE_GRAPH)
    g = build_file_graph(raw)
    assert g.number_of_nodes() > 0
    assert g.number_of_edges() > 0
    assert nx_has_no_self_loops(g)


def nx_has_no_self_loops(g):
    return all(u != v for u, v in g.edges())


def test_fan_in_fan_out():
    # hub <- a, b, c (fan-in 3); hub -> d (fan-out 1)
    g = nx.DiGraph()
    g.add_edges_from([("a", "hub"), ("b", "hub"), ("c", "hub"), ("hub", "d")])
    m = compute_graph_metrics(g)
    assert m["node_count"] == 5
    assert m["max_fan_in"] == 3
    assert m["max_fan_out"] == 1


def test_longest_dependency_path_on_chain():
    g = nx.DiGraph()
    g.add_edges_from([("a", "b"), ("b", "c"), ("c", "d")])
    m = compute_graph_metrics(g)
    assert m["longest_dependency_path"] == 3
    assert m["circular_dependencies"] == []


def test_cycle_is_detected():
    g = nx.DiGraph()
    g.add_edges_from([("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")])
    m = compute_graph_metrics(g)
    assert len(m["circular_dependencies"]) == 1
    cycle = m["circular_dependencies"][0]
    assert set(cycle) == {"a", "b", "c"}


def test_betweenness_on_star_graph():
    # hub sits on every path between a, b, c -> highest betweenness
    g = nx.DiGraph()
    g.add_edges_from([("a", "hub"), ("hub", "b"), ("hub", "c")])
    m = compute_graph_metrics(g)
    top_node = m["top_betweenness_nodes"][0]["node"]
    assert top_node == "hub"
    assert m["max_betweenness_centrality"] > 0


def test_empty_graph_does_not_crash():
    g = nx.DiGraph()
    m = compute_graph_metrics(g)
    assert m["node_count"] == 0
    assert m["avg_fan_in"] == 0.0
    assert m["modularity_score"] == 0.0
    assert m["circular_dependencies"] == []


def test_metrics_smoke_on_real_sample_graph():
    raw = load_graph(SAMPLE_GRAPH)
    g = build_file_graph(raw)
    m = compute_graph_metrics(g)
    assert m["node_count"] == g.number_of_nodes()
    assert m["max_fan_in"] >= m["avg_fan_in"]
    assert -1.0 <= m["modularity_score"] <= 1.0


def test_extract_codebase_modules_dedupes_and_sorts():
    raw = {
        "nodes": [
            make_node("a", "fileB.py"),
            make_node("b", "fileA.py"),
            make_node("c", "fileB.py"),
            make_node("d", ""),
            make_node("e", "doc.md", file_type="rationale"),
        ]
    }
    assert extract_codebase_modules(raw) == ["fileA.py", "fileB.py"]


def test_extract_codebase_modules_on_real_sample_graph():
    raw = load_graph(SAMPLE_GRAPH)
    modules = extract_codebase_modules(raw)
    assert "app/main.py" in modules
    assert modules == sorted(modules)
