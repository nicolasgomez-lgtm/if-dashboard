"""
IF Dashboard Generator — Foodology

Calls Redshift via the MCP HTTP server (same connection used by the Cowork artifact).

Outputs: docs/mex.html, docs/col.html, docs/per.html, docs/index.html

"""

import json
import os
import sys
import requests
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ── Paths ─────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
TEMPLATE = ROOT / "template.html"
DOCS.mkdir(exist_ok=True)

# MCP server — set MCP_URL secret in GitHub Actions, or hardcode below
MCP_URL = os.environ.get(
    "MCP_URL",
    "https://foodology-redshift-mcp-gx27.onrender.com/mcp"
)

# ── Maestro de cocinas ────────────────────────────────────────
# Fuente de verdad: maestro_de_cocinas.csv (actualizado 2026-06-25)
# kitchen_id = ID usado en Redshift (fdgy_views.ontime_infull_order)

MAESTRO = {
    "MEX": {
        "01 DOCTORES":          {"ops": "Sergio Torres",     "city": "CDMX"},
        "02 SAN ANGEL":         {"ops": "Guillermo Villalva","city": "CDMX"},
        "03 POLANCO":           {"ops": "Guillermo Villalva","city": "CDMX"},
        "04 SANTA FE":          {"ops": "Sergio Torres",     "city": "CDMX"},
        "05 COAPA":             {"ops": "Sergio Torres",     "city": "CDMX"},
        "06 SATELITE":          {"ops": "Sergio Torres",     "city": "CDMX"},
        "09 CHURUBUSCO":        {"ops": "Sergio Torres",     "city": "CDMX"},
        "10 SAN JERONIMO":      {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "11 AZCAPOTZALCO":      {"ops": "Guillermo Villalva","city": "CDMX"},
        "12 DEL VALLE":         {"ops": "Guillermo Villalva","city": "CDMX"},
        "13 TEC":               {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "14 JARDINES":          {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "15 LINDAVISTA":        {"ops": "Guillermo Villalva","city": "CDMX"},
        "16 PEDREGAL":          {"ops": "Guillermo Villalva","city": "CDMX"},
        "17 CUMBRES":           {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "19 LA CALMA":          {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "20 ESMERALDA":         {"ops": "Sergio Torres",     "city": "CDMX"},
        "21 SANTA TERESITA":    {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "22 SAN NICOLAS":       {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "23 SANTA CATARINA":    {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "24 METEPEC":           {"ops": "Guillermo Villalva","city": "Guadalajara"},
        "25 TABACHINES":        {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "26 CIUDAD JUDICIAL":   {"ops": "Sergio Torres",     "city": "Puebla"},
        "27 IZTAPALAPA":        {"ops": "Sergio Torres",     "city": "CDMX"},
        "28 CARRETERA NACIONA": {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "30 LINCOLN":           {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "31 MONTEJO":           {"ops": "Claudia Valdez",    "city": "Mérida"},
        "34 TLAQUEPAQUE":       {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "37 CANEK":             {"ops": "Claudia Valdez",    "city": "Mérida"},
        "38 SALTILLO CENTRO":   {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "39 MONTERREY CENTRO":  {"ops": "Carlos Garcia",     "city": "Monterrey"},
        "40 JARDINES DEL VALL": {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "41 VOLCANES":          {"ops": "Sergio Torres",     "city": "Puebla"},
        "43 CP MONTERREY":      {"ops": "Diego Cruz",        "city": "Monterrey"},
        "44 CP GUADALAJARA":    {"ops": "Diego Cruz",        "city": "Guadalajara"},
        "45 ESTADIO":           {"ops": "Selene Cabrera",    "city": "Guadalajara"},
        "51 SAMARA":            {"ops": "Paulina Lima",      "city": "CDMX"},
        "52 MANACAR":           {"ops": "Paulina Lima",      "city": "CDMX"},
        "54 CENTR INTERLOMAS":  {"ops": "Paulina Lima",      "city": "CDMX"},
    },
    "COL": {
        "01 USAQUEN":           {"ops": "Laura Hernández",      "city": "Bogotá"},
        "02 PARQUE 93":         {"ops": "Laura Hernández",      "city": "Bogotá"},
        "03 CHAPINERO":         {"ops": "Laura Hernández",      "city": "Bogotá"},
        "06 COLINA":            {"ops": "Leidy Pinzon",         "city": "Bogotá"},
        "08 ANDES":             {"ops": "Juan Sebastian Bernal","city": "Bogotá"},
        "11 MANILA":            {"ops": "Jose Rodriguez",       "city": "Medellín"},
        "12 LAURELES":          {"ops": "Jose Rodriguez",       "city": "Medellín"},
        "13 CHIA":              {"ops": "Laura Hernández",      "city": "Bogotá"},
        "14 ENVIGADO":          {"ops": "Ulises Torres",        "city": "Medellín"},
        "15 ENGATIVA":          {"ops": "Laura Hernández",      "city": "Bogotá"},
        "18 BELLO":             {"ops": "Ulises Torres",        "city": "Medellín"},
        "22 SANTA MONICA":      {"ops": "Juan Pablo Gómez",     "city": "Cali"},
        "24 SAN FERNANDO":      {"ops": "Juan Pablo Gómez",     "city": "Cali"},
        "28 PEREIRA":           {"ops": "Juan Pablo Gómez",     "city": "Pereira"},
        "29 ITAGUI":            {"ops": "Ulises Torres",        "city": "Medellín"},
        "32 BARRANQUILLA":      {"ops": "Juan Pablo Gómez",     "city": "Barranquilla"},
        "33 CARTAGENA":         {"ops": "Juan Pablo Gómez",     "city": "Cartagena"},
        "36 VILLA DEL PRADO":   {"ops": "Leidy Pinzon",         "city": "Bogotá"},
        "38 KENNEDY":           {"ops": "Leidy Pinzon",         "city": "Bogotá"},
        "39 SALVIO":            {"ops": "Kevin Ramirez",        "city": "Bogotá"},
        "42 CABECERA":          {"ops": "Juan Pablo Gómez",     "city": "Bucaramanga"},
        "45 VERAGUAS":          {"ops": "Leidy Pinzon",         "city": "Bogotá"},
        "46 INGENIO":           {"ops": "Juan Pablo Gómez",     "city": "Cali"},
        "50 CHICO":             {"ops": "Diana Flórez",         "city": "Bogotá"},
        "55 TITAN":             {"ops": "Kevin Ramirez",        "city": "Bogotá"},
        "56 SANTAFE BOG":       {"ops": "Kevin Ramirez",        "city": "Bogotá"},
        "57 SANTAFE MED":       {"ops": "Karen Urquijo",        "city": "Medellín"},
        "58 VIVA MED":          {"ops": "Karen Urquijo",        "city": "Medellín"},
        "61 CHICO CINNABON":    {"ops": "Kevin Ramirez",        "city": "Bogotá"},
        "65 CALLE 109":         {"ops": "Andres Pulgarin",      "city": "Bogotá"},
        "66 PLAZA CLARO CINNA": {"ops": "Kevin Ramirez",        "city": "Bogotá"},
        "67 PLAZA CLARO COURT": {"ops": "Daniel Beltran",       "city": "Bogotá"},
        "69 ARRECIFE":          {"ops": "Juan Sebastian Bernal","city": "Bogotá"},
    },
    "PER": {
        "01 SAN ISIDRO":        {"ops": "Anny de la Cruz", "city": "Lima"},
        "03 LA MOLINA":         {"ops": "Anny de la Cruz", "city": "Lima"},
        "04 LA ALBORADA":       {"ops": "Anny de la Cruz", "city": "Lima"},
        "06 SURQUILLO":         {"ops": "Anny de la Cruz", "city": "Lima"},
        "01 CP LIMA":           {"ops": "Alicia Caceres",  "city": "Lima"},
    }
}

# ── Date logic ────────────────────────────────────────────────
def get_dates():
    today = date.today()
    days_since_sat = (today.weekday() - 5) % 7
    last_sat = today - timedelta(days=days_since_sat if days_since_sat > 0 else 7)
    w2_end, w2_start = last_sat, last_sat - timedelta(days=6)
    w1_end, w1_start = w2_start - timedelta(days=1), w2_start - timedelta(days=7)
    fmt = lambda d: str(d)
    lbl = lambda d: d.strftime("%-d %b").lower()
    return {
        "w2_start": fmt(w2_start), "w2_end": fmt(w2_end),
        "w1_start": fmt(w1_start), "w1_end": fmt(w1_end),
        "w2_label": f"{lbl(w2_start)}–{lbl(w2_end)} {w2_end.year}",
        "w1_label": f"{lbl(w1_start)}–{lbl(w1_end)}",
    }

# ── MCP query helpers ─────────────────────────────────────────
_session_id = None

def _post(payload, timeout=120):
    """POST a JSON-RPC message to the MCP server, return parsed response."""
    global _session_id
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id
    resp = requests.post(MCP_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    if "mcp-session-id" in resp.headers:
        _session_id = resp.headers["mcp-session-id"]
    ct = resp.headers.get("content-type", "")
    if "text/event-stream" in ct:
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk and chunk != "[DONE]":
                    try:
                        obj = json.loads(chunk)
                        if "result" in obj or "error" in obj:
                            return obj
                    except Exception:
                        pass
        return {}
    return resp.json()

def _init_mcp():
    """MCP initialize handshake."""
    global _session_id
    try:
        _post({
            "jsonrpc": "2.0", "method": "initialize", "id": 0,
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "if-dashboard-generator", "version": "1.0"},
            },
        })
        try:
            _post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        except Exception:
            pass
    except Exception as e:
        print(f"  MCP init note: {e}")

def run(sql):
    """Execute SQL via MCP execute_query tool. Returns list of dicts."""
    global _session_id
    rpc = _post({
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "execute_query", "arguments": {"sql": sql}},
    })
    if "error" in rpc:
        err = rpc["error"]
        code = err.get("code") if isinstance(err, dict) else None
        if code in (-32600, -32001, -32002):
            _init_mcp()
            rpc = _post({
                "jsonrpc": "2.0", "method": "tools/call", "id": 1,
                "params": {"name": "execute_query", "arguments": {"sql": sql}},
            })
    if "error" in rpc:
        raise RuntimeError(f"MCP error: {rpc['error']}")
    content = rpc.get("result", {}).get("content", [])
    if not content:
        raise RuntimeError(f"Empty MCP result for query: {sql[:80]}")
    text = content[0].get("text", "")
    if not text.strip().startswith(("{", "[")):
        raise RuntimeError(f"Redshift error: {text[:300]}")
    data = json.loads(text)
    if isinstance(data, dict) and "columns" in data:
        cols = data["columns"]
        rows = data.get("rows", [])
        if rows and isinstance(rows[0], list):
            return [dict(zip(cols, row)) for row in rows]
        return rows
    return data if isinstance(data, list) else []

# ── SQL helpers ───────────────────────────────────────────────
def sql_kitchens(c, d):
    return f"""
    SELECT kitchen_id, kitchen, city,
        SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN 1 ELSE 0 END) AS w2o,
        SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN is_complaint ELSE 0 END) AS w2c,
        SUM(CASE WHEN order_date BETWEEN '{d['w1_start']}' AND '{d['w1_end']}' THEN 1 ELSE 0 END) AS w1o,
        SUM(CASE WHEN order_date BETWEEN '{d['w1_start']}' AND '{d['w1_end']}' THEN is_complaint ELSE 0 END) AS w1c
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w1_start']}' AND '{d['w2_end']}'
        AND provider_name!='foodologypos' AND country='{c}'
    GROUP BY kitchen_id, kitchen, city
    HAVING SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN 1 ELSE 0 END) >= 30
    ORDER BY kitchen_id"""

def sql_brands(c, d):
    return f"""
    SELECT brand, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*),0), 4) AS if_rate,
        ROUND(SUM(is_complaint)::float / NULLIF(COUNT(*),0) * 100, 2) AS pct,
        COUNT(DISTINCT kitchen_id) AS nk,
        SUM(CASE WHEN reason_area LIKE '%QUALITY%' THEN 1 ELSE 0 END) AS q,
        SUM(CASE WHEN reason_area LIKE '%PASE%' THEN 1 ELSE 0 END) AS pase,
        SUM(CASE WHEN reason_area LIKE '%PRICING%' THEN 1 ELSE 0 END) AS pri,
        SUM(CASE WHEN reason_area LIKE '%DELIVERY%' THEN 1 ELSE 0 END) AS del,
        SUM(CASE WHEN reason_category LIKE '%MISSING_ITEM%' THEN 1 ELSE 0 END) AS miss,
        SUM(CASE WHEN reason_category LIKE '%NOT_TASTY%' THEN 1 ELSE 0 END) AS ntasty,
        SUM(CASE WHEN reason_category LIKE '%SMALL_PORTIONS%' THEN 1 ELSE 0 END) AS small,
        SUM(CASE WHEN reason_category LIKE '%RAW_OVERCOOKED%' THEN 1 ELSE 0 END) AS raw,
        SUM(CASE WHEN reason_category LIKE '%WRONG_ITEM%' THEN 1 ELSE 0 END) AS wrong,
        SUM(CASE WHEN reason_category LIKE '%WRONG_TEMPERATURE%' THEN 1 ELSE 0 END) AS wrongtemp,
        SUM(CASE WHEN reason_category LIKE '%BAD_PRESENTATION%' THEN 1 ELSE 0 END) AS badpres,
        SUM(CASE WHEN reason_category LIKE '%DAMAGE_ITEM%' THEN 1 ELSE 0 END) AS damage
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND provider_name!='foodologypos' AND country='{c}'
    GROUP BY brand HAVING COUNT(*) >= 200
    ORDER BY SUM(is_complaint)::float / NULLIF(COUNT(*),0) DESC LIMIT 25"""

def sql_slots(c, d):
    return f"""
    SELECT time_slot, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*),0), 4) AS if_rate
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND provider_name!='foodologypos' AND country='{c}'
    GROUP BY time_slot HAVING COUNT(*) >= 30
    ORDER BY SUM(is_complaint)::float / NULLIF(COUNT(*),0) DESC"""

def sql_causes(c, d):
    return f"""
    SELECT
        SUM(CASE WHEN reason_area LIKE '%QUALITY%' THEN 1 ELSE 0 END) AS quality,
        SUM(CASE WHEN reason_area LIKE '%PASE%' THEN 1 ELSE 0 END) AS pase,
        SUM(CASE WHEN reason_area LIKE '%PRICING%' THEN 1 ELSE 0 END) AS pricing,
        SUM(CASE WHEN reason_area LIKE '%DELIVERY%' THEN 1 ELSE 0 END) AS delivery
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND is_complaint=1 AND provider_name!='foodologypos' AND country='{c}'"""

def sql_cal(c, d):
    return f"""
    SELECT kitchen_id,
        CASE EXTRACT(DOW FROM order_date)
            WHEN 0 THEN 'Dom' WHEN 1 THEN 'Lun' WHEN 2 THEN 'Mar'
            WHEN 3 THEN 'Mié' WHEN 4 THEN 'Jue' WHEN 5 THEN 'Vie' WHEN 6 THEN 'Sáb'
        END AS day_name,
        EXTRACT(DOW FROM order_date)::int AS dow,
        time_slot, COUNT(*) AS orders, SUM(is_complaint) AS comp
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND provider_name!='foodologypos' AND country='{c}'
    GROUP BY kitchen_id, day_name, dow, time_slot
    ORDER BY kitchen_id, dow, time_slot"""

def sql_bk(c, d):
    return f"""
    SELECT kitchen_id, brand, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*),0), 4) AS if_rate,
        ROUND(SUM(is_complaint)::float / NULLIF(COUNT(*),0) * 100, 2) AS pct,
        SUM(CASE WHEN reason_area LIKE '%QUALITY%' THEN 1 ELSE 0 END) AS q,
        SUM(CASE WHEN reason_area LIKE '%PASE%' THEN 1 ELSE 0 END) AS pase,
        SUM(CASE WHEN reason_area LIKE '%PRICING%' THEN 1 ELSE 0 END) AS pri,
        SUM(CASE WHEN reason_area LIKE '%DELIVERY%' THEN 1 ELSE 0 END) AS del,
        SUM(CASE WHEN reason_category LIKE '%MISSING_ITEM%' THEN 1 ELSE 0 END) AS miss,
        SUM(CASE WHEN reason_category LIKE '%NOT_TASTY%' THEN 1 ELSE 0 END) AS ntasty,
        SUM(CASE WHEN reason_category LIKE '%SMALL_PORTIONS%' THEN 1 ELSE 0 END) AS small,
        SUM(CASE WHEN reason_category LIKE '%RAW_OVERCOOKED%' THEN 1 ELSE 0 END) AS raw,
        SUM(CASE WHEN reason_category LIKE '%WRONG_ITEM%' THEN 1 ELSE 0 END) AS wrong,
        SUM(CASE WHEN reason_category LIKE '%WRONG_TEMPERATURE%' THEN 1 ELSE 0 END) AS wrongtemp
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND provider_name!='foodologypos' AND country='{c}'
    GROUP BY kitchen_id, brand HAVING COUNT(*) >= 20
    ORDER BY kitchen_id, SUM(is_complaint)::float / NULLIF(COUNT(*),0) DESC"""

# ── Build structured data ─────────────────────────────────────
def build_cal(rows):
    tmp = defaultdict(lambda: {"days": {}, "slots": {}})
    for r in rows:
        kid, dw = r["kitchen_id"], int(r["dow"])
        if dw not in tmp[kid]["days"]:
            tmp[kid]["days"][dw] = {"day": r["day_name"], "orders": 0, "comp": 0}
        tmp[kid]["days"][dw]["orders"] += int(r["orders"])
        tmp[kid]["days"][dw]["comp"] += int(r["comp"])
        s = r["time_slot"].split(".")[-1] if "." in str(r["time_slot"]) else str(r["time_slot"])
        if s not in tmp[kid]["slots"]:
            tmp[kid]["slots"][s] = {"orders": 0, "comp": 0}
        tmp[kid]["slots"][s]["orders"] += int(r["orders"])
        tmp[kid]["slots"][s]["comp"] += int(r["comp"])
    dow_order = [1,2,3,4,5,6,0]
    slot_order = ["Early Morning","Morning","Lunch","Afternoon","Early Evening","Late Evening"]
    result = {}
    for kid, v in tmp.items():
        days = [{"day":v["days"][d]["day"],"orders":v["days"][d]["orders"],"comp":v["days"][d]["comp"],
                 "if":round(1-v["days"][d]["comp"]/v["days"][d]["orders"],4) if v["days"][d]["orders"] else 1.0}
                for d in dow_order if d in v["days"]]
        slots = [{"slot":s,"orders":v["slots"][s]["orders"],"comp":v["slots"][s]["comp"],
                  "if":round(1-v["slots"][s]["comp"]/v["slots"][s]["orders"],4) if v["slots"][s]["orders"] else 1.0}
                 for s in slot_order if s in v["slots"]]
        result[kid] = {"days": days, "slots": slots}
    return result

def build_bk(rows):
    r = defaultdict(list)
    for row in rows:
        r[row["kitchen_id"]].append(row)
    return dict(r)

# ── Main generator ────────────────────────────────────────────
def generate(country, d):
    M = MAESTRO.get(country, {})
    flag = {"MEX":"🇲🇽","COL":"🇨🇴","PER":"🇵🇪"}[country]
    cname = {"MEX":"México","COL":"Colombia","PER":"Perú"}[country]

    print(f"  [{country}] Running queries via MCP...")
    kitchens  = run(sql_kitchens(country, d))
    brands    = run(sql_brands(country, d))
    slots     = run(sql_slots(country, d))
    causes_r  = run(sql_causes(country, d))
    cal_rows  = run(sql_cal(country, d))
    bk_rows   = run(sql_bk(country, d))

    causes   = causes_r[0] if causes_r else {}
    cal_data = build_cal(cal_rows)
    bk_data  = build_bk(bk_rows)

    w1_map = {k["kitchen_id"]: round(1 - int(k["w1c"]) / int(k["w1o"]), 4)
              for k in kitchens if int(k.get("w1o") or 0) > 0}

    generated = datetime.now().strftime("%-d %b %Y %H:%M")

    data_js = (
        f"const C='{country}',CNAME='{cname}',FLAG='{flag}';\n"
        f"const DATES={json.dumps(d, default=str)};\n"
        f"const W2={json.dumps(kitchens, default=str)};\n"
        f"const W1={json.dumps(w1_map)};\n"
        f"const AB={json.dumps(brands, default=str)};\n"
        f"const SL={json.dumps(slots, default=str)};\n"
        f"const CAU={json.dumps(dict(causes), default=str)};\n"
        f"const CAL={json.dumps(cal_data)};\n"
        f"const BK={json.dumps(bk_data, default=str)};\n"
        f"const MAESTRO_C={json.dumps(M)};\n"
        f"const GEN='{generated}';\n"
    )

    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("/*__DATA__*/", data_js)
    html = html.replace("__META__", f"W2: {d['w2_label']} | W1: {d['w1_label']} | {generated}")
    html = html.replace("__COUNTRY__", f"{flag} {cname}")
    html = html.replace("__COUNTRY_CODE__", country.lower())

    out = DOCS / f"{country.lower()}.html"
    out.write_text(html, encoding="utf-8")
    print(f"  [{country}] ✓ docs/{country.lower()}.html ({len(html)//1024} KB)")
    return True

def make_index():
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url=mex.html">
<title>IF Dashboard — Foodology</title>
</head><body>
<p>Redirigiendo… <a href="mex.html">🇲🇽 México</a> | <a href="col.html">🇨🇴 Colombia</a> | <a href="per.html">🇵🇪 Perú</a></p>
</body></html>"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print("  index.html created")

if __name__ == "__main__":
    if not TEMPLATE.exists():
        print(f"ERROR: template.html not found at {TEMPLATE}")
        sys.exit(1)

    print(f"IF Dashboard Generator — {datetime.now().isoformat()}")
    d = get_dates()
    print(f"Period: W2={d['w2_start']}→{d['w2_end']} | W1={d['w1_start']}→{d['w1_end']}")
    print(f"MCP URL: {MCP_URL}")

    _init_mcp()

    errors = []
    for country in ["MEX", "COL", "PER"]:
        try:
            generate(country, d)
        except Exception as e:
            print(f"  [{country}] ERROR: {e}")
            errors.append(country)

    make_index()

    if errors:
        print(f"\nCompleted with errors in: {errors}")
        sys.exit(1)
    else:
        print("\nAll dashboards generated successfully ✓")
