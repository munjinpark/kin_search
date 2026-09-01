"""
네이버 지식iN 오늘자 질문 수집기 — Flask 서버
"""
import os
import time
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

from lib.keyword_expander import expand_keywords, get_available_categories
from lib.calibrator import calibrate, calculate_cutoff, reset_cache
from lib.collector import call_naver_kin_api, collect_all
from lib.deduplicator import deduplicate
from lib.filter import filter_all

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')

CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')

def check_api_keys():
    if not CLIENT_ID or not CLIENT_SECRET or CLIENT_ID == 'your_client_id_here':
        return False
    return True

def api_caller(params: dict) -> dict:
    return call_naver_kin_api(params, CLIENT_ID, CLIENT_SECRET)

@app.route('/api/search', methods=['POST'])
def search():
    if not check_api_keys():
        return jsonify({'error': '네이버 API 키가 설정되지 않았습니다.'}), 500

    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    custom_keywords = data.get('customKeywords')

    if not query and not custom_keywords:
        return jsonify({'error': '검색어를 입력해주세요.'}), 400

    try:
        pipeline = {'steps': [], 'startTime': time.time()}

        # 실제 검색에 사용할 키워드: 원본 query 그대로 (또는 customKeywords)
        if custom_keywords and len(custom_keywords) > 0:
            keywords = custom_keywords
            suggested_keywords = []
            pipeline['steps'].append({'step': 0, 'name': '검색어 입력', 'keywords': keywords, 'source': 'custom'})
        else:
            # 확장은 추천용으로만 사용, 실제 검색은 원본 query만
            expansion = expand_keywords(query)
            keywords = [query]
            # 확장된 키워드 중 원본과 다른 것만 추천으로 제공
            suggested_keywords = [kw for kw in expansion['keywords'] if kw != query]
            pipeline['steps'].append({'step': 0, 'name': '검색어 입력', 'input': query, 'keywords': keywords, 'suggestedKeywords': suggested_keywords, 'source': expansion['source']})

        cal = calibrate(api_caller)
        pipeline['steps'].append({'step': 1, 'name': 'docId 실측', 'rate': round(cal['rate'], 2), 'maxDocId': cal['maxDocId']})

        cutoff = calculate_cutoff(cal['rate'], cal['maxDocId'])
        pipeline['steps'].append({'step': 2, 'name': '컷오프 계산', 'cutoffDocId': cutoff['cutoffDocId']})

        collect_result = collect_all(keywords, cutoff['cutoffDocId'], CLIENT_ID, CLIENT_SECRET)
        all_items = collect_result['allItems']
        pipeline['steps'].append({'step': 3, 'name': '질문 수집', 'totalRaw': collect_result['stats']['totalRaw']})

        dedup_result = deduplicate(all_items, cutoff['cutoffDocId'])
        deduped_items = dedup_result['items']
        pipeline['steps'].append({'step': 4, 'name': '중복 제거'})

        filter_result = filter_all(deduped_items, keywords)
        final_items = filter_result['items']
        pipeline['steps'].append({'step': 5, 'name': '노이즈 필터링'})

        pipeline['totalTime'] = round((time.time() - pipeline['startTime']) * 1000)

        return jsonify({
            'success': True,
            'meta': {
                'currentKST': cutoff['currentKST'],
                'totalCount': len(final_items),
                'keywords': keywords,
                'suggestedKeywords': suggested_keywords,
                'cutoffDocId': cutoff['cutoffDocId'],
                'rate': round(cal['rate'], 2),
            },
            'items': [{'rank': item['rank'], 'title': item.get('title', ''), 'answerCount': item.get('maxAnswerNo', 0), 'link': item.get('link', ''), 'docId': item.get('docId'), 'nearCutoff': item.get('nearCutoff', False), 'duplicateTitle': item.get('duplicateTitle', False), 'duplicateCount': item.get('duplicateCount', 0), 'sourceQueries': item.get('sourceQueries', [])} for item in final_items],
            'pipeline': pipeline,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibrate', methods=['POST'])
def calibrate_endpoint():
    cal = calibrate(api_caller)
    cutoff = calculate_cutoff(cal['rate'], cal['maxDocId'])
    return jsonify({'success': True, 'rate': round(cal['rate'], 2), 'cutoffDocId': cutoff['cutoffDocId']})

@app.route('/api/calibrate/reset', methods=['POST'])
def calibrate_reset():
    reset_cache()
    return jsonify({'success': True})

@app.route('/api/categories')
def categories():
    return jsonify({'categories': get_available_categories()})

@app.route('/api/expand')
def expand():
    return jsonify(expand_keywords(request.args.get('query', '')))

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    try:
        return send_from_directory('public', path)
    except:
        return send_from_directory('public', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
