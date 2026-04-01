#!/usr/bin/env python3
"""
patch_ventas.py — Inyecta funciones de ventas en lmb_dashboard_v2.html
Corre: python3 patch_ventas.py
"""
import re

PATH = 'lmb_dashboard_v2.html'
html = open(PATH).read()

# 1. Check if selEq already exists
if 'function selEq' in html:
    print("⚠ selEq ya existe, saltando...")
else:
    # Inject selEq + renderEqDetail + renderPromosCortesias + initVentasDetail
    # Before "function renderSalesCharts()"
    VENTAS_JS = r'''
// ── VENTAS: SELECCIONAR EQUIPO ──
function selEq(eq, btn) {
  document.querySelectorAll('#ventas > .frow .fb').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderEqDetail(eq);
}
function renderEqDetail(eq) {
  var wrap = document.getElementById('eq-detail');
  if(!wrap || !VENTAS) return;
  var v = VENTAS[eq];
  if(!v) { wrap.innerHTML=''; return; }
  var s = STATS.find(function(s){return s.equipo===eq;});
  var zona = s?s.zona:'Norte';
  var zClass = zona==='Norte'?'n':'s';
  var zColor = zona==='Norte'?'var(--norte)':'var(--sur)';
  var zonas = v.zonas||[];
  var maxZIng = Math.max.apply(null,zonas.map(function(z){return z.ingreso;}).concat([1]));
  var totalZBol = zonas.reduce(function(a,z){return a+z.boletos;},0)||1;
  var totalIng = v.ingreso_total||1;
  var pctOnlIng = (v.ingreso_online/totalIng*100).toFixed(1);
  var pctTaqIng = (v.ingreso_taquilla/totalIng*100).toFixed(1);
  var totalBol = v.total_boletos||1;
  var pctOnlBol = (v.online/totalBol*100).toFixed(1);
  var pctTaqBol = (v.taquilla/totalBol*100).toFixed(1);
  var cortTipos = Object.entries(v.tipo_cortesia||{}).sort(function(a,b){return b[1]-a[1];});
  var maxCort = cortTipos.length>0?cortTipos[0][1]:1;
  var promoTipos = Object.entries(v.tipo_promocion||{}).sort(function(a,b){return b[1]-a[1];});
  var maxPromo = promoTipos.length>0?promoTipos[0][1]:1;
  wrap.innerHTML = '<div class="card mb" style="border-color:'+zColor+'40">'+
    '<div class="chdr"><div style="display:flex;align-items:center;gap:10px">'+
    '<div class="ctitle" style="margin-bottom:0">Detalle Ventas — '+eq+'</div>'+
    '<span class="chip '+zClass+'">'+zona+'</span></div></div>'+
    '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:18px">'+
    '<div style="background:var(--bg3);border-radius:6px;padding:12px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">Boletos Total</div><div class="mono" style="font-size:18px;font-weight:600;margin-top:4px">'+fmtF(v.total_boletos)+'</div></div>'+
    '<div style="background:var(--bg3);border-radius:6px;padding:12px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--text3)">Ingreso Total</div><div class="mono" style="font-size:18px;font-weight:600;color:var(--gold);margin-top:4px">$'+fmt(v.ingreso_total)+'</div></div>'+
    '<div style="background:var(--bg3);border-radius:6px;padding:12px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--vendido)">Vendidos</div><div class="mono" style="font-size:18px;font-weight:600;color:var(--vendido);margin-top:4px">'+fmtF(v.vendidos)+'</div><div style="font-size:10px;color:var(--text3);margin-top:2px">'+v.pct_vendido+'%</div></div>'+
    '<div style="background:var(--bg3);border-radius:6px;padding:12px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--promocion)">Promociones</div><div class="mono" style="font-size:18px;font-weight:600;color:var(--promocion);margin-top:4px">'+fmtF(v.promociones)+'</div><div style="font-size:10px;color:var(--text3);margin-top:2px">'+v.pct_promocion+'%</div></div>'+
    '<div style="background:var(--bg3);border-radius:6px;padding:12px"><div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--cortesia)">Cortesías</div><div class="mono" style="font-size:18px;font-weight:600;color:var(--cortesia);margin-top:4px">'+fmtF(v.cortesias)+'</div><div style="font-size:10px;color:var(--text3);margin-top:2px">'+v.pct_cortesia+'%</div></div>'+
    '</div>'+
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">'+
    '<div>'+
    '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:10px">Canal de Venta</div>'+
    '<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text3);margin-bottom:4px"><span>Ingreso</span><span>$'+fmt(v.ingreso_total)+'</span></div>'+
    '<div style="display:flex;height:18px;border-radius:4px;overflow:hidden"><div style="width:'+pctOnlIng+'%;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:#fff;min-width:30px">'+pctOnlIng+'%</div><div style="width:'+pctTaqIng+'%;background:rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:var(--text2);min-width:30px">'+pctTaqIng+'%</div></div>'+
    '<div style="display:flex;justify-content:space-between;font-size:10px;margin-top:3px"><span style="color:var(--accent)">Online: $'+fmt(v.ingreso_online)+'</span><span style="color:var(--text3)">Taquilla: $'+fmt(v.ingreso_taquilla)+'</span></div></div>'+
    '<div><div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text3);margin-bottom:4px"><span>Boletos</span><span>'+fmtF(v.total_boletos)+'</span></div>'+
    '<div style="display:flex;height:18px;border-radius:4px;overflow:hidden"><div style="width:'+pctOnlBol+'%;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:#fff;min-width:30px">'+pctOnlBol+'%</div><div style="width:'+pctTaqBol+'%;background:rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:var(--text2);min-width:30px">'+pctTaqBol+'%</div></div>'+
    '<div style="display:flex;justify-content:space-between;font-size:10px;margin-top:3px"><span style="color:var(--accent)">Online: '+fmtF(v.online)+'</span><span style="color:var(--text3)">Taquilla: '+fmtF(v.taquilla)+'</span></div></div>'+
    '<div style="margin-top:14px;background:var(--bg3);border-radius:6px;padding:10px 12px;display:flex;align-items:center;gap:10px"><span style="font-size:20px">👤</span><div><div class="mono" style="font-size:16px;font-weight:600;color:var(--accent)">'+fmtF(v.fans_unicos_online)+'</div><div style="font-size:10px;color:var(--text3)">Fans únicos online</div></div></div>'+
    '</div>'+
    '<div><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:10px">Ingreso por Zona</div>'+
    zonas.map(function(z){var pctZ=(z.boletos/totalZBol*100).toFixed(1);var avgP=z.boletos>0?Math.round(z.ingreso/z.boletos):0;return '<div class="brow" style="margin-bottom:8px"><div class="blabels"><div class="bteam" style="font-size:11px">'+z.ZONA+'</div><div class="bpct" style="color:'+zColor+'">$'+fmt(z.ingreso)+' · '+fmtF(z.boletos)+' bol.</div></div><div class="btrack"><div class="bfill" style="width:'+(z.ingreso/maxZIng*100)+'%;background:'+zColor+'"></div></div><div style="display:flex;justify-content:space-between;font-size:9px;color:var(--text3);margin-top:1px"><span>'+pctZ+'% de boletos</span><span>Precio prom: $'+fmtF(avgP)+'</span></div></div>';}).join('')+
    '</div></div>'+
    renderPromosCortesias(v,cortTipos,maxCort,promoTipos,maxPromo)+
    '</div>';
}
function renderPromosCortesias(v,cortTipos,maxCort,promoTipos,maxPromo){
  if(!cortTipos.length&&!promoTipos.length) return '';
  var cols=cortTipos.length&&promoTipos.length?'1fr 1fr':'1fr';
  var h='<div style="margin-top:18px;border-top:1px solid var(--border);padding-top:14px;display:grid;grid-template-columns:'+cols+';gap:16px">';
  if(promoTipos.length){
    h+='<div><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--promocion);margin-bottom:10px">Desglose Promociones ('+fmtF(v.promociones)+' total)</div>';
    promoTipos.forEach(function(a){var t=a[0],c=a[1],p=v.promociones>0?(c/v.promociones*100).toFixed(1):'0';h+='<div class="brow" style="margin-bottom:4px"><div class="blabels"><div class="bteam" style="font-size:10px">'+t+'</div><div class="bpct" style="color:var(--promocion)">'+fmtF(c)+' ('+p+'%)</div></div><div class="btrack"><div class="bfill" style="width:'+(c/maxPromo*100)+'%;background:var(--promocion)"></div></div></div>';});
    h+='</div>';
  }
  if(cortTipos.length){
    h+='<div><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--cortesia);margin-bottom:10px">Desglose Cortesías ('+fmtF(v.cortesias)+' total)</div>';
    cortTipos.forEach(function(a){var t=a[0],c=a[1],p=v.cortesias>0?(c/v.cortesias*100).toFixed(1):'0';h+='<div class="brow" style="margin-bottom:4px"><div class="blabels"><div class="bteam" style="font-size:10px">'+t+'</div><div class="bpct" style="color:var(--cortesia)">'+fmtF(c)+' ('+p+'%)</div></div><div class="btrack"><div class="bfill" style="width:'+(c/maxCort*100)+'%;background:var(--cortesia)"></div></div></div>';});
    h+='</div>';
  }
  return h+'</div>';
}
function initVentasDetail(){if(VENTAS) renderEqDetail('Charros');}

'''

    target = 'function renderSalesCharts() {'
    if target not in html:
        print("❌ No encontré renderSalesCharts")
    else:
        html = html.replace(target, VENTAS_JS + target)
        print("✅ Inyectado selEq + renderEqDetail + renderPromosCortesias + initVentasDetail")

# 2. Add activeCanalFilter variable if missing
if 'activeCanalFilter' not in html:
    html = html.replace(
        "let activeEqPanel = null, activeFilter = 'Todos', panelSortCol = 'ing', panelSortDir = -1;",
        "let activeEqPanel = null, activeFilter = 'Todos', panelSortCol = 'ing', panelSortDir = -1, activeCanalFilter = 'todos';"
    )
    print("✅ Agregado activeCanalFilter")

# 3. Add initVentasDetail() to boot if missing
if 'initVentasDetail()' not in html:
    html = html.replace('initOutliers();\ninitFans();', 'initOutliers();\ninitVentasDetail();\ninitFans();')
    print("✅ Agregado initVentasDetail() al boot")

# 4. Fix Tecos duplicate notes if not fixed
if "tcard.querySelectorAll('.tecos-filter-note')" not in html:
    html = html.replace(
        """let noteEl = parent.nextElementSibling;
  if(noteEl && noteEl.classList.contains('tecos-filter-note')) noteEl.remove();""",
        """const tcard = btn.closest('.tcard');
  tcard.querySelectorAll('.tecos-filter-note').forEach(n=>n.remove());"""
    )
    print("✅ Fix Tecos notas duplicadas")

# Save
open(PATH, 'w').write(html)
print(f"\n✅ Archivo parchado: {PATH}")
print("Haz: git add -A && git commit -m 'patch ventas + outliers' && git push")
