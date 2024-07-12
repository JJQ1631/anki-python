import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import random
from tqdm import tqdm

# 设置 AnkiConnect 的端口
ANKI_CONNECT_PORT = 8765

# 剑桥词典查询的URL模板
CAMBRIDGE_URL = "https://dictionary.cambridge.org/dictionary/english/"

# 设置多个自定义请求头
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
]


def invoke(action, params):
    request_json = json.dumps({
        'action': action,
        'version': 6,
        'params': params
    })
    response = requests.post(f'http://localhost:{ANKI_CONNECT_PORT}', data=request_json)
    response_json = json.loads(response.text)
    if len(response_json) != 2:
        raise Exception('响应格式错误')
    if 'error' in response_json:
        if response_json['error'] is not None:
            raise Exception(response_json['error'])
    return response_json['result']


def get_notes_with_empty_pronunciations(deck_name):
    query = f'deck:{deck_name} "美式音标:" "英式音标:"'
    note_ids = invoke('findNotes', {'query': query})
    return note_ids


def get_note_fields(note_ids):
    notes = invoke('notesInfo', {'notes': note_ids})
    return notes


def find_empty_pronunciation_notes(deck_name):
    note_ids = get_notes_with_empty_pronunciations(deck_name)
    notes = get_note_fields(note_ids)

    empty_pronunciation_notes = []

    for note in notes:
        fields = note['fields']
        american_pronunciation = fields['美式音标']['value']
        british_pronunciation = fields['英式音标']['value']

        if not isinstance(american_pronunciation, str):
            american_pronunciation = ""
        if not isinstance(british_pronunciation, str):
            british_pronunciation = ""

        if not american_pronunciation.strip() or not british_pronunciation.strip():
            empty_pronunciation_notes.append({
                'Note ID': note['noteId'],
                'Text': fields['Text']['value'],
                'Audio': fields['Audio']['value'],
                '美式音标': american_pronunciation,
                '英式音标': british_pronunciation
            })

    return empty_pronunciation_notes


def get_pronunciations_from_cambridge(word):
    url = CAMBRIDGE_URL + word
    headers = random.choice(HEADERS_LIST)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    us_pron = soup.find('span', class_='us dpron-i')
    uk_pron = soup.find('span', class_='uk dpron-i')

    us_phonetic = f"/{us_pron.find('span', class_='ipa').text.strip()}/" if us_pron and us_pron.find('span',
                                                                                                     class_='ipa') else ""
    uk_phonetic = f"/{uk_pron.find('span', class_='ipa').text.strip()}/" if uk_pron and uk_pron.find('span',
                                                                                                     class_='ipa') else ""

    return us_phonetic, uk_phonetic


def update_note_field(note_id, field_name, value):
    params = {
        'note': {
            'id': note_id,
            'fields': {
                field_name: value
            }
        }
    }
    invoke('updateNoteFields', params)


# 主程序
deck_name = "Saladict"
empty_pronunciation_notes = find_empty_pronunciation_notes(deck_name)

if empty_pronunciation_notes:
    for note in tqdm(empty_pronunciation_notes, desc="Processing notes", unit="note"):
        text = note['Text']
        note_id = note['Note ID']

        # 如果是短语，将其拆分成单词
        words = text.split()

        us_phonetics = []
        uk_phonetics = []

        for word in words:
            us_phonetic, uk_phonetic = get_pronunciations_from_cambridge(word)
            if us_phonetic:
                us_phonetics.append(us_phonetic)
            if uk_phonetic:
                uk_phonetics.append(uk_phonetic)

        # 将多个单词的音标合并
        us_phonetic_combined = " ".join(us_phonetics)
        uk_phonetic_combined = " ".join(uk_phonetics)

        # 更新音标字段
        if us_phonetic_combined:
            update_note_field(note_id, '美式音标', us_phonetic_combined)
            print(f"Updated note {note_id}: 美式音标 => {us_phonetic_combined}")
        if uk_phonetic_combined:
            update_note_field(note_id, '英式音标', uk_phonetic_combined)
            print(f"Updated note {note_id}: 英式音标 => {uk_phonetic_combined}")
else:
    print("没有找到音标字段为空的笔记。")
