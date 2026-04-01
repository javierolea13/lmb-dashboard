/**
 * fans_detalle.js v2
 * ==================
 * Sección mejorada de Fans Online — LMB 2025
 */

let FANS_DET = null;
let fansDetDonut = null;
let fansDetActivEq = 'Liga';
let horaFilterCat = 'Todos';

async function loadFansDetalle() {
  try {
    const r = await fetch('data/fans_detalle.json');
    FANS_DET = await r.json();
    console.log('✅ fans_detalle.json cargado');
    initFansDetalle();
  } catch(e) {
    console.error('Error cargando fans_detalle:', e);
  }
}

const fmtN = n => n>=1e6?(n/1e6).toFixed(1)+'M':n>=1000?(n/1000).toFixed(1)+'k':Math.round(n).toLocaleString('es-MX');
const fmtMoney = n => '$'+fmtN(n);
const fmtFull = n => Math.round(n).toLocaleString('es-MX');

function initFansDetalle() {
  if (!FANS_DET) return;
  let totalFans=0, totalOrdenes=0, totalGasto=0;
  Object.entries(FANS_DET).forEach(([k,d]) => {
    if(k.startsWith('_')) return;
    totalFans += d.total_fans_online;
    totalOrdenes += d.total_ordenes_online;
    Object.values(d.frecuencia||{}).forEach(f => { totalGasto += f.gasto_total; });
  });
  const el = id => document.getElementById(id);
  if(el('fd-total')) el('fd-total').textContent = fmtN(totalFans);
  if(el('fd-ordenes')) el('fd-ordenes').textContent = fmtN(totalOrdenes);
  if(el('fd-gasto-avg')) el('fd-gasto-avg').textContent = fmtMoney(totalGasto/totalFans);
  let f1Total = 0;
  Object.entries(FANS_DET).forEach(([k,d]) => { if(!k.startsWith('_')) f1Total += (d.frecuencia['1']?.fans||0); });
  if(el('fd-f1-pct')) el('fd-f1-pct').textContent = (f1Total/totalFans*100).toFixed(1)+'%';
  if(el('fd-recurrentes')) el('fd-recurrentes').textContent = fmtN(totalFans - f1Total);
  renderFansDetEq('Liga');
}

function selFansDetEq(eq, btn) {
  fansDetActivEq = eq;
  document.querySelectorAll('#fans .frow .fb').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  horaFilterCat = 'Todos';
  renderFansDetEq(eq);
}

function renderFansDetEq(eq) {
  const container = document.getElementById('fans-det-content');
  if (!container || !FANS_DET) return;
  const data = eq === 'Liga' ? aggregateLiga() : FANS_DET[eq];
  if (!data) return;

  container.innerHTML = `
    <div class="g2 mb">
      <div class="card">
        <div class="ctitle">Segmentación por Frecuencia — ${eq}</div>
        <div style="display:flex;gap:20px;align-items:center">
          <div style="width:170px;height:170px;position:relative"><canvas id="fd-donut"></canvas></div>
          <div style="flex:1" id="fd-freq-table"></div>
        </div>
      </div>
      <div class="card">
        <div class="ctitle">Plataformas de Compra</div>
        <div id="fd-plat-bars"></div>
      </div>
    </div>
    <div class="g2 mb">
      <div class="card">
        <div class="chdr">
          <div class="ctitle" style="margin-bottom:0">Compras por Día de la Semana</div>
          <div style="display:flex;gap:4px;align-items:center">
            <span style="width:8px;height:8px;border-radius:2px;background:var(--accent);display:inline-block"></span>
            <span style="font-size:9px;color:var(--text3)">L-V</span>
            <span style="width:8px;height:8px;border-radius:2px;background:var(--norte);display:inline-block;margin-left:6px"></span>
            <span style="font-size:9px;color:var(--text3)">Fin de semana</span>
          </div>
        </div>
        <div style="font-size:10px;color:var(--text3);margin-bottom:8px">← Clic en un día para ver desglose por equipo</div>
        <div id="fd-dia-bars"></div>
        <div id="fd-dia-drilldown" style="margin-top:10px"></div>
      </div>
      <div class="card">
        <div class="chdr">
          <div class="ctitle" style="margin-bottom:0">Horario de Compra</div>
          <div style="display:flex;gap:4px" id="fd-hora-filters">
            <button class="fb active" onclick="setHoraFilter('Todos',this)">Todos</button>
            <button class="fb" onclick="setHoraFilter('TR',this)">Temp. Regular</button>
            <button class="fb" onclick="setHoraFilter('Playoffs',this)">Playoffs</button>
            <button class="fb" onclick="setHoraFilter('Abono',this)">Abonos</button>
          </div>
        </div>
        <div id="fd-hora-bars"></div>
      </div>
    </div>
    <div class="g2 mb">
      <div class="card">
        <div class="ctitle">🏆 Top 10 Fans por Gasto${eq==='Liga'?' — Todos los equipos':' — '+eq}</div>
        <div class="twrap" id="fd-top-fans"></div>
      </div>
      <div class="card">
        <div class="ctitle">Métodos de Pago</div>
        <div id="fd-metodos"></div>
      </div>
    </div>
    <div class="card mb">
      <div class="ctitle">📊 Oportunidad de Retención por Equipo</div>
      <div class="twrap" id="fd-retention"></div>
    </div>
  `;

  renderFreqDonut(data);
  renderFreqTable(data);
  renderPlatBars(data);
  renderDiaBars(data, eq);
  renderHoraBars(data, 'Todos');
  renderTopFans(data, eq);
  renderMetodos(data);
  renderRetention();
}

function aggregateLiga() {
  const agg = {
    total_fans_online:0, total_ordenes_online:0,
    frecuencia:{'1':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'2-5':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'6-10':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'+10':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0}},
    plataformas:[], top_fans:[], compras_por_dia:{}, compras_por_hora:{}, compras_por_hora_cat:{}, compras_por_dia_detalle:{}, metodos_pago:{}
  };
  const platMap={};
  const horaCat = {TR:{},Playoffs:{},Abono:{}};
  Object.entries(FANS_DET).forEach(([k,d]) => {
    if(k.startsWith('_')) return;
    agg.total_fans_online += d.total_fans_online;
    agg.total_ordenes_online += d.total_ordenes_online;
    ['1','2-5','6-10','+10'].forEach(c => {
      const f=d.frecuencia[c]; if(f){agg.frecuencia[c].fans+=f.fans;agg.frecuencia[c].gasto_total+=f.gasto_total;agg.frecuencia[c].ordenes+=f.ordenes;}
    });
    (d.plataformas||[]).forEach(p => {
      if(!platMap[p.nombre]) platMap[p.nombre]={nombre:p.nombre,ordenes:0,ingreso:0,fans_unicos:0};
      platMap[p.nombre].ordenes+=p.ordenes; platMap[p.nombre].ingreso+=p.ingreso; platMap[p.nombre].fans_unicos+=p.fans_unicos;
    });
    Object.entries(d.compras_por_dia||{}).forEach(([k2,v])=>{agg.compras_por_dia[k2]=(agg.compras_por_dia[k2]||0)+v;});
    Object.entries(d.compras_por_hora||{}).forEach(([k2,v])=>{agg.compras_por_hora[k2]=(agg.compras_por_hora[k2]||0)+v;});
    Object.entries(d.metodos_pago||{}).forEach(([k2,v])=>{agg.metodos_pago[k2]=(agg.metodos_pago[k2]||0)+v;});
    Object.entries(d.compras_por_hora_cat||{}).forEach(([cat,horas])=>{
      Object.entries(horas).forEach(([h,v])=>{
        if(!horaCat[cat]) horaCat[cat]={};
        horaCat[cat][h]=(horaCat[cat][h]||0)+v;
      });
    });
  });
  ['1','2-5','6-10','+10'].forEach(c => {
    const f=agg.frecuencia[c];
    f.pct=agg.total_fans_online>0?Math.round(f.fans/agg.total_fans_online*1000)/10:0;
    f.gasto_promedio=f.fans>0?Math.round(f.gasto_total/f.fans*100)/100:0;
  });
  agg.plataformas=Object.values(platMap).sort((a,b)=>b.ordenes-a.ordenes);
  agg.plataformas.forEach(p=>{p.pct_ordenes=Math.round(p.ordenes/agg.total_ordenes_online*1000)/10;});
  agg.compras_por_hora_cat = horaCat;
  return agg;
}

function renderFreqDonut(data) {
  if(fansDetDonut){fansDetDonut.destroy();fansDetDonut=null;}
  const canvas=document.getElementById('fd-donut'); if(!canvas) return;
  const cats=['1','2-5','6-10','+10'];
  const vals=cats.map(c=>data.frecuencia[c]?.fans||0);
  fansDetDonut=new Chart(canvas,{type:'doughnut',
    data:{labels:['1 juego','2-5 juegos','6-10 juegos','+10 juegos'],
      datasets:[{data:vals,backgroundColor:['rgba(248,113,113,.8)','rgba(245,166,35,.8)','rgba(79,127,255,.8)','rgba(77,202,128,.8)'],borderColor:'transparent'}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',plugins:{legend:{display:false}}}
  });
}

function renderFreqTable(data) {
  const el=document.getElementById('fd-freq-table'); if(!el) return;
  const cats=[{k:'1',label:'1 juego',color:'#f87171',icon:'🎟'},{k:'2-5',label:'2-5 juegos',color:'#f5a623',icon:'🔄'},{k:'6-10',label:'6-10 juegos',color:'#4f7fff',icon:'⭐'},{k:'+10',label:'+10 juegos',color:'#4dca80',icon:'💎'}];
  el.innerHTML=`<table style="width:100%"><thead><tr><th></th><th>Fans</th><th>%</th><th>Gasto Prom</th><th>Gasto Total</th></tr></thead>
    <tbody>${cats.map(c=>{const f=data.frecuencia[c.k]||{};return `<tr>
      <td><span style="color:${c.color};font-weight:600">${c.icon} ${c.label}</span></td>
      <td class="mono">${fmtFull(f.fans||0)}</td><td class="mono">${f.pct||0}%</td>
      <td class="mono" style="color:var(--gold)">${fmtMoney(f.gasto_promedio||0)}</td>
      <td class="mono">${fmtMoney(f.gasto_total||0)}</td></tr>`;}).join('')}</tbody></table>`;
}

function renderPlatBars(data) {
  const el=document.getElementById('fd-plat-bars'); if(!el) return;
  const plats=data.plataformas||[];
  const maxOrd=Math.max(...plats.map(p=>p.ordenes),1);
  const icons={'iOS':'📱','Android':'🤖','Web Mobile':'🌐','Web Desktop':'💻','Otro':'❓'};
  el.innerHTML=plats.map(p=>`<div class="brow"><div class="blabels">
    <div class="bteam">${icons[p.nombre]||'📦'} ${p.nombre}</div>
    <div class="bpct" style="color:var(--accent)">${p.pct_ordenes}% · ${fmtN(p.ordenes)} órdenes</div></div>
    <div class="btrack"><div class="bfill" style="width:${p.ordenes/maxOrd*100}%;background:var(--accent)"></div></div>
    <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text3);margin-top:2px">
      <span>${fmtFull(p.fans_unicos)} fans únicos</span><span>${fmtMoney(p.ingreso)} ingreso</span></div></div>`).join('');
}

function renderDiaBars(data, eq) {
  const el=document.getElementById('fd-dia-bars'); if(!el) return;
  const dias=data.compras_por_dia||{};
  const orden=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  const maxVal=Math.max(...orden.map(d=>dias[d]||0),1);
  el.innerHTML=orden.map(d=>{
    const isFds = d==='Sábado'||d==='Domingo';
    const color = isFds?'var(--norte)':'var(--accent)';
    return `<div class="brow" style="margin-bottom:6px;cursor:pointer" onclick="drilldownDia('${d}')">
      <div class="blabels"><div class="bteam" style="min-width:90px">${d}</div>
        <div class="bpct" style="color:${color}">${fmtFull(dias[d]||0)}</div></div>
      <div class="btrack"><div class="bfill" style="width:${(dias[d]||0)/maxVal*100}%;background:${color}"></div></div></div>`;
  }).join('');
  const dd=document.getElementById('fd-dia-drilldown'); if(dd) dd.innerHTML='';
}

function drilldownDia(dia) {
  const dd=document.getElementById('fd-dia-drilldown'); if(!dd) return;
  const equipos=[];
  Object.entries(FANS_DET).forEach(([eq,d])=>{
    if(eq.startsWith('_')) return;
    const det=d.compras_por_dia_detalle||{};
    if(det[dia]){equipos.push({equipo:eq, ordenes:det[dia].ordenes||0, ingreso:det[dia].ingreso||0});}
  });
  equipos.sort((a,b)=>b.ordenes-a.ordenes);
  const maxOrd=equipos.length>0?equipos[0].ordenes:1;
  const zona = eq => (typeof STATS!=='undefined'?STATS.find(s=>s.equipo===eq)?.zona:'Norte')||'Norte';

  dd.innerHTML=`<div style="background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:12px">
    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:8px">
      📊 Desglose ${dia} — Órdenes por equipo
      <span style="float:right;cursor:pointer;color:var(--danger)" onclick="document.getElementById('fd-dia-drilldown').innerHTML=''">✕</span>
    </div>
    ${equipos.map(e=>{
      const z=zona(e.equipo);
      const c=z==='Norte'?'var(--norte)':'var(--sur)';
      return `<div class="brow" style="margin-bottom:4px"><div class="blabels">
        <div class="bteam" style="font-size:11px"><div class="bdot ${z==='Norte'?'n':'s'}"></div>${e.equipo}</div>
        <div class="bpct" style="color:${c}">${fmtFull(e.ordenes)} · ${fmtMoney(e.ingreso)}</div></div>
        <div class="btrack"><div class="bfill" style="width:${e.ordenes/maxOrd*100}%;background:${c}"></div></div></div>`;
    }).join('')}</div>`;
}

function setHoraFilter(cat, btn) {
  horaFilterCat = cat;
  document.querySelectorAll('#fd-hora-filters .fb').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  const data = fansDetActivEq==='Liga' ? aggregateLiga() : FANS_DET[fansDetActivEq];
  if(data) renderHoraBars(data, cat);
}

function renderHoraBars(data, cat) {
  const el=document.getElementById('fd-hora-bars'); if(!el) return;
  let horas;
  if(cat==='Todos'){horas=data.compras_por_hora||{};}
  else{horas=(data.compras_por_hora_cat||{})[cat]||{};}
  const sorted=[];
  for(let i=0;i<24;i++){sorted.push([String(i),horas[String(i)]||0]);}
  const maxVal=Math.max(...sorted.map(([,v])=>v),1);
  const catColors={Todos:'var(--accent)',TR:'var(--accent)',Playoffs:'var(--gold)',Abono:'var(--success)'};
  const barColor=catColors[cat]||'var(--accent)';

  el.innerHTML=`<div style="display:flex;align-items:flex-end;gap:2px;height:130px;padding-top:10px">
    ${sorted.map(([h,v])=>{
      const pct=v/maxVal*100;const isTop=v>=maxVal*0.85;
      return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px">
        <div style="font-size:7px;color:${isTop?'var(--gold)':'var(--text3)'};white-space:nowrap">${v>0?fmtN(v):''}</div>
        <div style="width:100%;height:${Math.max(pct,1)}%;background:${isTop?'var(--gold)':barColor};border-radius:2px 2px 0 0;min-height:2px;opacity:${v>0?1:0.15}"></div>
        <div style="font-size:8px;color:var(--text3)">${h}h</div></div>`;
    }).join('')}</div>
    <div style="text-align:center;margin-top:6px;font-size:10px;color:var(--text3)">
      ${cat==='Todos'?'Todas las categorías':cat} · Horas pico resaltadas en dorado
    </div>`;
}

function renderTopFans(data, eq) {
  const el=document.getElementById('fd-top-fans'); if(!el) return;
  let fans;
  if(eq==='Liga'){fans=FANS_DET['_liga_top_fans']||[];}
  else{fans=data.top_fans||[];}
  if(fans.length===0){el.innerHTML='<div style="color:var(--text3);padding:20px;text-align:center">Sin datos</div>';return;}
  const medals=['🥇','🥈','🥉'];const showEq=eq==='Liga';
  el.innerHTML=`<table style="width:100%"><thead><tr>
    <th>#</th>${showEq?'<th>Equipo</th>':''}<th>Fan</th><th>Eventos</th><th>Órdenes</th><th>Gasto</th><th>Plataforma</th>
  </tr></thead><tbody>${fans.map((f,i)=>`<tr>
    <td>${i<3?medals[i]:(i+1)}</td>
    ${showEq?`<td style="font-weight:600;font-size:11px">${f.equipo||''}</td>`:''}
    <td style="font-family:'DM Mono',monospace;font-size:11px">${f.correo}</td>
    <td class="mono">${f.eventos}</td><td class="mono">${f.ordenes}</td>
    <td class="mono" style="color:var(--gold)">${fmtMoney(f.gasto)}</td>
    <td style="font-size:11px">${f.plataforma}</td></tr>`).join('')}</tbody></table>`;
}

function renderMetodos(data) {
  const el=document.getElementById('fd-metodos'); if(!el) return;
  const metodos=data.metodos_pago||{};
  const total=Object.values(metodos).reduce((a,b)=>a+b,0);
  const sorted=Object.entries(metodos).sort((a,b)=>b[1]-a[1]);
  const maxVal=sorted.length>0?sorted[0][1]:1;
  const labels={'fiserv-3ds':'💳 Tarjeta (Fiserv)','visa-cybersource':'💳 Visa (Cybersource)',
    'conekta-spei':'🏦 SPEI (Conekta)','conekta-oxxo-pay':'🏪 OXXO Pay',
    'kueski-pay':'📱 Kueski Pay','openpay-3ds':'💳 OpenPay','bmpay':'📱 BMPay'};
  el.innerHTML=sorted.slice(0,7).map(([k,v])=>`<div class="brow" style="margin-bottom:6px"><div class="blabels">
    <div class="bteam">${labels[k]||k}</div>
    <div class="bpct" style="color:var(--success)">${(v/total*100).toFixed(1)}% · ${fmtFull(v)}</div></div>
    <div class="btrack"><div class="bfill" style="width:${v/maxVal*100}%;background:var(--success)"></div></div></div>`).join('');
}

function renderRetention() {
  const el=document.getElementById('fd-retention'); if(!el) return;
  const rows=Object.entries(FANS_DET).filter(([k])=>!k.startsWith('_'))
    .sort((a,b)=>b[1].total_fans_online-a[1].total_fans_online)
    .map(([eq,d])=>{
      const f=d.frecuencia;const t=d.total_fans_online;
      const f1=f['1']?.fans||0;const pct1=t>0?(f1/t*100).toFixed(1):0;
      const rec=t-f1;const pctRec=t>0?(rec/t*100).toFixed(1):0;
      const avgG=d.avg_gasto;const extra=Math.round(f1*avgG);
      return `<tr><td style="font-weight:600">${eq}</td>
        <td class="mono">${fmtFull(t)}</td>
        <td class="mono" style="color:var(--cortesia)">${pct1}%</td>
        <td class="mono" style="color:var(--success)">${pctRec}%</td>
        <td class="mono">${fmtMoney(avgG)}</td>
        <td class="mono">${fmtMoney(d.median_gasto||0)}</td>
        <td class="mono" style="color:var(--success)">+${fmtMoney(extra)}</td></tr>`;
    }).join('');
  el.innerHTML=`<table style="width:100%"><thead><tr>
    <th>Equipo</th><th>Fans</th><th>% 1 vez</th><th>% Recurrentes</th>
    <th>Gasto Prom</th><th>Mediana</th><th>💡 Si 1-vez vuelven</th></tr></thead><tbody>${rows}</tbody></table>`;
}

if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',loadFansDetalle);}
else{loadFansDetalle();}
