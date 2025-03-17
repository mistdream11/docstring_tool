### 项目概述
此项目为 `DocstringGenerator` 类，其功能是为 Python 与 TypeScript 项目中的函数与类自动生成文档字符串。借助 OpenAI API，该工具能分析代码并生成规范的文档字符串，从而提升代码的可读性与可维护性。

### 功能特性
1. **项目统计**：对项目里的 Python 和 TypeScript 文件的数量、字符数、行数以及函数数量进行统计。
2. **文档字符串生成**：利用 OpenAI API 为缺少文档字符串的函数和类生成相应的文档字符串。
3. **支持多语言**：支持 Python 和 TypeScript 两种编程语言。
4. **确认机制**：在处理文件之前，会显示项目统计信息，并且让用户确认是否继续操作。

### 安装依赖
要运行此项目，你得安装 `openai` 库。可以使用以下命令进行安装：
```bash
pip install openai
```

### 使用方法
1. **运行脚本**：
    - 确保你已经安装了所需的依赖。
    - 运行脚本，按照提示输入 OpenAI API 密钥和项目文件夹路径。
```bash
python script_name.py  # 将 script_name.py 替换为实际的脚本文件名
```
2. **确认操作**：
    - 脚本会展示项目的统计信息，询问你是否开始生成注释。
    - 输入 `y` 开始处理，输入 `n` 则取消操作。

### 代码结构
- **`__init__` 方法**：初始化 OpenAI 客户端。
- **`get_project_stats` 方法**：统计项目中 Python 和 TypeScript 文件的相关信息。
- **`has_docstring` 方法**：检查函数或类是否已有文档字符串。
- **`generate_docstring` 方法**：调用 OpenAI API 来生成文档字符串。
- **`process_file` 方法**：依据文件类型处理单个文件。
- **`_process_python_file` 方法**：处理 Python 文件。
- **`_process_typescript_file` 方法**：处理 TypeScript 文件。
- **`process_with_confirmation` 方法**：遍历项目文件夹，显示统计信息，等待用户确认后开始处理文件。

### 注意事项
- 要保证你的 OpenAI API 密钥有效，不然 API 调用会失败。
- 对于 Python 文件，使用 `ast` 模块进行解析；对于 TypeScript 文件，使用正则表达式来查找函数定义。
- 处理大型项目时，由于 API 调用次数较多，可能会产生较高的费用，要谨慎操作。

### 示例运行
```
请输入 OpenAI API 密钥: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
请输入项目文件夹路径: /path/to/your/project

项目统计信息:
=== Python ===
文件数量: 10
函数数量: 50

=== TypeScript ===
文件数量: 5
函数/方法数量: 20

是否开始生成注释？(y/n): y

已处理文件: /path/to/your/project/file1.py
已处理文件: /path/to/your/project/file2.py
已处理 TypeScript 文件: /path/to/your/project/file3.ts

所有文件处理完成！
```

### 错误处理
- 若文件解析失败，脚本会输出错误信息并跳过该文件。
- 若 API 调用失败，脚本会输出错误信息并跳过生成文档字符串的步骤。

### 贡献与反馈
若你发现任何问题或者有改进建议，请在项目的 GitHub 仓库中提交 issue 或者 pull request。
