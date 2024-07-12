import os
import requests

# 设置Anki媒体库路径
media_folder = "C:\\Users\\17486\\AppData\\Roaming\\Anki2\\账户1\\collection.media"

# Anki Connect API 地址
anki_connect_url = "http://localhost:8765"

# 获取媒体库中的音频文件
def get_audio_files(media_folder):
    audio_files = [f for f in os.listdir(media_folder) if f.endswith(".mp3")]
    return {os.path.splitext(f)[0]: f for f in audio_files}

# 通过Anki Connect获取Saladict牌组的所有卡片ID
def get_cards(deck_name):
    payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            "query": f"deck:{deck_name}"
        }
    }
    response = requests.post(anki_connect_url, json=payload).json()
    return response.get("result", [])

# 通过Anki Connect获取卡片的详细信息
def get_card_info(card_ids):
    payload = {
        "action": "cardsInfo",
        "version": 6,
        "params": {
            "cards": card_ids
        }
    }
    response = requests.post(anki_connect_url, json=payload).json()
    return response.get("result", [])

# 通过Anki Connect获取笔记的详细信息
def get_note_info(note_ids):
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    }
    response = requests.post(anki_connect_url, json=payload).json()
    return response.get("result", [])

# 通过Anki Connect更新笔记的Audio字段
def update_note_audio(note_id, audio_field):
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    "Audio": audio_field
                }
            }
        }
    }
    response = requests.post(anki_connect_url, json=payload).json()
    return response.get("result")

# 主函数
def main():
    deck_name = "Saladict"
    audio_files = get_audio_files(media_folder)
    print(f"找到 {len(audio_files)} 个音频文件")

    card_ids = get_cards(deck_name)
    print(f"找到 {len(card_ids)} 个卡片")

    if not card_ids:
        print(f"牌组 {deck_name} 中没有找到任何卡片")
        return

    card_infos = get_card_info(card_ids)

    note_ids = list(set(card['note'] for card in card_infos))
    print(f"找到 {len(note_ids)} 个笔记")

    note_infos = get_note_info(note_ids)

    for note_info in note_infos:
        note_id = note_info['noteId']
        fields = note_info['fields']

        # 打印 fields 的内容以调试
        print(f"Note ID: {note_id}, Fields: {fields}")

        # 查找包含单词的字段
        text_field = None
        for field_name, field_value in fields.items():
            # 打印每个字段的名称和内容以帮助调试
            print(f"Field Name: {field_name}, Field Value: {field_value}")

            if isinstance(field_value, dict) and 'value' in field_value:
                stripped_value = field_value['value'].strip()
                if stripped_value in audio_files:
                    text_field = stripped_value
                    break

        if text_field:
            audio_filename = audio_files.get(text_field)
            if audio_filename:
                audio_field = f"[sound:{audio_filename}]"
                update_result = update_note_audio(note_id, audio_field)
                if update_result:
                    print(f"Updated note {note_id} with audio file {audio_filename}")
                else:
                    print(f"Failed to update note {note_id}")
            else:
                print(f"Audio file for {text_field} not found in media folder")
        else:
            print(f"Text field for note {note_id} is missing or not a string")

if __name__ == "__main__":
    main()
