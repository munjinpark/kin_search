KEYWORD_MAP = {
    '개인회생': ['개인회생', '채무조정', '개인파산', '면책'],
    '파산': ['개인파산', '파산신청', '면책', '개인회생'],
    '신혼부부': ['신혼부부 대출', '디딤돌대출', '신혼부부 특별공급', '보금자리론'],
    '내집마련': ['디딤돌대출', '보금자리론', '생애최초 주택구입', '주택청약'],
    '전세': ['전세대출', '전세자금', '버팀목대출', '전세보증금'],
    '대출': ['대출', '신용대출', '담보대출', '대출금리'],
    '종합소득세': ['종합소득세', '종소세', '소득세 신고', '세금신고'],
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
