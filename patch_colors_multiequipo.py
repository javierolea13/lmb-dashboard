#!/usr/bin/env python3
"""
patch_colors_multiequipo.py
Aplica nuevos colores y agrega sección Fans Multi-Equipo.
Corre: python3 patch_colors_multiequipo.py
"""

PATH = 'lmb_dashboard_v2.html'
html = open(PATH).read()

# ══════════════════════════════════════════════════════════════
# 1. ACTUALIZAR COLORES — #00c677 como accent, #0E1423 como bg
# ══════════════════════════════════════════════════════════════
OLD_COLORS = """--bg:#090d13;--bg2:#101520;--bg3:#161c28;--card:#192030;--card2:#1e273d;
  --border:#253040;--border2:#2e3d55;
  --text:#dde4f0;--text2:#7d8faa;--text3:#47556a;
  --norte:#f5a623;--norte-dim:rgba(245,166,35,.1);
  --sur:#3ecfbe;--sur-dim:rgba(62,207,190,.1);
  --accent:#4f7fff;--accent-dim:rgba(79,127,255,.1);
  --danger:#ff5252;--danger-dim:rgba(255,82,82,.08);
  --success:#4dca80;--gold:#f5c83a;
  --vendido:#4f7fff;--promocion:#a78bfa;--cortesia:#f87171;"""

NEW_COLORS = """--bg:#0E1423;--bg2:#111827;--bg3:#172033;--card:#1a2538;--card2:#1f2d44;
  --border:#263348;--border2:#304060;
  --text:#e0e7f1;--text2:#8298b5;--text3:#4a5f7a;
  --norte:#f5a623;--norte-dim:rgba(245,166,35,.1);
  --sur:#3ecfbe;--sur-dim:rgba(62,207,190,.1);
  --accent:#00c677;--accent-dim:rgba(0,198,119,.12);
  --danger:#ff5252;--danger-dim:rgba(255,82,82,.08);
  --success:#00c677;--gold:#f5c83a;
  --vendido:#00c677;--promocion:#a78bfa;--cortesia:#f87171;"""

if OLD_COLORS in html:
    html = html.replace(OLD_COLORS, NEW_COLORS)
    print("✅ Colores actualizados (#00c677 + #0E1423)")
elif '--accent:#00c677' in html:
    print("⚠ Colores ya actualizados, saltando...")
else:
    print("⚠ No encontré los colores originales exactos — actualizando manualmente...")
    # Fallback: replace individual values
    replacements = {
        '--bg:#090d13': '--bg:#0E1423',
        '--bg2:#101520': '--bg2:#111827',
        '--bg3:#161c28': '--bg3:#172033',
        '--card:#192030': '--card:#1a2538',
        '--card2:#1e273d': '--card2:#1f2d44',
        '--border:#253040': '--border:#263348',
        '--border2:#2e3d55': '--border2:#304060',
        '--accent:#4f7fff': '--accent:#00c677',
        '--accent-dim:rgba(79,127,255,.1)': '--accent-dim:rgba(0,198,119,.12)',
        '--success:#4dca80': '--success:#00c677',
        '--vendido:#4f7fff': '--vendido:#00c677',
    }
    for old, new in replacements.items():
        if old in html:
            html = html.replace(old, new)
    print("✅ Colores actualizados (fallback)")

# Also update the logo background
html = html.replace(
    'background:var(--accent);color:#fff;font-family:',
    'background:#00c677;color:#fff;font-family:'
)

# ══════════════════════════════════════════════════════════════
# 2. AGREGAR NAV ITEM "MULTI-EQUIPO" si no existe
# ══════════════════════════════════════════════════════════════
if 'multiequipo' not in html:
    # Add nav item before Simulador
    html = html.replace(
        """<div class="ni disabled" onclick="show('simulador')">Simulador""",
        """<div class="ni" onclick="show('multiequipo')">Multi-Equipo</div>
  <div class="ni disabled" onclick="show('simulador')">Simulador"""
    )
    
    # Add section before closing </div><!-- /main -->
    MULTI_SECTION = '''
<!-- ══ MULTI-EQUIPO ══ -->
<div id="multiequipo" class="sec">
  <div class="shdr"><div class="stitle">Fans Multi-Equipo</div><div class="sdesc">Fans online que compraron boletos para más de un equipo · Viajeros de béisbol</div></div>

  <div class="g4 mb">
    <div class="card"><div class="ctitle">Fans Multi-Equipo</div><div class="kv" style="color:var(--accent)" id="me-total">—</div><div class="kl">Compraron en 2+ equipos</div></div>
    <div class="card"><div class="ctitle">Equipos Promedio</div><div class="kv" id="me-avg-eq">—</div><div class="kl">Equipos por fan multi</div></div>
    <div class="card"><div class="ctitle">Gasto Promedio</div><div class="kv" style="color:var(--gold)" id="me-avg-gasto">—</div><div class="kl">Total across equipos</div></div>
    <div class="card"><div class="ctitle">Max Equipos</div><div class="kv" style="color:var(--danger)" id="me-max-eq">—</div><div class="kl">Récord de un solo fan</div></div>
  </div>

  <div class="g2 mb">
    <div class="card">
      <div class="ctitle">Distribución: ¿Cuántos equipos visitan?</div>
      <div id="me-dist-bars"></div>
    </div>
    <div class="card">
      <div class="ctitle">Combinaciones más frecuentes</div>
      <div id="me-combos"></div>
    </div>
  </div>

  <div class="card mb">
    <div class="ctitle">🏆 Top 20 Fans Viajeros — Más equipos visitados</div>
    <div class="twrap" id="me-top-fans"></div>
  </div>

  <div class="card mb">
    <div class="ctitle">Red de Equipos — ¿Qué equipos comparten más fans?</div>
    <div id="me-network"></div>
  </div>

  <div class="nota">
    <span>ℹ</span>
    <span>Análisis basado en correos electrónicos únicos que aparecen en órdenes online de más de un equipo. Un fan que compró boletos para Charros y Sultanes cuenta como "multi-equipo" con 2 equipos.</span>
  </div>
</div>
'''
    html = html.replace('</div><!-- /main -->', MULTI_SECTION + '\n</div><!-- /main -->')
    if '</div><!-- /main -->' not in html:
        # Fallback: insert before last </div> before <script>
        html = html.replace('\n<script>', MULTI_SECTION + '\n<script>')
    print("✅ Sección Multi-Equipo agregada al HTML")
else:
    print("⚠ Sección multiequipo ya existe")

# ══════════════════════════════════════════════════════════════
# 3. AGREGAR JS para renderizar Multi-Equipo
# ══════════════════════════════════════════════════════════════
if 'function initMultiEquipo' not in html:
    MULTI_JS = '''
// ── MULTI-EQUIPO ──
var MULTI_EQ = null;
function loadMultiEquipo(){
  fetch('data/fans_multiequipo.json').then(r=>r.json()).then(function(d){
    MULTI_EQ=d; initMultiEquipo();
  }).catch(function(){
    var sec=document.getElementById('multiequipo');
    if(sec){var c=sec.querySelector('.g4');if(c)c.insertAdjacentHTML('afterend','<div class="nota mb"><span>⚠</span><span>Requiere generar fans_multiequipo.json: <code>python3 generar_fans_detalle.py</code></span></div>');}
  });
}
function initMultiEquipo(){
  if(!MULTI_EQ) return;
  var d=MULTI_EQ;
  var el=function(id){return document.getElementById(id);};
  if(el('me-total')) el('me-total').textContent=fmtF(d.total_multi);
  if(el('me-avg-eq')) el('me-avg-eq').textContent=d.avg_equipos.toFixed(1);
  if(el('me-avg-gasto')) el('me-avg-gasto').textContent='$'+fmt(d.avg_gasto);
  if(el('me-max-eq')) el('me-max-eq').textContent=d.max_equipos;
  // Distribution bars
  var distEl=el('me-dist-bars');
  if(distEl&&d.distribucion){
    var maxV=Math.max.apply(null,d.distribucion.map(function(x){return x.fans;}));
    distEl.innerHTML=d.distribucion.map(function(x){
      return '<div class="brow" style="margin-bottom:8px"><div class="blabels"><div class="bteam">'+x.equipos+' equipos</div><div class="bpct" style="color:var(--accent)">'+fmtF(x.fans)+' fans</div></div><div class="btrack"><div class="bfill" style="width:'+(x.fans/maxV*100)+'%;background:var(--accent)"></div></div></div>';
    }).join('');
  }
  // Top combos
  var comboEl=el('me-combos');
  if(comboEl&&d.top_combos){
    var maxC=d.top_combos.length>0?d.top_combos[0].fans:1;
    comboEl.innerHTML=d.top_combos.slice(0,12).map(function(x){
      return '<div class="brow" style="margin-bottom:6px"><div class="blabels"><div class="bteam" style="font-size:11px">'+x.combo+'</div><div class="bpct" style="color:var(--gold)">'+fmtF(x.fans)+' fans</div></div><div class="btrack"><div class="bfill" style="width:'+(x.fans/maxC*100)+'%;background:var(--gold)"></div></div></div>';
    }).join('');
  }
  // Top fans table
  var topEl=el('me-top-fans');
  if(topEl&&d.top_fans){
    var medals=['🥇','🥈','🥉'];
    topEl.innerHTML='<table style="width:100%"><thead><tr><th>#</th><th>Fan</th><th>Equipos</th><th>Detalle Equipos</th><th>Gasto Total</th><th>Órdenes</th></tr></thead><tbody>'+
      d.top_fans.map(function(f,i){
        return '<tr><td>'+(i<3?medals[i]:(i+1))+'</td><td class="mono" style="font-size:11px">'+f.correo+'</td><td class="mono" style="color:var(--accent);font-weight:600">'+f.n_equipos+'</td><td style="font-size:11px">'+f.equipos.join(', ')+'</td><td class="mono" style="color:var(--gold)">$'+fmt(f.gasto)+'</td><td class="mono">'+fmtF(f.ordenes)+'</td></tr>';
      }).join('')+'</tbody></table>';
  }
  // Network: shared fans between team pairs
  var netEl=el('me-network');
  if(netEl&&d.network){
    var maxN=d.network.length>0?d.network[0].shared:1;
    netEl.innerHTML='<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px">'+
      d.network.slice(0,20).map(function(x){
        return '<div class="brow" style="margin-bottom:4px"><div class="blabels"><div class="bteam" style="font-size:11px">'+x.pair+'</div><div class="bpct" style="color:var(--accent)">'+fmtF(x.shared)+' fans</div></div><div class="btrack"><div class="bfill" style="width:'+(x.shared/maxN*100)+'%;background:var(--accent)"></div></div></div>';
      }).join('')+'</div>';
  }
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',loadMultiEquipo);}
else{loadMultiEquipo();}
'''
    # Insert before closing </script>
    html = html.replace('</script>\n</body>', MULTI_JS + '\n</script>\n</body>')
    print("✅ JS de Multi-Equipo inyectado")
else:
    print("⚠ JS Multi-Equipo ya existe")

# 4. Add 'multiequipo' to the show() nav ids
if "'multiequipo'" not in html:
    html = html.replace(
        "const ids = ['overview','equipos','asistencia','ventas','fans','outliers']",
        "const ids = ['overview','equipos','asistencia','ventas','fans','outliers','multiequipo']"
    )
    print("✅ multiequipo agregado a nav ids")

# Save
open(PATH, 'w').write(html)
print(f"\n✅ Parchado: {PATH}")
print("Haz: git add -A && git commit -m 'colores + multi-equipo' && git push")
