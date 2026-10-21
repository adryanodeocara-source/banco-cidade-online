from flask import Flask,request,jsonify,send_from_directory
import random,string,threading,time,os
app=Flask(__name__,static_folder='.',static_url_path='')
rooms={}; lock=threading.RLock()
NAMES=['INÍCIO','Rua das Flores','Sorte ou Revés','Rua do Sol','Imposto','Estação Central','Av. Brasil','Sorte ou Revés','Rua das Palmeiras','Av. da Liberdade','PRISÃO','Rua do Comércio','Companhia Elétrica','Av. Boa Viagem','Rua do Mercado','Estação Norte','Av. Beira-Mar','Sorte ou Revés','Rua das Acácias','Av. Afonso Pena','ESTACIONAMENTO','Rua da Bahia','Sorte ou Revés','Av. Sete de Setembro','Rua do Porto','Estação Sul','Av. Atlântica','Av. Independência','Companhia de Água','Rua 25 de Março','VÁ PARA PRISÃO','Av. Paulista','Rua dos Jardins','Sorte ou Revés','Av. Copacabana','Estação Oeste','Sorte ou Revés','Av. Vieira Souto','Imposto de Luxo','Av. das Nações']
SPECIAL={0:'start',2:'card',4:'tax',5:'station',7:'card',10:'jail',12:'utility',17:'card',20:'parking',22:'card',25:'station',28:'utility',30:'gotojail',33:'card',35:'station',36:'card',38:'tax'}
PRICES={i: (200 if i in (5,15,25,35) else 150 if i in (12,28) else 60+(i//5)*35) for i in range(40) if i not in SPECIAL or SPECIAL[i] in ('station','utility')}
COLORS=['#ef4444','#3b82f6','#22c55e','#eab308','#a855f7','#f97316']
GROUPS=['#8b5cf6','#38bdf8','#ec4899','#f97316','#ef4444','#eab308','#22c55e','#1d4ed8']
def board():
 out=[]
 for i,n in enumerate(NAMES):
  kind=SPECIAL.get(i,'property'); out.append(dict(id=i,name=n,kind=kind,price=PRICES.get(i,0),group=GROUPS[min(7,max(0,(i-1)//5))] if kind=='property' else None))
 return out
BOARD=board()
def err(s,code=400):return jsonify(error=s),code
def room_for(data):
 code=str(data.get('room','')).strip().upper();return rooms.get(code)
def auth(s,d):
 token=d.get('token');return next((i for i,p in enumerate(s['players']) if p['token']==token),None)
def event(s,msg):s['log']=(s['log']+[msg])[-20:]
def next_turn(s):
 s['turn']=(s['turn']+1)%len(s['players']);s['phase']='roll';s['doubles']=0
 while s['players'][s['turn']]['bankrupt']:s['turn']=(s['turn']+1)%len(s['players'])
def card(s,p):
 options=[('Receba uma herança de R$ 100',100),('Pague uma multa de R$ 50',-50),('Receba dividendos de R$ 50',50),('Pague despesas de R$ 100',-100),('Vá diretamente para a prisão','jail'),('Avance até o INÍCIO e receba R$ 200','start'),('Você ganhou um cartão de saída livre da prisão','free')]
 label,value=random.choice(options)
 if isinstance(value,int):p['money']+=value
 elif value=='jail':p['pos']=10;p['jail']=True;p['jail_tries']=0
 elif value=='start':p['pos']=0;p['money']+=200
 else:p['free']+=1
 s['card']=label;event(s,p['name']+': '+label)
def resolve(s,p):
 pos=p['pos'];tile=BOARD[pos];kind=tile['kind'];s['offer']=None;s['card']=None
 if kind=='gotojail':p['pos']=10;p['jail']=True;p['jail_tries']=0;s['phase']='end';event(s,p['name']+' foi para a prisão');return
 if kind=='card':card(s,p);s['phase']='end';return
 if kind=='tax':amount=100 if pos==4 else 75;p['money']-=amount;event(s,p['name']+f' pagou R$ {amount} de imposto')
 if pos in s['owners']:
  asset=s['owners'][pos];owner=s['players'][asset['owner']]
  if asset['owner']!=s['turn'] and not asset['mortgaged'] and not owner['bankrupt']:
   rent=max(10,tile['price']//10)*(1+asset['houses']*2) if kind=='property' else (25 if kind=='station' else 30)
   p['money']-=rent;owner['money']+=rent;event(s,p['name']+f' pagou R$ {rent} a '+owner['name'])
 elif pos in PRICES:s['offer']=pos
 s['phase']='decide' if s['offer'] is not None else 'end'
def view(s,token=None):
 ps=[{k:v for k,v in p.items() if k!='token'} for p in s['players']]
 me=next((i for i,p in enumerate(s['players']) if p['token']==token),None)
 return dict(room=s['room'],players=ps,board=BOARD,owners=s['owners'],started=s['started'],turn=s['turn'],phase=s['phase'],dice=s['dice'],offer=s['offer'],card=s['card'],log=s['log'],me=me,admin=(token==s['admin']),winner=s['winner'],doubles=s['doubles'])
@app.route('/')
def home():return send_from_directory('.','index.html')
@app.route('/<path:path>')
def static_files(path):return send_from_directory('.',path)
@app.route('/api',methods=['POST'])
def api():
 d=request.get_json(silent=True) or {};act=d.get('action')
 with lock:
  if act=='create':
   code=''.join(random.choices(string.ascii_uppercase+string.digits,k=5))
   while code in rooms:code=''.join(random.choices(string.ascii_uppercase+string.digits,k=5))
   token=''.join(random.choices(string.ascii_letters+string.digits,k=30))
   rooms[code]=dict(room=code,admin=token,players=[],owners={},started=False,turn=0,phase='lobby',dice=[],offer=None,card=None,log=[],winner=None,doubles=0)
   return jsonify(room=code,token=token)
  s=room_for(d)
  if not s:return err('Sala não encontrada')
  if act=='state':return jsonify(view(s,d.get('token')))
  if act=='join':
   if s['started']:return err('A partida já começou')
   if len(s['players'])>=6:return err('Sala cheia')
   name=str(d.get('name','')).strip()[:20]
   if not name:return err('Informe seu nome')
   color=d.get('color')
   if color not in COLORS or any(p['color']==color for p in s['players']):return err('Escolha uma cor disponível')
   token=''.join(random.choices(string.ascii_letters+string.digits,k=30))
   s['players'].append(dict(name=name,color=color,token=token,pos=0,money=1500,jail=False,jail_tries=0,free=0,bankrupt=False))
   event(s,name+' entrou na sala');return jsonify(token=token)
  if act in ('start','restart'):
   if d.get('token')!=s['admin']:return err('Somente o administrador pode iniciar')
   if len(s['players'])<2:return err('São necessários pelo menos 2 jogadores')
   s.update(started=True,owners={},turn=0,phase='roll',dice=[],offer=None,card=None,winner=None,doubles=0,log=[])
   for p in s['players']:p.update(pos=0,money=1500,jail=False,jail_tries=0,free=0,bankrupt=False)
   event(s,'Partida iniciada!');return jsonify(ok=True)
  i=auth(s,d)
  if i is None:return err('Acesso de jogador inválido')
  p=s['players'][i]
  if not s['started'] or s['winner'] is not None:return err('Partida não está ativa')
  if act in ('build','mortgage','unmortgage'):
   pos=int(d.get('pos',-1));asset=s['owners'].get(pos)
   if not asset or asset['owner']!=i:return err('Terreno não pertence a você')
   if act=='build':
    if BOARD[pos]['kind']!='property' or asset['mortgaged'] or asset['houses']>=5:return err('Não é possível construir aqui')
    cost=max(50,BOARD[pos]['price']//2)
    if p['money']<cost:return err('Dinheiro insuficiente')
    p['money']-=cost;asset['houses']+=1;event(s,p['name']+f' construiu em {BOARD[pos]["name"]}')
   if act=='mortgage':
    if asset['mortgaged'] or asset['houses']:return err('Venda as construções antes de hipotecar')
    asset['mortgaged']=True;p['money']+=BOARD[pos]['price']//2
   if act=='unmortgage':
    cost=int(BOARD[pos]['price']*.55)
    if not asset['mortgaged'] or p['money']<cost:return err('Não é possível quitar a hipoteca')
    p['money']-=cost;asset['mortgaged']=False
   return jsonify(ok=True)
  if i!=s['turn']:return err('Não é sua vez')
  if act=='roll':
   if s['phase']!='roll':return err('Aguarde sua vez de jogar os dados')
   a,b=random.randint(1,6),random.randint(1,6);s['dice']=[a,b];double=a==b
   if p['jail']:
    if double:p['jail']=False;p['jail_tries']=0;event(s,p['name']+' saiu da prisão com dados iguais')
    else:
     p['jail_tries']+=1
     if p['jail_tries']<3:s['phase']='end';event(s,p['name']+' permanece na prisão');return jsonify(ok=True)
     p['money']-=50;p['jail']=False;p['jail_tries']=0;event(s,p['name']+' pagou R$ 50 e saiu da prisão')
    double=False
   else:
    s['doubles']=s['doubles']+1 if double else 0
    if s['doubles']>=3:p['pos']=10;p['jail']=True;p['jail_tries']=0;s['phase']='end';s['doubles']=0;event(s,p['name']+' tirou 3 duplas e foi preso');return jsonify(ok=True)
   old=p['pos'];p['pos']=(old+a+b)%40
   if old+a+b>=40:p['money']+=200;event(s,p['name']+' recebeu R$ 200 ao passar pelo INÍCIO')
   s['extra']=double;resolve(s,p);return jsonify(ok=True)
  if act=='buy':
   if s['phase']!='decide' or s['offer'] is None:return err('Não há propriedade disponível')
   pos=s['offer'];price=BOARD[pos]['price']
   if p['money']<price:return err('Dinheiro insuficiente')
   p['money']-=price;s['owners'][pos]=dict(owner=i,houses=0,mortgaged=False);event(s,p['name']+' comprou '+BOARD[pos]['name']);s['offer']=None;s['phase']='end';return jsonify(ok=True)
  if act=='pass':
   if s['phase']!='decide':return err('Não há compra pendente')
   s['offer']=None;s['phase']='end';return jsonify(ok=True)
  if act=='payjail':
   if not p['jail'] or s['phase']!='roll':return err('Você não está preso')
   if p['money']<50:return err('Dinheiro insuficiente')
   p['money']-=50;p['jail']=False;p['jail_tries']=0;event(s,p['name']+' pagou para sair da prisão');return jsonify(ok=True)
  if act=='usefree':
   if not p['jail'] or not p['free'] or s['phase']!='roll':return err('Cartão indisponível')
   p['free']-=1;p['jail']=False;p['jail_tries']=0;return jsonify(ok=True)
  if act=='end':
   if s['phase']!='end':return err('Conclua a ação atual')
   if p['money']<0:return err('Saldo negativo: negociações e falência serão adicionadas na próxima etapa')
   if s.get('extra') and not p['jail']:s['phase']='roll';s['extra']=False
   else:s['extra']=False;next_turn(s)
   return jsonify(ok=True)
  return err('Ação desconhecida')
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
