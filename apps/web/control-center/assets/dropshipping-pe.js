"use strict";
const $ = id => document.getElementById(id);
const prefix = "/api/v1/ecommerce-readiness/dropshipping-pe";
let token = "", events = [];
const actionNames = {confirm:"Confirmar",cancel:"Cancelar",dispatch:"Despachar (sim.)",deliver:"Entregar (sim.)",reject:"Rechazar",request_return:"Solicitar devolución",resolve_return:"Resolver devolución"};
const available = {received:["confirm","cancel"],confirmed:["dispatch","cancel"],dispatched:["deliver","reject"],delivered:["request_return"],return_requested:["resolve_return"]};
const names = {received:"Recibido",confirmed:"Confirmado",cancelled:"Cancelado",dispatched:"Despachado",delivered:"Entregado",rejected:"Rechazado",return_requested:"Devolución solicitada",return_resolved:"Devolución resuelta"};
async function api(path, data, authenticated = true) {
  const headers = {"Content-Type":"application/json"};
  if (authenticated) headers.Authorization = "Bearer " + token;
  const response = await fetch(path, {method:data === undefined ? "GET":"POST",headers,body:data === undefined ? undefined : JSON.stringify(data),cache:"no-store"});
  if (response.status === 401 && authenticated) {clearSession(); throw Error("Sesión no válida. Vuelve a entrar.");}
  if (!response.ok) throw Error("La operación no se completó (HTTP " + response.status + ").");
  return response.json();
}
function list(id, values) { $(id).replaceChildren(...values.map(v => {const li=document.createElement("li");li.textContent=v;return li;})); }
function clearSession(){token="";events=[];$("workspace").hidden=true;$("session").hidden=false;$("financial-result").textContent="";$("order-result").textContent="";$("history").replaceChildren();$("message").textContent="Sesión cerrada.";}
$("login").addEventListener("submit",async e=>{
  e.preventDefault();const form=e.currentTarget;const data=Object.fromEntries(new FormData(form));
  $("message").textContent="Comprobando acceso…";
  try {const result=await api("/api/v1/auth/login",data,false);token=result.token;if(!token)throw Error("No se recibió sesión.");
    const status=await api(prefix+"/status");
    if(status.mode!=="simulation"||status.live_enabled!==false)throw Error("Modo no seguro.");
    list("providers",status.providers.map(p=>p.name+" — "+(p.connection==="not_connected"?"sin conexión":"revisar")));
    list("blockers",status.launch_blockers);
    $("session").hidden=true;$("workspace").hidden=false;await runOrder([]);
  }catch(err){clearSession();$("message").textContent=err.message;}finally{form.reset();}
});
$("logout").addEventListener("click",async()=>{try{await api("/api/v1/auth/logout",{});}catch{}finally{clearSession();}});
$("finance").addEventListener("submit",async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));try{const result=await api(prefix+"/financial-scenario",data);$("financial-result").textContent="S/ "+result.contribution_per_delivery+" por entrega · "+(result.meets_provisional_target?"Alcanza":"No alcanza")+" el objetivo provisional de S/ 15.";}catch(err){$("financial-result").textContent=err.message;}});
async function runOrder(next){
  try{const result=await api(prefix+"/order-simulation",{events:next});events=next;
    list("history",result.history.map(s=>names[s]||s));$("order-result").textContent="Estado simulado: "+(names[result.state]||result.state);
    $("actions").replaceChildren(...(available[result.state]||[]).map(action=>{const btn=document.createElement("button");btn.type="button";btn.textContent=actionNames[action];btn.addEventListener("click",()=>{btn.disabled=true;runOrder([...events,action]).finally(()=>{btn.disabled=false;});});return btn;}));
  }catch(err){$("order-result").textContent=err.message;}
}
$("reset-order").addEventListener("click",()=>runOrder([]));
