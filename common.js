const api=async(action,params={})=>{let r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...params})});let j=await r.json();if(!r.ok)throw Error(j.error||'Erro');return j};
const qs=new URLSearchParams(location.search);let room=qs.get('room')||localStorage.getItem('banco_room')||'';
const money=n=>'R$ '+n.toLocaleString('pt-BR');const $=s=>document.querySelector(s);
function go(page,code){localStorage.setItem('banco_room',code);location.href=page+'?room='+encodeURIComponent(code)}
const showErr=e=>alert(e.message||e);
