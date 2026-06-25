const appsConfig = {
    forja: { title: "FORJA", sub: "IDEAS - EJECUCION - IMPACTO", percent: 78, lbl: "Ejecucion Total", metrics: [{num:"24", lbl:"En curso"},{num:"12", lbl:"Revision"},{num:"8", lbl:"Listos"},{num:"5", lbl:"Bloqueados"}], p1: "Construimos lo que imaginamos.", p2: "En FORJA, las ideas toman forma.", cards: [ {t:"Implementacion", s:"Construyendo", l:["Analiticas <span>70%</span>","Notif. <span>45%</span>","Pasarelas <span>30%</span>"]}, {t:"Cola Ejecucion", s:"Prioridades", l:["Panel admin <span>Alta</span>","Motor rec. <span>Alta</span>","Exportacion <span>Media</span>"]}, {t:"En Progreso", s:"Trabajando", l:["App reportes <span>65%</span>","Filtro IA <span>40%</span>"]}, {t:"Listo Entregar", s:"Calidad", l:["Bugs criticos <span>100%</span>","UX/UI <span>100%</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Nueva metrica","Mobile app","IA predictiva"]} ] },
    pluma: { title: "PLUMA", sub: "IDEAS - PALABRAS - ESTRATEGIA", percent: 85, lbl: "Productividad Total", metrics: [{num:"12k", lbl:"Palabras"},{num:"3", lbl:"Articulos"},{num:"1", lbl:"Libro"},{num:"5", lbl:"Guiones"}], p1: "Las palabras construyen imperios.", p2: "En PLUMA, las ideas se transforman en texto.", cards: [ {t:"Articulos Cientificos", s:"Investigacion", l:["IA finanzas <span>80%</span>","Ciberseg <span>50%</span>"]}, {t:"Libros Amazon", s:"Backselling", l:["Adultos <span>30%</span>","Ninios <span>10%</span>"]}, {t:"Posts LinkedIn", s:"Marca Personal", l:["CEO <span>100%</span>","Empresa <span>90%</span>"]}, {t:"Guiones LENTE", s:"Videos y Podcasts", l:["Video IA <span>100%</span>","Podcast <span>60%</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Tema libro","Estrategia","Guion corto"]} ] },
    lente: { title: "LENTE", sub: "VISION - NARRATIVA - IMPACTO", percent: 92, lbl: "Produccion Total", metrics: [{num:"8", lbl:"Videos hoy"},{num:"4", lbl:"Canales YT"},{num:"2", lbl:"Podcasts"},{num:"15k", lbl:"Vistas"}], p1: "Creamos contenido que conecta.", p2: "En LENTE, los guiones de PLUMA cobran vida.", cards: [ {t:"Canal YT Principal", s:"Empresa - Tech", l:["Video IA <span>100%</span>","Tutorial <span>70%</span>"]}, {t:"Canal YT Marketing", s:"Estrategia", l:["Embudos <span>80%</span>","Metricas <span>45%</span>"]}, {t:"Podcasts", s:"Entrevistas", l:["IA Futuro <span>100%</span>","Ciberseg <span>30%</span>"]}, {t:"Videos Cortos", s:"Reels/TikToks", l:["Clip IA <span>100%</span>","Clip Mkt <span>90%</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Nuevo canal","Shorts","Equipo"]} ] },
    marketing: { title: "MARKETING", sub: "CONEXION - ALCANCE - CRECIMIENTO", percent: 65, lbl: "Conversion Total", metrics: [{num:"5", lbl:"Campanas"},{num:"120", lbl:"Leads hoy"},{num:"4.5%", lbl:"Conversion"},{num:"$2k", lbl:"ROAS"}], p1: "Conectamos, contamos y crecemos impacto.", p2: "Distribuimos el contenido de LENTE.", cards: [ {t:"Redes Sociales", s:"Empresa y CEO", l:["LinkedIn <span>100%</span>","Twitter <span>80%</span>"]}, {t:"Embudos Venta", s:"Conversion", l:["App IA <span>70%</span>","Libro <span>40%</span>"]}, {t:"Generacion Leads", s:"Captacion", l:["Ads <span>90%</span>","Magnet <span>100%</span>"]}, {t:"SEO Analytics", s:"Trafico", l:["Blog <span>50%</span>","Backlinks <span>20%</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Presupuesto","Nicho","Email"]} ] },
    tendencias: { title: "TENDENCIAS", sub: "RADAR - SENALES - OPORTUNIDADES", percent: 95, lbl: "Cobertura Radar", metrics: [{num:"24h", lbl:"Reporte"},{num:"3", lbl:"Oportunidades"},{num:"12", lbl:"Senales"},{num:"5", lbl:"IAs nuevas"}], p1: "Exploramos senales y oportunidades.", p2: "Somos el radar de la empresa.", cards: [ {t:"Radar Tecnologico", s:"Nuevas IAs", l:["IA Gratis <span>Nueva</span>","API Video <span>Probada</span>"]}, {t:"Mercado Nichos", s:"Amazon y E-comm", l:["Ninios <span>Alta</span>","Finanzas <span>Media</span>"]}, {t:"Competencia", s:"Monitoreo", l:["Empresa A <span>Lanz.</span>","Empresa B <span>Baja</span>"]}, {t:"Oportunidades", s:"Para CEREBRO", l:["Skill Ventas <span>Prop.</span>","App IA <span>Prop.</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Aprobar IA","Validar","Asignar"]} ] },
    auditoria: { title: "AUDITORIA", sub: "VERDAD - CALIDAD - CONTROL", percent: 88, lbl: "Calidad Aprobada", metrics: [{num:"8", lbl:"Aprobados"},{num:"3", lbl:"Rechazados"},{num:"2", lbl:"En rev."},{num:"100%", lbl:"Transp."}], p1: "Transparencia, datos y verdad operativa.", p2: "Revisamos todo lo que produce FORJA.", cards: [ {t:"Revision FORJA", s:"Calidad codigo", l:["API King <span>Aprob.</span>","Skill <span>Rechaz.</span>"]}, {t:"Auditoria Ingresos", s:"Por aplicacion", l:["Amazon <span>$1.2k</span>","YT <span>$800</span>"]}, {t:"Control Calidad", s:"Estandares", l:["Seguridad <span>100%</span>","Rendim. <span>85%</span>"]}, {t:"En ARSENAL", s:"Aprobados", l:["API King <span>Lista</span>","CSP <span>Lista</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Aprobar App","Revisar Skill"]} ] },
    centinela: { title: "CENTINELA", sub: "ESCUDOS - VIGILANCIA - DEFENSA", percent: 98, lbl: "Seguridad Total", metrics: [{num:"0", lbl:"Brechas"},{num:"14", lbl:"Amenazas"},{num:"100%", lbl:"Escudos"},{num:"24/7", lbl:"Monitor"}], p1: "Protegemos lo que importa.", p2: "Somos el escudo del ecosistema.", cards: [ {t:"Monitoreo Red", s:"Trafico", l:["Anomalo <span>0</span>","Servers <span>100%</span>"]}, {t:"Proteccion Datos", s:"Clientes", l:["Cifrado <span>100%</span>","Backups <span>100%</span>"]}, {t:"Escudos Activos", s:"Defensas", l:["WAF <span>Activo</span>","Anti-DDoS <span>Activo</span>"]}, {t:"Gestion Riesgo", s:"Evaluacion", l:["Critico <span>0</span>","Medio <span>2</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Actualizar WAF","Pen Test"]} ] },
    marca: { title: "MARCA PERSONAL", sub: "IDENTIDAD - AUTORIDAD - INFLUENCIA", percent: 72, lbl: "Crecimiento Marca", metrics: [{num:"15k", lbl:"LinkedIn"},{num:"8k", lbl:"Twitter"},{num:"3", lbl:"Posts hoy"},{num:"4.2%", lbl:"Engage"}], p1: "Tu identidad como CEO es el activo mas valioso.", p2: "Gestionamos tu LinkedIn y redes.", cards: [ {t:"LinkedIn CEO", s:"Autoridad", l:["Post IA <span>100%</span>","Liderazgo <span>80%</span>"]}, {t:"Twitter/X", s:"Hilos", l:["Hilo IA <span>100%</span>","Thread <span>60%</span>"]}, {t:"YouTube Personal", s:"Vlogs", l:["Vlog CEO <span>40%</span>"]}, {t:"Reputacion", s:"Monitoreo", l:["Menciones <span>24</span>","Sentiment <span>Pos.</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Aprobar post","Responder"]} ] },
    ecommer: { title: "E-COMMER", sub: "VENTAS - AMAZON - BACKSELLING", percent: 82, lbl: "Ventas del Mes", metrics: [{num:"$3.2k", lbl:"Ingresos"},{num:"147", lbl:"Ventas hoy"},{num:"12", lbl:"Productos"},{num:"4.8", lbl:"Rating"}], p1: "La tienda del ecosistema.", p2: "Gestionamos productos en Amazon y apps.", cards: [ {t:"Amazon Libros", s:"PLUMA produce", l:["IA Adultos <span>$1.2k</span>","Ninios <span>$400</span>"]}, {t:"Apps Comerciales", s:"Aprobadas", l:["API King <span>$800</span>","Financiera <span>$500</span>"]}, {t:"Backselling", s:"Recurrente", l:["Membresias <span>45</span>","Premium <span>12</span>"]}, {t:"Doctor Contable", s:"App propia", l:["Ventas <span>$200</span>"]}, {t:"Pendientes Cerebro", s:"Decision", l:["Precio libro","Promo","Nuevo"]} ] },
    bunker: { title: "BUNKER CEO", sub: "CONTROL - SEGURIDAD - EMERGENCIA", percent: 100, lbl: "DEFCON 1 (Riesgo Bajo)", metrics: [{num:"$0.50", lbl:"Costo IA"},{num:"0", lbl:"Amenazas"},{num:"2", lbl:"Cli Riesgo"},{num:"1", lbl:"Decision"}], p1: "Lo que otros no ven — tu ya lo sabes.", p2: "Centro de operaciones de emergencia.", cards: [ {t:"Riesgo Personal", s:"Exposicion CEO", l:["Doxxing <span>Bajo</span>","Phishing <span>Medio</span>"]}, {t:"Amenazas Activas", s:"Monitoreo", l:["Bots <span>12</span>","DDoS <span>0</span>"]}, {t:"Estado SOMBRA", s:"Coordinado", l:["Runtime <span>Estable</span>","Canal <span>Sellado</span>"]}, {t:"Inteligencia Hoy", s:"Estrategia", l:["Mercado <span>Alcista</span>","IA <span>3 nuevas</span>"]}, {t:"Codigos CEO", s:"Sin leer", l:["Codigo 001 <span>Alta</span>","Codigo 002 <span>Med.</span>"]} ] }
};

let currentView = 'main';

function fixChatHeights() {
    // Arreglar Chat Principal de CEREBRO
    const chatArea = document.getElementById('chatArea');
    if (chatArea && chatArea.offsetParent !== null) {
        const parent = chatArea.parentElement;
        const parentHeight = parent.clientHeight;
        const title = parent.querySelector('h4');
        const inputArea = parent.querySelector('.chat-input-area');
        let usedHeight = 40; // padding base
        if (title) usedHeight += title.offsetHeight;
        if (inputArea) usedHeight += inputArea.offsetHeight;
        chatArea.style.height = (parentHeight - usedHeight) + 'px';
    }

    // Arreglar Chat Flotante (Widget)
    const widgetArea = document.getElementById('widgetChatArea');
    if (widgetArea && widgetArea.offsetParent !== null) {
        const parent = widgetArea.parentElement;
        const parentHeight = parent.clientHeight;
        const inputArea = parent.querySelector('.widget-input-area');
        let usedHeight = 20;
        if (inputArea) usedHeight += inputArea.offsetHeight;
        widgetArea.style.height = (parentHeight - usedHeight) + 'px';
    }
}
window.addEventListener('resize', fixChatHeights);

function navigateTo(view) {
    currentView = view;
    document.getElementById('main-office').style.display = 'none';
    document.getElementById('cerebro-office').style.display = 'none';
    document.getElementById('dynamic-office').style.display = 'none';
    
    const widgetTitle = document.getElementById('widgetTitle');
    
    if (view === 'main') {
        document.getElementById('main-office').style.display = 'flex';
        document.getElementById('chatWidget').style.display = 'none';
    } else if (view === 'cerebro') {
        document.getElementById('cerebro-office').style.display = 'flex'; setTimeout(fixChatHeights, 50);
        document.getElementById('chatWidget').style.display = 'none';
    } else if (view === 'more') {
        renderMoreApps();
        document.getElementById('dynamic-office').style.display = 'flex';
        document.getElementById('chatWidget').style.display = 'none';
    } else {
        renderDynamicOffice(view); setTimeout(fixChatHeights, 50);
        document.getElementById('dynamic-office').style.display = 'flex';
        document.getElementById('chatWidget').style.display = 'flex';
        widgetTitle.innerText = 'CEREBRO en ' + view.toUpperCase();
    }
}

function renderMoreApps() {
    const dyn = document.getElementById('dynamic-office');
    dyn.innerHTML = `
        <header class="sub-office-header">
            <button class="apple-back-btn" onclick="navigateTo('main')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg> Volver</button>
            <div class="pulse-container"><span>Mas Espacios</span><div class="ekg-monitor"><div class="ekg-line"></div></div></div>
            <div class="header-icons">[ Config ]</div>
        </header>
        <div class="more-apps-grid">
            <div class="glass-card more-card" onclick="navigateTo('marca')"><h3>MARCA PERSONAL</h3><p>Identidad, autoridad e influencia del CEO.</p><span class="enter-btn">Entrar</span></div>
            <div class="glass-card more-card" onclick="navigateTo('ecommer')"><h3>E-COMMER</h3><p>Ventas, Amazon y backselling del ecosistema.</p><span class="enter-btn">Entrar</span></div>
            <div class="glass-card more-card disabled"><h3>NUBE</h3><p>Proximamente.</p></div>
            <div class="glass-card more-card disabled"><h3>HERMES</h3><p>Proximamente.</p></div>
        </div>
        <footer class="sub-office-footer"><div class="quote">"El ecosistema crece. Estas son las aplicaciones del futuro."</div><button class="signature" onclick="navigateTo('bunker')">Daniel</button></footer>
    `;
}

function renderDynamicOffice(view) {
    const app = appsConfig[view];
    const dyn = document.getElementById('dynamic-office');
    let metricsHtml = app.metrics.map(m => `<div class="metric-item"><span>${m.num}</span><label>${m.lbl}</label></div>`).join('');
    let cardsHtml = app.cards.map(c => `<div class="op-card"><h5>${c.t}</h5><div class="sub">${c.s}</div><ul class="op-list">${c.l.map(li => `<li>${li}</li>`).join('')}</ul></div>`).join('');
    
    dyn.innerHTML = `
        <header class="sub-office-header">
            <button class="apple-back-btn" onclick="navigateTo('main')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg> Volver</button>
            <div class="pulse-container"><span>Oficina ${app.title}</span><div class="ekg-monitor"><div class="ekg-line"></div></div></div>
            <div class="header-icons">[ Config ]</div>
        </header>
        <div class="dyn-grid">
            <div class="glass-panel dyn-panel-left">
                <h1>Oficina <span>${app.title}</span></h1>
                <p>${app.p1}</p>
                <p>${app.p2}</p>
                <div class="purpose-card"><h5>Nuestro Proposito</h5><p>Ejecutar la vision del CEO con precision. Todo fluye, todo se conecta.</p><button class="apple-btn" onclick="navigateTo('cerebro')">Ir a CEREBRO</button></div>
            </div>
            <div class="glass-panel dyn-panel-center">
                <div class="hero-bg-glow"></div>
                <div class="hero-logo">${app.title}</div>
                <div class="hero-sub">${app.sub}</div>
            </div>
            <div class="glass-panel" style="display:flex; flex-direction:column; gap:10px;">
                <div class="dyn-panel-right-top">
                    <h4>Estado General</h4>
                    <div class="circle-progress" style="background: conic-gradient(#d4af37 0% ${app.percent}%, rgba(255,255,255,0.1) ${app.percent}% 100%);"><span>${app.percent}%</span></div>
                    <div style="color:#888; font-size:0.7rem; margin-bottom:10px;">${app.lbl}</div>
                    <div class="metrics-grid">${metricsHtml}</div>
                </div>
                <div class="dyn-panel-right-bottom">
                    <h4>Impacto en Marcha</h4>
                    <div class="list-item">Sistemas operativos al maximo</div>
                    <div class="list-item">Reporte enviado a CEREBRO</div>
                    <div class="list-item">Ingresos generados activamente</div>
                </div>
            </div>
        </div>
        <div class="bottom-cards">${cardsHtml}</div>
        <footer class="sub-office-footer"><div class="quote">"La ejecucion disciplinada convierte la vision en valor."</div><button class="signature" onclick="navigateTo('bunker')">Daniel</button></footer>
    `;
}

function toggleChat() {
    const body = document.getElementById('chatBody');
    const icon = document.getElementById('chatToggleIcon');
    const widget = document.getElementById('chatWidget');
    if (body.style.display === 'flex') { body.style.display = 'none'; widget.style.height = '50px'; icon.innerText = '+'; }
    else { body.style.display = 'flex'; widget.style.height = '350px'; setTimeout(fixChatHeights, 50); icon.innerText = 'x'; }
}
function handleWidgetChat(event) { if (event.key === 'Enter') sendWidgetMsg(); }
function sendWidgetMsg() {
    const input = document.getElementById('widgetInput');
    const text = input.value.trim();
    if (text === '') return;
    const area = document.getElementById('widgetChatArea');
    const userMsg = document.createElement('div');
    userMsg.className = 'widget-msg user';
    userMsg.innerText = 'CEO: ' + text;
    area.appendChild(userMsg);
    input.value = '';
    area.scrollTop = area.scrollHeight;

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'widget-msg ai';
    loadingMsg.innerText = 'CEREBRO: Procesando...';
    area.appendChild(loadingMsg);

    fetch('/api/v1/cerebro/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) })
    .then(res => res.json())
    .then(data => { loadingMsg.innerText = 'CEREBRO: ' + (data.response || data.message || data.reply || 'Recibido.'); area.scrollTop = area.scrollHeight; })
    .catch(err => { loadingMsg.innerText = 'CEREBRO: Conexion con backend en mantenimiento.'; area.scrollTop = area.scrollHeight; });
}

function handleKeyPress(event) { if (event.key === 'Enter') sendMessage(); }
function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (text === '') return;
    const chatArea = document.getElementById('chatArea');
    const userMsg = document.createElement('div');
    userMsg.className = 'msg user';
    userMsg.innerText = 'CEO: ' + text;
    chatArea.appendChild(userMsg);
    input.value = '';
    chatArea.scrollTop = chatArea.scrollHeight;

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'msg ai';
    loadingMsg.innerText = 'CEREBRO: Procesando...';
    chatArea.appendChild(loadingMsg);

    fetch('/api/v1/cerebro/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) })
    .then(res => res.json())
    .then(data => { loadingMsg.innerText = 'CEREBRO: ' + (data.response || data.message || data.reply || 'Recibido.'); chatArea.scrollTop = chatArea.scrollHeight; })
    .catch(err => { loadingMsg.innerText = 'CEREBRO: Conexion con backend en mantenimiento.'; chatArea.scrollTop = chatArea.scrollHeight; });
}

function showContext(type) {
    const chatArea = document.getElementById('chatArea');
    let message = '';
    if (type === 'manana') message = 'CEREBRO: Buenos dias CEO. Para hoy tenemos: 1) Lanzar campaña de Marketing. 2) Revision de seguridad con Centinela. 3) Cierre financiero.';
    if (type === 'tarde') message = 'CEREBRO: Revision de la tarde. Forja avanzo 40% en el modulo nuevo. Pluma tiene 3 borradores listos. Marketing genero 5 leads hoy.';
    if (type === 'ingresos') message = 'CEREBRO: Reporte de ingresos. Proyeccion diaria: $1,200. Decision autonoma tomada: Descuento del 10% aplicado a clientes antiguos para fidelizar.';
    const aiMsg = document.createElement('div');
    aiMsg.className = 'msg ai';
    aiMsg.innerText = message;
    chatArea.appendChild(aiMsg);
    chatArea.scrollTop = chatArea.scrollHeight;
}

