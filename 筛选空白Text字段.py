import json
import requests
import pandas as pd

# AnkiConnect的端口号
ANKI_CONNECT_URL = 'http://localhost:8765'

# 发送请求到AnkiConnect
def invoke(action, **params):
    return json.loads(requests.post(ANKI_CONNECT_URL, json.dumps({'action': action, 'params': params, 'version': 6})).text)

# 获取指定牌组的所有笔记
def get_notes(deck_name):
    query = f'deck:"{deck_name}"'
    response = invoke('findNotes', query=query)
    return response['result']

# 获取笔记的详细信息
def get_note_info(note_ids):
    response = invoke('notesInfo', notes=note_ids)
    return response['result']

# 主函数
def main():
    deck_name = "Saladict"
    notes = get_notes(deck_name)
    notes_info = get_note_info(notes)

    empty_text_notes = []

    for note in notes_info:
        text_field = note['fields']['Text']['value']
        if not text_field.strip():  # 检查Text字段是否为空白
            note_id = note['noteId']
            context_cloze_field = note['fields']['ContextCloze']['value']
            empty_text_notes.append({'Note ID': note_id, 'ContextCloze': context_cloze_field})

    # 将筛选结果导出到Excel表格
    df = pd.DataFrame(empty_text_notes)
    df.to_excel('empty_text_notes.xlsx', index=False)
    print("导出完成，文件名为 empty_text_notes.xlsx")

if __name__ == "__main__":
    main()
