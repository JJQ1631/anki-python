def convert_first_letter_to_lowercase(text):
    if not text:
        return text
    return text[0].lower() + text[1:]

# 测试函数
test_strings = [
    "Outspend",
    "WORLD",
    
]

for string in test_strings:
    print(f"Original: {string} -> Converted: {convert_first_letter_to_lowercase(string)}")
