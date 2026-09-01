import re

def strip_html(text: str) -> str:
    if not text: return ''
    return re.sub(r'<[^>]*>', '', text)

def build_question_url(dir_id: str, doc_id: int) -> str:
    return f'https://kin.naver.com/qna/detail.naver?dirId={dir_id}&docId={doc_id}'

def deduplicate(all_items: list, cutoff_doc_id: int, max_results: int = 50) -> dict:
    doc_map = {}
    for item in all_items:
        doc_id = item.get('docId')
        if not doc_id: continue
        
        if doc_id in doc_map:
            existing = doc_map[doc_id]
            answer_no = item.get('answerNo') or 0
            if answer_no > existing['maxAnswerNo']: existing['maxAnswerNo'] = answer_no
            sq = item.get('sourceQuery', '')
            if sq and sq not in existing['sourceQueries']: existing['sourceQueries'].append(sq)
        else:
            doc_map[doc_id] = {
                'docId': doc_id,
                'dirId': item.get('dirId'),
                'title': strip_html(item.get('title', '')),
                'description': item.get('description', ''),
                'descriptionClean': strip_html(item.get('description', '')),
                'maxAnswerNo': item.get('answerNo') or 0,
                'link': build_question_url(item.get('dirId', ''), doc_id),
                'sourceQueries': [item.get('sourceQuery', '')],
            }

    filtered = []
    removed_by_cutoff = 0
    for doc_id, item in doc_map.items():
        if doc_id >= cutoff_doc_id:
            filtered.append(item)
        else:
            removed_by_cutoff += 1

    filtered.sort(key=lambda x: x['docId'], reverse=True)
    result = filtered[:max_results]

    if result: margin = (result[0]['docId'] - cutoff_doc_id) * 0.1
    else: margin = 0

    for i, item in enumerate(result):
        item['rank'] = i + 1
        item['nearCutoff'] = item['docId'] < (cutoff_doc_id + margin)

    return {
        'items': result,
        'stats': {
            'totalBeforeDedupe': len(all_items),
            'uniqueQuestions': len(doc_map),
            'removedByCutoff': removed_by_cutoff,
            'returnedCount': len(result),
        },
    }
