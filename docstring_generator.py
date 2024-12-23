import os
from openai import OpenAI
from pathlib import Path
import ast
import re

class DocstringGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url='https://xiaoai.plus/v1',
            api_key=api_key
        )

    def get_project_stats(self, directory_path):
        stats = {'file_count': 0, 'char_count': 0, 'line_count': 0, 'function_count': 0, 'total_function_lines': 0}
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    stats['file_count'] += 1
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        stats['char_count'] += len(content)
                        stats['line_count'] += len(content.splitlines())
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                    stats['function_count'] += 1
                                    stats['total_function_lines'] += len(node.body)
                        except:
                            continue
        return stats

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        new_content = content
        offset = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                code_segment = ast.get_source_segment(content, node)
                prompt = f"为以下Python代码生成详细的docstring描述，包括功能、参数和返回值（如果适用）:\n\n{code_segment}\n\n"
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                docstring = response.choices[0].message.content.strip()
                if not node.body or not isinstance(node.body[0], ast.Expr) or not isinstance(node.body[0].value, ast.Str):
                    docstring = f'"""\n{docstring}\n"""'
                    insert_position = node.body[0].lineno - 1 + offset
                    lines = new_content.splitlines()
                    lines.insert(insert_position, docstring)
                    new_content = "\n".join(lines)
                    offset += 1

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def process_with_confirmation(self, directory_path):
        stats = self.get_project_stats(directory_path)
        print("\n项目统计信息:")
        print(f"Python文件数量: {stats['file_count']}")
        print(f"总字符数: {stats['char_count']}")
        print(f"总代码行数: {stats['line_count']}")
        print(f"总函数/类数量: {stats['function_count']}")
        avg_lines = (stats['total_function_lines'] / stats['function_count'] if stats['function_count'] > 0 else 0)
        print(f"平均函数/类行数: {avg_lines:.2f}")
        
        response = input("\n是否开始生成docstring注释？(y/n): ")
        if response.lower() == 'y':
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        self.process_file(str(file_path))
            print("\n所有文件处理完成！")
        else:
            print("\n操作已取消")

if __name__ == "__main__":
    api_key = input("请输入你的OpenAI API密钥: ")
    project_path = input("请输入项目文件夹路径: ")
    if not os.path.exists(project_path):
        print("错误：指定的路径不存在！")
        exit(1)
    generator = DocstringGenerator(api_key)
    generator.process_with_confirmation(project_path) 