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

# 设置剑桥字典URL模板
url_template = "https://dictionary.cambridge.org/zhs/%E8%AF%8D%E5%85%B8/%E8%8B%B1%E8%AF%AD/{}"

# 自定义请求头
headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "49.2950.2956.2958.2961.2963.2964.2965.2966.2968.2973.2975.2979.2980.2981.2983.2985.2986.2987.2994.2995.2997.2999.3000.3002.3003.3005.3008.3009.3010.3012.3016.3017.3018.3019.3024.3025.3028.3034.3038.3043.3048.3052.3053.3055.3058.3059.3063.3066.3068.3070.3073.3074.3075.3076.3077.3078.3089.3090.3093.3094.3095.3097.3099.3100.3106.3109.3112.3117.3119.3126.3127.3128.3130.3135.3136.3145.3150.3151.3154.3155.3163.3167.3172.3173.3182.3183.3184.3185.3187.3188.3189.3190.3194.3196.3209.3210.3211.3214.3215.3217.3219.3222.3223.3225.3226.3227.3228.3230.3231.3234.3235.3236.3237.3238.3240.3244.3245.3250.3251.3253.3257.3260.3270.3272.3281.3288.3290.3292.3293.3296.3299.3300.3306.3307.3309.3314.3315.3316.3318.3324.3328.3330.3531.3731.3831.3931.4131.4531.4631.4731.4831.5231.6931.7031.7235.7831.7931.8931.9731.10231.10631.10831.11031.11531.12831.13632.13731.14237.14332.15731.16831.16931.21233.23031.24431.25731.25931.26031.26831.27731.28031.28731.28831.29631; usprivacy=1YNN; OneTrustWPCCPAGoogleOptOut=false; XSRF-TOKEN=9cde3263-9976-4a81-b97d-3b482a0f0589; OptanonAlertBoxClosed=2024-06-27T09:39:57.512Z; beta-redesign=active; _cfuvid=m54tJDOWuc_C84ydl4o0GIrAEpRyrsGPPVcirzlekTM-1719626561830-0.0.1.1-604800000; cf_clearance=N54wNS8T8dtDhrUlA11L1OVxOo8yewaAzoge2JCdEH0-1719626564-1.0.1.1-4Tlp9jalJqJ2ThRVnAck7fKLyTcRGdbpMRAJIJvJr.6N4Uq6lxrppIHrPVSTLzoZT8y.kFjnHhuykNwzGr9OEg; _sp_ses.7ecc=*; preferredDictionaries=\"english,english-chinese-simplified,english-russian,british-grammar,english-polish\"; loginPopup=32; OptanonConsent=isGpcEnabled=0&datestamp=Sun+Jun+30+2024+12%3A11%3A39+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CBG95%3A1&consentId=7b99cdd0-ef35-4632-a7b7-9e663d704b07&interactionCount=2&isAnonUser=1&AwaitingReconsent=false&geolocation=US%3BCA; _sp_id.7ecc=26a2ad3e-4117-4938-abaf-5626cb88c0d5.1708303951.16.1719720700.1719631934.c326e89d-dc04-44e8-ac21-5b22b4d8473f.dfb7dfa5-c1cb-43c6-8673-1c7305d0b007.58fe8a45-ca71-41f4-b506-cc388034ca27.1719719449907.36",  # 请在此处补充您的Cookie
    "Referer": "https://dictionary.cambridge.org/zhs/%E8%AF%8D%E5%85%B8/%E8%8B%B1%E8%AF%AD/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
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
        response = session.get(url, stream=True, headers=headers, proxies=proxies, timeout=20)
        total_size = int(response.headers.get('content-length', 0))
        if response.status_code == 200:
            with open(filename, 'wb') as f, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
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
            audio_element = soup.find('source', {'type': 'audio/mpeg'})
            if audio_element:
                audio_url = audio_element['src']
                print(f"{query} 的音频URL: {audio_url}")
                if audio_url.startswith('/'):
                    audio_url = 'https://dictionary.cambridge.org' + audio_url
                print(f"完整的音频URL: {audio_url}")
                # 下载音频文件
                audio_filename = query.replace(' ', '_') + ".mp3"  # 使用查询内容作为文件名，空格替换为下划线
                audio_path = os.path.join(media_folder, audio_filename)
                download_file(audio_url, audio_path, proxies)

                # 更新Audio字段
                note.fields[note._field_index("Audio")] = f"[sound:{audio_filename}]"
                note.flush()
            else:
                print(f"未找到 {query} 的音频元素")
        else:
            print(f"无法访问 {query} 的字典页面")

    # 保存更改
    col.save()
    col.close()
except Exception as e:
    print(f"连接Anki数据库失败: {e}")
