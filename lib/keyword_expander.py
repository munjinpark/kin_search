KEYWORD_MAP = {
    '개인회생': ['개인회생', '자격조건', '신청방법', '변제금', '비용', '신용회복'],
    '개인파산': ['개인파산', '파산신청', '자격', '파산절차', '법률구조공단'],
    '법률상담': ['법률상담', '무료상담', '마을변호사', '변호사 상담예약'],
    '정부지원대출': ['대출', '정부지원 대출', '햇살론', '사잇돌', '버팀목', '특례보증'],
    '내집마련': ['내집마련', '디딤돌대출', '보금자리론', '생애최초', '신생아 특례', '주택구입'],
    '청약통장': ['청약통장', '주택청약', '청약신청', '소득공제', '청년 주택드림'],
    '병원비': ['병원비', '비급여 진료비', '심평원', 'MRI', '도수치료', '건강검진비'],
    '실손보험': ['실손보험', '보험금 청구', '4세대 실손', '내보험찾아줌', '보험료 인상'],
    '영화': ['영화', '영화 할인', '문화가 있는 날', '경로우대', '통신사 멤버십', '청년문화예술패스'],
    '수능': ['수능', '원서 접수', '재수생', 'N수생', '검정고시', '응시 수수료'],
    '불꽃축제': ['불꽃축제', '서울불꽃축제'],
    'KTX': ['KTX', '코레일톡', '추석예매', 'SRT'],
}

SYNONYMS = {
    '주담대': '주택담보대출',
    '종소세': '종합소득세',
}

def expand_keywords(user_input: str) -> dict:
    trimmed = user_input.strip()
    normalized = trimmed
    for synonym, canonical in SYNONYMS.items():
        if synonym in normalized:
            normalized = normalized.replace(synonym, canonical)
            
    matched = []
    all_keywords = []
    for trigger, expansions in KEYWORD_MAP.items():
        if trigger in normalized:
            matched.append(trigger)
            all_keywords.extend(expansions)
            
    if all_keywords:
        unique = list(dict.fromkeys(all_keywords))
        return {'keywords': unique[:5], 'source': 'dictionary', 'matched': matched}

    words = normalized.split()
    if len(words) == 1:
        return {'keywords': [words[0]], 'source': 'passthrough', 'matched': []}

    combos = list(dict.fromkeys([w for w in words if len(w) >= 2] + [f'{words[i]} {words[i+1]}' for i in range(len(words) - 1)]))
    result = combos[:5] if combos else [trimmed]
    return {'keywords': result, 'source': 'split', 'matched': []}

def get_available_categories() -> list:
    return list(KEYWORD_MAP.keys())
