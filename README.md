# Auto_Medium

Medium Daily Digest 뉴스레터를 기반으로 하는 블로그 수집 자동화 파이프라인

다이제스트 메일 본문 → 각 글의 실제 URL 복원 → 크롤링(제목+본문) → (선택) Notion DB 저장.

## 구조

- `auto_medium/` — 핵심 로직 패키지 (로컬/Lambda 공용)
  - `utils.py` 파싱·URL 복원 / `crawler.py` 크롤링 / `notion_store.py` Notion 저장 / `pipeline.py` 전체 흐름
- `run_local.py` — 로컬 테스트 진입점 (`mail.json` 사용)
- `lambda_function.py` — AWS Lambda 진입점

## 로컬 실행

```bash
pip install -r requirements.txt

python run_local.py                  # mail.json 크롤링 후 JSON 출력
SAVE_TO_NOTION=1 python run_local.py # 크롤링 + Notion 저장
```

Notion 저장은 `.env.example` 를 `.env` 로 복사해 `NOTION_TOKEN`, `NOTION_DB_ID` 를 채워야 한다.

## 참고

- `test/` 는 초기 탐색용 노트북/드래프트로 참고용이며 실제 코드는 `auto_medium/` 패키지를 사용한다.
- Medium 은 네트워크에 따라 봇 요청을 403 으로 차단할 수 있다 (자세한 내용은 `CLAUDE.md` 의 "Known limitations").
