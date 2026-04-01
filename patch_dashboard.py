#!/usr/bin/env python3
"""
patch_dashboard.py
==================
Modifica lmb_dashboard_v2.html para que cargue datos desde JSONs
en vez de tenerlos hardcodeados.

USO:
    cd ~/Desktop/LMB
    python3 patch_dashboard.py
"""

import re
import os

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lmb_dashboard_v2.html')

with open(FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# ── CAMBIO 1: Reemplazar datos hardcodeados por variables ──
# Buscar desde "// ══ DATOS LMB 2025" hasta el fin de "const FANS = {...};"
pattern1 = r'// ══ DATOS LMB 2025[^\n]*\n.*?const FANS = \{[^}]*(\{[^}]*\}[^}]*)*\};\s*'
replacement1 = '''// ══ DATOS LMB 2025 — Cargados desde JSON ══
let STATS, OUTLIERS, VENTAS, JUEGOS, JUEGOS2, FANS;

'''

# Approach más seguro: buscar las líneas exactas
lines = html.split('\n')
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if '// ══ DATOS LMB 2025' in line:
        start_idx = i
    if start_idx and line.strip().startswith('const FANS = {'):
        # Encontrar el fin de esta línea (el }; al final)
        end_idx = i
        break

if start_idx is not None and end_idx is not None:
    # Reemplazar las líneas de datos
    new_lines = lines[:start_idx]
    new_lines.append('// ══ DATOS LMB 2025 — Cargados desde JSON ══')
    new_lines.append('let STATS, OUTLIERS, VENTAS, JUEGOS, JUEGOS2, FANS;')
    new_lines.append('')
    new_lines.extend(lines[end_idx + 1:])
    html = '\n'.join(new_lines)
    print(f'  ✓ Cambio 1: Reemplazadas líneas {start_idx+1}-{end_idx+1} (datos hardcodeados → variables)')
else:
    print('  ⚠ No encontré los datos hardcodeados. ¿Ya se aplicó el cambio?')

# ── CAMBIO 2: Reemplazar BOOT por loader async ──
old_boot = """// ── BOOT ──
// Inicializar dashboard
initOverview();
initEquipos();
initOutliers();
initFans();"""

new_boot = """// ── BOOT ── Cargar JSONs y luego inicializar
async function loadDashboard() {
  try {
    const [statsR, ventasR, fansR, outliersR, juegosR, juegos2R] = await Promise.all([
      fetch('data/stats.json'),
      fetch('data/ventas.json'),
      fetch('data/fans.json'),
      fetch('data/outliers.json'),
      fetch('data/juegos.json'),
      fetch('data/juegos2.json'),
    ]);
    STATS = await statsR.json();
    VENTAS = await ventasR.json();
    FANS = await fansR.json();
    OUTLIERS = await outliersR.json();
    JUEGOS = await juegosR.json();
    JUEGOS2 = await juegos2R.json();

    initOverview();
    initEquipos();
    initOutliers();
    initFans();
    console.log('✅ Dashboard cargado desde JSONs');
  } catch(err) {
    console.error('❌ Error cargando datos:', err);
    document.querySelector('.main').innerHTML = '<div style="color:#ff5252;padding:40px;text-align:center;font-size:16px">Error cargando datos. Verifica que los archivos JSON estén en data/</div>';
  }
}
loadDashboard();"""

if old_boot in html:
    html = html.replace(old_boot, new_boot)
    print('  ✓ Cambio 2: BOOT reemplazado por loader async')
else:
    print('  ⚠ No encontré el bloque BOOT original. ¿Ya se aplicó?')

# ── GUARDAR ──
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ Archivo actualizado: {FILE}')
print('   Abre Live Server y revisa la consola del navegador (Cmd+Option+J)')
print('   Deberías ver: "✅ Dashboard cargado desde JSONs"')
