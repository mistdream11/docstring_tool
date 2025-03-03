import os
import ast
from openai import OpenAI
from pathlib import Path

class DocstringGenerator:
    def __init__(self, api_key):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url='https://az.gptplus5.com/v1',  # 自定义 API 地址
            api_key=api_key
        )

    def get_project_stats(self, directory_path):
        """统计项目中的 Python 文件数量、字符数、代码行数、函数数量等信息"""
        stats = {
            'file_count': 0,
            'char_count': 0,
            'line_count': 0,
            'function_count': 0,
            'total_function_lines': 0
        }

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
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    stats['function_count'] += 1
                                    stats['total_function_lines'] += (node.end_lineno - node.lineno + 1)
                        except SyntaxError as e:
                            print(f"文件 {file_path} 解析失败: {str(e)}")
                            continue

        return stats

    def has_docstring(self, node):
        """检查函数或类是否已经有 docstring"""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, (ast.Str, ast.Constant)):
                return True
        return False

    def generate_docstring(self, code_segment):
        """调用 OpenAI API 生成 docstring"""
        prompt = f"""请为以下 Python 代码生成注释的文本，只需要文本即可：
要求包含以下内容（中英文均可）：
1. 功能描述
2. 参数说明（如有）
3. 返回值说明（如有）
4. 使用示例（可选）


代码：
{code_segment}
在回答的生成的docstring中不重复写出原代码
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 替换为实际的 GPT-4-mini 模型名称
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            docstring = response.choices[0].message.content.strip()
            # 确保 docstring 使用三重双引号包裹
            if not docstring.startswith('"""'):
                docstring = f'"""{docstring}\n"""'
            return docstring
        except Exception as e:
            print(f"API 调用失败: {str(e)}")
            return None

    def process_file(self, file_path):
        """处理单个 Python 文件，为函数生成 docstring"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"文件 {file_path} 解析失败: {str(e)}")
            return

        # 按行号逆序处理，避免修改偏移问题
        nodes = sorted([
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ], key=lambda x: x.lineno, reverse=True)

        lines = content.splitlines(keepends=True)
        modified = False

        for node in nodes:
            # 如果已有 docstring，则跳过
            if self.has_docstring(node):
                continue

            # 获取代码段
            code_segment = ast.get_source_segment(content, node)
            if not code_segment:
                continue

            # 生成 docstring
            docstring = self.generate_docstring(code_segment)
            if not docstring:
                continue

            # 计算插入位置
            insert_line = node.body[0].lineno - 1 if node.body else node.lineno - 1

            # 计算缩进
            indent = " " * (node.col_offset + 4)  # 保持缩进格式

            # 插入 docstring
            lines.insert(insert_line, indent + docstring + "\n")
            modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"已处理文件: {file_path}")

    def process_with_confirmation(self, directory_path):
        """遍历项目文件夹并生成 docstring"""
        stats = self.get_project_stats(directory_path)
        print("\n项目统计信息:")
        print(f"Python 文件数量: {stats['file_count']}")
        print(f"总字符数: {stats['char_count']}")
        print(f"总代码行数: {stats['line_count']}")
        print(f"总函数数量: {stats['function_count']}")
        avg_lines = (stats['total_function_lines'] / stats['function_count'] if stats['function_count'] > 0 else 0)
        print(f"每个函数的平均行数: {avg_lines:.2f}")

        proceed = input("\n是否开始生成 docstring 注释？(y/n): ").lower()
        if proceed == 'y':
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        self.process_file(str(file_path))
            print("\n所有文件处理完成！")
        else:
            print("\n操作已取消。")


if __name__ == "__main__":
    api_key = input("请输入 OpenAI API 密钥: ")
    project_path = input("请输入项目文件夹路径: ")

    if not os.path.exists(project_path):
        print("错误：指定的路径不存在！")
        exit(1)

    generator = DocstringGenerator(api_key)
    generator.process_with_confirmation(project_path)