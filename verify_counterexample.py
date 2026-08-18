"""Standalone verifier for the 58-vertex counterexample.

Claim: the planar triangulation T* (in data/counterexample_58.json, key
"T_dual_58_adj") has NO partition of its vertex set into two induced
pseudoforests; equivalently, no orientation with min(d+, d-) <= 1 everywhere.

This script is self-contained modulo `pip install networkx python-sat`.
It re-checks, from the archived adjacency lists alone:
  1. G* is a 112-vertex 3-connected cubic planar graph;
  2. T* is a simple planar triangulation on 58 vertices (m = 3n - 6),
     and T* is isomorphic to the dual of G*;
  3. the Barnette-Bosak-Lederberg base graph is non-Hamiltonian
     (lazy sub-tour elimination SAT);
  4. T* has no valid orientation  -- via a direct encoding written here,
     independent of the discovery pipeline: variables = one direction bit
     per edge + one witness bit per vertex; witness=1 forces out-degree<=1,
     witness=0 forces in-degree<=1 (pairwise AMO);
  5. positive control: the icosahedron is feasible under the same code.

Run:  python verify_counterexample.py
Expected output ends with:  ALL CHECKS PASSED - T* is a counterexample.
"""
import json
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx
from pysat.solvers import Cadical195

HERE = Path(__file__).parent
DATA = json.loads((HERE / "data" / "counterexample_58.json").read_text(encoding="utf-8"))


def graph_from(adj):
    G = nx.Graph()
    for u, nbrs in adj.items():
        for v in nbrs:
            G.add_edge(int(u), int(v))
    return G


def feasible(T):
    """SAT: exists orientation of T with min(d+,d-)<=1 at every vertex."""
    edges = sorted(tuple(sorted(e)) for e in T.edges())
    eidx = {e: i + 1 for i, e in enumerate(edges)}
    mE = len(edges)
    vids = {v: mE + i + 1 for i, v in enumerate(sorted(T.nodes()))}
    cnf = []
    for v in T.nodes():
        outs, ins = [], []
        for w in T.neighbors(v):
            e = tuple(sorted((v, w)))
            lit = eidx[e] if v == e[0] else -eidx[e]   # true = low->high
            outs.append(lit)      # v's edge oriented away from v
            ins.append(-lit)
        wv = vids[v]
        for a, b in combinations(outs, 2):
            cnf.append([-wv, -a, -b])                  # witness -> outdeg<=1
        for a, b in combinations(ins, 2):
            cnf.append([wv, -a, -b])                   # else   -> indeg<=1
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()


def hamiltonian(G):
    """Lazy 2-factor + connectivity: True iff G has a Hamiltonian cycle."""
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    eidx = {e: i + 1 for i, e in enumerate(edges)}
    cnf = []
    for v in G.nodes():
        inc = [eidx[tuple(sorted((v, w)))] for w in G.neighbors(v)]
        for comb in combinations(inc, len(inc) - 1):
            cnf.append(list(comb))                     # degree >= 2
        for comb in combinations(inc, 3):
            cnf.append([-x for x in comb])             # degree <= 2
    with Cadical195(bootstrap_with=cnf) as s:
        while s.solve():
            model = set(s.get_model())
            chosen = [e for e, i in eidx.items() if i in model]
            H = nx.Graph(chosen)
            comps = list(nx.connected_components(H))
            if len(comps) == 1 and H.number_of_nodes() == G.number_of_nodes():
                return True
            for c in comps:
                ces = [eidx[e] for e in chosen if e[0] in c and e[1] in c]
                s.add_clause([-x for x in ces])
    return False


def dual_of(G):
    ok, emb = nx.check_planarity(G)
    assert ok
    faces, vis = [], set()
    for u in emb.nodes():
        for v in emb[u]:
            if (u, v) in vis:
                continue
            faces.append(tuple(emb.traverse_face(u, v, mark_half_edges=vis)))
    e2f = {}
    for fi, f in enumerate(faces):
        L = len(f)
        for i in range(L):
            e2f.setdefault(frozenset((f[i], f[(i + 1) % L])), []).append(fi)
    D = nx.Graph()
    D.add_nodes_from(range(len(faces)))
    for e, fs in e2f.items():
        assert len(fs) == 2, "not a closed surface embedding"
        D.add_edge(*fs)
    return D


def main():
    G = graph_from(DATA["G_cubic_112"])
    T = graph_from(DATA["T_dual_58_adj"])

    # 1. G* sanity
    assert G.number_of_nodes() == 112 and all(d == 3 for _, d in G.degree())
    assert nx.check_planarity(G)[0], "G* not planar"
    assert nx.node_connectivity(G) >= 3, "G* not 3-connected"
    print("1. G*: 112 vertices, cubic, planar, 3-connected  OK")

    # 2. T* is a triangulation and equals dual(G*)
    n, m = T.number_of_nodes(), T.number_of_edges()
    assert n == 58 and m == 3 * n - 6, (n, m)
    assert nx.check_planarity(T)[0], "T* not planar"
    assert nx.node_connectivity(T) >= 3, "T* not 3-connected"
    D = dual_of(G)
    assert nx.is_isomorphic(D, T), "archived T* is not the dual of G*"
    print("2. T*: simple planar triangulation on 58 vertices, = dual(G*)  OK")

    # 3. base graph non-Hamiltonian
    # reconstruct Gamma by re-adding v0 joined to the three degree-2 ports
    # of fragment 1 (vertices 1,2,3 in copy 0 of the archive layout):
    Gamma = nx.Graph()
    frag = [(u, v) for u, v in G.edges() if 1 <= u <= 37 and 1 <= v <= 37]
    Gamma.add_edges_from(frag)
    v0 = 0
    for p in (1, 2, 3):
        Gamma.add_edge(v0, p)
    assert all(d == 3 for _, d in Gamma.degree()) and Gamma.number_of_nodes() == 38
    assert not hamiltonian(Gamma), "base graph IS Hamiltonian?!"
    print("3. 38-vertex base graph: cubic, non-Hamiltonian  OK")

    # 4. positive control
    assert feasible(nx.icosahedral_graph()), "control failed - encoder broken"
    print("4. positive control (icosahedron): feasible  OK")

    # 5. the verdict
    assert not feasible(T), "T* is feasible?! claim refuted"
    print("5. T*: NO valid orientation / pseudoforest 2-partition  OK")

    print("\nALL CHECKS PASSED - T* is a counterexample.")


if __name__ == "__main__":
    main()
