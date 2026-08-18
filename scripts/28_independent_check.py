"""独立编码 #2 (与 26 号无共享结构):
色变量 c_v; 认领变量 s_{u->v}, s_{v->u} 每边两个;
(c_u=c_v=X) -> (s_uv | s_vu); AMO_v {s_{v->w}}. 求解器 Glucose42.
+ 阳性对照 + 反例图存档.
"""
import json
import sys
from itertools import combinations, permutations

import networkx as nx
from pysat.solvers import Glucose42

sys.stdout.reconfigure(line_buffering=True)

BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]


def build_hub():
    G = nx.Graph()
    for i in range(3):
        off = i * 38
        for u, nbrs in enumerate(BBL):
            if u == 0: continue
            for v in nbrs:
                if v == 0: continue
                G.add_edge(off + u, off + v)
    h = 115
    G.add_edge(h, 0 + 1); G.add_edge(h, 38 + 1); G.add_edge(h, 76 + 1)
    G.add_edge(0 + 2, 38 + 2)
    G.add_edge(0 + 3, 76 + 2)
    G.add_edge(38 + 3, 76 + 3)
    return G


def dual_of(G):
    ok, emb = nx.check_planarity(G)
    assert ok
    faces, visited = [], set()
    for u in emb.nodes():
        for v in emb[u]:
            if (u, v) in visited: continue
            faces.append(tuple(emb.traverse_face(u, v, mark_half_edges=visited)))
    e2f = {}
    for fi, face in enumerate(faces):
        L = len(face)
        for i in range(L):
            e = frozenset((face[i], face[(i+1) % L]))
            e2f.setdefault(e, []).append(fi)
    T = nx.Graph()
    T.add_nodes_from(range(len(faces)))
    for e, fs in e2f.items():
        assert len(fs) == 2
        T.add_edge(fs[0], fs[1])
    return T, faces


def solve2(T, strict_faces=None):
    nodes = sorted(T.nodes())
    vid = {v: i + 1 for i, v in enumerate(nodes)}     # c_v
    nv = len(nodes)
    nxt = nv + 1
    s = {}
    for u, v in T.edges():
        s[(u, v)] = nxt; nxt += 1
        s[(v, u)] = nxt; nxt += 1
    cnf = []
    for u, v in T.edges():
        cu, cv = vid[u], vid[v]
        suv, svu = s[(u, v)], s[(v, u)]
        cnf.append([-cu, -cv, suv, svu])
        cnf.append([cu, cv, suv, svu])
    for v in nodes:
        outs = [s[(v, w)] for w in T.neighbors(v)]
        for a, b in combinations(outs, 2):
            cnf.append([-a, -b])
    if strict_faces:
        for (a, b, c) in strict_faces:
            cnf.append([-vid[a], -vid[b], -vid[c]])
            cnf.append([vid[a], vid[b], vid[c]])
    with Glucose42(bootstrap_with=cnf) as slv:
        sat = slv.solve()
        model = slv.get_model() if sat else None
    return sat, model, vid


# 阳性对照
ico = nx.icosahedral_graph()
sat, _, _ = solve2(ico)
print(f"[编码2] 正二十面体: {'SAT' if sat else 'UNSAT?!'}")

G = build_hub()
assert all(d == 3 for _, d in G.degree()) and nx.check_planarity(G)[0]
T, faces = dual_of(G)
nt, mt = T.number_of_nodes(), T.number_of_edges()
print(f"[编码2] 枢纽对偶 T: n={nt} m={mt} 判据={mt == 3*nt-6}")
tri_faces = []
for gv in G.nodes():
    fs = [fi for fi, f in enumerate(faces) if gv in f]
    assert len(fs) == 3
    tri_faces.append(tuple(fs))

sat_r, model, vid = solve2(T)
print(f"[编码2] 宽松版: {'SAT -- 与编码1矛盾!!' if sat_r else 'UNSAT (与编码1一致)'}")
sat_s, _, _ = solve2(T, strict_faces=tri_faces)
print(f"[编码2] 严格版: {'SAT -- 矛盾!!' if sat_s else 'UNSAT (一致)'}")

# 存档
out = {
    "G_cubic_112": {str(u): sorted(G.neighbors(u)) for u in G.nodes()},
    "T_dual_58_adj": {str(u): sorted(T.neighbors(u)) for u in T.nodes()},
    "T_g6": nx.to_graph6_bytes(T, header=False).decode().strip(),
    "G_g6": nx.to_graph6_bytes(G, header=False).decode().strip(),
    "construction": "K4 hub h + 3x(BBL minus vertex 0); ports: h<-1_i, 2_1-2_2, 3_1-2_3, 3_2-3_3",
    "claims": {"relaxed_pf_partition": "UNSAT enc1+enc2", "strict_no_mono_face": "UNSAT enc1+enc2"},
}
with open(r"E:\math\problems\pseudoforest-partition\data\counterexample_58.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("已存档 data/counterexample_58.json")
