import logging
import os

logger = logging.getLogger(__name__)


class NotionStore:
    """크롤링 결과를 Notion 데이터베이스에 페이지로 저장한다.

    필요한 환경변수:
      - NOTION_TOKEN       : Notion 통합(integration) 시크릿 토큰
      - NOTION_DB_ID       : 저장할 데이터베이스 ID
      - NOTION_TITLE_PROP  : (선택) 제목 속성명. 기본 "Name"
      - NOTION_URL_PROP    : (선택) URL 속성명. 기본 "URL"

    주의: NOTION_TITLE_PROP / NOTION_URL_PROP 는 실제 내 Notion DB의
    속성(컬럼) 이름과 정확히 일치해야 한다. URL 속성이 없다면
    NOTION_URL_PROP 를 빈 값으로 두면 URL 저장을 건너뛴다.
    """

    def __init__(self, token=None, database_id=None):
        from notion_client import Client  # 지연 import: 로컬 테스트 시 미설치 허용

        self.token = token or os.environ.get("NOTION_TOKEN")
        self.database_id = database_id or os.environ.get("NOTION_DB_ID")
        self.title_prop = os.environ.get("NOTION_TITLE_PROP", "Name")
        self.url_prop = os.environ.get("NOTION_URL_PROP", "URL")

        if not self.token or not self.database_id:
            raise ValueError("NOTION_TOKEN / NOTION_DB_ID 환경변수가 필요합니다.")

        self.client = Client(auth=self.token)

    def save(self, item):
        """{url, title, text} 한 건을 Notion DB 페이지로 생성."""
        title = item.get("title", "No Title")
        url = item.get("url", "")
        text = item.get("text", "")

        properties = {
            self.title_prop: {"title": [{"text": {"content": title[:2000]}}]},
        }
        if self.url_prop and url:
            properties[self.url_prop] = {"url": url}

        self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=self._text_to_blocks(text),
        )

    def save_many(self, items):
        """여러 건 저장. 개별 실패는 로깅 후 계속 진행."""
        for item in items:
            try:
                self.save(item)
                logger.info("Notion 저장 완료: %s", item.get("title"))
            except Exception as e:
                logger.error("Notion 저장 실패 (%s): %s", item.get("title"), e)

    @staticmethod
    def _text_to_blocks(text):
        """본문을 Notion 단락 블록 리스트로 변환.

        Notion 은 rich_text 한 조각당 2000자, children 100개 제한이 있어
        문단 단위로 나누고 길면 추가로 잘라 담는다.
        """
        blocks = []
        for para in text.split("\n"):
            para = para.strip()
            if not para:
                continue
            for i in range(0, len(para), 1900):
                chunk = para[i : i + 1900]
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": chunk}}
                            ]
                        },
                    }
                )
                if len(blocks) >= 100:
                    return blocks
        return blocks
