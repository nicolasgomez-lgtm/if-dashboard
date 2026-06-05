"""SQL queries for IF Dashboard — Foodology"""

def get_date_ranges():
    """
    Returns the last two complete Sun→Sat weeks from today.
    Same logic as the JavaScript artifact.
    """
    from datetime import date, timedelta
    today = date.today()
    # Days to last Saturday: (dow+1)%7, where Mon=0..Sun=6 (Python weekday)
    # Python: Mon=0, Tue=1, ..., Sat=5, Sun=6
    # We want Sun→Sat weeks. Last Saturday:
    dow = today.weekday()  # Mon=0..Sun=6
    # Convert: Sat=5 in Python, distance to last Sat:
    days_to_last_sat = (dow - 5) % 7  # 0 if today is Sat
    last_sat = today - timedelta(days=days_to_last_sat if days_to_last_sat > 0 else 7)
    
    w2_end = last_sat
    w2_start = last_sat - timedelta(days=6)
    w1_end = w2_start - timedelta(days=1)
    w1_start = w1_end - timedelta(days=6)
    
    return {
        'w2_start': str(w2_start),
        'w2_end': str(w2_end),
        'w1_start': str(w1_start),
        'w1_end': str(w1_end),
        'w2_label': f"{w2_start.strftime('%-d %b')}–{w2_end.strftime('%-d %b %Y')}",
        'w1_label': f"{w1_start.strftime('%-d %b')}–{w1_end.strftime('%-d %b %Y')}",
    }


def q_kitchens(country, d):
    return f"""
    SELECT kitchen_id, kitchen, city,
        SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN 1 ELSE 0 END) AS w2o,
        SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN is_complaint ELSE 0 END) AS w2c,
        SUM(CASE WHEN order_date BETWEEN '{d['w1_start']}' AND '{d['w1_end']}' THEN 1 ELSE 0 END) AS w1o,
        SUM(CASE WHEN order_date BETWEEN '{d['w1_start']}' AND '{d['w1_end']}' THEN is_complaint ELSE 0 END) AS w1c
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w1_start']}' AND '{d['w2_end']}'
        AND provider_name != 'foodologypos' AND country = '{country}'
    GROUP BY kitchen_id, kitchen, city
    HAVING SUM(CASE WHEN order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}' THEN 1 ELSE 0 END) >= 30
    ORDER BY kitchen_id
    """


def q_brands(country, d):
    return f"""
    SELECT brand, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*), 0), 4) AS if_rate,
        ROUND(SUM(is_complaint)::float / NULLIF(COUNT(*), 0) * 100, 2) AS pct,
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
        AND provider_name != 'foodologypos' AND country = '{country}'
    GROUP BY brand
    HAVING COUNT(*) >= 200
    ORDER BY pct DESC
    LIMIT 25
    """


def q_slots(country, d):
    return f"""
    SELECT time_slot, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*), 0), 4) AS if_rate
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND provider_name != 'foodologypos' AND country = '{country}'
    GROUP BY time_slot
    HAVING COUNT(*) >= 30
    ORDER BY SUM(is_complaint)::float / NULLIF(COUNT(*), 0) DESC
    """


def q_causes(country, d):
    return f"""
    SELECT
        SUM(CASE WHEN reason_area LIKE '%QUALITY%' THEN 1 ELSE 0 END) AS quality,
        SUM(CASE WHEN reason_area LIKE '%PASE%' THEN 1 ELSE 0 END) AS pase,
        SUM(CASE WHEN reason_area LIKE '%PRICING%' THEN 1 ELSE 0 END) AS pricing,
        SUM(CASE WHEN reason_area LIKE '%DELIVERY%' THEN 1 ELSE 0 END) AS delivery
    FROM fdgy_views.ontime_infull_order
    WHERE order_date BETWEEN '{d['w2_start']}' AND '{d['w2_end']}'
        AND is_complaint = 1 AND provider_name != 'foodologypos' AND country = '{country}'
    """


def q_cal(country, d):
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
        AND provider_name != 'foodologypos' AND country = '{country}'
    GROUP BY kitchen_id, day_name, dow, time_slot
    ORDER BY kitchen_id, dow, time_slot
    """


def q_bk(country, d):
    return f"""
    SELECT kitchen_id, brand, COUNT(*) AS orders, SUM(is_complaint) AS comp,
        ROUND(1.0 - SUM(is_complaint)::float / NULLIF(COUNT(*), 0), 4) AS if_rate,
        ROUND(SUM(is_complaint)::float / NULLIF(COUNT(*), 0) * 100, 2) AS pct,
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
        AND provider_name != 'foodologypos' AND country = '{country}'
    GROUP BY kitchen_id, brand
    HAVING COUNT(*) >= 20
    ORDER BY kitchen_id, SUM(is_complaint)::float / NULLIF(COUNT(*), 0) DESC
    """
