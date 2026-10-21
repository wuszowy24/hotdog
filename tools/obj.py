import collections,math
def load(path):
    V=[];F=[];mat=None;fm=[]
    for l in open(path):
        if l.startswith('v '):V.append(tuple(map(float,l.split()[1:4])))
        elif l.startswith('usemtl'):mat=l.split()[1]
        elif l.startswith('f '):
            idx=[int(t.split('/')[0])-1 for t in l.split()[1:]]
            for i in range(1,len(idx)-1):F.append((idx[0],idx[i],idx[i+1]));fm.append(mat)
    return V,F,fm
def components(V,F):
    p=list(range(len(V)))
    def find(a):
        while p[a]!=a:p[a]=p[p[a]];a=p[a]
        return a
    for a,b,c in F:
        for x,y in((a,b),(b,c)):
            rx,ry=find(x),find(y)
            if rx!=ry:p[rx]=ry
    comp=collections.defaultdict(list)
    used=set(i for f in F for i in f)
    for i in used:comp[find(i)].append(i)
    return list(comp.values())
