#!/usr/bin/env python3
"""
generar_fans_detalle.py
=======================
Genera fans_detalle.json + fans_multiequipo.json
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
    m = str(medio).lower()
    if 'ios' in m or 'iphone' in m: return 'iOS'
    elif 'android' in m: return 'Android'
    elif 'mobile' in m: return 'Web Mobile'
    elif 'desktop' in m: return 'Web Desktop'
    elif 'taquilla' in m: return 'Taquilla'
    else: return 'Otro'

print("=" * 60)
print("GENERADOR DE FANS DETALLE")
print("=" * 60)

fans_detalle = {}
for eq in EQUIPOS:
    path = os.path.join(CSV_DIR, f'Ordenes {eq} 25.csv')
    if not os.path.exists(path):
        print(f"  No encontrado: {path}"); continue
    print(f"\n Procesando {eq}...", flush=True)
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['SUBTOTAL'] = df['SUBTOTAL'].apply(limpiar_dinero)
    df['es_online'] = df['MEDIO DE COMPRA'].str.strip() != 'Taquilla'
    online = df[df['es_online']].copy()
    online = online[online['CORREO USUARIO'].notna()]
    online = online[~online['CORREO USUARIO'].isin(['-', '', ' '])]
    if len(online) == 0: continue
    online['plataforma'] = online['MEDIO DE COMPRA'].apply(clasificar_plataforma)
    fan_stats = online.groupby('CORREO USUARIO').agg(
        eventos_distintos=('ID_EVENTO', 'nunique'),
        total_ordenes=('NUMERO DE ORDEN', 'count') if 'NUMERO DE ORDEN' in online.columns else ('SUBTOTAL', 'count'),
        gasto_total=('SUBTOTAL', 'sum'),
        plataforma_principal=('plataforma', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Otro'),
    ).reset_index()
    total_fans = len(fan_stats)
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
            'ordenes': int(subset['total_ordenes'].sum()) if 'total_ordenes' in subset.columns else 0,
        }
    plat_counts = online.groupby('plataforma').agg(ordenes=('SUBTOTAL', 'count'),ingreso=('SUBTOTAL', 'sum'),fans_unicos=('CORREO USUARIO', 'nunique')).sort_values('ordenes', ascending=False).reset_index()
    plataformas = [{'nombre': r['plataforma'],'ordenes': int(r['ordenes']),'pct_ordenes': round(r['ordenes'] / len(online) * 100, 1),'ingreso': round(float(r['ingreso']), 2),'fans_unicos': int(r['fans_unicos'])} for _, r in plat_counts.iterrows()]
    top_fans = fan_stats.nlargest(10, 'gasto_total')
    top_fans_list = []
    for _, fan in top_fans.iterrows():
        correo = fan['CORREO USUARIO']
        parts = correo.split('@')
        correo_anon = (parts[0][:3] + '***@' + parts[1]) if len(parts) == 2 else correo[:3] + '***'
        top_fans_list.append({'correo': correo_anon,'eventos': int(fan['eventos_distintos']),'ordenes': int(fan.get('total_ordenes', 0)),'gasto': round(float(fan['gasto_total']), 2),'plataforma': fan['plataforma_principal']})
    compras_por_dia = {}
    if 'FECHA' in online.columns:
        oc = online.copy()
        oc['fecha_dt'] = pd.to_datetime(oc['FECHA'], format='%d/%m/%y', errors='coerce')
        vd = oc[oc['fecha_dt'].notna()]
        if len(vd) > 0:
            dias_nombres = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
            dc = vd['fecha_dt'].dt.dayofweek.value_counts().sort_index()
            compras_por_dia = {dias_nombres[i]: int(dc.get(i, 0)) for i in range(7)}
    compras_por_hora = {}
    if 'HORA' in online.columns:
        horas = online['HORA'].dropna()
        horas = horas[horas != '-']
        if len(horas) > 0:
            hora_num = horas.str.split(':').str[0].astype(int, errors='ignore')
            if hasattr(hora_num, 'value_counts'):
                hc = hora_num.value_counts().sort_index()
                compras_por_hora = {str(int(h)): int(c) for h, c in hc.items() if pd.notna(h)}
    metodos_pago = {}
    if 'METODO DE PAGO' in online.columns or 'MÉTODO DE PAGO' in online.columns:
        col = 'MÉTODO DE PAGO' if 'MÉTODO DE PAGO' in online.columns else 'METODO DE PAGO'
        metodo = online[col].fillna('Otro').replace('-', 'Otro')
        mc = metodo.value_counts().head(6)
        metodos_pago = {str(k): int(v) for k, v in mc.items()}
    avg_gasto = round(float(fan_stats['gasto_total'].mean()), 2) if total_fans > 0 else 0
    median_gasto = round(float(fan_stats['gasto_total'].median()), 2) if total_fans > 0 else 0
    fans_detalle[eq] = {
        'total_fans_online': total_fans,'total_ordenes_online': int(len(online)),
        'avg_gasto': avg_gasto,'median_gasto': median_gasto,
        'frecuencia': freq_data,'plataformas': plataformas,'top_fans': top_fans_list,
        'compras_por_dia': compras_por_dia,'compras_por_hora': compras_por_hora,'metodos_pago': metodos_pago,
    }
    print(f"  {eq}: {total_fans:,} fans, avg=${avg_gasto:,.0f}")

out_path = os.path.join(OUT_DIR, 'fans_detalle.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(fans_detalle, f, ensure_ascii=False, indent=2)
print(f"\nfans_detalle.json: {os.path.getsize(out_path):,} bytes")

print(f"\nAnalizando fans multi-equipo...")
all_fan_data = {}
for eq in EQUIPOS:
    path = os.path.join(CSV_DIR, f'Ordenes {eq} 25.csv')
    if not os.path.exists(path): continue
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()
    df['SUBTOTAL'] = df['SUBTOTAL'].apply(limpiar_dinero)
    online = df[df['MEDIO DE COMPRA'].str.strip() != 'Taquilla'].copy()
    online = online[online['CORREO USUARIO'].notna()]
    online = online[~online['CORREO USUARIO'].isin(['-', '', ' '])]
    for _, row in online.iterrows():
        correo = str(row['CORREO USUARIO']).strip().lower()
        if correo not in all_fan_data:
            all_fan_data[correo] = {'equipos': set(), 'gasto': 0.0, 'ordenes': 0}
        all_fan_data[correo]['equipos'].add(eq)
        all_fan_data[correo]['gasto'] += row.get('SUBTOTAL', 0)
        all_fan_data[correo]['ordenes'] += 1

multi_fans = {c: d for c, d in all_fan_data.items() if len(d['equipos']) >= 2}
print(f"  Total correos: {len(all_fan_data):,}, Multi-equipo: {len(multi_fans):,}")

if len(multi_fans) > 0:
    from collections import Counter
    from itertools import combinations
    eq_counts = Counter(len(d['equipos']) for d in multi_fans.values())
    distribucion = [{'equipos': k, 'fans': v} for k, v in sorted(eq_counts.items())]
    combo_counter = Counter()
    for d in multi_fans.values():
        eqs = sorted(d['equipos'])
        for i in range(len(eqs)):
            for j in range(i+1, len(eqs)):
                combo_counter[eqs[i] + ' + ' + eqs[j]] += 1
    top_combos = [{'combo': k, 'fans': v} for k, v in combo_counter.most_common(15)]
    network = []
    for eq1, eq2 in combinations(EQUIPOS, 2):
        shared = sum(1 for d in multi_fans.values() if eq1 in d['equipos'] and eq2 in d['equipos'])
        if shared > 0:
            network.append({'pair': f'{eq1} <-> {eq2}', 'shared': shared})
    network.sort(key=lambda x: -x['shared'])
    top_fans_multi = sorted(multi_fans.items(), key=lambda x: (-len(x[1]['equipos']), -x[1]['gasto']))[:20]
    top_fans_list = []
    for correo, d in top_fans_multi:
        parts = correo.split('@')
        correo_anon = (parts[0][:3] + '***@' + parts[1]) if len(parts)==2 else correo[:3]+'***'
        top_fans_list.append({'correo': correo_anon, 'n_equipos': len(d['equipos']),'equipos': sorted(d['equipos']), 'gasto': round(d['gasto'], 2), 'ordenes': d['ordenes']})
    multi_data = {
        'total_multi': len(multi_fans), 'total_fans': len(all_fan_data),
        'avg_equipos': round(float(np.mean([len(d['equipos']) for d in multi_fans.values()])), 2),
        'avg_gasto': round(float(np.mean([d['gasto'] for d in multi_fans.values()])), 2),
        'max_equipos': max(len(d['equipos']) for d in multi_fans.values()),
        'distribucion': distribucion, 'top_combos': top_combos,
        'top_fans': top_fans_list, 'network': network,
    }
    out_multi = os.path.join(OUT_DIR, 'fans_multiequipo.json')
    with open(out_multi, 'w', encoding='utf-8') as f:
        json.dump(multi_data, f, ensure_ascii=False, indent=2)
    print(f"  fans_multiequipo.json: {os.path.getsize(out_multi):,} bytes")
else:
    print("  No hay fans multi-equipo")
print("\nLISTO")
