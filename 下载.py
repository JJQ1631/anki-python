import os
import requests
import psutil
from bs4 import BeautifulSoup
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from anki.storage import Collection

# 设置Anki媒体库路径
media_folder = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.media"
if not os.path.exists(media_folder):
    os.makedirs(media_folder)

# 设置牌组文件路径
anki_col_path = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.anki2"

# 设置词典URL模板
ldoce_url_template = "https://www.ldoceonline.com/dictionary/{}"
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

# 定义代理获取和删除函数
def get_proxy():
    proxy = requests.get("http://127.0.0.1:5010/get/").json()
    proxy_url = proxy.get("proxy")
    proxies = {
        "http": f"http://{proxy_url}",
        "https": f"https://{proxy_url}",
    } if proxy.get("https") else {
        "http": f"http://{proxy_url}",
    }
    return proxies, proxy_url

def delete_proxy(proxy):
    if proxy:
        requests.get(f"http://127.0.0.1:5010/delete/?proxy={proxy}")

# 定义下载函数
def download_file(url, filename, proxies):
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
        else:
            print(f"无法下载文件: {url}, 状态码: {response.status_code}")
    except Exception as e:
        print(f"下载文件时发生错误: {e}")

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

# 获取美式发音音标
def get_cambridge_ipa(word, proxies):
    url = cambridge_url_template.format(word)
    try:
        response = requests.get(url, headers=headers_template, proxies=proxies, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找美式音标
            ipa_element = soup.find('span', {'class': 'ipa dipa lpr-2 lpl-1'})
            if ipa_element:
                ipa = f"/{ipa_element.text.strip()}/"
                print(f"{word} 的美式音标: {ipa}")
                return ipa
            print(f"未找到 {word} 的美式音标")
            return None
        else:
            print(f"无法访问 {word} 的剑桥字典页面，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"访问剑桥字典时发生错误: {e}")
        return None

# 从朗文字典获取美式发音音频URL
def get_ldoce_pronunciation(word, proxies):
    url = ldoce_url_template.format(word)
    try:
        response = requests.get(url, headers=headers_template, proxies=proxies, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找美式发音音频URL
            audio_elements = soup.find_all('span', class_='speaker', attrs={'data-src-mp3': True})
            for element in audio_elements:
                if 'ameProns' in element['data-src-mp3']:
                    audio_url = element['data-src-mp3']
                    print(f"{word} 的朗文美式发音音频URL: {audio_url}")
                    return audio_url
            print(f"未找到 {word} 的朗文美式发音音频元素")
            return None
        else:
            print(f"无法访问 {word} 的朗文字典页面，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"访问朗文字典时发生错误: {e}")
        return None

# 关闭Anki应用程序
def close_anki():
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'anki.exe':
            process.terminate()
            process.wait()

close_anki()

# 连接Anki数据库
try:
    col = Collection(anki_col_path)

    # 获取所有笔记
    notes = col.find_notes("")

    for index, note_id in enumerate(notes):
        note = col.get_note(note_id)
        if "Text" in note:
            text = note.fields[note._field_index("Text")]
        else:
            print(f"笔记ID {note_id} 缺少Text字段，跳过。")
            continue

        if not text:
            continue

        query = text.strip()
        
        # 获取代理
        proxies, proxy_url = get_proxy()
        print(f"获取代理: {proxies}")

        # 先尝试从朗文字典获取音频
        audio_url = get_ldoce_pronunciation(query, proxies)
        
        # 如果朗文字典没有找到音频，则从剑桥词典获取
        if not audio_url:
            audio_url = get_cambridge_pronunciation(query, proxies)

        if audio_url:
            audio_filename = query.replace(' ', '_') + ".mp3"
            audio_path = os.path.join(media_folder, audio_filename)
            download_file(audio_url, audio_path, proxies)
            note.fields[note._field_index("Audio")] = f"[sound:{audio_filename}]"
        
        # 获取音标
        ipa = get_cambridge_ipa(query, proxies)
        if ipa:
            note.fields[note._field_index("音标")] = ipa

        col.update_note(note)
        delete_proxy(proxy_url)
        print(f"处理单词 {index + 1}/{len(notes)}: {query}")

    col.save()
    col.close()
except Exception as e:
    print(f"连接Anki数据库失败: {e}")
