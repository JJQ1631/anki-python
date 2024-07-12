import os
import requests
import psutil
import pandas as pd
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from anki.storage import Collection
import concurrent.futures
from tqdm import tqdm

# 设置媒体库路径
media_folder = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.media"
if not os.path.exists(media_folder):
    os.makedirs(media_folder)

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

# 定义下载函数
def download_file(url, filename, proxies):
    if os.path.exists(filename):
        print(f"{filename} 已存在，跳过下载")
        return True

    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get(url, headers=headers_template, proxies=proxies, timeout=20)
        if response.status_code in [200, 206]:
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"{filename} 下载完成")
            return True
        else:
            print(f"无法下载文件: {url}, 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"下载文件时发生错误: {e}")
        return False

# 从剑桥词典获取美式发音音频URL
def get_cambridge_pronunciation(word, proxies):
    url = cambridge_url_template.format(word)
    try:
        response = requests.get(url, headers=headers_template, proxies=proxies, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找美式发音音频URL
            audio_elements = soup.find_all('source', {'type': 'audio/mpeg'})
            for audio_element in audio_elements:
                if 'us_pron' in audio_element['src']:
                    audio_url = audio_element['src']
                    if audio_url.startswith('/'):
                        audio_url = 'https://dictionary.cambridge.org' + audio_url
                    print(f"{word} 的美式发音音频URL: {audio_url}")
                    return audio_url
            print(f"未找到 {word} 的美式发音音频元素")
            return None
        else:
            print(f"无法访问 {word} 的剑桥字典页面，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"访问剑桥字典时发生错误: {e}")
        return None

# 关闭Anki应用程序
def close_anki():
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'anki.exe':
            process.terminate()
            process.wait()

close_anki()

def get_all_notes_in_deck(col, deck_name):
    notes = []
    deck_id = col.decks.id(deck_name)
    if not deck_id:
        print(f"未找到牌组: {deck_name}")
        return notes
    for subdeck_name in col.decks.children(deck_id):
        notes += col.find_notes(f"deck:{subdeck_name}")
    notes += col.find_notes(f"deck:{deck_name}")
    return notes

# 定义处理单词的函数
def process_word(note_id, expression, col, failed_words, index, total, progress_bar):
    query = expression.strip()
    # 获取代理
    proxies, proxy_url = get_proxy()
    if not proxies:
        print("无法获取代理，跳过此单词")
        failed_words.append((query, "无可用代理"))
        progress_bar.update(1)
        return

    print(f"获取代理: {proxies}")

    # 从剑桥词典获取音频
    audio_url = get_cambridge_pronunciation(query, proxies)
    result = None

    if audio_url:
        audio_filename = query.replace(' ', '_') + ".mp3"
        audio_path = os.path.join(media_folder, audio_filename)
        if download_file(audio_url, audio_path, proxies):
            note = col.get_note(note_id)
            note.fields[note._field_index("Audio")] = f"[sound:{audio_filename}]"
            col.update_note(note)
            result = "下载成功"
        else:
            result = "下载失败"
    else:
        result = "未找到音频URL"

    progress_bar.update(1)
    print(f"处理单词 {index + 1}/{total}: {query}，结果: {result}")
    if result != "下载成功":
        failed_words.append((query, result))

# 连接Anki数据库
try:
    col = Collection(anki_col_path)
    print("成功连接到Anki数据库")

    # 获取COCA20000及其子牌组的所有笔记
    all_notes = get_all_notes_in_deck(col, "COCA20000")
    print(f"找到 {len(all_notes)} 条笔记")

    failed_words = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        progress_bar = tqdm(total=len(all_notes), desc="处理进度")
        for index, note_id in enumerate(all_notes):
            note = col.get_note(note_id)
            if "expression" in note:
                expression = note.fields[note._field_index("expression")]
            else:
                print(f"笔记ID {note_id} 缺少expression字段，跳过。")
                progress_bar.update(1)
                continue

            if not expression:
                progress_bar.update(1)
                continue

            futures.append(executor.submit(process_word, note_id, expression, col, failed_words, index, len(all_notes), progress_bar))

        concurrent.futures.wait(futures)
        progress_bar.close()

    col.close()

    # 导出未能下载的单词为Excel文件
    if failed_words:
        df = pd.DataFrame(failed_words, columns=["Failed Words", "Reason"])
        output_path = os.path.join(media_folder, "failed_words.xlsx")
        df.to_excel(output_path, index=False)
        print(f"未能下载的单词已导出到 {output_path}")

except Exception as e:
    print(f"连接Anki数据库失败: {e}")
