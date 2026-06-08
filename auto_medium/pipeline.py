import logging

from .crawler import MailCrawler

logger = logging.getLogger(__name__)


def run(mail_text, index=None, save_to_notion=False):
    """메일 본문 → 크롤링 → (선택) Notion 저장. 크롤링 결과 리스트를 반환.

    로컬 실행기와 Lambda 핸들러가 공유하는 핵심 진입점.

    Args:
        mail_text: 다이제스트 메일 본문 텍스트.
        index: 특정 글 1건만 처리하려면 정수 인덱스. None 이면 전체.
        save_to_notion: True 면 결과를 Notion DB 에 저장.
    """
    crawler = MailCrawler(mail_text)

    if index is not None:
        item = crawler.crawl_one(index)
        results = [item] if item else []
    else:
        results = crawler.crawl_all()

    if save_to_notion and results:
        from .notion_store import NotionStore

        NotionStore().save_many(results)

    return results
