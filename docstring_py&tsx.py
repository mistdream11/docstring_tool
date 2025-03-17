import os
import ast
from openai import OpenAI
from pathlib import Path
import re

class DocstringGenerator:
    def __init__(self, api_key):
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url='https://az.gptplus5.com/v1',
            api_key=api_key
        )

    def get_project_stats(self, directory_path):
        """统计项目中 Python 和 TypeScript 文件的统计信息"""
        stats = {
            'py': {'file_count': 0, 'char_count': 0, 'line_count': 0, 'function_count': 0},
            'ts': {'file_count': 0, 'char_count': 0, 'line_count': 0, 'function_count': 0}
        }

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_type = None
                if file.endswith('.py'):
                    file_type = 'py'
                elif file.endswith(('.ts', '.tsx')):
                    file_type = 'ts'
                
                if file_type:
                    file_path = Path(root) / file
                    stats[file_type]['file_count'] += 1
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        stats[file_type]['char_count'] += len(content)
                        stats[file_type]['line_count'] += len(content.splitlines())

                        # 统计函数数量
                        if file_type == 'py':
                            try:
                                tree = ast.parse(content)
                                stats[file_type]['function_count'] += len([
                                    node for node in ast.walk(tree)
                                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                                ])
                            except SyntaxError:
                                pass
                        elif file_type == 'ts':
                            # 使用正则表达式统计 TypeScript 函数
                            stats[file_type]['function_count'] += len(re.findall(
                                r'(?:function|const\s+\w+\s*=\s*|class\s+\w+\s*{[\s\S]*?)(\b\w+\s*\([^)]*\))',
                                content
                            ))

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
        """处理单个文件（Python 或 TypeScript）"""
        if file_path.endswith('.py'):
            self._process_python_file(file_path)
        elif file_path.endswith(('.ts', '.tsx')):
            self._process_typescript_file(file_path)

    def _process_python_file(self, file_path):
        """处理 Python 文件（原有逻辑）"""
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

    def _process_typescript_file(self, file_path):
        """处理 TypeScript 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式查找函数定义
        pattern = r'''(?x)
        (?:^|\n)                         # 开头或换行后
        ((\/\/.*?\n)*)                   # 已有注释
        (?:export\s+)?                   # 可能有 export
        (?:async\s+)?                    # 可能有 async
        (function\s+\w+\s*\([^)]*\)\s*{  # 函数声明
        |const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{  # 箭头函数
        |class\s+\w+\s*{[\s\S]*?^\s*\w+\s*\([^)]*\)\s*{  # 类方法
        )'''

        matches = list(re.finditer(pattern, content, re.MULTILINE))
        modified = False

        # 逆序处理避免影响行号
        for match in reversed(matches):
            full_match = match.group(0)
            existing_comments = match.group(1) or ''

            # 如果已有 JSDoc 注释则跳过
            if '/**' in existing_comments:
                continue

            # 提取函数签名
            func_signature = re.search(r'(\w+\s*\([^)]*\))', full_match).group(1)

            # 生成注释
            docstring = self.generate_docstring(func_signature)
            if not docstring:
                continue

            # 转换格式为 JSDoc
            jsdoc = f"/**\n * {docstring.replace('\n', '\n * ')}\n */\n"

            # 插入注释
            start_pos = match.start()
            new_content = content[:start_pos] + jsdoc + content[start_pos:]
            content = new_content
            modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已处理 TypeScript 文件: {file_path}")

    def process_with_confirmation(self, directory_path):
        """遍历项目文件夹并生成注释"""
        stats = self.get_project_stats(directory_path)
        
        print("\n项目统计信息:")
        print("=== Python ===")
        print(f"文件数量: {stats['py']['file_count']}")
        print(f"函数数量: {stats['py']['function_count']}")
        
        print("\n=== TypeScript ===")
        print(f"文件数量: {stats['ts']['file_count']}")
        print(f"函数/方法数量: {stats['ts']['function_count']}")

        proceed = input("\n是否开始生成注释？(y/n): ").lower()
        if proceed == 'y':
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = Path(root) / file
                    if file.endswith(('.py', '.ts', '.tsx')):
                        self.process_file(str(file_path))
            print("\n所有文件处理完成！")
        else:
            print("\n操作已取消。")

# ... 其他方法保持不变 ...

if __name__ == "__main__":
    api_key = input("请输入 OpenAI API 密钥: ")
    project_path = input("请输入项目文件夹路径: ")

    if not os.path.exists(project_path):
        print("错误：指定的路径不存在！")
        exit(1)

    generator = DocstringGenerator(api_key)
    generator.process_with_confirmation(project_path)