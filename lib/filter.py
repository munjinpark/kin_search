import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def _has_faq_signal_in_description(description: str) -> bool:
    if not description: return False
    if '관련태그:' in description or '관련 태그:' in description: return True
    profile_markers = ['[변호사 프로필보기]', '[더 많은 변호사 답변 보기]', '# 질문글 원문 링크', '프로필보기]', '더 많은 답변 보기]', '질문글 원문']
    for marker in profile_markers:
        if marker in description: return True
    if re.search(r'법무법인\s*.+\s*[|｜]\s*.+\s*변호사', description) or re.search(r'[#]\s*법무법인', description): return True
    return False

def _is_editorial_title(title: str) -> bool:
    if not title: return False
    patterns = [r'가능할까\??$', r'방법은\??$', r'해결\s*방법은\??$', r'가능성은\??$', r'어떻게\s*하나요\??$', r'어떻게\s*될까\??$', r'어떻게\s*해야\s*할까\??$', r'무엇인가요?\??$', r'알아보기$', r'알아볼까요?\??$', r'총정리$', r'완벽\s*정리$', r'핵심\s*정리$']
    for pattern in patterns:
        if re.search(pattern, title): return True
    return False

def _check_page_is_faq(link: str) -> bool:
    """실제 네이버 지식iN 페이지를 요청하여 FAQ 태그가 있는지 확인"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(link, headers=headers, timeout=5)
        html = resp.text[:10000]  # 상단 부분만 확인 (성능)

        # FAQ 태그 감지 패턴들
        faq_patterns = [
            r'class="[^"]*faq[^"]*"',          # class에 faq 포함
            r'<a[^>]*>FAQ</a>',                 # FAQ 링크
            r'<span[^>]*>FAQ</span>',           # FAQ 스팬
            r'>FAQ<',                           # FAQ 텍스트
            r'class="[^"]*tag_faq[^"]*"',       # tag_faq 클래스
            r'"categoryName"\s*:\s*"FAQ"',      # JSON 데이터에 FAQ
        ]
        for pattern in faq_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                return True
        return False
    except:
        return False

def _batch_check_faq_pages(items: list, max_workers: int = 10) -> dict:
    """여러 페이지를 병렬로 FAQ 체크"""
    faq_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {}
        for item in items:
            link = item.get('link', '')
            doc_id = item.get('docId')
            if link and doc_id:
                future = executor.submit(_check_page_is_faq, link)
                future_to_doc[future] = doc_id
        
        for future in as_completed(future_to_doc):
            doc_id = future_to_doc[future]
            try:
                faq_map[doc_id] = future.result()
            except:
                faq_map[doc_id] = False
    return faq_map

def _is_faq(item: dict, page_faq_map: dict = None) -> dict:
    # 1. 실제 페이지 체크 결과 (가장 신뢰도 높음)
    if page_faq_map:
        doc_id = item.get('docId')
        if doc_id and page_faq_map.get(doc_id):
            return {'isFaq': True, 'reason': 'FAQ 페이지 (실제 페이지 확인)'}

    # 2. description 기반 체크
    desc_faq = _has_faq_signal_in_description(item.get('description', ''))
    editorial = _is_editorial_title(item.get('title', ''))
    low_answer = (item.get('maxAnswerNo') or 0) <= 1
    if desc_faq: return {'isFaq': True, 'reason': 'FAQ 콘텐츠 (description 신호)'}
    if editorial and low_answer: return {'isFaq': True, 'reason': 'FAQ 의심 (기사체 제목 + 답변 1개)'}
    return {'isFaq': False, 'reason': None}

NOISE_PATTERNS = [
    {'searchTerm': '개인회생', 'noiseWords': ['회생제동', '손금', '당적', '자동차 브레이크', '게임']},
    {'searchTerm': '파산', 'noiseWords': ['회사 파산 게임', '파산 게임']},
    {'searchTerm': '대출', 'noiseWords': ['대출 게임', '대출 시뮬레이션 게임']},
]

def _is_noise(item: dict, search_keywords: list) -> dict:
    title_lower = (item.get('title') or '').lower()
    for pattern in NOISE_PATTERNS:
        relevant = any(pattern['searchTerm'] in kw or kw in pattern['searchTerm'] for kw in search_keywords)
        if relevant:
            for noise in pattern['noiseWords']:
                if noise.lower() in title_lower:
                    return {'isNoise': True, 'reason': f'노이즈: "{noise}" 감지'}
    return {'isNoise': False, 'reason': None}

def filter_all(items: list, search_keywords: list) -> dict:
    # 실제 페이지를 병렬로 FAQ 체크
    page_faq_map = _batch_check_faq_pages(items)

    kept = []
    removed = []
    for item in items:
        # 1. 제목(Title) 매칭 검사: 검색어(연관 검색어 포함) 중 하나라도 제목에 있는지 확인
        title = item.get('title', '')
        title_nospace = title.replace(' ', '').lower()
        title_matched = False
        for kw in search_keywords:
            if kw.replace(' ', '').lower() in title_nospace:
                title_matched = True
                break
        
        if not title_matched:
            removed.append({**item, 'removeReason': '제목에 검색어 미포함'})
            continue

        faq_result = _is_faq(item, page_faq_map)
        if faq_result['isFaq']:
            removed.append({**item, 'removeReason': faq_result['reason']})
            continue
        noise_result = _is_noise(item, search_keywords)
        if noise_result['isNoise']:
            removed.append({**item, 'removeReason': noise_result['reason']})
            continue
        kept.append(item)

    for i, item in enumerate(kept): item['rank'] = i + 1

    title_groups = {}
    for item in kept:
        clean_title = item.get('title', '').strip()
        if clean_title not in title_groups: title_groups[clean_title] = []
        title_groups[clean_title].append(item['docId'])

    for item in kept:
        clean_title = item.get('title', '').strip()
        group = title_groups.get(clean_title, [])
        if len(group) > 1:
            item['duplicateTitle'] = True
            item['duplicateCount'] = len(group)
        else:
            item['duplicateTitle'] = False
            item['duplicateCount'] = 0

    faq_count = sum(1 for r in removed if r.get('removeReason', '').startswith('FAQ'))
    noise_count = sum(1 for r in removed if r.get('removeReason', '').startswith('노이즈'))

    return {
        'items': kept,
        'removed': removed,
        'stats': {'faqRemoved': faq_count, 'noiseRemoved': noise_count, 'totalRemoved': len(removed), 'totalKept': len(kept)},
    }
