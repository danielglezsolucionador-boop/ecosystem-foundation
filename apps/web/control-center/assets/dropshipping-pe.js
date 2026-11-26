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
function clearSession(){sessionEpoch++;resetIntegration();resetDurable();resetTasks();for(const id of ["growth-plan-result","growth-review-result","growth-campaign-result"])$(id).textContent="";$("growth-review").reset();currentRole="";$("evidence-rows").replaceChildren();$("evidence-candidate").replaceChildren();$("playbook-list").replaceChildren();$("evidence-message").textContent="";$("playbook-message").textContent="";token="";events=[];orderBusy=false;candidates=[];$("catalog-rows").replaceChildren();$("candidate").replaceChildren();$("comparison-result").textContent="";$("pipeline-result").textContent="";$("catalog-summary").textContent="";$("workspace").hidden=true;$("session").hidden=false;$("financial-result").textContent="";$("order-result").textContent="";$("history").replaceChildren();$("message").textContent="Sesión cerrada.";}
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

const growthPath=prefix+"/growth";
const growthChecks={sample_verified:"Muestra verificada",claims_verified:"Afirmaciones verificadas",price_verified:"Precio verificado",media_rights_verified:"Derechos de uso verificados",policy_reviewed:"Políticas revisadas",clear_hook:"Gancho claro",clear_cta:"Llamada a la acción clara",mobile_readable:"Legibilidad móvil"};
for(const [key,label] of Object.entries(growthChecks)){const wrapper=document.createElement("label"),span=document.createElement("span"),input=document.createElement("input");input.type="checkbox";input.name=key;input.style.width="auto";span.append(input,document.createTextNode(" "+label));wrapper.append(span);$("growth-checks").append(wrapper);}
function growthForm(id,output,run){
  $(id).addEventListener("submit",async e=>{
    e.preventDefault();if(!token)return;
    const form=e.currentTarget,button=form.querySelector("button"),epoch=sessionEpoch;
    if(button.disabled)return;button.disabled=true;$(output).textContent="Procesando ensayo…";
    try{const text=await run(new FormData(form));if(epoch===sessionEpoch)$(output).textContent=text;}
    catch(err){if(epoch===sessionEpoch)$(output).textContent=err.message;}
    finally{button.disabled=false;}
  });
}
growthForm("growth-plan","growth-plan-result",async data=>{
  const result=await api(growthPath+"/creative-plan?"+new URLSearchParams(data));
  if(result.live_enabled!==false||result.published!==false)throw Error("Modo no seguro.");
  return result.scripts.map(s=>s.angle+" · "+s.duration_seconds+" s · "+s.format+"\n"+s.shots.map(x=>x.seconds+" s: "+x.text).join("\n")).join("\n\n")+"\n\nPendiente de MARKETING / PLUMA / LENTE; sin publicación.";
});
growthForm("growth-review","growth-review-result",async data=>{
  const result=await api(growthPath+"/creative-review",Object.fromEntries(Object.keys(growthChecks).map(key=>[key,data.has(key)])));
  if(result.approved_for_publication!==false)throw Error("Modo no seguro.");
  return "Puntuación: "+result.score+"/"+result.max_score+"\nBloqueos: "+(result.blockers.map(key=>growthChecks[key]).join(", ")||"ninguno declarado")+
    "\n"+(result.review_ready?"Preparado para revisión humana.":"Completar verificación.")+" Sin aprobación de publicación.";
});
const growthDecisions={pause_budget_cap:"Pausar: límite de presupuesto",wait_for_settlement:"Esperar cierre de pedidos",insufficient_sample:"Muestra insuficiente",pause_loss:"Pausar: pérdida",revise_campaign:"Revisar campaña",review_scaling_with_ceo:"Evaluar escalamiento con CEO"};
growthForm("growth-campaign","growth-campaign-result",async data=>{
  const payload={};
  for(const [key,value] of data){const n=Number(value);if(!Number.isFinite(n)||n<0)throw Error("Importe no válido.");payload[key]=key.endsWith("_cents")?Math.round(n*100):n;}
  const result=await api(growthPath+"/campaign-simulation",payload);
  if(result.live_enabled!==false||result.spend_executed!==false||result.campaign_changed!==false)throw Error("Modo no seguro.");
  const pen=v=>v===null?"No disponible":"S/ "+v;
  return [growthDecisions[result.decision],"CPA pedido: "+pen(result.cpa_order_pen),"CPA entrega cobrada: "+pen(result.cpa_delivered_pen),
    "ROAS ventas netas: "+(result.net_sales_roas??"No disponible"),"Contribución observada: "+pipelineMoney(result.contribution_cents),
    "Contribución por entrega cerrada: "+pen(result.contribution_per_delivery_pen),"Presupuesto restante: "+pipelineMoney(result.budget_remaining_cents),
    "Revisión CEO requerida; no se cambió ninguna campaña."].join("\n");
});

const durablePath=prefix+"/persistent-orders";
let durableBusy=false,durablePaused=true,durableAvailable=false;
function resetDurable(){
  durableBusy=false;durablePaused=true;durableAvailable=false;
  $("durable-form").reset();
  for(const id of ["durable-rows","durable-audit"])$(id).replaceChildren();
  for(const id of ["durable-message","durable-detail"])$(id).textContent="";
  $("durable-status").textContent="Sin consultar.";
  durableButtons();
}
function durableButtons(){
  $("durable-refresh").disabled=durableBusy;
  $("durable-form").querySelector("button").disabled=durableBusy||!durableAvailable||durablePaused||!["CEO","ADMIN","OPERATOR"].includes(currentRole);
  $("durable-pause").disabled=durableBusy||!durableAvailable||currentRole!=="CEO"||durablePaused;
  $("durable-resume").disabled=durableBusy||!durableAvailable||currentRole!=="CEO"||!durablePaused;
}
function assertDurable(data){
  if(data.mode!=="simulation"||data.live_enabled!==false||data.real_order_created!==false)throw Error("Modo no seguro.");
}
async function refreshDurable(epoch){
  const data=await api(durablePath);
  if(epoch!==sessionEpoch)return;
  assertDurable(data);
  durableAvailable=true;durablePaused=data.paused;
  $("durable-status").textContent=durablePaused?"Ensayo pausado":"Ensayo activo · ventas reales bloqueadas";
  $("durable-rows").replaceChildren(...data.items.map(item=>{
    const row=document.createElement("tr");
    for(const value of [item.reference,item.provider,names[item.state]||item.state]){
      const cell=document.createElement("td");cell.textContent=value;row.append(cell);
    }
    const cell=document.createElement("td"),btn=document.createElement("button");
    btn.type="button";btn.textContent="Ver "+item.reference;
    btn.addEventListener("click",()=>durableAction(async ep=>{
      const result=await api(durablePath+"/"+encodeURIComponent(item.id));
      if(ep!==sessionEpoch)return;assertDurable(result);
      $("durable-detail").textContent=result.reference+" · "+pipelineMoney(result.quote.total_cents)+" · "+(names[result.state]||result.state)+"\n"+result.events.map(e=>e.event_id+" · "+e.state+" · "+e.created_at).join("\n");
    }));
    cell.append(btn);row.append(cell);return row;
  }));
  list("durable-audit",data.audit.map(e=>e.action+" · "+(e.order_id||"control")+" · "+e.actor+" · "+e.created_at));
}
async function durableAction(run){
  if(!token||durableBusy)return;const epoch=sessionEpoch;durableBusy=true;durableButtons();
  $("durable-message").textContent="";
  try{await run(epoch);}
  catch(err){if(epoch===sessionEpoch){$("durable-message").textContent=err.message;}}
  finally{if(epoch===sessionEpoch){durableBusy=false;durableButtons();}}
}
$("durable-refresh").addEventListener("click",()=>durableAction(refreshDurable));
$("durable-form").addEventListener("submit",e=>{
  e.preventDefault();const values=new FormData(e.currentTarget);
  durableAction(async epoch=>{
    const result=await api(durablePath,{reference:values.get("reference"),provider:values.get("provider"),cart:{lines:[{product_id:values.get("product_id"),pack:Number(values.get("pack")),quantity:1}],region:values.get("region")}});
    if(epoch!==sessionEpoch)return;assertDurable(result);
    $("durable-message").textContent=result.duplicate?"Referencia recuperada sin duplicar.":"Pedido de ensayo registrado.";
    await refreshDurable(epoch);
  });
});
for(const [id,paused] of [["durable-pause",true],["durable-resume",false]]){
  $(id).addEventListener("click",()=>durableAction(async epoch=>{
    const result=await api(prefix+"/demo-pause",{paused});
    if(epoch!==sessionEpoch)return;assertDurable(result);await refreshDurable(epoch);
  }));
}

const tasksPath=prefix+"/tasks";
let taskBusy=false,taskAvailable=false,taskPaused=true;
const taskStates={queued:"En cola",retry_wait:"Reintento pendiente",escalated:"Escalado al CEO",awaiting_ceo:"Pendiente de revisión CEO",draft_ready:"Borrador preparado",reviewed_demo:"Revisado (ensayo)"};
const taskIntents={order_confirmation:"Confirmación",delivery_delay:"Retraso",return_request:"Devolución",settlement_difference:"Conciliación"};
function taskButtons(){
  const write=["CEO","ADMIN","OPERATOR"].includes(currentRole);
  $("tasks-refresh").disabled=taskBusy;
  $("tasks-tick").disabled=taskBusy||!taskAvailable||taskPaused||!write;
  $("tasks-form").querySelector("button").disabled=taskBusy||!taskAvailable||taskPaused||!write||!$("tasks-order").value;
}
function resetTasks(){
  taskBusy=false;taskAvailable=false;taskPaused=true;
  $("tasks-form").reset();
  for(const id of ["tasks-order","tasks-rows","tasks-audit"])$(id).replaceChildren();
  $("tasks-status").textContent="Sin consultar."; $("tasks-message").textContent="";
  taskButtons();
}
function assertTasks(data){
  if(data.mode!=="simulation"||data.live_enabled!==false||data.external_action_executed!==false)throw Error("Modo no seguro.");
}
async function refreshTasks(epoch){
  const [data,orders]=await Promise.all([api(tasksPath),api(durablePath)]);
  if(epoch!==sessionEpoch)return;assertTasks(data);assertDurable(orders);
  taskAvailable=true;taskPaused=data.paused;
  $("tasks-status").textContent=taskPaused?"Cola pausada":"Cola disponible · ciclo manual · acciones reales bloqueadas";
  const selection=$("tasks-order").value;
  $("tasks-order").replaceChildren(...orders.items.map(o=>{const option=document.createElement("option");option.value=o.id;option.textContent=o.reference+" · "+o.provider;return option;}));
  if(orders.items.some(o=>o.id===selection))$("tasks-order").value=selection;
  $("tasks-rows").replaceChildren(...data.items.map(item=>{
    const row=document.createElement("tr");
    const due=["queued","retry_wait"].includes(item.state)?new Date(item.due_at*1000).toLocaleString("es-PE"):"—";
    for(const value of [item.reference,taskIntents[item.intent]||item.intent,taskStates[item.state]||item.state,item.attempts,due]){
      const cell=document.createElement("td");cell.textContent=value;row.append(cell);
    }
    const cell=document.createElement("td");cell.textContent=item.result||"—";
    if(currentRole==="CEO"&&["escalated","awaiting_ceo"].includes(item.state)){
      const btn=document.createElement("button");btn.type="button";btn.textContent="Revisar "+item.reference;
      btn.addEventListener("click",()=>taskAction(async ep=>{
        const result=await api(tasksPath+"/"+encodeURIComponent(item.id)+"/acknowledge",{});
        if(ep!==sessionEpoch)return;assertTasks(result);await refreshTasks(ep);
      }));cell.append(document.createElement("br"),btn);
    }
    row.append(cell);return row;
  }));
  list("tasks-audit",data.audit.map(a=>a.action+" · "+a.task_id+" · "+a.actor+" · "+a.created_at));
}
async function taskAction(run){
  if(!token||taskBusy)return;const epoch=sessionEpoch;taskBusy=true;taskButtons();$("tasks-message").textContent="";
  try{await run(epoch);}catch(err){if(epoch===sessionEpoch)$("tasks-message").textContent=err.message;}
  finally{if(epoch===sessionEpoch){taskBusy=false;taskButtons();}}
}
$("tasks-refresh").addEventListener("click",()=>taskAction(refreshTasks));
$("tasks-order").addEventListener("change",taskButtons);
$("tasks-form").addEventListener("submit",e=>{
  e.preventDefault();const values=Object.fromEntries(new FormData(e.currentTarget));
  values.simulated_failures=Number(values.simulated_failures);
  taskAction(async ep=>{
    const result=await api(tasksPath,values);
    if(ep!==sessionEpoch)return;assertTasks(result);
    $("tasks-message").textContent=result.duplicate?"Tarea recuperada sin duplicar.":"Tarea registrada.";
    await refreshTasks(ep);
  });
});
$("tasks-tick").addEventListener("click",()=>taskAction(async ep=>{
  const result=await api(tasksPath+"/tick",{});
  if(ep!==sessionEpoch)return;assertTasks(result);
  $("tasks-message").textContent=result.task?(taskStates[result.task.state]||result.task.state):"No hay tareas vencidas.";
  await refreshTasks(ep);
}));

function resetIntegration(){
  $("offer-result").textContent="";
  $("supplier-form").reset();
  $("supplier-checks").replaceChildren();
  $("supplier-result").textContent="";
  $("integration-status").textContent="Sin consultar.";
  $("supplier-form").querySelector("button").disabled=true;
}
$("integration-load").addEventListener("click",async e=>{
  const button=e.currentTarget,epoch=sessionEpoch;
  if(!token||button.disabled)return;button.disabled=true;
  try{
    const data=await api(prefix+"/integration-contract");
    if(epoch!==sessionEpoch)return;
    if(data.live_enabled!==false||data.real_adapter_implemented!==false)throw Error("Modo no seguro.");
    $("supplier-checks").replaceChildren(...Object.entries(data.requirements).map(([key,label])=>{
      const wrapper=document.createElement("label"),span=document.createElement("span"),input=document.createElement("input");
      input.type="checkbox";input.name=key;input.style.width="auto";span.append(input,document.createTextNode(" "+label));wrapper.append(span);return wrapper;
    }));
    $("supplier-form").querySelector("button").disabled=false;
    $("integration-status").textContent="Perú · PEN. Estados Unidos · USD, desactivado. Ningún proveedor conectado.";
    $("supplier-result").textContent="";
  }catch(err){if(epoch===sessionEpoch)$("integration-status").textContent=err.message;}
  finally{button.disabled=false;}
});
$("supplier-form").addEventListener("submit",async e=>{
  e.preventDefault();const form=e.currentTarget,button=form.querySelector("button"),epoch=sessionEpoch;
  if(!token||button.disabled)return;button.disabled=true;
  try{
    const data=await api(prefix+"/supplier-checklist",{provider:form.elements.provider.value,declared:Object.fromEntries([...$("supplier-checks").querySelectorAll("input")].map(x=>[x.name,x.checked]))});
    if(epoch!==sessionEpoch)return;
    if(data.live_enabled!==false||data.evidence_verified!==false||data.approved_for_sale!==false)throw Error("Modo no seguro.");
    $("supplier-result").textContent=data.declared_count+"/"+data.required_count+" requisitos declarados. Sin evidencia verificada ni autorización de venta.";
  }catch(err){if(epoch===sessionEpoch)$("supplier-result").textContent=err.message;}
  finally{if(epoch===sessionEpoch)button.disabled=false;}
});
$("offer-form").addEventListener("submit",async e=>{
  e.preventDefault();const form=e.currentTarget,button=form.querySelector("button"),epoch=sessionEpoch;
  if(!token||button.disabled||!$("finance").reportValidity())return;button.disabled=true;
  try{
    const data=await api(prefix+"/offer-scenario",{...Object.fromEntries(new FormData($("finance"))),...Object.fromEntries(new FormData(form))});
    if(epoch!==sessionEpoch)return;
    if(data.live_enabled!==false||data.budget_approved!==false)throw Error("Modo no seguro.");
    $("offer-result").textContent=["Contribución por entrega: S/ "+data.contribution_per_delivery,"Margen de contribución: "+data.contribution_margin_pct+"%","Límite de publicidad por pedido recibido: S/ "+data.max_ad_spend_per_received_order,data.target_possible_before_ads?"Objetivo posible antes de publicidad.":"Objetivo imposible incluso sin publicidad.",data.meets_both_targets?"Cumple ambos objetivos.":"No cumple ambos objetivos.","Simulación sin presupuesto autorizado."].join("\n");
  }catch(err){if(epoch===sessionEpoch)$("offer-result").textContent=err.message;}
  finally{button.disabled=false;}
});
