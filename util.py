import json
import re

class Utils:
    def __init__(self):
        pass
        
    def convert_text(self, input_text):
        if not isinstance(input_text, str):
            return None
        # Convert text to lowercase
        input_text = input_text.lower()
        
        # Replace spaces with hyphens
        input_text = input_text.replace(" ", "-")
        
        # Remove non-alphanumeric characters except hyphens
        input_text = re.sub(r'[^a-z0-9-]', '', input_text)
        
        return input_text

    def make_url(self, author_name, base_url, article_title):
            # 튜플 요소 분리
            slug = self.convert_text(article_title)

            # 최종 URL 생성
            final_url = f"{base_url.split('?')[0]}/{slug}-{base_url.split('?')[1].split('.reader-')[1].split('-')[1]}?{base_url.split('?')[1]}"

            return author_name, final_url