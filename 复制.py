import pandas as pd

# 读取源文件
source_file_path = "C:\\Users\\17486\\Desktop\\updated_saladict_updated.xlsx"
source_df = pd.read_excel(source_file_path)

# 打印源文件的列名
print("源文件的列名：", source_df.columns)

# 读取目标文件
target_file_path = "C:\\Users\\17486\\Desktop\\saladict 0628.xlsx"
target_df = pd.read_excel(target_file_path)

# 打印目标文件的列名
print("目标文件的列名：", target_df.columns)

# 创建一个映射，将源文件的列名映射到目标文件的列索引
column_mapping = {
    'Audio': '_11',  # 目标文件的列名
    '美式音标': '_12',  # 目标文件的列名
    '英式音标': '_13'  # 目标文件的列名
}

# 假设目标文件中的单词列是'_1'
target_text_column = '_1'

# 遍历源文件的每一行，将相应列的内容复制到目标文件的对应列
for index, row in source_df.iterrows():
    text_field = row['Text']

    # 查找目标文件中对应的行，从第6行开始
    target_row_index = target_df[target_df[target_text_column] == text_field].index

    # 如果找到了对应行，则更新目标文件中的相应列
    if not target_row_index.empty:
        for source_column, target_column in column_mapping.items():
            target_df.at[target_row_index[0], target_column] = row[source_column]

# 保存更新后的目标文件
updated_target_file_path = "C:\\Users\\17486\\Desktop\\saladict_0628_updated.xlsx"
target_df.to_excel(updated_target_file_path, index=False)

print("复制完成，结果已保存到:", updated_target_file_path)

