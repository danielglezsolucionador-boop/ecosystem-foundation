"use strict";
const $ = id => document.getElementById(id);
const prefix = "/api/v1/ecommerce-readiness/dropshipping-pe";
let token = "", events = [], orderBusy = false, sessionEpoch = 0, candidates = [], currentRole = "";
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
function clearSession(){sessionEpoch++;currentRole="";$("evidence-rows").replaceChildren();$("evidence-candidate").replaceChildren();$("playbook-list").replaceChildren();$("evidence-message").textContent="";$("playbook-message").textContent="";token="";events=[];orderBusy=false;candidates=[];$("catalog-rows").replaceChildren();$("candidate").replaceChildren();$("comparison-result").textContent="";$("pipeline-result").textContent="";$("catalog-summary").textContent="";$("workspace").hidden=true;$("session").hidden=false;$("financial-result").textContent="";$("order-result").textContent="";$("history").replaceChildren();$("message").textContent="Sesión cerrada.";}
$("login").addEventListener("submit",async e=>{
  e.preventDefault();const form=e.currentTarget;const data=Object.fromEntries(new FormData(form));
  $("message").textContent="Comprobando acceso…";
  try {const result=await api("/api/v1/auth/login",data,false);token=result.token;currentRole=result.user?.role||"";if(!token)throw Error("No se recibió sesión.");
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
  $("evidence-candidate").replaceChildren(...candidates.map(item=>{
    const option=document.createElement("option");option.value=item.id;
    option.textContent=item.id+" · "+item.name;return option;
  }));
  $("evidence-form").querySelector("button").disabled=!["CEO","ADMIN","OPERATOR"].includes(currentRole);
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

const pipelineStates={delivered:["confirmed","dispatched","delivered"],rejected:["confirmed","dispatched","rejected"],returned:["confirmed","dispatched","delivered","returned"],cancelled:["cancelled"],confirmed:["confirmed"]};
const pipelineMoney=c=>c===null?"Pendiente":"S/ "+(c/100).toFixed(2);
$("pipeline").addEventListener("submit",async e=>{
  e.preventDefault();if(!token)return;
  const form=e.currentTarget,button=form.querySelector("button"),epoch=sessionEpoch;
  if(button.disabled)return;
  button.disabled=true;$("pipeline-result").textContent="Ejecutando escenario…";
  try{
    const values=new FormData(form),provider=values.get("provider");
    const contract=await api(prefix+"/pipeline-contract");
    if(epoch!==sessionEpoch)return;
    const adapter=contract.providers.find(p=>p.name===provider);
    if(contract.live_enabled!==false||!adapter||adapter.real_contract_verified!==false)throw Error("Contrato de simulación inválido.");
    const events=pipelineStates[values.get("outcome")].map((state,i)=>({event_id:"DEMO-"+(i+1),code:adapter.codes[state]}));
    if(values.has("duplicate"))events.splice(1,0,{...events[0]});
    const payload={provider,cart:{lines:[{product_id:values.get("product"),pack:1,quantity:1}],region:values.get("region")},events};
    for(const key of ["product_cost_cents","logistics_cost_cents","advertising_cost_cents","provider_fee_cents","observed_remittance_cents"]){
      const amount=Number(values.get(key));if(!Number.isFinite(amount)||amount<0)throw Error("Importe no válido.");
      payload[key]=Math.round(amount*100);
    }
    const result=await api(prefix+"/pipeline-simulation",payload);
    if(epoch!==sessionEpoch)return;
    if(result.live_enabled!==false||result.real_order_created!==false||result.payment_processed!==false||result.supplier_contacted!==false)throw Error("Resultado no seguro.");
    $("pipeline-result").textContent=[
      "Estado: "+(names[result.state]||result.state),
      "Eventos duplicados ignorados: "+result.duplicates_ignored,
      "Cobro bruto COD: "+pipelineMoney(result.gross_cod_cents),
      "Liquidación esperada: "+pipelineMoney(result.expected_remittance_cents),
      "Liquidación recibida: "+pipelineMoney(result.observed_remittance_cents),
      "Diferencia: "+pipelineMoney(result.remittance_difference_cents),
      "Conciliación: "+({matched:"Coincide",review:"Revisar diferencia",pending:"Pendiente"}[result.reconciliation]),
      "Contribución bruta de caja (antes de ajuste tributario): "+pipelineMoney(result.gross_cash_contribution_cents),
      "Simulación solamente; sin efecto real."
    ].join("\n");
  }catch(err){if(epoch===sessionEpoch)$("pipeline-result").textContent=err.message;}
  finally{button.disabled=false;}
});

$("load-playbooks").addEventListener("click",async()=>{
  const epoch=sessionEpoch;
  try{
    const result=await api(prefix+"/playbooks");
    if(epoch!==sessionEpoch)return;
    if(result.live_enabled!==false)throw Error("Modo no seguro.");
    list("playbook-list",result.items.map(p=>p.agent+" · "+p.reviewer+" · "+p.draft));
    $("playbook-message").textContent="Protocolos de ensayo; sin mensajes enviados.";
  }catch(err){if(epoch===sessionEpoch)$("playbook-message").textContent=err.message;}
});
async function loadEvidence(){
  const epoch=sessionEpoch;
  try{
    const result=await api(prefix+"/evidence");
    if(epoch!==sessionEpoch)return;
    if(result.live_enabled!==false||result.approved_for_sale!==false)throw Error("Modo no seguro.");
    $("evidence-rows").replaceChildren(...result.items.map(item=>{
      const row=document.createElement("tr");
      for(const value of [item.candidate,item.provider,item.kind,item.reference]){
        const cell=document.createElement("td");cell.textContent=value;row.append(cell);
      }
      const cell=document.createElement("td");
      if(item.decision)cell.textContent=item.decision==="accepted_demo"?"Aceptado (ensayo)":"Rechazado (ensayo)";
      else if(currentRole==="CEO"){
        for(const [label,decision] of [["Aceptar ensayo","accepted_demo"],["Rechazar ensayo","rejected_demo"]]){
          const btn=document.createElement("button");btn.type="button";btn.textContent=label;
          btn.addEventListener("click",async()=>{
            const reviewEpoch=sessionEpoch;
            cell.querySelectorAll("button").forEach(b=>b.disabled=true);
            try{await api(prefix+"/evidence/"+encodeURIComponent(item.id)+"/review",{decision});if(reviewEpoch===sessionEpoch)await loadEvidence();}
            catch(err){if(reviewEpoch===sessionEpoch)$("evidence-message").textContent=err.message;}
            finally{if(reviewEpoch===sessionEpoch)cell.querySelectorAll("button").forEach(b=>b.disabled=false);}
          });cell.append(btn);
        }
      }else cell.textContent="Pendiente de CEO";
      row.append(cell);return row;
    }));
    $("evidence-message").textContent=result.items.length+" registros recientes. Ninguna autorización real.";
  }catch(err){if(epoch===sessionEpoch)$("evidence-message").textContent=err.message;}
}
$("refresh-evidence").addEventListener("click",loadEvidence);
$("evidence-form").addEventListener("submit",async e=>{
  e.preventDefault();if(!token)return;
  const form=e.currentTarget,btn=form.querySelector("button"),epoch=sessionEpoch;
  if(btn.disabled)return;btn.disabled=true;
  try{
    await api(prefix+"/evidence",Object.fromEntries(new FormData(form)));
    if(epoch!==sessionEpoch)return;
    form.elements.reference.value="";await loadEvidence();
  }catch(err){if(epoch===sessionEpoch)$("evidence-message").textContent=err.message;}
  finally{if(epoch===sessionEpoch)btn.disabled=false;}
});
