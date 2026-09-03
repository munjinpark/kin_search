KEYWORD_MAP = {
    '개인회생': ['개인회생', '신용회복', '워크아웃', '채무조정', '프리워크아웃'],
    '개인파산': ['개인파산', '파산신청', '파산절차', '법률구조공단', '면책신청', '파산면책'],
    '법률상담': ['법률상담', '마을변호사', '로톡', '국선변호인', '대한법률구조공단'],
    '대출': ['대출', '햇살론', '사잇돌', '버팀목', '특례보증', '내집마련', '보금자리론', '생애최초', '신생아 특례', '주택구입', '디딤돌', '새희망홀씨', '마이너스통장'],
    '청약통장': ['청약통장', '주택청약', '청약신청', '청년 주택드림', '청약저축', '특별공급', '청약가점'],
    '병원비': ['병원비', '비급여 진료비', '심평원', '도수치료', '건강검진비', '의료비', '진료비', '수술비', '입원비'],
    '실손보험': ['실손보험', '4세대 실손', '내보험찾아줌', '실비보험', '의료실비', '실비청구'],
    '영화': ['영화', '문화가 있는 날', '통신사 멤버십', '청년문화예술패스', 'CGV', '메가박스', '롯데시네마'],
    '드라마': ['드라마', '넷플릭스', '티빙', '웨이브', '디즈니플러스', '정주행', '미드', '일드'],
    '수능': ['수능', '재수생', 'N수생', '검정고시', '대학수학능력시험', '반수생', '정시모집'],
    '불꽃축제': ['불꽃축제', '세계불꽃축제', '불꽃놀이'],
    'KTX': ['KTX', '코레일톡', '추석예매', 'SRT', '기차표', '승차권', '열차예매', 'ITX'],
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
