"use strict";
const $ = id => document.getElementById(id);
const prefix = "/api/v1/ecommerce-readiness/dropshipping-pe";
let token = "", events = [], orderBusy = false, sessionEpoch = 0, candidates = [];
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
function clearSession(){sessionEpoch++;token="";events=[];orderBusy=false;candidates=[];$("catalog-rows").replaceChildren();$("candidate").replaceChildren();$("comparison-result").textContent="";$("catalog-summary").textContent="";$("workspace").hidden=true;$("session").hidden=false;$("financial-result").textContent="";$("order-result").textContent="";$("history").replaceChildren();$("message").textContent="Sesión cerrada.";}
$("login").addEventListener("submit",async e=>{
  e.preventDefault();const form=e.currentTarget;const data=Object.fromEntries(new FormData(form));
  $("message").textContent="Comprobando acceso…";
  try {const result=await api("/api/v1/auth/login",data,false);token=result.token;if(!token)throw Error("No se recibió sesión.");
    const status=await api(prefix+"/status");
    if(status.mode!=="simulation"||status.live_enabled!==false)throw Error("Modo no seguro.");
    list("providers",status.providers.map(p=>p.name+" — "+(p.connection==="not_connected"?"sin conexión":"revisar")));
    list("blockers",status.launch_blockers);
    await loadCatalog();$("session").hidden=true;$("workspace").hidden=false;await runOrder([]);
  }catch(err){clearSession();$("message").textContent=err.message;}finally{form.reset();}
});
$("logout").addEventListener("click",async()=>{try{await api("/api/v1/auth/logout",{});}catch{}finally{clearSession();}});
$("finance").addEventListener("submit",async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));try{const result=await api(prefix+"/financial-scenario",data);$("financial-result").textContent="S/ "+result.contribution_per_delivery+" por entrega · "+(result.meets_provisional_target?"Alcanza":"No alcanza")+" el objetivo provisional de S/ 15.";}catch(err){$("financial-result").textContent=err.message;}});
async function runOrder(next){
  if(orderBusy||!token)return;
  const epoch=sessionEpoch;orderBusy=true;
  $("actions").querySelectorAll("button").forEach(btn=>btn.disabled=true);$("reset-order").disabled=true;
  try{const result=await api(prefix+"/order-simulation",{events:next});if(epoch!==sessionEpoch)return;events=next;
    list("history",result.history.map(s=>names[s]||s));$("order-result").textContent="Estado simulado: "+(names[result.state]||result.state);
    $("actions").replaceChildren(...(available[result.state]||[]).map(action=>{const btn=document.createElement("button");btn.type="button";btn.textContent=actionNames[action];btn.addEventListener("click",()=>runOrder([...events,action]));return btn;}));
  }catch(err){if(epoch===sessionEpoch)$("order-result").textContent=err.message;}finally{if(epoch===sessionEpoch){orderBusy=false;$("actions").querySelectorAll("button").forEach(btn=>btn.disabled=false);$("reset-order").disabled=false;}}
}
$("reset-order").addEventListener("click",()=>runOrder([]));

const stageNames = {quote_candidate:"Finalista para cotizar",research:"Investigar",hold:"En reserva"};
const quoteProviders = ["Aliclik","Dropi","Easydrop"];
const quoteInputs = [
 ["supplier_cost","Coste producto (S/)","20",".01","0",null],
 ["delivered_shipping","Envío entregado (S/)","15",".01","0",null],
 ["failed_shipping","Coste envío fallido (S/)","10",".01","0",null],
 ["delivery_rate","Tasa de entrega (0–1)",".8",".0001",".0001","1"]
];
function renderCatalog(){
  const query=$("catalog-search").value.trim().toLocaleLowerCase("es");
  const stage=$("catalog-filter").value;
  const filtered=candidates.filter(item=>(!stage||item.stage===stage)&&
      (item.name+" "+item.id).toLocaleLowerCase("es").includes(query));
  $("catalog-rows").replaceChildren(...filtered.map(item=>{
    const row=document.createElement("tr");
    for(const value of [item.id,item.name,stageNames[item.stage]||item.stage]){
      const cell=document.createElement("td");cell.textContent=value;row.append(cell);
    }
    return row;
  }));
  $("catalog-summary").textContent=filtered.length+" de "+candidates.length+" candidatos; 0 aprobados para venta.";
}
async function loadCatalog(){
  const data=await api(prefix+"/catalog");
  if(data.live_enabled!==false)throw Error("Catálogo en modo no seguro.");
  candidates=data.items;
  $("candidate").replaceChildren(...candidates.map(item=>{
    const option=document.createElement("option");option.value=item.id;
    option.textContent=item.id+" · "+item.name;return option;
  }));
  const first=candidates.find(item=>item.stage==="quote_candidate");
  if(first)$("candidate").value=first.id;
  renderCatalog();
}
$("catalog-search").addEventListener("input",renderCatalog);
$("catalog-filter").addEventListener("change",renderCatalog);
for(const provider of quoteProviders){
  const box=document.createElement("fieldset");
  const legend=document.createElement("legend");legend.textContent=provider+" (hipótesis)";box.append(legend);
  for(const [key,label,value,step,min,max] of quoteInputs){
    const wrapper=document.createElement("label");wrapper.textContent=label;
    const input=document.createElement("input");input.name=provider+"_"+key;input.type="number";
    input.value=value;input.step=step;input.min=min;if(max!==null)input.max=max;input.required=true;
    wrapper.append(input);box.append(wrapper);
  }
  $("quote-fields").append(box);
}
$("comparison").addEventListener("submit",async e=>{
  e.preventDefault();if(!token)return;
  if(!$("finance").reportValidity())return;
  const form=e.currentTarget, button=form.querySelector("button"), epoch=sessionEpoch;
  if(button.disabled)return;
  button.disabled=true;$("comparison-result").textContent="Calculando hipótesis…";
  const common=Object.fromEntries(new FormData($("finance"))), values=new FormData(form);
  const quotes=quoteProviders.map(provider=>({provider,economics:{...common,
    ...Object.fromEntries(quoteInputs.map(([key])=>[key,values.get(provider+"_"+key)]))}}));
  try{
    const result=await api(prefix+"/provider-comparison",{candidate_id:$("candidate").value,quotes});
    if(epoch!==sessionEpoch)return;
    $("comparison-result").textContent=result.ranked_hypothetical_quotes.map(row=>
      row.provider+": S/ "+row.contribution_per_delivery_pen+" por entrega"+
      (row.meets_provisional_target?" · alcanza objetivo":" · no alcanza objetivo")).join("\n")+
      "\nSin proveedor recomendado ni venta autorizada: falta evidencia real.";
  }catch(err){if(epoch===sessionEpoch)$("comparison-result").textContent=err.message;}
  finally{button.disabled=false;}
});
