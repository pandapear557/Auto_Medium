import logging
import urllib.request

from bs4 import BeautifulSoup

from .utils import Utils

logger = logging.getLogger(__name__)

# 메일 메뉴/푸터 링크 (실제 글이 아니므로 크롤링 제외)
EXCEPT_LIST = [
    "·Member",
    "Edit who you follow",
    "Control your recommendations",
    "·Terms of service",
]


class MailCrawler:
    """다이제스트 메일 본문을 받아 각 글을 크롤링한다."""

    def __init__(self, mail_text, timeout=10):
        # Medium 은 단순 User-Agent 만으로는 403 을 주는 경우가 많아
        # 브라우저에 가깝게 헤더를 채운다. (그래도 네트워크/IP 에 따라
        # 차단될 수 있음 — README 의 "알려진 제약" 참고)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.timeout = timeout
        self.utils = Utils()
        self.entries = self.utils.url_tuples(mail_text)

    def _fetch(self, url):
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return BeautifulSoup(resp.read(), "html.parser")

    def crawl_one(self, index):
        """인덱스 한 건을 크롤링해 {url, title, text} 반환 (제외/실패 시 None)."""
        if index < 0 or index >= len(self.entries):
            logger.warning("잘못된 인덱스: %s (0 ~ %s)", index, len(self.entries) - 1)
            return None

        author_name, base_url, article_title = self.entries[index]
        if author_name in EXCEPT_LIST:
            logger.info("건너뜀 (메뉴 링크): %s", author_name)
            return None

        _, url = self.utils.make_url(author_name, base_url, article_title)

        try:
            soup = self._fetch(url)
        except Exception as e:
            logger.error("크롤링 실패 %s: %s", url, e)
            return None

        title_el = soup.select_one("h1")
        title = title_el.get_text() if title_el else "No Title Found"

        # 기본 셀렉터(.pw-post-body-paragraph)가 비면 <article> 전체로 폴백
        paragraphs = soup.select(".pw-post-body-paragraph")
        if paragraphs:
            text = "\n".join(p.get_text() for p in paragraphs)
        else:
            article = soup.select_one("article")
            text = article.get_text("\n") if article else "No Paragraph Found"

        return {"url": url, "title": title, "text": text}

    def crawl_all(self):
        """메일 내 모든 글을 크롤링해 리스트로 반환."""
        results = []
        for i in range(len(self.entries)):
            item = self.crawl_one(i)
            if item:
                results.append(item)
        return results
