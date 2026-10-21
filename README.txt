BANCO CIDADE ONLINE — PRIMEIRA VERSÃO JOGÁVEL

Páginas:
/             criar sala
/admin.html   administrador
/tv.html      TV
/celular.html jogador

Deploy Render:
1. Envie todos os arquivos da pasta para um repositório GitHub novo.
2. Render > New > Web Service > conectar repositório.
3. Runtime Python, Build Command: pip install -r requirements.txt
4. Start Command: gunicorn server:app --workers 1 --threads 4 --bind 0.0.0.0:$PORT

IMPORTANTE: É um protótipo inicial, não a versão final completa. Já permite criar sala, entrar com 2-6 jogadores, jogar dados, movimentar peões, comprar ou recusar propriedades, cobrar aluguel, construir, hipotecar, cartas, prisão e turnos. A negociação entre jogadores, venda de construções, falência, vitória e animação suave dos peões ainda NÃO estão implementadas. A TV atualiza automaticamente, mas a movimentação ainda não é animada casa a casa. Salas ficam na memória do servidor e desaparecem quando ele reinicia. Não publique atualizações durante partidas. Não use dinheiro real.
