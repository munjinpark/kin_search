document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('searchForm');
  const input = document.getElementById('searchInput');
  const btn = document.getElementById('searchBtn');
  const errorBox = document.getElementById('errorBox');
  const resultsContainer = document.getElementById('resultsContainer');
  const catsContainer = document.getElementById('categoriesContainer');
  const suggestedBox = document.getElementById('suggestedKeywordsBox');
  const suggestedList = document.getElementById('suggestedKeywordsList');

  fetch('/api/categories').then(r=>r.json()).then(data => {
    if(data.categories) {
      data.categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.textContent = cat;
        btn.onclick = () => { input.value = cat; doSearch(cat); };
        catsContainer.appendChild(btn);
      });
    }
  }).catch(console.error);

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if(!query) return;
    doSearch(query);
  });

  async function doSearch(query, customKeywords) {
    btn.disabled = true;
    btn.textContent = '검색 중...';
    errorBox.classList.add('hidden');
    resultsContainer.classList.add('hidden');
    suggestedBox.classList.add('hidden');

    try {
      const timeLimitVal = document.getElementById('timeLimitSelect').value;
      const body = customKeywords
        ? { query, customKeywords, timeLimit: timeLimitVal }
        : { query, timeLimit: timeLimitVal };

      const res = await fetch('/api/search', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      
      if(!res.ok || data.error) throw new Error(data.error || '검색 오류');
      
      document.getElementById('metaTime').textContent = data.meta.currentKST;
      document.getElementById('metaCount').textContent = `${data.meta.totalCount}건`;
      document.getElementById('metaKeywords').innerHTML = data.meta.keywords.map(kw => `<span>${kw}</span>`).join('');
      
      // 추천 키워드 표시
      const suggested = data.meta.suggestedKeywords || [];
      if(suggested.length > 0) {
        suggestedList.innerHTML = '';
        suggested.forEach(kw => {
          const sbtn = document.createElement('button');
          sbtn.className = 'suggested-btn';
          sbtn.textContent = kw;
          sbtn.onclick = () => {
            input.value = kw;
            doSearch(kw);
          };
          suggestedList.appendChild(sbtn);
        });
        suggestedBox.classList.remove('hidden');
      } else {
        suggestedBox.classList.add('hidden');
      }

      const list = document.getElementById('questionsList');
      list.innerHTML = '';
      if(data.items.length === 0) {
        list.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-secondary);">오늘 올라온 질문이 없습니다.</div>';
      } else {
        data.items.forEach(item => {
          const isZero = item.answerCount === 0;
          const cutoffHtml = item.nearCutoff ? '<span class="q-cutoff-tag">마감임박</span>' : '';
          list.innerHTML += `
            <a href="${item.link}" target="_blank" class="question-item">
              <div>
                <div style="margin-bottom:8px;">
                  <span class="q-rank">#${item.rank}</span> ${cutoffHtml}
                </div>
                <h3 class="q-title">${item.title}</h3>
              </div>
              <div class="q-answer-box">
                <div class="meta-label">답변수</div>
                <div class="q-answer-count ${isZero ? 'zero' : ''}">${item.answerCount}</div>
              </div>
            </a>
          `;
        });
      }
      resultsContainer.classList.remove('hidden');
    } catch(err) {
      errorBox.textContent = err.message;
      errorBox.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btn.textContent = '질문 찾기';
    }
  }
});
