import re


class Utils:
    """메일 본문 파싱 및 Medium 글 URL 복원 유틸리티."""

    def url_tuples(self, data):
        """다이제스트 메일 본문을 (작성자, 링크, 제목) 튜플 리스트로 변환."""
        pattern = r"(.*)\((https?://[^\s)]+)\)\n\n(.*)"
        matches = re.findall(pattern, data)
        return [
            (
                match[0].strip() if match[0] else None,
                match[1].strip() if match[1] else None,
                match[2].strip() if match[2] else None,
            )
            for match in matches
        ]

    def convert_text(self, input_text):
        """제목을 URL 슬러그로 변환 (소문자 → 공백을 '-'로 → 영숫자/하이픈만)."""
        if not isinstance(input_text, str):
            return None
        input_text = input_text.lower()
        input_text = input_text.replace(" ", "-")
        return re.sub(r"[^a-z0-9-]", "", input_text)

    def make_url(self, author_name, base_url, article_title):
        """리다이렉트 링크에서 실제 Medium 글 주소를 복원해 (작성자, URL) 반환.

        다이제스트 메일의 링크는 `?source=...reader-<x>-<hash>----...` 형태의
        리다이렉트 주소다. 제목을 슬러그로 바꾸고, 쿼리스트링의 `.reader-`
        토큰에서 글 해시를 뽑아 `medium.com/<퍼블리케이션>/<슬러그>-<해시>`
        형태의 정식 주소를 만든다.
        """
        slug = self.convert_text(article_title)
        query = base_url.split("?")[1]
        article_hash = query.split(".reader-")[1].split("-")[1]
        base = base_url.split("?")[0]
        final_url = f"{base}/{slug}-{article_hash}?{query}"
        return author_name, final_url

    def merge_json(self, titles, contents):
        """제목/본문 리스트를 [{title, content}] 형태로 병합."""
        return [{"title": t, "content": c} for t, c in zip(titles, contents)]
