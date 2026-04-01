#!/usr/bin/env python3
"""
patch_fans.py
=============
Integra la sección mejorada de Fans al dashboard.
1. Agrega <script src="fans_detalle.js"> al HTML
2. Reemplaza el HTML de la sección fans con la nueva estructura
3. Conecta los botones de equipo a selFansDetEq

USO:
    cd ~/Desktop/LMB
    python3 patch_fans.py
"""

import os

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lmb_dashboard_v2.html')

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# ══ 1. REEMPLAZAR SECCIÓN FANS HTML ══
old_fans_start = '<!-- ══ FANS ══ -->'
old_fans_end = '<!-- ══ OUTLIERS ══ -->'

# Find the section
i_start = html.find(old_fans_start)
i_end = html.find(old_fans_end)

if i_start == -1 or i_end == -1:
    print("⚠ No encontré la sección FANS. ¿Ya se aplicó el patch?")
else:
    new_fans_html = '''<!-- ══ FANS ══ -->
<div id="fans" class="sec">
  <div class="shdr"><div class="stitle">Comportamiento Fans Online</div><div class="sdesc">Únicos por equipo · segmentación por frecuencia · solo boletos en línea</div></div>

  <!-- LIGA KPIs -->
  <div class="g5 mb">
    <div class="card"><div class="ctitle">Total Fans Online</div><div class="kv" id="fd-total">—</div><div class="kl">Usuarios únicos por correo</div></div>
    <div class="card"><div class="ctitle">Órdenes Online</div><div class="kv" style="color:var(--accent)" id="fd-ordenes">—</div><div class="kl">Total compras en línea</div></div>
    <div class="card"><div class="ctitle">Gasto Promedio</div><div class="kv" style="color:var(--gold)" id="fd-gasto-avg">—</div><div class="kl">Por fan online</div></div>
    <div class="card"><div class="ctitle">Van 1 sola vez</div><div class="kv" style="color:var(--cortesia)" id="fd-f1-pct">—</div><div class="kl">% del total online</div></div>
    <div class="card"><div class="ctitle">Recurrentes (2+)</div><div class="kv" style="color:var(--success)" id="fd-recurrentes">—</div><div class="kl">Fans que regresan</div></div>
  </div>

  <!-- EQUIPO SELECTOR -->
  <div class="frow mb">
    <span class="fl">Equipo:</span>
    <button class="fb active" onclick="selFansDetEq('Liga',this)">Liga</button>
    <button class="fb" onclick="selFansDetEq('Sultanes',this)">Sultanes</button>
    <button class="fb" onclick="selFansDetEq('Charros',this)">Charros</button>
    <button class="fb" onclick="selFansDetEq('Toros',this)">Toros</button>
    <button class="fb" onclick="selFansDetEq('Saraperos',this)">Saraperos</button>
    <button class="fb" onclick="selFansDetEq('Bravos',this)">Bravos</button>
    <button class="fb" onclick="selFansDetEq('Dorados',this)">Dorados</button>
    <button class="fb" onclick="selFansDetEq('Guerreros',this)">Guerreros</button>
    <button class="fb" onclick="selFansDetEq('Rieleros',this)">Rieleros</button>
    <button class="fb" onclick="selFansDetEq('Caliente',this)">Caliente</button>
    <button class="fb" onclick="selFansDetEq('Tecos',this)">Tecos</button>
  </div>

  <!-- CONTENIDO DINÁMICO -->
  <div id="fans-det-content"></div>

  <div class="nota">
    <span>ℹ</span>
    <span>Análisis basado exclusivamente en boletos comprados en línea con correo registrado. Fans de taquilla sin correo no están incluidos. La frecuencia es por partidos distintos (ID_EVENTO único) en la temporada 2025.</span>
  </div>
</div>

'''
    html = html[:i_start] + new_fans_html + html[i_end:]
    print('  ✓ Sección FANS HTML reemplazada')

# ══ 2. AGREGAR SCRIPT fans_detalle.js ANTES DE </body> ══
if 'fans_detalle.js' not in html:
    html = html.replace('</body>', '<script src="fans_detalle.js"></script>\n</body>')
    print('  ✓ Script fans_detalle.js agregado')
else:
    print('  ℹ Script fans_detalle.js ya estaba incluido')

# ══ 3. QUITAR LA VIEJA initFans() del BOOT ══
# La vieja función initFans puede quedarse, el nuevo JS la reemplaza
# Pero quitamos la llamada del boot para evitar conflictos
html = html.replace('initFans();', '// initFans(); // Reemplazado por fans_detalle.js')
print('  ✓ initFans() comentada en BOOT')

# ══ GUARDAR ══
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ Dashboard actualizado')
print('   Recarga Live Server con Cmd+Shift+R')
