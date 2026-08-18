"""机制对照: 鸽笼论证的谓词逐一可辨识.
C1: 三部件全换成可穿越小部件(三角形) => 应 SAT
C2: 两个 BBL 部件 + 一个三角形部件 => 应 SAT (2 组, 一侧一组)
C3: BBL 无哈密顿圈 (惰性子回路法) => 应 UNSAT
"""
import sys
from itertools import combinations

import networkx as nx
from pysat.solvers import Cadical195, Glucose42

sys.stdout.reconfigure(line_buffering=True)

BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]


def gadget_bbl(off):
    """返回 (边列表, 端口三元组): BBL-0, 顶点 off+1..off+37, 端口 off+1,2,3."""
    E = []
    for u, nbrs in enumerate(BBL):
        if u == 0: continue
        for v in nbrs:
            if v == 0: continue
            if off + u < off + v: E.append((off + u, off + v))
    return E, (off + 1, off + 2, off + 3)


def gadget_tri(off):
    """三角形部件: 3 点圈, 每点一个外部端口 (即部件=三角形, 端口=其3点)."""
    a, b, c = off + 1, off + 2, off + 3
    return [(a, b), (b, c), (a, c)], (a, b, c)


def build(gadgets):
    """gadgets: 三个 (E, ports). 布线: h-ports[0]; g1.p1-g2.p1... 同 26 号."""
    G = nx.Graph()
    for E, _ in gadgets: G.add_edges_from(E)
    h = 500
    (E1, p1), (E2, p2), (E3, p3) = gadgets
    G.add_edge(h, p1[0]); G.add_edge(h, p2[0]); G.add_edge(h, p3[0])
    G.add_edge(p1[1], p2[1]); G.add_edge(p1[2], p3[1]); G.add_edge(p2[2], p3[2])
    return G


def dual_T(G):
    ok, emb = nx.check_planarity(G)
    assert ok, "非平面"
    faces, vis = [], set()
    for u in emb.nodes():
        for v in emb[u]:
            if (u, v) in vis: continue
            faces.append(tuple(emb.traverse_face(u, v, mark_half_edges=vis)))
    e2f = {}
    for fi, f in enumerate(faces):
        L = len(f)
        for i in range(L):
            e2f.setdefault(frozenset((f[i], f[(i+1) % L])), []).append(fi)
    T = nx.Graph()
    T.add_nodes_from(range(len(faces)))
    for e, fs in e2f.items():
        assert len(fs) == 2
        T.add_edge(*fs)
    return T


def pf_sat(T):
    adjT = {v: sorted(T.neighbors(v)) for v in T.nodes()}
    edges = sorted(tuple(sorted(e)) for e in T.edges())
    eidx = {e: i for i, e in enumerate(edges)}
    mE = len(edges)
    cnf = []
    for v in T.nodes():
        outl, inl = [], []
        for w in adjT[v]:
            e = (min(v, w), max(v, w)); x = eidx[e] + 1
            if v == e[0]: outl.append(x); inl.append(-x)
            else: outl.append(-x); inl.append(x)
        mv = mE + v + 1
        for a, b in combinations(outl, 2): cnf.append([-mv, -a, -b])
        for a, b in combinations(inl, 2): cnf.append([mv, -a, -b])
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()


# C1: 全三角形部件
G = build([gadget_tri(0), gadget_tri(10), gadget_tri(20)])
assert all(d == 3 for _, d in G.degree())
T = dual_T(G)
print(f"C1 全可穿越部件: n(G)={G.number_of_nodes()} n(T)={T.number_of_nodes()} "
      f"=> {'SAT ✓机制辨识' if pf_sat(T) else 'UNSAT ?!'}")

# C2: 两 BBL + 一三角
G = build([gadget_bbl(0), gadget_bbl(100), gadget_tri(200)])
assert all(d == 3 for _, d in G.degree())
T = dual_T(G)
print(f"C2 两BBL+一三角: n(G)={G.number_of_nodes()} n(T)={T.number_of_nodes()} "
      f"=> {'SAT ✓ (2组各占一侧)' if pf_sat(T) else 'UNSAT ?! (预测应SAT)'}")

# C3: BBL 非 Ham (惰性)
Gb = nx.Graph()
for u, nbrs in enumerate(BBL):
    for v in nbrs: Gb.add_edge(u, v)
edges = sorted(tuple(sorted(e)) for e in Gb.edges())
eidx = {e: i + 1 for i, e in enumerate(edges)}
cnf = []
for v in Gb.nodes():
    inc = [eidx[tuple(sorted((v, w)))] for w in Gb.neighbors(v)]
    for comb in combinations(inc, len(inc) - 1):
        cnf.append(list(comb))
    for comb in combinations(inc, 3):
        cnf.append([-x for x in comb])
found = False
with Cadical195(bootstrap_with=cnf) as s:
    while s.solve():
        model = set(s.get_model())
        chosen = [e for e, i in eidx.items() if i in model]
        H = nx.Graph(chosen)
        comps = list(nx.connected_components(H))
        if len(comps) == 1:
            found = True; break
        for c in comps:
            ces = [eidx[e] for e in chosen if e[0] in c and e[1] in c]
            s.add_clause([-x for x in ces])
print(f"C3 BBL 哈密顿圈存在: {found} (应 False)")
