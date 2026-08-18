"""引理2(左右侧)直接机器复核: 对每条割曲线, 被穿越割边的"左端点"全在同一单色分量,
"右端点"全在另一分量, 且两分量异色.
实现: 曲线 = 对偶H的圈 (三角形序列); 相邻被穿越边共享少数派顶点或其另两端由未割边相连.
直接验证更强命题: 对每条曲线 C, {割边的A侧端点} 在 A 的同一分量, B 侧同理.
在 plantri n=9..11 全体三角剖分 x 全部合法划分(位掩码枚举)上断言.
"""
import subprocess
import sys
from itertools import combinations

import networkx as nx

PLANTRI = r"E:\math\vendor\plantri55\plantri.exe"


def parse(line):
    line = line.strip()
    if not line: return None
    head, _, rest = line.partition(" ")
    n = int(head)
    parts = rest.split(",")
    if len(parts) != n: return None
    return [[ord(c) - ord("a") for c in p] for p in parts]


def pf_ok(n, edges, mask):
    for side in (0, 1):
        idx = {}
        par = []
        extra = {}
        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        for v in range(n):
            if ((mask >> v) & 1) == side:
                idx[v] = len(par); par.append(len(par))
        for (a, b) in edges:
            if a in idx and b in idx:
                ra, rb = find(idx[a]), find(idx[b])
                if ra == rb:
                    extra[ra] = extra.get(ra, 0) + 1
                    if extra[ra] > 1: return False
                else:
                    par[ra] = rb
                    extra[rb] = extra.get(rb, 0) + extra.pop(ra, 0)
                    if extra[rb] > 1: return False
    return True


def main(n_tri):
    proc = subprocess.Popen([PLANTRI, "-a", str(n_tri)], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1 << 20)
    graphs = parts_checked = curves_checked = 0
    for line in proc.stdout:
        rot = parse(line)
        if rot is None: continue
        graphs += 1
        n = len(rot)
        G = nx.Graph((u, v) for u, nb in enumerate(rot) for v in nb)
        edges = sorted(tuple(sorted(e)) for e in G.edges())
        _, emb = nx.check_planarity(G)
        faces, vis = [], set()
        for u in emb.nodes():
            for v in emb[u]:
                if (u, v) in vis: continue
                faces.append(tuple(emb.traverse_face(u, v, mark_half_edges=vis)))
        e2f = {}
        for fi, f in enumerate(faces):
            for i in range(3):
                e2f.setdefault(frozenset((f[i], f[(i+1) % 3])), []).append(fi)
        for mask in range(1 << (n - 1)):        # 顶点0固定色0, 避免对称
            if not pf_ok(n, edges, mask): continue
            parts_checked += 1
            col = [(mask >> v) & 1 for v in range(n)]
            cut = [e for e in edges if col[e[0]] != col[e[1]]]
            if not cut: continue
            # 单色分量标号
            Gm = nx.Graph((a, b) for (a, b) in edges if col[a] == col[b])
            Gm.add_nodes_from(range(n))
            comp = {}
            for ci, cc in enumerate(nx.connected_components(Gm)):
                for v in cc: comp[v] = ci
            # 对偶 H 圈
            Hd = nx.Graph()
            for e in cut:
                fs = e2f[frozenset(e)]
                Hd.add_edge(fs[0], fs[1], primal=e)
            assert all(d == 2 for _, d in Hd.degree())
            for cyc in nx.connected_components(Hd):
                curves_checked += 1
                sub = Hd.subgraph(cyc)
                a_comps, b_comps = set(), set()
                for _, _, dat in sub.edges(data=True):
                    u, v = dat["primal"]
                    (a_comps if col[u] == 0 else b_comps).add(comp[u])
                    (a_comps if col[v] == 0 else b_comps).add(comp[v])
                assert len(a_comps) == 1 and len(b_comps) == 1, \
                    f"引理2破! n={n} mask={mask:b} A侧分量{a_comps} B侧{b_comps}"
    proc.wait()
    print(f"n={n_tri}: 图{graphs} 合法划分{parts_checked} 曲线{curves_checked} 全部通过引理2断言")


if __name__ == "__main__":
    for nt in (int(x) for x in sys.argv[1:]):
        main(nt)
