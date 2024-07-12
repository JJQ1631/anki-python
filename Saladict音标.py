import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
import concurrent.futures
from anki.storage import Collection
import psutil

# 设置牌组文件路径
anki_col_path = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.anki2"

# 设置词典URL模板
cambridge_url_template = "https://dictionary.cambridge.org/pronunciation/english/{}"

# 自定义请求头
headers_template = {
    "Accept": "*/*",
    "Accept-Encoding": "identity;q=1, *;q=0",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Cookie": "your_cookie_here",  # 请替换为你的Cookie
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 定义代理获取函数
def get_proxy():
    try:
        proxy = requests.get("http://127.0.0.1:5010/get/").json()
        proxy_url = proxy.get("proxy")
        if proxy_url:
            proxies = {
                "http": f"http://{proxy_url}"
            }
            return proxies, proxy_url
        else:
            return None, None
    except Exception as e:
        print(f"获取代理时发生错误: {e}")
        return None, None

# 从剑桥词典获取美式音标
def get_cambridge_ipa(word, proxies):
    url = cambridge_url_template.format(word)
    try:
        response = requests.get(url, headers=headers_template, proxies=proxies, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # 查找所有美式音标
            ipa_elements = soup.find_all('span', {'class': 'ipa'})
            if len(ipa_elements) >= 2:
                ipa = f"/{ipa_elements[1].text.strip()}/"
                print(f"{word} 的美式音标: {ipa}")
                return ipa
            else:
                print(f"未找到 {word} 的美式音标")
                return None
        else:
            print(f"无法访问 {word} 的剑桥字典页面，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"访问剑桥字典时发生错误: {e}")
        return None

# 处理单词的函数
def process_word(note_id, text, col, proxies, failed_words, index, total):
    ipa = get_cambridge_ipa(text, proxies)
    if ipa:
        note = col.get_note(note_id)
        note.fields[note._field_index("音标")] = ipa
        col.update_note(note)
    else:
        failed_words.append(text)
    print(f"处理进度: {index + 1}/{total}")

# 关闭Anki应用程序
def close_anki():
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'anki.exe':
            process.terminate()
            process.wait()

# 主程序
def main():
    close_anki()

    try:
        col = Collection(anki_col_path)
        print("成功连接到Anki数据库")

        # 获取Saladict牌组的所有笔记
        deck_name = "Saladict"
        notes = col.find_notes(f"deck:{deck_name}")
        print(f"找到 {len(notes)} 条笔记")

        failed_words = []
        total = len(notes)

        with tqdm(total=total, desc="处理进度") as progress_bar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for index, note_id in enumerate(notes):
                    note = col.get_note(note_id)
                    if "Text" in note:
                        text = note.fields[note._field_index("Text")]
                    else:
                        print(f"笔记ID {note_id} 缺少Text字段，跳过。")
                        continue

                    if not text:
                        continue

                    proxies, proxy_url = get_proxy()
                    if proxies:
                        print(f"使用代理: {proxies}")
                    futures.append(executor.submit(process_word, note_id, text, col, proxies, failed_words, index, total))

                concurrent.futures.wait(futures)

        col.close()

        # 导出未能抓取到的单词为Excel文件
        if failed_words:
            df = pd.DataFrame(failed_words, columns=["Failed Words"])
            output_path = "failed_words.xlsx"
            df.to_excel(output_path, index=False)
            print(f"未能抓取到的单词已导出到 {output_path}")

    except Exception as e:
        print(f"连接Anki数据库失败: {e}")

if __name__ == "__main__":
    main()
