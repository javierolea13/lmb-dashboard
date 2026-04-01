#!/usr/bin/env python3
"""
generar_fans_detalle.py
=======================
Genera fans_detalle.json con métricas enriquecidas por equipo:
- Segmentación por frecuencia con gasto
- Distribución por plataforma (iOS, Android, Web, Desktop)
- Top 10 fans por gasto
- Distribución por método de pago
- Compras por día de la semana y hora

USO:
    cd ~/Desktop/LMB
    python3 generar_fans_detalle.py
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, 'data', 'csv')
OUT_DIR = os.path.join(BASE_DIR, 'data')

EQUIPOS = ['Bravos','Caliente','Charros','Dorados','Guerreros',
           'Rieleros','Saraperos','Sultanes','Tecos','Toros']

def limpiar_dinero(val):
    if pd.isna(val) or val == '-' or val == '':
        return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def clasificar_plataforma(medio):
    """Clasifica el medio de compra en plataforma."""
    m = str(medio).lower()
    if 'ios' in m or 'iphone' in m:
        return 'iOS'
    elif 'android' in m:
        return 'Android'
    elif 'mobile' in m:
        return 'Web Mobile'
    elif 'desktop' in m:
        return 'Web Desktop'
    elif 'taquilla' in m:
        return 'Taquilla'
    else:
        return 'Otro'

print("=" * 60)
print("GENERADOR DE FANS DETALLE")
print("=" * 60)

fans_detalle = {}

for eq in EQUIPOS:
    path = os.path.join(CSV_DIR, f'Ordenes {eq} 25.csv')
    if not os.path.exists(path):
        print(f"  ⚠ No encontrado: {path}")
        continue
    
    print(f"\n📊 Procesando {eq}...", flush=True)
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    
    # Limpiar dinero
    df['SUBTOTAL'] = df['SUBTOTAL'].apply(limpiar_dinero)
    
    # Separar online
    df['es_online'] = df['MEDIO DE COMPRA'].str.strip() != 'Taquilla'
    online = df[df['es_online']].copy()
    
    # Filtrar correos válidos
    online = online[online['CORREO USUARIO'].notna()]
    online = online[~online['CORREO USUARIO'].isin(['-', '', ' '])]
    
    if len(online) == 0:
        print(f"  ⚠ Sin datos online para {eq}")
        continue
    
    # Clasificar plataforma
    online['plataforma'] = online['MEDIO DE COMPRA'].apply(clasificar_plataforma)
    
    # ── MÉTRICAS POR FAN ──
    fan_stats = online.groupby('CORREO USUARIO').agg(
        eventos_distintos=('ID_EVENTO', 'nunique'),
        total_ordenes=('NÚMERO DE ORDEN', 'count'),
        gasto_total=('SUBTOTAL', 'sum'),
        plataforma_principal=('plataforma', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Otro'),
    ).reset_index()
    
    total_fans = len(fan_stats)
    
    # ── SEGMENTACIÓN POR FRECUENCIA ──
    def freq_cat(n):
        if n == 1: return '1'
        elif n <= 5: return '2-5'
        elif n <= 10: return '6-10'
        else: return '+10'
    
    fan_stats['freq_cat'] = fan_stats['eventos_distintos'].apply(freq_cat)
    
    freq_data = {}
    for cat in ['1', '2-5', '6-10', '+10']:
        subset = fan_stats[fan_stats['freq_cat'] == cat]
        freq_data[cat] = {
            'fans': int(len(subset)),
            'pct': round(len(subset) / total_fans * 100, 1) if total_fans > 0 else 0,
            'gasto_total': round(float(subset['gasto_total'].sum()), 2),
            'gasto_promedio': round(float(subset['gasto_total'].mean()), 2) if len(subset) > 0 else 0,
            'ordenes': int(subset['total_ordenes'].sum()),
        }
    
    # ── PLATAFORMAS ──
    plat_counts = online.groupby('plataforma').agg(
        ordenes=('NÚMERO DE ORDEN', 'count'),
        ingreso=('SUBTOTAL', 'sum'),
        fans_unicos=('CORREO USUARIO', 'nunique'),
    ).sort_values('ordenes', ascending=False).reset_index()
    
    plataformas = []
    for _, row in plat_counts.iterrows():
        plataformas.append({
            'nombre': row['plataforma'],
            'ordenes': int(row['ordenes']),
            'pct_ordenes': round(row['ordenes'] / len(online) * 100, 1),
            'ingreso': round(float(row['ingreso']), 2),
            'fans_unicos': int(row['fans_unicos']),
        })
    
    # ── TOP 10 FANS POR GASTO ──
    top_fans = fan_stats.nlargest(10, 'gasto_total')
    top_fans_list = []
    for _, fan in top_fans.iterrows():
        # Anonimizar correo: mostrar primeros 3 chars + ***@dominio
        correo = fan['CORREO USUARIO']
        parts = correo.split('@')
        if len(parts) == 2:
            correo_anon = parts[0][:3] + '***@' + parts[1]
        else:
            correo_anon = correo[:3] + '***'
        
        top_fans_list.append({
            'correo': correo_anon,
            'eventos': int(fan['eventos_distintos']),
            'ordenes': int(fan['total_ordenes']),
            'gasto': round(float(fan['gasto_total']), 2),
            'plataforma': fan['plataforma_principal'],
        })
    
    # ── COMPRAS POR DÍA DE SEMANA ──
    if 'FECHA' in online.columns:
        online_copy = online.copy()
        online_copy['fecha_dt'] = pd.to_datetime(online_copy['FECHA'], format='%d/%m/%y', errors='coerce')
        valid_dates = online_copy[online_copy['fecha_dt'].notna()]
        if len(valid_dates) > 0:
            dias = valid_dates['fecha_dt'].dt.dayofweek  # 0=Lunes
            dias_nombres = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            dia_counts = dias.value_counts().sort_index()
            compras_por_dia = {dias_nombres[i]: int(dia_counts.get(i, 0)) for i in range(7)}
        else:
            compras_por_dia = {}
    else:
        compras_por_dia = {}
    
    # ── COMPRAS POR HORA ──
    if 'HORA' in online.columns:
        horas = online['HORA'].dropna()
        horas = horas[horas != '-']
        if len(horas) > 0:
            # Extraer hora del formato HH:MM
            hora_num = horas.str.split(':').str[0].astype(int, errors='ignore')
            if hasattr(hora_num, 'value_counts'):
                hora_counts = hora_num.value_counts().sort_index()
                compras_por_hora = {str(int(h)): int(c) for h, c in hora_counts.items() if pd.notna(h)}
            else:
                compras_por_hora = {}
        else:
            compras_por_hora = {}
    else:
        compras_por_hora = {}
    
    # ── MÉTODO DE PAGO ──
    if 'MÉTODO DE PAGO' in online.columns:
        metodo = online['MÉTODO DE PAGO'].fillna('Otro').replace('-', 'Otro')
        metodo_counts = metodo.value_counts().head(6)
        metodos_pago = {str(k): int(v) for k, v in metodo_counts.items()}
    else:
        metodos_pago = {}
    
    # ── GASTO PROMEDIO GENERAL ──
    avg_gasto = round(float(fan_stats['gasto_total'].mean()), 2) if total_fans > 0 else 0
    median_gasto = round(float(fan_stats['gasto_total'].median()), 2) if total_fans > 0 else 0
    
    # ── ENSAMBLAR ──
    fans_detalle[eq] = {
        'total_fans_online': total_fans,
        'total_ordenes_online': int(len(online)),
        'avg_gasto': avg_gasto,
        'median_gasto': median_gasto,
        'frecuencia': freq_data,
        'plataformas': plataformas,
        'top_fans': top_fans_list,
        'compras_por_dia': compras_por_dia,
        'compras_por_hora': compras_por_hora,
        'metodos_pago': metodos_pago,
    }
    
    print(f"  ✓ {eq}: {total_fans:,} fans, avg=${avg_gasto:,.0f}, {len(plataformas)} plataformas")

# ── GUARDAR ──
out_path = os.path.join(OUT_DIR, 'fans_detalle.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(fans_detalle, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"✅ Archivo generado: {out_path}")
print(f"   Tamaño: {os.path.getsize(out_path):,} bytes")
print(f"{'='*60}")
print("\nPush a GitHub:")
print("  git add data/fans_detalle.json")
print('  git commit -m "Agregar fans detalle"')
print("  git push")
