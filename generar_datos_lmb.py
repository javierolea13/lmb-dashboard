#!/usr/bin/env python3
"""
generar_datos_lmb.py
====================
Lee los CSVs de Eventos y Órdenes de la temporada LMB 2025,
calcula todas las métricas y genera archivos JSON para el dashboard.

USO:
    cd ~/Desktop/LMB
    python3 generar_datos_lmb.py

REQUIERE:
    pip3 install pandas

ENTRADA:  data/csv/Eventos *.csv  +  data/csv/Ordenes *.csv
SALIDA:   data/stats.json, data/ventas.json, data/fans.json,
          data/outliers.json, data/juegos.json, data/juegos2.json
"""

import pandas as pd
import numpy as np
import json
import os
import re
import warnings
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN — ajusta estas rutas si cambian
# ══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'csv')
OUT_DIR = os.path.join(BASE_DIR, 'data')

EQUIPOS = ['Bravos','Caliente','Charros','Dorados','Guerreros',
           'Rieleros','Saraperos','Sultanes','Tecos','Toros']

# Aforos por equipo (máximo y promedio real)
AFOROS = {
    'Charros':    {'max': 14887, 'prom': 6949},
    'Bravos':     {'max': 6556,  'prom': 6400},
    'Dorados':    {'max': 14402, 'prom': 7879},
    'Guerreros':  {'max': 4800,  'prom': 4720},
    'Saraperos':  {'max': 12381, 'prom': 11578},
    'Rieleros':   {'max': 6954,  'prom': 5546},
    'Sultanes':   {'max': 26590, 'prom': 22749},
    'Caliente':   {'max': 6833,  'prom': 6833},
    'Toros':      {'max': 20947, 'prom': 16089},
    'Tecos':      {'max': 10718, 'prom': 7386},
}

ZONAS = {
    'Charros': 'Norte', 'Bravos': 'Sur', 'Dorados': 'Norte',
    'Guerreros': 'Sur', 'Saraperos': 'Norte', 'Rieleros': 'Norte',
    'Sultanes': 'Norte', 'Caliente': 'Norte', 'Toros': 'Norte',
    'Tecos': 'Norte',
}

DOBLE_ESTADIO = {'Tecos': True}

# Tipo × 17 para Tecos USD
TECOS_USD_FACTOR = 17

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def limpiar_dinero(val):
    """Convierte '$1,234.56' o '-' a float."""
    if pd.isna(val) or val == '-' or val == '':
        return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def es_cortesia(tipo, subtotal):
    """Clasifica si un boleto es cortesía."""
    if subtotal == 0:
        return True
    tipo_lower = str(tipo).lower()
    keywords = ['cortesi', 'canje', 'staff', 'direcci', 'mercadotecnia',
                'giveaway', 'comercial', 'deportivo', 'forms', 'gratis',
                'responsabilidad', 'convenio', 'pase', 'upgrade',
                'dama', 'ladies', 'compas', 'hombres', 'universitario',
                'ni\u00f1o', 'sector salud', 'escuelita', 'dia del']
    return any(kw in tipo_lower for kw in keywords)

def es_vendido(tipo):
    """Clasifica si un boleto es vendido."""
    tipo_lower = str(tipo).lower().strip()
    return tipo_lower in ['adulto', 'abonados', 'abonado', 'estudiante']

def clasificar_boleto(tipo, subtotal):
    """Retorna 'vendido', 'cortesia' o 'promocion'."""
    if es_cortesia(tipo, subtotal):
        return 'cortesia'
    if es_vendido(tipo):
        return 'vendido'
    # Check subtotal = 0 catch-all
    if subtotal == 0:
        return 'cortesia'
    return 'vendido'  # default: si paga algo y no es cortesía/promo conocida

def parse_fecha_evento(fecha_str):
    """Parsea fecha en formato DD/MM/YY o MM/DD/YY."""
    try:
        return pd.to_datetime(fecha_str, format='%d/%m/%y')
    except:
        try:
            return pd.to_datetime(fecha_str, format='%m/%d/%y')
        except:
            return pd.NaT


# ══════════════════════════════════════════════════════════════
# PASO 1: LEER EVENTOS
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("GENERADOR DE DATOS LMB 2025")
print("=" * 60)

all_eventos = []
for eq in EQUIPOS:
    path = os.path.join(CSV_DIR, f'Eventos {eq}.csv')
    if not os.path.exists(path):
        print(f"  ⚠ No encontrado: {path}")
        continue
    df = pd.read_csv(path, encoding='utf-8')
    # Normalizar nombres de columna
    df.columns = df.columns.str.strip()
    # Estandarizar orden de columnas
    if 'EVENTOS' not in df.columns and 'FECHA EVENTO' in df.columns:
        # Sultanes tiene FECHA EVENTO primero
        pass
    df['EQUIPO_NORM'] = eq
    all_eventos.append(df)
    print(f"  ✓ Eventos {eq}: {len(df)} registros")

eventos_df = pd.concat(all_eventos, ignore_index=True)
# Normalizar nombre de evento
if 'EVENTOS' in eventos_df.columns:
    eventos_df['EVENTO_NOMBRE'] = eventos_df['EVENTOS']
elif 'EVENTO' in eventos_df.columns:
    eventos_df['EVENTO_NOMBRE'] = eventos_df['EVENTO']

print(f"\n  Total eventos: {len(eventos_df)}")

# ══════════════════════════════════════════════════════════════
# PASO 2: LEER ÓRDENES
# ══════════════════════════════════════════════════════════════
print("\n📦 Leyendo órdenes...")

all_ordenes = []
for eq in EQUIPOS:
    path = os.path.join(CSV_DIR, f'Ordenes {eq} 25.csv')
    if not os.path.exists(path):
        print(f"  ⚠ No encontrado: {path}")
        continue
    print(f"  Leyendo {eq}...", end=' ', flush=True)
    df = pd.read_csv(path, encoding='utf-8', low_memory=False)
    df.columns = df.columns.str.strip()
    df['EQUIPO_NORM'] = eq
    
    # Limpiar valores monetarios
    for col in ['PRECIO', 'DESCUENTO', 'SUBTOTAL', 'COMISIÓN', 'TOTAL',
                'RECIBIDO', 'EFECTIVO', 'TARJETA', 'CRÉDITO', 'OTRO']:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_dinero)
    
    # Clasificar tipo de boleto
    df['CLASIFICACION'] = df.apply(
        lambda row: clasificar_boleto(row.get('TIPO', ''), row.get('SUBTOTAL', 0)),
        axis=1
    )
    
    all_ordenes.append(df)
    print(f"{len(df):,} órdenes")

ordenes_df = pd.concat(all_ordenes, ignore_index=True)
print(f"\n  Total órdenes: {len(ordenes_df):,}")

# ══════════════════════════════════════════════════════════════
# PASO 3: CALCULAR STATS (asistencia por equipo)
# ══════════════════════════════════════════════════════════════
print("\n📊 Calculando STATS...")

# Agrupar órdenes por equipo y evento para contar boletos
boletos_por_evento = ordenes_df.groupby(['EQUIPO_NORM', 'ID_EVENTO']).agg(
    boletos=('NÚMERO DE ORDEN', 'count'),
).reset_index()

# Merge con eventos para tener la info del evento
# (escaneados no están en los CSVs de órdenes, se calculan por proxy)

stats_list = []
for eq in EQUIPOS:
    af = AFOROS[eq]
    zona = ZONAS[eq]
    
    eq_eventos = eventos_df[eventos_df['EQUIPO_NORM'] == eq]
    eq_ordenes = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    
    # Boletos por evento
    bp_ev = eq_ordenes.groupby('ID_EVENTO').agg(
        boletos=('NÚMERO DE ORDEN', 'count')
    ).reset_index()
    
    total_juegos = len(eq_eventos)
    
    # Para asistencia usamos boletos como proxy (escaneados no disponibles en CSV)
    # Detectar outliers con IQR
    if len(bp_ev) > 0:
        Q1 = bp_ev['boletos'].quantile(0.25)
        Q3 = bp_ev['boletos'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        outlier_mask = (bp_ev['boletos'] < lower) | (bp_ev['boletos'] > upper)
        n_outliers = outlier_mask.sum()
        
        normal = bp_ev[~outlier_mask]
        juegos_normales = len(normal)
        total_asistencia = int(normal['boletos'].sum())
        avg_asistencia = int(normal['boletos'].mean()) if len(normal) > 0 else 0
    else:
        n_outliers = 0
        juegos_normales = total_juegos
        total_asistencia = 0
        avg_asistencia = 0
    
    ocup_max = round(avg_asistencia / af['max'] * 100, 1) if af['max'] > 0 else 0
    ocup_prom = round(avg_asistencia / af['prom'] * 100, 1) if af['prom'] > 0 else 0
    
    nota = ""
    if eq == 'Sultanes':
        nota = "Sultanes emite masivamente cortesías/abonos (hasta 105k boletos/juego vs aforo de 22k). Datos de boletos excluidos; se usa aforo como referencia."
    
    stats_list.append({
        'equipo': eq,
        'zona': zona,
        'aforo_max': af['max'],
        'aforo_prom': af['prom'],
        'juegos': total_juegos,
        'juegos_normales': juegos_normales,
        'outliers': int(n_outliers),
        'avg_asistencia': avg_asistencia,
        'total_asistencia': total_asistencia,
        'ocup_aforo_max': ocup_max,
        'ocup_aforo_prom': ocup_prom,
        'nota': nota,
        'doble_estadio': DOBLE_ESTADIO.get(eq, False),
    })
    print(f"  {eq}: {juegos_normales} juegos, avg={avg_asistencia:,}, outliers={n_outliers}")


# ══════════════════════════════════════════════════════════════
# PASO 4: CALCULAR VENTAS
# ══════════════════════════════════════════════════════════════
print("\n💰 Calculando VENTAS...")

ventas_dict = {}
for eq in EQUIPOS:
    eq_ord = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    
    total_boletos = len(eq_ord)
    vendidos = len(eq_ord[eq_ord['CLASIFICACION'] == 'vendido'])
    promociones = len(eq_ord[eq_ord['CLASIFICACION'] == 'promocion'])
    cortesias = len(eq_ord[eq_ord['CLASIFICACION'] == 'cortesia'])
    
    ingreso_total = eq_ord['SUBTOTAL'].sum()
    ingreso_vendidos = eq_ord[eq_ord['CLASIFICACION'] == 'vendido']['SUBTOTAL'].sum()
    ingreso_promociones = eq_ord[eq_ord['CLASIFICACION'] == 'promocion']['SUBTOTAL'].sum()
    
    # Online vs Taquilla
    online_mask = eq_ord['MEDIO DE COMPRA'].str.strip().ne('Taquilla')
    online = int(online_mask.sum())
    taquilla = total_boletos - online
    
    ingreso_online = eq_ord[online_mask]['SUBTOTAL'].sum()
    ingreso_taquilla = ingreso_total - ingreso_online
    
    # Fans únicos online (por correo)
    online_orders = eq_ord[online_mask]
    correos = online_orders['CORREO USUARIO'].dropna()
    correos = correos[correos != '-']
    correos = correos[correos != '']
    fans_unicos = correos.nunique()
    
    # Frecuencia de fans online
    if fans_unicos > 0:
        fan_eventos = online_orders[online_orders['CORREO USUARIO'].isin(correos.unique())]
        fan_freq = fan_eventos.groupby('CORREO USUARIO')['ID_EVENTO'].nunique()
        f1 = int((fan_freq == 1).sum())
        f25 = int(((fan_freq >= 2) & (fan_freq <= 5)).sum())
        f610 = int(((fan_freq >= 6) & (fan_freq <= 10)).sum())
        f10plus = int((fan_freq > 10).sum())
    else:
        f1, f25, f610, f10plus = 0, 0, 0, 0
    
    # Zonas (top 8 por ingreso)
    if 'ZONA' in eq_ord.columns:
        zonas = eq_ord.groupby('ZONA').agg(
            boletos=('NÚMERO DE ORDEN', 'count'),
            ingreso=('SUBTOTAL', 'sum')
        ).sort_values('ingreso', ascending=False).head(8).reset_index()
        zonas_list = zonas.to_dict('records')
    else:
        zonas_list = []
    
    # Tipos de cortesía (top 8)
    cortesia_orders = eq_ord[eq_ord['CLASIFICACION'] == 'cortesia']
    if len(cortesia_orders) > 0:
        tipo_cort = cortesia_orders.groupby('TIPO').size().sort_values(ascending=False).head(8)
        tipo_cortesia = tipo_cort.to_dict()
    else:
        tipo_cortesia = {}
    
    pct_vendido = round(vendidos / total_boletos * 100, 1) if total_boletos > 0 else 0
    pct_promocion = round(promociones / total_boletos * 100, 1) if total_boletos > 0 else 0
    pct_cortesia = round(cortesias / total_boletos * 100, 1) if total_boletos > 0 else 0
    
    ventas_dict[eq] = {
        'equipo': eq,
        'total_boletos': total_boletos,
        'vendidos': vendidos,
        'promociones': promociones,
        'cortesias': cortesias,
        'ingreso_total': round(ingreso_total, 2),
        'ingreso_vendidos': round(ingreso_vendidos, 2),
        'ingreso_promociones': round(ingreso_promociones, 2),
        'ingreso_online': round(ingreso_online, 2),
        'ingreso_taquilla': round(ingreso_taquilla, 2),
        'online': online,
        'taquilla': taquilla,
        'fans_unicos_online': fans_unicos,
        'frecuencia': {
            '1 juego': f1,
            '2-5 juegos': f25,
            '6-10 juegos': f610,
            '+10 juegos': f10plus,
        },
        'zonas': zonas_list,
        'tipo_cortesia': tipo_cortesia,
        'pct_vendido': pct_vendido,
        'pct_promocion': pct_promocion,
        'pct_cortesia': pct_cortesia,
    }
    print(f"  {eq}: {total_boletos:,} boletos, ${ingreso_total:,.0f}")


# ══════════════════════════════════════════════════════════════
# PASO 5: CALCULAR FANS
# ══════════════════════════════════════════════════════════════
print("\n👥 Calculando FANS...")

fans_dict = {}
for eq in EQUIPOS:
    eq_ord = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    online_mask = eq_ord['MEDIO DE COMPRA'].str.strip().ne('Taquilla')
    online_orders = eq_ord[online_mask]
    
    correos = online_orders['CORREO USUARIO'].dropna()
    correos = correos[(correos != '-') & (correos != '')]
    
    if correos.nunique() == 0:
        fans_dict[eq] = {
            'total_fans_online': 0,
            'freq': {'1': 0, '2-5': 0, '6-10': 0, '+10': 0},
            'rev_por_cat': {'+10': 0, '1': 0, '2-5': 0, '6-10': 0},
            'avg_gasto': 0,
        }
        continue
    
    fan_data = online_orders[online_orders['CORREO USUARIO'].isin(correos.unique())]
    
    # Frecuencia por correo
    fan_freq = fan_data.groupby('CORREO USUARIO')['ID_EVENTO'].nunique()
    fan_gasto = fan_data.groupby('CORREO USUARIO')['SUBTOTAL'].sum()
    
    total_fans = correos.nunique()
    f1 = int((fan_freq == 1).sum())
    f25 = int(((fan_freq >= 2) & (fan_freq <= 5)).sum())
    f610 = int(((fan_freq >= 6) & (fan_freq <= 10)).sum())
    f10plus = int((fan_freq > 10).sum())
    
    # Revenue por categoría
    def cat_rev(freq_series, gasto_series, low, high=None):
        if high:
            mask = (freq_series >= low) & (freq_series <= high)
        else:
            mask = freq_series >= low if low > 1 else freq_series == low
        users = freq_series[mask].index
        return round(gasto_series[gasto_series.index.isin(users)].sum(), 2)
    
    rev_1 = cat_rev(fan_freq, fan_gasto, 1)
    rev_25 = cat_rev(fan_freq, fan_gasto, 2, 5)
    rev_610 = cat_rev(fan_freq, fan_gasto, 6, 10)
    rev_10 = cat_rev(fan_freq, fan_gasto, 11)  # > 10
    
    avg_gasto = int(fan_gasto.mean()) if len(fan_gasto) > 0 else 0
    
    fans_dict[eq] = {
        'total_fans_online': total_fans,
        'freq': {'1': f1, '2-5': f25, '6-10': f610, '+10': f10plus},
        'rev_por_cat': {'+10': rev_10, '1': rev_1, '2-5': rev_25, '6-10': rev_610},
        'avg_gasto': avg_gasto,
    }
    print(f"  {eq}: {total_fans:,} fans online, avg=${avg_gasto:,}")


# ══════════════════════════════════════════════════════════════
# PASO 6: OUTLIERS
# ══════════════════════════════════════════════════════════════
print("\n⚠ Detectando OUTLIERS...")

outliers_list = []
for eq in EQUIPOS:
    eq_ord = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    eq_ev = eventos_df[eventos_df['EQUIPO_NORM'] == eq]
    
    bp_ev = eq_ord.groupby('ID_EVENTO').agg(
        boletos=('NÚMERO DE ORDEN', 'count')
    ).reset_index()
    
    if len(bp_ev) < 4:
        continue
    
    Q1 = bp_ev['boletos'].quantile(0.25)
    Q3 = bp_ev['boletos'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    
    outlier_events = bp_ev[(bp_ev['boletos'] < lower) | (bp_ev['boletos'] > upper)]
    
    for _, row in outlier_events.iterrows():
        ev_id = row['ID_EVENTO']
        boletos = int(row['boletos'])
        
        # Buscar info del evento
        ev_info = eq_ev[eq_ev['ID_EVENTO'] == ev_id]
        if len(ev_info) > 0:
            ev_row = ev_info.iloc[0]
            evento_nombre = ev_row.get('EVENTOS', ev_row.get('EVENTO_NOMBRE', f'Evento {ev_id}'))
            fecha = str(ev_row.get('FECHA EVENTO', ''))
        else:
            evento_nombre = f'Evento {ev_id}'
            fecha = ''
        
        if boletos > upper:
            reason = f"Asistencia atípicamente alta ({boletos:,})"
        else:
            reason = f"Asistencia atípicamente baja ({boletos:,})"
        
        outliers_list.append({
            'EQUIPO': eq,
            'EVENTOS': str(evento_nombre),
            'FECHA EVENTO': fecha,
            'Boletos': boletos,
            'Escaneados': 0,  # No disponible en CSVs
            'outlier_reason': reason,
        })

print(f"  Total outliers: {len(outliers_list)}")


# ══════════════════════════════════════════════════════════════
# PASO 7: JUEGOS (top partidos por asistencia)
# ══════════════════════════════════════════════════════════════
print("\n🏟 Generando JUEGOS (top partidos)...")

juegos_dict = {}
for eq in EQUIPOS:
    eq_ord = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    eq_ev = eventos_df[eventos_df['EQUIPO_NORM'] == eq]
    
    bp_ev = eq_ord.groupby('ID_EVENTO').agg(
        boletos=('NÚMERO DE ORDEN', 'count')
    ).reset_index()
    
    bp_ev = bp_ev.sort_values('boletos', ascending=False).head(10)
    
    games = []
    for _, row in bp_ev.iterrows():
        ev_id = row['ID_EVENTO']
        ev_info = eq_ev[eq_ev['ID_EVENTO'] == ev_id]
        if len(ev_info) > 0:
            ev_row = ev_info.iloc[0]
            nombre = str(ev_row.get('EVENTOS', ev_row.get('EVENTO_NOMBRE', f'Evento {ev_id}')))
            fecha_raw = str(ev_row.get('FECHA EVENTO', ''))
            categoria = str(ev_row.get('CATEGORIA', 'TR'))
            # Parse fecha
            dt = parse_fecha_evento(fecha_raw)
            fecha = dt.strftime('%Y-%m-%d') if pd.notna(dt) else fecha_raw
        else:
            nombre = f'Evento {ev_id}'
            fecha = ''
            categoria = 'TR'
        
        games.append({
            'n': nombre,
            'f': fecha,
            'e': 0,  # escaneados no disponible
            'b': int(row['boletos']),
            'o': 0,  # ocupación — requiere escaneados
            'c': categoria,
        })
    
    juegos_dict[eq] = games
    print(f"  {eq}: {len(games)} top juegos")


# ══════════════════════════════════════════════════════════════
# PASO 8: JUEGOS2 (top partidos por ingreso)
# ══════════════════════════════════════════════════════════════
print("\n💵 Generando JUEGOS2 (top partidos por ingreso)...")

juegos2_dict = {}
for eq in EQUIPOS:
    eq_ord = ordenes_df[ordenes_df['EQUIPO_NORM'] == eq]
    eq_ev = eventos_df[eventos_df['EQUIPO_NORM'] == eq]
    
    online_mask = eq_ord['MEDIO DE COMPRA'].str.strip().ne('Taquilla')
    
    ing_ev = eq_ord.groupby('ID_EVENTO').agg(
        ing=('SUBTOTAL', 'sum'),
    ).reset_index()
    
    ing_onl = eq_ord[online_mask].groupby('ID_EVENTO')['SUBTOTAL'].sum().reset_index()
    ing_onl.columns = ['ID_EVENTO', 'ing_onl']
    
    ing_ev = ing_ev.merge(ing_onl, on='ID_EVENTO', how='left')
    ing_ev['ing_onl'] = ing_ev['ing_onl'].fillna(0)
    ing_ev['ing_taq'] = ing_ev['ing'] - ing_ev['ing_onl']
    
    ing_ev = ing_ev.sort_values('ing', ascending=False).head(20)
    
    games = []
    for _, row in ing_ev.iterrows():
        ev_id = row['ID_EVENTO']
        ev_info = eq_ev[eq_ev['ID_EVENTO'] == ev_id]
        if len(ev_info) > 0:
            ev_row = ev_info.iloc[0]
            nombre = str(ev_row.get('EVENTOS', ev_row.get('EVENTO_NOMBRE', f'Evento {ev_id}')))
            fecha_raw = str(ev_row.get('FECHA EVENTO', ''))
            categoria = str(ev_row.get('CATEGORIA', 'TR'))
            dt = parse_fecha_evento(fecha_raw)
            fecha = dt.strftime('%Y-%m-%d') if pd.notna(dt) else fecha_raw
        else:
            nombre = f'Evento {ev_id}'
            fecha = ''
            categoria = 'TR'
        
        games.append({
            'n': nombre,
            'f': fecha,
            'id': int(ev_id),
            'ing': round(row['ing'], 0),
            'ing_onl': round(row['ing_onl'], 0),
            'ing_taq': round(row['ing_taq'], 0),
            'c': categoria,
        })
    
    juegos2_dict[eq] = games
    print(f"  {eq}: {len(games)} juegos")


# ══════════════════════════════════════════════════════════════
# PASO 9: GUARDAR JSONs
# ══════════════════════════════════════════════════════════════
print("\n💾 Guardando archivos JSON...")

os.makedirs(OUT_DIR, exist_ok=True)

def save_json(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(path)
    print(f"  ✓ {filename} ({size:,} bytes)")

save_json(stats_list, 'stats.json')
save_json(ventas_dict, 'ventas.json')
save_json(fans_dict, 'fans.json')
save_json(outliers_list, 'outliers.json')
save_json(juegos_dict, 'juegos.json')
save_json(juegos2_dict, 'juegos2.json')

print("\n" + "=" * 60)
print("✅ LISTO — Archivos generados en:", OUT_DIR)
print("=" * 60)
print("\nPróximos pasos:")
print("  1. Revisa los JSONs en data/")
print("  2. Haz push a GitHub:")
print("     cd ~/Desktop/LMB")
print("     git add data/*.json")
print('     git commit -m "Actualizar datos LMB"')
print("     git push")
print("  3. El dashboard leerá estos archivos automáticamente")
