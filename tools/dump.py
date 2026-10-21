import sys,json,math;sys.path.insert(0,'/tmp')
from obj import *
MAT={'accent_cream':(0.94,0.82,0.64),'accent_red':(0.72,0.32,0.09),'black':(0.012,0.009,0.008),'blue':(0.12,0.48,0.88),'fur_black':(0.025,0.022,0.028),'fur_brindle':(0.48,0.17,0.045),'fur_chocolate':(0.18,0.065,0.03),'fur_cream':(0.86,0.74,0.53),'fur_merle':(0.28,0.3,0.34),'fur_red':(0.55,0.19,0.045),'fur_wildboar':(0.36,0.3,0.21),'merle_patch':(0.1,0.11,0.13),'stripe':(0.12,0.065,0.03),'tan':(0.72,0.34,0.1),'tan_choc':(0.58,0.29,0.1),'white':(0.94,0.9,0.82),'wild_back':(0.18,0.15,0.11)}
def conv(p):return (p[0],p[2],-p[1])   # obj (x,y,z-up) -> engine (x, up, lateral)
def orient(T,n):
    from collections import defaultdict,deque
    T=[list(t) for t in T]
    ef=defaultdict(list)
    for fi,t in enumerate(T):
        for k in range(3):ef[frozenset((t[k],t[(k+1)%3]))].append(fi)
    seen=[False]*len(T)
    for s0 in range(len(T)):
        if seen[s0]:continue
        seen[s0]=True;q=deque([s0])
        while q:
            f=q.popleft();t=T[f]
            for k in range(3):
                a,b=t[k],t[(k+1)%3]
                for g in ef[frozenset((a,b))]:
                    if g==f or seen[g]:continue
                    u=T[g]
                    # neighbour must traverse edge as (b,a)
                    same=any((u[j],u[(j+1)%3])==(a,b) for j in range(3))
                    if same:u[1],u[2]=u[2],u[1]
                    seen[g]=True;q.append(g)
    return [tuple(t) for t in T]
def dump(path):
    V,F,fm=load(path);C=components(V,F)
    vm={}
    for (a,b,c),m in zip(F,fm):
        for i in(a,b,c):vm[i]=m
    comps=[]
    for c in C:
        idx=sorted(c);remap={v:k for k,v in enumerate(idx)}
        P=[conv(V[i]) for i in idx]
        T=[tuple(remap[i] for i in f) for f in F if f[0] in remap]
        T=orient(T,len(P))
        # fix winding by signed volume
        vol=0
        for a,b,cc in T:
            pa,pb,pc=P[a],P[b],P[cc]
            vol+=(pa[0]*(pb[1]*pc[2]-pb[2]*pc[1])-pa[1]*(pb[0]*pc[2]-pb[2]*pc[0])+pa[2]*(pb[0]*pc[1]-pb[1]*pc[0]))/6
        if vol<0:T=[(a,cc,b) for a,b,cc in T]
        comps.append({'p':[round(x,4) for q in P for x in q],'t':[i for f in T for i in f],'m':vm[idx[0]]})
    return comps
if __name__=='__main__':
    out={}
    for name in sys.argv[1:]:
        out[name]=dump(f'/tmp/pak/Assets/Dachshunds/Meshes/{name.split("_")[0]}/Jamnik_{name}.obj')
    json.dump({'mat':MAT,'dogs':out},open('/tmp/pk/raw.json','w'))
    print({k:len(v) for k,v in out.items()})
