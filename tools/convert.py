import sys,json,math,base64,struct,hashlib,collections
sys.path.insert(0,'/tmp');sys.path.insert(0,'/tmp/pk')
from obj import *
from dump import dump,MAT
MESH='/tmp/pak/Assets/Dachshunds/Meshes'
COATS={'smooth':'Krotkowlosy','long':'Dlugowlosy','wire':'Szorstkowlosy'}
COLORS={'red':'Rudy','bt':'Czarny_podpalany','ct':'Czekoladowy_podpalany','cream':'Kremowy','merle':'Merle','piebald':'Srokaty','brindle':'Pregowany','boar':'Dzikowaty'}

# ---------------- szkielet (pozycje spoczynkowe, układ silnika: x przód, y góra, z bok) ----------------
BONES=[ # name, parent, pivot
 ('body',-1,(0,.48,0)),('chest',0,(.50,.50,0)),('hip',0,(-.55,.48,0)),
 ('neck',1,(.60,.56,0)),('head',3,(1.0,.57,0)),('jaw',4,(1.04,.47,0)),
 ('earA',4,(.98,.60,.20)),('earB',4,(.98,.60,-.20)),('earA2',6,(.98,.42,.21)),('earB2',7,(.98,.42,-.21)),
 ('fShA',1,(.53,.40,.17)),('fElA',10,(.53,.25,.17)),('fWrA',11,(.53,.12,.17)),
 ('fShB',1,(.53,.40,-.17)),('fElB',13,(.53,.25,-.17)),('fWrB',14,(.53,.12,-.17)),
 ('rHpA',2,(-.57,.40,.17)),('rKnA',16,(-.57,.25,.17)),('rHkA',17,(-.57,.12,.17)),
 ('rHpB',2,(-.57,.40,-.17)),('rKnB',19,(-.57,.25,-.17)),('rHkB',20,(-.57,.12,-.17)),
 ('tail0',2,(-.69,.54,0)),('tail1',22,(-.79,.565,0)),('tail2',23,(-.89,.585,0)),('tail3',24,(-.99,.605,0)),
 ('eyeA',4,(1.1904,.6132,.1883)),('eyeB',4,(1.1904,.6132,-.1883)),
]
BI={b[0]:i for i,b in enumerate(BONES)}
def ss(a,b,x):  # smoothstep (działa też dla a>b)
    t=(x-a)/(b-a) if a!=b else 1.0
    t=max(0.0,min(1.0,t));return t*t*(3-2*t)

# oczy: przesunięcie na powierzchnię czaszki
SKULL_C=(1.0,.57,0.0);SKULL_R=(.30,.25,.25)
def eye_target(side):
    phi=.78*side;th=.16
    d=(math.cos(th)*math.cos(phi),math.sin(th),math.cos(th)*math.sin(phi))
    t=1/math.sqrt((d[0]/SKULL_R[0])**2+(d[1]/SKULL_R[1])**2+(d[2]/SKULL_R[2])**2)
    return tuple(SKULL_C[i]+t*d[i] for i in range(3)),phi
EYE_SCALE=2.3
DY=-.035

def bbox(P):
    xs=P[0::3];ys=P[1::3];zs=P[2::3]
    return (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))

def classify(c):
    P=c['p'];n=len(P)//3;x0,x1,y0,y1,z0,z1=bbox(P);cx=(x0+x1)/2;cy=(y0+y1)/2;cz=(z0+z1)/2
    side=1 if cz>0 else -1
    m=c['m']
    if m in('black','blue') and n==86:
        if x0>1.3:return 'nose',0
        return 'eye',side
    if n==314:return 'torso',0
    if n==222 and abs(x0-.22)<.03:return 'chest',0
    if n==222 and abs(x0-.70)<.03:return 'skull',0
    if n==200:return 'neck',0
    if n==164:return 'muzzle',0
    if n==128:
        if y1>.65 or (y1<.5 and y0>.1 and (x1-x0)<.22 and x1<1.07 and m.endswith('patch') and False):return 'ear',side
        return 'ear',side
    if n==52:return 'brow_dot',side
    if n==146:
        if x1<-.8:return 'plume',0
        if x1-x0>.9 and y1<.4:return 'belly',0
        if y1<.35 and (abs(cx)>.4):return 'legfeather',(1 if cx>0 else -1,side)
        if x0>1.05 and x1<1.45 and y1<.5:return 'beard',0
        if x0>.9 and x1<1.2 and y0>.65:return 'brow',side
        if x0>1.2:return 'blaze',0
        return 'patch',0
    if n==86:
        if x1<-.65 and cx<-.8:return 'tail',0
        if y1>=.35 and y1<=.43 and y0>.07:return 'leg',(1 if cx>0 else -1,side)
        if y1<.16:return 'paw',(1 if cx>0 else -1,side)
        if y0>.55 and y1<.8 and (x1-x0)<.3 and (y1-y0)<.2:return 'patch',0   # kępki / łaty
        return 'patch',0
    raise Exception('unclassified %d %s'%(n,bbox(P)))

def wpair(a,b,w):return (BI[a],BI[b],w)
def torso_w(x):
    if x<=-.55:return wpair('hip','hip',0)
    if x<0:return wpair('hip','body',ss(-.55,0,x))
    if x<.5:return wpair('body','chest',ss(0,.5,x))
    return wpair('chest','chest',0)
def legchain(names,y):
    sp,el,wr=names
    if y>=.245:return wpair(sp,el,ss(.34,.245,y) if False else 1-ss(.245,.34,y))
    return wpair(el,wr,1-ss(.10,.17,y))
def legw(front,side,y):
    s='A' if side>0 else 'B'
    names=(('fSh'+s,'fEl'+s,'fWr'+s) if front else ('rHp'+s,'rKn'+s,'rHk'+s))
    return legchain(names,y)
def tailw(x):
    t=(-.69-x)/.10
    if t<=0:return wpair('tail0','tail0',0)
    i=int(min(2,math.floor(t)));f=min(1.0,t-i) if t<3 else 1.0
    f=ss(0,1,f);names=['tail0','tail1','tail2','tail3']
    if t>=3:return wpair('tail3','tail3',0)
    return wpair(names[i],names[i+1],f)
def earw(side,y):
    a,b=('earA','earA2') if side>0 else ('earB','earB2')
    return wpair(a,b,1-ss(.34,.50,y))
def neckw(x):
    if x<.72:return wpair('chest','neck',ss(.50,.72,x))
    return wpair('neck','head',ss(.72,.94,x))
def muzzlew(x,y):
    jw=ss(.505,.43,y)*ss(1.04,1.20,x)
    return wpair('head','jaw',jw),jw

def weights_for(kind,side,P):
    out=[]
    lip=[]
    for i in range(0,len(P),3):
        x,y,z=P[i],P[i+1],P[i+2];l=0.0
        if kind in('torso','belly','patch') :
            if kind=='patch' and x>1.05:w=muzzlew(x,y)[0]
            else:w=torso_w(x)
        elif kind=='chest':
            w=wpair('body','chest',ss(.22,.45,x))
        elif kind=='neck':w=neckw(x)
        elif kind in('skull','nose','brow','brow_dot'):w=wpair('head','head',0)
        elif kind in('muzzle','blaze','beard'):
            w,jw=muzzlew(x,y)
            if kind=='beard':jw=max(jw,.9);w=wpair('head','jaw',jw)
            l=4*jw*(1-jw) if kind!='beard' else 0
        elif kind=='ear':w=earw(side,y)
        elif kind in('leg','paw','legfeather'):
            fr,sd=side
            w=legw(fr>0,sd,y if kind!='paw' else .05)
        elif kind in('tail','plume'):w=tailw(x)
        elif kind=='eye':
            nm='eyeA' if side>0 else 'eyeB';w=wpair(nm,nm,0)
        else:raise Exception(kind)
        out.append(w);lip.append(l)
    return out,lip

def flatten_back(P):
    out=list(P)
    for i in range(0,len(P),3):
        x,y,z=P[i],P[i+1],P[i+2]
        t=1-(x/.82)**2-(z/.27)**2
        if t>0:
            ys=.48+.28*math.sqrt(t)
            if y>ys+.004:out[i+1]=ys+.004
    return out
def move_eye(P,side):
    x0,x1,y0,y1,z0,z1=bbox(P);c=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
    tgt,phi=eye_target(side)
    cp,sp=math.cos(phi),math.sin(phi)
    out=[]
    for i in range(0,len(P),3):
        dx,dy,dz=P[i]-c[0],P[i+1]-c[1],P[i+2]-c[2]
        # spłaszczona wzdłuż x -> obracamy tak, by cienka oś wskazywała na zewnątrz
        # (obrót wokół osi pionowej o phi)
        rx=dx*cp-dz*sp*(-1 if False else 1)
        rz=dx*sp+dz*cp
        # obrót: x'=x cos - z sin ; z'= x sin + z cos  (phi znakowane stroną)
        rx=dx*cp-dz*sp;rz=dx*sp+dz*cp
        out+= [tgt[0]+rx*EYE_SCALE,tgt[1]+dy*EYE_SCALE,tgt[2]+rz*EYE_SCALE]
    return out,tgt

def normals(P,T):
    n=[0.0]*len(P)
    for i in range(0,len(T),3):
        a,b,c=T[i]*3,T[i+1]*3,T[i+2]*3
        ux,uy,uz=P[b]-P[a],P[b+1]-P[a+1],P[b+2]-P[a+2];vx,vy,vz=P[c]-P[a],P[c+1]-P[a+1],P[c+2]-P[a+2]
        nx,ny,nz=uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx
        for k in(a,b,c):n[k]+=nx;n[k+1]+=ny;n[k+2]+=nz
    return n

def main():
    comps=[];index={};variants={};kinds=collections.Counter();eyecenters={}
    for ck,cname in COATS.items():
        for ok,oname in COLORS.items():
            name=f'{cname}_{oname}'
            raw=dump(f'{MESH}/{cname}/Jamnik_{name}.obj')
            lst=[]
            raw=[c for c in raw if c['m']!='wild_back']
            for c in raw:
                kind,side=classify(c)
                P=list(c['p'])
                if kind=='eye':
                    P,tgt=move_eye(P,side);eyecenters[side]=tgt
                    sd=side
                if c['m']=='wild_back' and kind=='patch':P=flatten_back(P)
                if kind=='nose':
                    # lekko powiększamy nos, żeby był widoczny
                    x0,x1,y0,y1,z0,z1=bbox(P);cc=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
                    P=[cc[i%3]+(P[i]-cc[i%3])*1.25 for i in range(len(P))]
                key=hashlib.md5((kind+str(side)+','.join('%.3f'%v for v in P)).encode()).hexdigest()
                if key not in index:
                    W,lip=weights_for(kind,side,P)
                    index[key]=len(comps)
                    comps.append({'kind':kind,'side':side,'P':P,'T':c['t'],'W':W,'lip':lip})
                lst.append((index[key],c['m']))
                kinds[kind]+=1
            variants[f'{ck}_{ok}']=lst
    # --- zapis binarny
    out_comps=[]
    tv=tt=0
    for c in comps:
        n=len(c['P'])//3
        pos=struct.pack('<%dh'%(n*3),*[max(-32767,min(32767,int(round((v+(DY if i%3==1 else 0))*8192)))) for i,v in enumerate(c['P'])])
        tri=struct.pack('<%dH'%len(c['T']),*c['T'])
        sk=bytearray()
        for b0,b1,w in c['W']:sk+=bytes([b0,b1,int(round(max(0,min(1,w))*255))])
        lip=bytes(int(round(max(0,min(1,l))*255)) for l in c['lip'])
        ks={'eye':1,'nose':2,'ear':3,'muzzle':4,'blaze':4,'paw':5,'tail':6,'plume':6}.get(c['kind'],0)
        out_comps.append({'n':n,'k':ks,'kind':c['kind'],'pos':base64.b64encode(pos).decode(),'tri':base64.b64encode(tri).decode(),'sk':base64.b64encode(bytes(sk)).decode(),'lip':base64.b64encode(lip).decode()})
        tv+=n;tt+=len(c['T'])//3
    data={'v':1,'dy':DY,'bones':[[b[0],b[1],[b[2][0],b[2][1]+DY,b[2][2]]] for b in BONES],'comps':out_comps,'variants':variants,'mat':{k:list(v) for k,v in MAT.items()},
          'eyes':{str(k):list(v) for k,v in eyecenters.items()},'bi':BI}
    js='const DACH='+json.dumps(data,separators=(',',':'))+';\n'
    open('/tmp/pk/dach_data.js','w').write(js)
    print('unique comps',len(comps),'verts',tv,'tris',tt,'bytes',len(js))
    print(kinds)
    print('eye targets',eyecenters)
main()
