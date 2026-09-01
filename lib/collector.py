import re
import time
import requests

def call_naver_kin_api(params: dict, client_id: str, client_secret: str) -> dict:
    url = 'https://openapi.naver.com/v1/search/kin.json'
    headers = {'X-Naver-Client-Id': client_id, 'X-Naver-Client-Secret': client_secret}
    query_params = {
        'query': params.get('query', ''),
        'sort': params.get('sort', 'date'),
        'display': params.get('display', 50),
        'start': params.get('start', 1),
    }
    resp = requests.get(url, headers=headers, params=query_params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def parse_link(link: str) -> dict:
    result = {'docId': None, 'dirId': None, 'answerNo': None}
    m = re.search(r'docId=(\d+)', link)
    if m: result['docId'] = int(m.group(1))
    m = re.search(r'dirId=(\d+)', link)
    if m: result['dirId'] = m.group(1)
    m = re.search(r'answerNo=(\d+)', link)
    if m: result['answerNo'] = int(m.group(1))
    return result

def collect_for_query(query: str, cutoff_doc_id: int, client_id: str, client_secret: str, max_pages: int = 3, display_per_page: int = 50) -> list:
    collected = []
    for page in range(max_pages):
        start = page * display_per_page + 1
        try:
            data = call_naver_kin_api({'query': query, 'sort': 'date', 'display': display_per_page, 'start': start}, client_id, client_secret)
        except:
            break
            
        items = data.get('items', [])
        if not items: break

        below_cutoff_count = 0
        for item in items:
            parsed = parse_link(item.get('link', ''))
            if not parsed['docId']: continue
            
            collected.append({
                'docId': parsed['docId'],
                'dirId': parsed['dirId'],
                'answerNo': parsed['answerNo'],
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'link': item.get('link', ''),
                'sourceQuery': query,
            })
            
            if parsed['docId'] < cutoff_doc_id:
                below_cutoff_count += 1

        if below_cutoff_count / len(items) > 0.7:
            break
    return collected

def collect_all(keywords: list, cutoff_doc_id: int, client_id: str, client_secret: str) -> dict:
    all_items = []
    stats = {'perQuery': {}}
    for keyword in keywords:
        items = collect_for_query(keyword, cutoff_doc_id, client_id, client_secret)
        stats['perQuery'][keyword] = len(items)
        all_items.extend(items)
        time.sleep(0.2)
    stats['totalRaw'] = len(all_items)
    return {'allItems': all_items, 'stats': stats}
