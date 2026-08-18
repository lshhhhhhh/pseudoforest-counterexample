"""枢纽构造: K4 的三个顶点吹胀成 BBL-v.  G = h + 3x(BBL-0), 112 点三次图.
预测: 对偶三角剖分 T(58点) 的伪森林二划分 -- 严格版(无单色面, =路径嵌套2-因子)
UNSAT (鸽笼论证), 宽松版(允许漏点) 待裁决. 若宽松版也 UNSAT => 原问题反例!
"""
import sys
from itertools import combinations, permutations

import networkx as nx
from pysat.solvers import Cadical195

BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]


def build(perm2, perm3):
    """B_i 顶点 = i*38 + (1..37). 端口 = {1,2,3}+off. h = 114.
    B1 端口角色固定 (1->h, 2->B2, 3->B3); B2 角色 = perm2, B3 = perm3."""
    G = nx.Graph()
    for i in range(3):
        off = i * 38
        for u, nbrs in enumerate(BBL):
            if u == 0: continue
            for v in nbrs:
                if v == 0: continue
                G.add_edge(off + u, off + v)
    h = 114 + 1  # 任意不冲突标号
    role1 = {"h": 1, "n2": 2, "n3": 3}
    role2 = {"h": perm2[0], "n1": perm2[1], "n3": perm2[2]}
    role3 = {"h": perm3[0], "n1": perm3[1], "n2": perm3[2]}
    o1, o2, o3 = 0, 38, 76
    G.add_edge(h, o1 + role1["h"]); G.add_edge(h, o2 + role2["h"]); G.add_edge(h, o3 + role3["h"])
    G.add_edge(o1 + role1["n2"], o2 + role2["n1"])
    G.add_edge(o1 + role1["n3"], o3 + role3["n1"])
    G.add_edge(o2 + role2["n3"], o3 + role3["n2"])
    return G


found = None
for perm2 in permutations((1, 2, 3)):
    for perm3 in permutations((1, 2, 3)):
        G = build(perm2, perm3)
        if not all(d == 3 for _, d in G.degree()):
            continue
        ok, emb = nx.check_planarity(G)
        if ok:
            found = (perm2, perm3, G, emb)
            break
    if found: break

if not found:
    print("无平面布线?!")
    sys.exit(1)

perm2, perm3, G, emb = found
n, m = G.number_of_nodes(), G.number_of_edges()
print(f"布线 {perm2} {perm3}: n={n} m={m} 平面=True 三次=True "
      f"3-连通={nx.node_connectivity(G) >= 3}")

faces, visited = [], set()
for u in emb.nodes():
    for v in emb[u]:
        if (u, v) in visited: continue
        faces.append(tuple(emb.traverse_face(u, v, mark_half_edges=visited)))
print(f"面数={len(faces)} (Euler 需 {2 - n + m})")

edge2faces = {}
for fi, face in enumerate(faces):
    L = len(face)
    for i in range(L):
        e = frozenset((face[i], face[(i+1) % L]))
        edge2faces.setdefault(e, []).append(fi)
T = nx.Graph()
T.add_nodes_from(range(len(faces)))
for e, fs in edge2faces.items():
    assert len(fs) == 2
    T.add_edge(fs[0], fs[1])
nt, mt = T.number_of_nodes(), T.number_of_edges()
print(f"对偶 T: n={nt} m={mt} 三角剖分判据={mt == 3*nt - 6} "
      f"简单={not any(u==v for u,v in T.edges())}")

# T 的面 = G 的顶点: 每个 G 顶点对应其关联 3 面组成的三角形
tri_faces = []
for gv in G.nodes():
    fs = [fi for fi, face in enumerate(faces) if gv in face]
    assert len(fs) == 3, (gv, len(fs))
    tri_faces.append(tuple(fs))

def solve(strict):
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
    if strict:
        for (a, b, c) in tri_faces:
            ma, mb, mc = mE + a + 1, mE + b + 1, mE + c + 1
            cnf.append([-ma, -mb, -mc]); cnf.append([ma, mb, mc])
    with Cadical195(bootstrap_with=cnf) as s:
        sat = s.solve()
        model = s.get_model() if sat else None
    return sat, model

sat_relax, model_r = solve(strict=False)
print(f"宽松版(原问题, 允许漏点): {'SAT 可行' if sat_relax else 'UNSAT -- 原问题反例!!!'}")
sat_strict, model_s = solve(strict=True)
print(f"严格版(零漏点=路径嵌套2-因子): {'SAT' if sat_strict else 'UNSAT -- C1 反例确认!'}")

if sat_relax and model_r:
    mE = T.number_of_edges()
    A = [v for v in T.nodes() if model_r[mE + v] > 0]
    B = [v for v in T.nodes() if v not in set(A)]
    # 独立验证划分合法性
    for S, name in ((A, "A"), (B, "B")):
        sub = T.subgraph(S)
        bad = False
        for comp in nx.connected_components(sub):
            cs = sub.subgraph(comp)
            if cs.number_of_edges() > len(comp): bad = True
        print(f"  {name}: |{name}|={len(S)} 伪森林={'否!!' if bad else '是'}")
    # 漏点位置(单色面)
    mono = [t for t in tri_faces if len({(model_r[mE+x] > 0) for x in t}) == 1]
    print(f"  单色面(漏点)数={len(mono)}")
