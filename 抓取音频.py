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

# 设置朗文词典URL模板
url_template = "https://www.ldoceonline.com/dictionary/{}"

# 自定义请求头
headers_template = {
    "Accept": "*/*",
    "Accept-Encoding": "identity;q=1, *;q=0",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Cookie": "OptanonConsent=isGpcEnabled=0&datestamp=Thu+Jul+04+2024+11%3A47%3A09+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202404.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=US%3B&AwaitingReconsent=false; OptanonAlertBoxClosed=2024-07-04T03:47:09.626Z",
    "Host": "www.ldoceonline.com",
    "Pragma": "no-cache",
    "Range": "bytes=0-",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "audio",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
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

    for note_id in notes:
        note = col.get_note(note_id)
        if "Text" in note:
            text = note.fields[note._field_index("Text")]
        else:
            print(f"笔记ID {note_id} 缺少Text字段，跳过。")
            continue

        if not text:
            continue

        query = text.strip()  # 使用完整的Text字段作为查询内容
        query_url = url_template.format(query)
        
        headers = headers_template.copy()
        headers["Referer"] = query_url
        
        # 获取代理
        proxies, proxy_url = get_proxy()
        print(f"获取代理: {proxies}")

        retry_count = 5
        while retry_count > 0:
            try:
                response = requests.get(query_url, headers=headers, proxies=proxies, timeout=20)
                print(f"使用代理 {proxies} 请求 {query_url}")
                print(f"访问页面，状态码: {response.status_code}")
                break
            except Exception as e:
                print(f"请求失败，剩余重试次数: {retry_count - 1}")
                retry_count -= 1
                delete_proxy(proxy_url)
                proxies, proxy_url = get_proxy()

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # 寻找美式发音的音频URL
            audio_elements = soup.find_all('span', class_='speaker', attrs={'data-src-mp3': True})  # 找到所有包含音频URL的元素
            audio_url = None
            for element in audio_elements:
                if 'ameProns' in element['data-src-mp3']:
                    audio_url = element['data-src-mp3']
                    break

            if audio_url:
                print(f"{query} 的音频URL: {audio_url}")
                # 下载音频文件
                audio_filename = query.replace(' ', '_') + ".mp3"  # 使用查询内容作为文件名，空格替换为下划线
                audio_path = os.path.join(media_folder, audio_filename)
                download_file(audio_url, audio_path, proxies)

                # 更新Audio字段
                note.fields[note._field_index("Audio")] = f"[sound:{audio_filename}]"
                col.update_note(note)  # 使用更新的方法
            else:
                print(f"未找到 {query} 的美式发音音频元素")
        else:
            print(f"无法访问 {query} 的字典页面")

    # 保存更改
    col.save()
    col.close()
except Exception as e:
    print(f"连接Anki数据库失败: {e}")
