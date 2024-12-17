import json
import re

class Utils:
    def __init__(self):
        pass
    
    def url_tuples(self, data): # json -> tuple[3]
        pattern = r"(.*)\((https?://[^\s)]+)\)\n\n(.*)" # 정규표현식 패턴

        # 매칭
        matches = re.findall(pattern, data)

        # 결과를 튜플리스트로 변환 [0: author_name 1: base_url 2: article_title]으로 저장됨.
        result = [(match[0].strip() if match[0] else None, 
                match[1].strip() if match[1] else None, 
                match[2].strip() if match[2] else None) for match in matches]
        
        return result
    
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
    
    def merge_json(self, ls1, ls2):
        # title과 txt의 각 인덱스를 병합하여 새로운 리스트 생성
        merged_data = []

        for t, text in zip(ls1, ls2):  # title과 txt의 각 요소를 병합
            merged_data.append({
                "title": t,
                "content": text
            })

        return merged_data
    
def main():
    with open("mail.txt", "r", encoding="utf-8") as file:
        event = file.read()  

    utils_instance = Utils()
    origin_url = utils_instance.url_tuples(event)
    
    temp = []
    for i in range(len(origin_url)-1):
        temp.append(utils_instance.make_url(origin_url,i))
        print()
    print(temp[-3][1]) #1열 가져오기

if __name__ == "__main__":
    main()