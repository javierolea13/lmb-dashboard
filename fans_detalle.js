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
  let totalFans=0, totalOrdenes=0, totalGasto=0, totalCompradores=0, totalCortesia=0, totalGastoCompradores=0;
  Object.entries(FANS_DET).forEach(([k,d]) => {
    if(k.startsWith('_')) return;
    totalFans += d.total_fans_online;
    totalOrdenes += d.total_ordenes_online;
    totalCompradores += (d.fans_compradores||d.total_fans_online);
    totalCortesia += (d.fans_cortesia||0);
    Object.values(d.frecuencia||{}).forEach(f => { totalGasto += f.gasto_total; });
    // Weighted sum for comprador avg
    totalGastoCompradores += (d.avg_gasto_compradores||d.avg_gasto||0) * (d.fans_compradores||d.total_fans_online);
  });
  const avgGastoCompradores = totalCompradores > 0 ? totalGastoCompradores / totalCompradores : 0;
  const el = id => document.getElementById(id);
  if(el('fd-total')) el('fd-total').textContent = fmtN(totalFans);
  if(el('fd-ordenes')) el('fd-ordenes').textContent = fmtN(totalOrdenes);
  // Show comprador avg if available, fallback to overall
  if(el('fd-gasto-avg')) {
    el('fd-gasto-avg').textContent = fmtMoney(avgGastoCompradores || (totalGasto/totalFans));
    el('fd-gasto-avg').title = 'Solo compradores reales (excluye cortesías)';
  }
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
        <div style="font-size:10px;color:var(--text3);margin-bottom:8px;margin-top:-8px">← Clic en segmento del donut para desglose por equipo</div>
        <div style="display:flex;gap:20px;align-items:center">
          <div style="width:170px;height:170px;position:relative"><canvas id="fd-donut"></canvas></div>
          <div style="flex:1" id="fd-freq-table"></div>
        </div>
        <div id="fd-freq-drilldown" style="margin-top:10px"></div>
      </div>
      <div class="card">
        <div class="ctitle">Plataformas de Compra</div>
        <div id="fd-plat-bars"></div>
      </div>
    </div>
    <div class="g2 mb">
      <div class="card" style="border-color:rgba(245,166,35,.3);background:linear-gradient(135deg,var(--card) 0%,rgba(245,166,35,.03) 100%)">
        <div class="ctitle" style="color:var(--norte)">🎯 Oportunidad de Conversión — Fans Cortesía</div>
        <div id="fd-cortesia-card"></div>
      </div>
      <div class="card">
        <div class="ctitle">🏟 Gasto por Zona — Fans Online${eq==='Liga'?' (Liga)':' ('+eq+')'}</div>
        <div id="fd-zonas-fans"></div>
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
  renderCortesiaCard(data, eq);
  renderZonasFans(data, eq);
  renderDiaBars(data, eq);
  renderHoraBars(data, 'Todos');
  renderTopFans(data, eq);
  renderMetodos(data);
  renderRetention();
}

function aggregateLiga() {
  const agg = {
    total_fans_online:0, total_ordenes_online:0,
    fans_compradores:0, fans_cortesia:0,
    frecuencia:{'1':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'2-5':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'6-10':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0},'+10':{fans:0,pct:0,gasto_total:0,gasto_promedio:0,ordenes:0}},
    plataformas:[], top_fans:[], compras_por_dia:{}, compras_por_hora:{}, compras_por_hora_cat:{}, compras_por_dia_detalle:{}, metodos_pago:{}, zonas_fans:[]
  };
  const platMap={};
  const horaCat = {TR:{},Playoffs:{},Abono:{}};
  const zonasMap = {};
  let totalGastoCompradores = 0, totalCompradores = 0;
  Object.entries(FANS_DET).forEach(([k,d]) => {
    if(k.startsWith('_')) return;
    agg.total_fans_online += d.total_fans_online;
    agg.total_ordenes_online += d.total_ordenes_online;
    agg.fans_compradores += (d.fans_compradores||0);
    agg.fans_cortesia += (d.fans_cortesia||0);
    totalGastoCompradores += (d.avg_gasto_compradores||0) * (d.fans_compradores||0);
    totalCompradores += (d.fans_compradores||0);
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
    // Aggregate zonas (by zona name across teams)
    (d.zonas_fans||[]).forEach(z => {
      if(!zonasMap[z.zona]) zonasMap[z.zona]={zona:z.zona,ordenes:0,ingreso:0,fans_unicos:0};
      zonasMap[z.zona].ordenes+=z.ordenes;
      zonasMap[z.zona].ingreso+=z.ingreso;
      zonasMap[z.zona].fans_unicos+=z.fans_unicos;
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
  // Computed cortesia fields
  agg.avg_gasto_compradores = totalCompradores > 0 ? Math.round(totalGastoCompradores/totalCompradores*100)/100 : 0;
  agg.median_gasto_compradores = 0; // Can't compute true median from per-team avgs
  agg.pct_cortesia_fans = agg.total_fans_online > 0 ? Math.round(agg.fans_cortesia/agg.total_fans_online*1000)/10 : 0;
  // Zonas aggregated — sort by ingreso, top 10
  agg.zonas_fans = Object.values(zonasMap).map(z => ({...z, gasto_prom_fan: z.fans_unicos>0?Math.round(z.ingreso/z.fans_unicos*100)/100:0})).sort((a,b)=>b.ingreso-a.ingreso).slice(0,10);
  return agg;
}

function renderFreqDonut(data) {
  if(fansDetDonut){fansDetDonut.destroy();fansDetDonut=null;}
  const canvas=document.getElementById('fd-donut'); if(!canvas) return;
  const cats=['1','2-5','6-10','+10'];
  const labels=['1 juego','2-5 juegos','6-10 juegos','+10 juegos'];
  const vals=cats.map(c=>data.frecuencia[c]?.fans||0);
  const bgColors=['rgba(248,113,113,.8)','rgba(245,166,35,.8)','rgba(79,127,255,.8)','rgba(77,202,128,.8)'];
  fansDetDonut=new Chart(canvas,{type:'doughnut',
    data:{labels,
      datasets:[{data:vals,backgroundColor:bgColors,borderColor:'transparent'}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>`${c.label}: ${fmtFull(c.raw)} fans (${vals.reduce((a,b)=>a+b,0)>0?(c.raw/vals.reduce((a,b)=>a+b,0)*100).toFixed(1)+'%':'0%'})`}}},
      onClick:(e,els)=>{
        if(els.length){
          const idx=els[0].index;
          drilldownFreqByTeam(cats[idx], labels[idx], bgColors[idx]);
        }
      }}
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

function drilldownFreqByTeam(freqCat, freqLabel, color) {
  const dd = document.getElementById('fd-freq-drilldown');
  if(!dd || !FANS_DET) return;
  // If already showing this category, toggle off
  if(dd.dataset.activeCat === freqCat) { dd.innerHTML=''; dd.dataset.activeCat=''; return; }
  dd.dataset.activeCat = freqCat;

  const equipos = [];
  Object.entries(FANS_DET).forEach(([eq,d]) => {
    if(eq.startsWith('_')) return;
    const f = d.frecuencia[freqCat];
    if(f && f.fans > 0) {
      equipos.push({
        equipo: eq,
        fans: f.fans,
        gasto_total: f.gasto_total,
        gasto_promedio: f.gasto_promedio,
        ordenes: f.ordenes,
        pct_of_team: d.total_fans_online > 0 ? (f.fans / d.total_fans_online * 100).toFixed(1) : 0,
      });
    }
  });
  equipos.sort((a,b) => b.fans - a.fans);
  const maxFans = equipos.length > 0 ? equipos[0].fans : 1;
  const zona = eq => (typeof STATS!=='undefined' ? STATS.find(s=>s.equipo===eq)?.zona : 'Norte') || 'Norte';

  dd.innerHTML = `<div style="background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:12px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">
        📊 Desglose "${freqLabel}" — Por equipo
      </div>
      <span style="cursor:pointer;color:var(--danger);font-size:12px" onclick="document.getElementById('fd-freq-drilldown').innerHTML='';document.getElementById('fd-freq-drilldown').dataset.activeCat=''">✕</span>
    </div>
    <div class="twrap">
      <table style="width:100%"><thead><tr>
        <th>Equipo</th><th>Fans</th><th>% del equipo</th><th>Gasto Prom</th><th>Gasto Total</th><th>Órdenes</th><th></th>
      </tr></thead><tbody>
      ${equipos.map(e => {
        const z = zona(e.equipo);
        const c = z==='Norte'?'var(--norte)':'var(--sur)';
        return `<tr>
          <td style="font-weight:600"><div class="bdot ${z==='Norte'?'n':'s'}" style="display:inline-block;margin-right:6px;vertical-align:middle"></div>${e.equipo}</td>
          <td class="mono">${fmtFull(e.fans)}</td>
          <td class="mono">${e.pct_of_team}%</td>
          <td class="mono" style="color:var(--gold)">${fmtMoney(e.gasto_promedio)}</td>
          <td class="mono">${fmtMoney(e.gasto_total)}</td>
          <td class="mono">${fmtFull(e.ordenes)}</td>
          <td><div style="width:60px;height:4px;background:var(--bg2);border-radius:2px;overflow:hidden">
            <div style="width:${e.fans/maxFans*100}%;height:100%;background:${color};border-radius:2px"></div>
          </div></td>
        </tr>`;
      }).join('')}
      </tbody></table>
    </div>
  </div>`;
}

function renderCortesiaCard(data, eq) {
  const el = document.getElementById('fd-cortesia-card');
  if(!el) return;
  
  // Check if new fields exist (need re-generated JSON)
  const hasNewFields = data.fans_compradores !== undefined;
  
  if(!hasNewFields) {
    el.innerHTML = `<div style="color:var(--text3);font-size:11px;padding:10px;text-align:center;line-height:1.6">
      ⚠ Requiere re-generar fans_detalle.json con el script actualizado.<br>
      <code style="background:var(--bg3);padding:2px 6px;border-radius:3px;font-size:10px">python3 generar_fans_detalle.py</code>
    </div>`;
    return;
  }

  const compradores = data.fans_compradores||0;
  const cortesia = data.fans_cortesia||0;
  const total = data.total_fans_online||1;
  const pctCort = data.pct_cortesia_fans||0;
  const avgComp = data.avg_gasto_compradores||0;
  const potencial = Math.round(cortesia * avgComp * 0.1); // 10% conversion estimate

  el.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px">
      <div style="background:var(--bg3);border-radius:6px;padding:10px">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">Compradores</div>
        <div class="mono" style="font-size:20px;font-weight:600;color:var(--success);margin-top:4px">${fmtFull(compradores)}</div>
        <div style="font-size:10px;color:var(--text3)">${(100-pctCort).toFixed(1)}% del total</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:10px">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">Cortesía (gasto $0)</div>
        <div class="mono" style="font-size:20px;font-weight:600;color:var(--cortesia);margin-top:4px">${fmtFull(cortesia)}</div>
        <div style="font-size:10px;color:var(--text3)">${pctCort}% del total</div>
      </div>
      <div style="background:var(--bg3);border-radius:6px;padding:10px">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">Gasto Prom Comprador</div>
        <div class="mono" style="font-size:20px;font-weight:600;color:var(--gold);margin-top:4px">${fmtMoney(avgComp)}</div>
        <div style="font-size:10px;color:var(--text3)">Mediana: ${fmtMoney(data.median_gasto_compradores||0)}</div>
      </div>
    </div>
    <!-- Split bar -->
    <div style="margin-bottom:10px">
      <div style="display:flex;height:20px;border-radius:4px;overflow:hidden">
        <div style="width:${100-pctCort}%;background:var(--success);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:#fff;min-width:25px">Compradores</div>
        <div style="width:${pctCort}%;background:var(--cortesia);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:#fff;min-width:25px">Cortesía</div>
      </div>
    </div>
    <div style="background:rgba(245,166,35,.06);border:1px solid rgba(245,166,35,.2);border-radius:6px;padding:10px 12px;font-size:11px;line-height:1.6">
      <strong style="color:var(--norte)">💡 Oportunidad:</strong>
      Si el <strong>10%</strong> de fans cortesía se convierten en compradores al gasto promedio actual,
      representaría <strong style="color:var(--gold)">+${fmtMoney(potencial)}</strong> en ingreso adicional.
      <div style="margin-top:4px;color:var(--text3);font-size:10px">
        ${fmtFull(cortesia)} fans ya conocen el estadio. Estrategias: cupones primer compra, upgrades de zona, paquetes descuento.
      </div>
    </div>
  `;
}

function renderZonasFans(data, eq) {
  const el = document.getElementById('fd-zonas-fans');
  if(!el) return;

  const zonas = data.zonas_fans;
  if(!zonas || zonas.length === 0) {
    el.innerHTML = `<div style="color:var(--text3);font-size:11px;padding:10px;text-align:center;line-height:1.6">
      ⚠ Requiere re-generar fans_detalle.json con el script actualizado.<br>
      <code style="background:var(--bg3);padding:2px 6px;border-radius:3px;font-size:10px">python3 generar_fans_detalle.py</code>
    </div>`;
    return;
  }

  const maxIng = Math.max(...zonas.map(z=>z.ingreso),1);
  const zona_eq = eq !== 'Liga' && typeof STATS !== 'undefined' ? STATS.find(s=>s.equipo===eq)?.zona : null;
  const barColor = zona_eq==='Norte'?'var(--norte)':zona_eq==='Sur'?'var(--sur)':'var(--accent)';

  el.innerHTML = zonas.map(z => `
    <div class="brow" style="margin-bottom:8px">
      <div class="blabels">
        <div class="bteam" style="font-size:11px">${z.zona}</div>
        <div class="bpct" style="color:${barColor}">${fmtMoney(z.ingreso)}</div>
      </div>
      <div class="btrack"><div class="bfill" style="width:${z.ingreso/maxIng*100}%;background:${barColor}"></div></div>
      <div style="display:flex;justify-content:space-between;font-size:9px;color:var(--text3);margin-top:1px">
        <span>${fmtFull(z.fans_unicos)} fans · ${fmtFull(z.ordenes)} órdenes</span>
        <span>Gasto prom/fan: ${fmtMoney(z.gasto_prom_fan)}</span>
      </div>
    </div>
  `).join('');
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
      const avgGComp=d.avg_gasto_compradores||d.avg_gasto;
      const nCort=d.fans_cortesia||0;
      const pctCort=d.pct_cortesia_fans||0;
      const extra=Math.round(f1*avgGComp);
      return `<tr><td style="font-weight:600">${eq}</td>
        <td class="mono">${fmtFull(t)}</td>
        <td class="mono" style="color:var(--cortesia)">${pct1}%</td>
        <td class="mono" style="color:var(--success)">${pctRec}%</td>
        <td class="mono">${fmtMoney(avgGComp)}</td>
        <td class="mono">${fmtMoney(d.median_gasto_compradores||d.median_gasto||0)}</td>
        <td class="mono" style="color:var(--cortesia)">${fmtFull(nCort)}${pctCort?' ('+pctCort+'%)':''}</td>
        <td class="mono" style="color:var(--success)">+${fmtMoney(extra)}</td></tr>`;
    }).join('');
  el.innerHTML=`<table style="width:100%"><thead><tr>
    <th>Equipo</th><th>Fans</th><th>% 1 vez</th><th>% Recurrentes</th>
    <th>Gasto Prom Comprador</th><th>Mediana</th><th>Fans Cortesía</th><th>💡 Si 1-vez vuelven</th></tr></thead><tbody>${rows}</tbody></table>`;
}

if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',loadFansDetalle);}
else{loadFansDetalle();}
