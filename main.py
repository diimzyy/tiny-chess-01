import json,os,urllib.request,re
U=os.environ["MAKEFUN_ENV_URL"]
def q(p,o):r=urllib.request.Request(U+p,data=json.dumps(o).encode(),headers={"Content-Type":"application/json"})
return json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
PST=[[0]*8 for _ in range(8)]
VAL={'p':1,'n':3,'b':3,'r':5,'q':9,'k':0}
OFF={'p':[0,-1,1],'n':[(-2,-1),(-2,1),(-1,-2),(1,-2),(2,-1),(2,1),(1,2),(-1,2)],'b':[(i,i) for i in [-3,-2,-1,1,2,3]],'r':[(i,0) for i in [-7,-6,-5,-4,4,5,6,7]]+[(0,i) for i in [-7,-6,-5,-4,4,5,6,7]],'q':[],'k':[]}
for d in OFF['b']:OFF['q'].append(d)
for d in OFF['r']:OFF['q'].append(d)
OFF['q']=[(a,b) for a in range(-7,8) for b in range(-7,8) if(a==0)!=(b==0)or abs(a)==abs(b)]
for i in range(8):for j in range(8):PST[j][i]=max(0,(min(i,j)+min(7-i,7-j))*2-14)//2
FILES='abcdefgh'
def parse_fen(f):parts=f.split();board=[[None]*8 for _ in range(8)];rank=7;file_idx=0
for ch in parts[0]:if ch=='/':rank-=1;file_idx=0
elif ch.isdigit():file_idx+=int(ch)
else:color='w' if ch.isupper() else 'b'
board[rank][file_idx]=(color,ch.lower());file_idx+=1
turn='w' if parts[1]=='w' else 'b'
castle=parts[2];ep=parts[3];half=parts[4];full=parts[5]
return board,turn,castle,ep,int(half),int(full)
def to_fen(board,turn,castle,ep,half,full):rows=[]
for r in range(7,-1,-1):row='';cnt=0
for f in range(8):pc=board[r][f]
if cnt:row+=str(cnt);cnt=0
if pc:row+=(pc[0].upper()+pc[1]) if pc[0]=='w' else(pc[0]+pc[1]).lower()
else:cnt+=1
if cnt:row+=str(cnt)
rows.append(row)
return '/'.join(rows)+' '+turn+' '+castle+' '+ep+' '+str(half)+' '+str(full)
def gen_moves(board,turn,castle,ep):moves=[]
for r in range(8):for f in range(8):pc=board[r][f]
if not pc or pc[0]!=turn:continue
t=pc[1]
if t=='p':d=-1 if turn=='w' else 1
nr=r+d
if 0<=nr<8 and not board[nr][f]:moves.append((r,f,nr,f))
sr=r+(2*d) if(turn=='w'and r==6)or(turn=='b'and r==1)else None
if sr is not None and 0<=sr<8 and not board[sr][f]:moves.append((r,f,sr,f))
for df in[-1,1]:nf=f+df
if 0<=nf<8 and 0<=nr<8:tgt=board[nr][nf]
if tgt and tgt[0]!=turn:moves.append((r,f,nr,nf))
if ep!='-' and FILES[nf]==ep[0] and int(ep[1])-1==nr:moves.append((r,f,nr,nf))
elif t=='n':for dr,dc in[(-2,-1),(-2,1),(-1,-2),(1,-2),(2,-1),(2,1),(1,2),(-1,2)]:nr,nc=r+dr,f+dc
if 0<=nr<8 and 0<=nc<8 and(not board[nr][nc]or board[nr][nc][0]!=turn):moves.append((r,f,nr,nc))
elif t in'bqr':dirs=OFF[t]
for dr,dc in dirs:nr,nc=r+dr,f+dc
while 0<=nr<8 and 0<=nc<8:if board[nr][nc]:if board[nr][nc][0]!=turn:moves.append((r,f,nr,nc))
break
moves.append((r,f,nr,nc));nr+=dr;nc+=dc
elif t=='k':for dr,dc in[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:nr,nc=r+dr,f+dc
if 0<=nr<8 and 0<=nc<8 and(not board[nr][nc]or board[nr][nc][0]!=turn):moves.append((r,f,nr,nc))
cr=0 if turn=='w' else 7
if castle=('KQkq'[0:4]if turn=='w'else'kq')[0]!='-':pass
return moves
def make_move(board,r1,f1,r2,f2,promo='q'):nb=[row[:]for row in board]
pc=nb[r1][f1]
nb[r1][f1]=None
if pc[1]=='p'and(r2==0orr2==7):pc=(pc[0],promo)
nb[r2][f2]=pc
return nb
def evaluate(board,turn):sc=0
for r in range(8):for f in range(8):pc=board[r][f]
if not pc:continue
v=VAL[pc[1]];pst=PST[f][r] if pc[0]=='w' else PST[7-f][7-r]
total=v+pst
sc+=total if pc[0]=='w' else-total
return sc if turn=='w' else-sc
def negamax(board,depth,alpha,beta,turn,castle,ep,node_budget):if node_budget[0]<=0:return evaluate(board,turn)
node_budget[0]-=1
if depth==0:return evaluate(board,turn)
best=-9999
moves=gen_moves(board,turn,castle,ep)
for m in sorted(moves,key=lambda x:-(VAL.get(board[x[0]][x[1]][1]if board[x[0]][x[1]]else 0))):r1,f1,r2,f2=m
nb=make_move(board,r1,f1,r2,f2)
nt='b'if turn=='w'else'w'
val=-negamax(nb,depth-1,-beta,-alpha,nt,castle,ep,node_budget)
if val>best:best=val
if best>alpha:alpha=best
if alpha>=beta:break
return best
def uci(r1,f1,r2,f2):return FILES[f1]+str(r1+1)+FILES[f2]+str(r2+1)
NODE_LIMIT=50000
def choose_move(fen):board,turn,castle,ep,half,full=parse_fen(fen)
budget=[NODE_LIMIT]
best_score=-9999;best_move=None
moves=gen_moves(board,turn,castle,ep)
for m in sorted(moves,key=lambda x:-(VAL.get(board[x[0]][x[1]][1]if board[x[0]][x[1]]else 0))):r1,f1,r2,f2=m
nb=make_move(board,r1,f1,r2,f2)
nt='b'if turn=='w'else'w'
val=-negamax(nb,3,-9999,9999,nt,castle,ep,[budget[0]])
if val>best_score:best_score=val;best_move=m
budget[0]-=1
if budget[0]<=0:break
if best_move:return uci(*best_move)
return uci(*moves[0])if moves else'resign'
for gi in range(1,9):game=q("/game",{})
fen=game["fen"]
moves=[];plies=0;result="ongoing"
while result=="ongoing"and plies<150:mv=choose_move(fen)
res=q("/move",{"game":gi,"move":mv})
moves.append(mv);plies+=1
fen=res.get("fen","");result=res.get("outcome","ongoing")
print(f"GAME {gi}->{result} plies {plies}")