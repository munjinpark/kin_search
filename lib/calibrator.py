import re
import time
from typing import Optional
from datetime import datetime, timezone, timedelta

_cached_calibration = None
CACHE_TTL_SEC = 30 * 60
KST = timezone(timedelta(hours=9))

def _extract_doc_id(link: str) -> Optional[int]:
    m = re.search(r'docId=(\d+)', link)
    return int(m.group(1)) if m else None

def _take_sample(api_caller) -> dict:
    data = api_caller({'query': '어떻게', 'sort': 'date', 'display': 10, 'start': 1})
    max_doc_id = 0
    for item in data.get('items', []):
        doc_id = _extract_doc_id(item.get('link', ''))
        if doc_id and doc_id > max_doc_id:
            max_doc_id = doc_id
    return {'maxDocId': max_doc_id, 'lastBuildDate': data.get('lastBuildDate', ''), 'timestamp': time.time()}

def calibrate(api_caller) -> dict:
    global _cached_calibration
    if _cached_calibration and (time.time() - _cached_calibration['measuredAt'] < CACHE_TTL_SEC):
        return {'rate': _cached_calibration['rate'], 'maxDocId': _cached_calibration['maxDocId'], 'lastBuildDate': _cached_calibration['lastBuildDate'], 'cached': True}

    sample_a = _take_sample(api_caller)
    time.sleep(5)
    sample_b = _take_sample(api_caller)

    time_diff_min = (sample_b['timestamp'] - sample_a['timestamp']) / 60
    doc_id_diff = sample_b['maxDocId'] - sample_a['maxDocId']

    rate = 15
    if time_diff_min >= 0.5 and doc_id_diff > 0:
        calculated_rate = doc_id_diff / time_diff_min
        if 5 <= calculated_rate <= 50:
            rate = calculated_rate

    _cached_calibration = {'rate': rate, 'maxDocId': sample_b['maxDocId'], 'measuredAt': time.time(), 'lastBuildDate': sample_b['lastBuildDate']}
    return {'rate': rate, 'maxDocId': sample_b['maxDocId'], 'lastBuildDate': sample_b['lastBuildDate'], 'cached': False}

def calculate_cutoff(rate: float, max_doc_id: int) -> dict:
    now_kst = datetime.now(KST)
    total_minutes = now_kst.hour * 60 + now_kst.minute
    
    if now_kst.hour < 7:
        estimated = total_minutes * (rate * 0.25)
    else:
        estimated = (420 * (rate * 0.25)) + ((total_minutes - 420) * rate)

    return {
        'cutoffDocId': int(max_doc_id - estimated),
        'estimatedError': '±2시간',
        'currentKST': now_kst.strftime('%Y-%m-%d %H:%M KST'),
        'rate': rate,
        'maxDocId': max_doc_id,
    }

def reset_cache():
    global _cached_calibration
    _cached_calibration = None
