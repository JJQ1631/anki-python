import os  
import requests  
from bs4 import BeautifulSoup  
from requests.adapters import HTTPAdapter  
from urllib3.util.retry import Retry  
  
# 设置媒体库路径  
media_folder = "E:\\test"  
if not os.path.exists(media_folder):  
    os.makedirs(media_folder)  
  
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
    try:  
        proxy = requests.get("http://127.0.0.1:5010/get/").json()  
        proxy_url = proxy.get("proxy")  
        proxies = {  
            "http": f"http://{proxy_url}"  
        }  
        return proxies, proxy_url  
    except Exception as e:  
        print(f"获取代理时发生错误: {e}")  
        return None, None  
  
def delete_proxy(proxy):  
    if proxy:  
        try:  
            requests.get(f"http://127.0.0.1:5010/delete/?proxy={proxy}")  
        except Exception as e:  
            print(f"删除代理时发生错误: {e}")  
  
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
  
# 下载音频主函数  
def download_audio(word):  
    proxies, proxy_url = get_proxy()  
    if not proxies:  
        print(f"无法获取代理，跳过单词: {word}")  
        return  
  
    audio_url = get_ldoce_pronunciation(word, proxies)  
    if not audio_url:  
        audio_url = get_cambridge_pronunciation(word, proxies)  
  
    if audio_url:  
        audio_filename = word.replace(' ', '_') + ".mp3"  
        audio_path = os.path.join(media_folder, audio_filename)  
        download_file(audio_url, audio_path, proxies)  
    else:  
        print(f"无法找到 {word} 的音频URL")  
  
    delete_proxy(proxy_url)  
  
# 测试函数  
def test_download_audio():  
    test_words = ["Preliminary",  "machine"]  
    for word in test_words:  
        download_audio(word)  
  
# 运行测试  
test_download_audio()


