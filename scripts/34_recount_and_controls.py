"""审稿修订三连: (1) n=4..12 全扫重跑拿一手 per-n 数; (2) 脚本31累计 n=4..10;
(3) 缺失的 1-BBL 机制对照."""
import subprocess
import sys
from itertools import combinations

import networkx as nx
from pysat.solvers import Cadical195
from importlib.machinery import SourceFileLoader

sys.stdout.reconfigure(line_buffering=True)
PLANTRI = r"E:\math\vendor\plantri55\plantri.exe"


def parse(line):
    line = line.strip()
    if not line: return None
    head, _, rest = line.partition(" ")
    n = int(head)
    parts = rest.split(",")
    if len(parts) != n: return None
    return [[ord(c) - ord("a") for c in p] for p in parts]


def feasible(G):
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    eidx = {e: i + 1 for i, e in enumerate(edges)}
    mE = len(edges)
    vid = {v: mE + i + 1 for i, v in enumerate(sorted(G.nodes()))}
    cnf = []
    for v in G.nodes():
        outs, ins = [], []
        for w in G.neighbors(v):
            e = tuple(sorted((v, w)))
            lit = eidx[e] if v == e[0] else -eidx[e]
            outs.append(lit); ins.append(-lit)
        wv = vid[v]
        for a, b in combinations(outs, 2): cnf.append([-wv, -a, -b])
        for a, b in combinations(ins, 2): cnf.append([wv, -a, -b])
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()


# (1) n=4..12 recount
print("== (1) n=4..12 全扫重跑 ==")
total_sum = 0
for n in range(4, 13):
    proc = subprocess.Popen([PLANTRI, "-a", str(n)], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1 << 20)
    tot = feas = 0
    for line in proc.stdout:
        rot = parse(line)
        if rot is None: continue
        tot += 1
        G = nx.Graph((u, v) for u, nb in enumerate(rot) for v in nb)
        if feasible(G): feas += 1
    proc.wait()
    total_sum += tot
    print(f"n={n}: total={tot} feasible={feas} {'OK' if tot == feas else 'COUNTEREX?!'}")
print(f"n=4..12 合计: {total_sum}  (A000109 和应为 9150)")

# (2) 脚本31 累计 n=4..10
print("== (2) 引理2.3断言 累计 n=4..10 ==")
l31 = SourceFileLoader("l31", r"E:\math\problems\pseudoforest-partition\scripts\31_lemma_sides_check.py")
mod = l31.load_module()
# 31 的 main 打印各自行; 直接调用
for n in range(4, 11):
    mod.main(n)

# (3) 1-BBL 对照
print("== (3) 1-BBL + 2三角形 机制对照 ==")
c30 = SourceFileLoader("c30", r"E:\math\problems\pseudoforest-partition\scripts\30_mechanism_controls.py").load_module.__wrapped__ if False else None
m30 = SourceFileLoader("m30", r"E:\math\problems\pseudoforest-partition\scripts\30_mechanism_controls.py")
# 不能直接 load (会执行主体); 重写内联:
BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]

def gadget_bbl(off):
    E = []
    for u, nbrs in enumerate(BBL):
        if u == 0: continue
        for v in nbrs:
            if v == 0: continue
            if off + u < off + v: E.append((off + u, off + v))
    return E, (off + 1, off + 2, off + 3)

def gadget_tri(off):
    a, b, c = off + 1, off + 2, off + 3
    return [(a, b), (b, c), (a, c)], (a, b, c)

def build(gads):
    G = nx.Graph()
    for E, _ in gads: G.add_edges_from(E)
    h = 500
    (E1, p1), (E2, p2), (E3, p3) = gads
    G.add_edge(h, p1[0]); G.add_edge(h, p2[0]); G.add_edge(h, p3[0])
    G.add_edge(p1[1], p2[1]); G.add_edge(p1[2], p3[1]); G.add_edge(p2[2], p3[2])
    return G

def dual_T(G):
    ok, emb = nx.check_planarity(G)
    assert ok
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
    T = nx.Graph(); T.add_nodes_from(range(len(faces)))
    for e, fs in e2f.items():
        assert len(fs) == 2
        T.add_edge(*fs)
    return T

for name, gads in [("1BBL+2tri", [gadget_bbl(0), gadget_tri(100), gadget_tri(110)]),
                   ("2BBL+1tri", [gadget_bbl(0), gadget_bbl(100), gadget_tri(200)]),
                   ("3BBL",      [gadget_bbl(0), gadget_bbl(100), gadget_bbl(200)])]:
    G = build(gads)
    assert all(d == 3 for _, d in G.degree())
    T = dual_T(G)
    print(f"{name}: n(T)={T.number_of_nodes()} => {'SAT' if feasible(T) else 'UNSAT'}")
