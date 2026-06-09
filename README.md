# RAG_wd

这是一个按 `AGENTS.md` 生成的 PDF-first RAG 项目。系统会扫描输入文档，统一转换或处理为 PDF，解析文本，切分文本块，生成 embedding，保存本地向量索引，然后基于索引回答问题。

支持输入格式：

- PDF
- DOCX
- Markdown

DOCX 和 Markdown 会先转换为 PDF，再进入 PDF 解析流程。

## 1. 配置千问 API

复制配置模板：

```powershell
Copy-Item .env.example .env
```

打开 `.env`：

```powershell
notepad .env
```

填写你的千问 API Key：

```env
DASHSCOPE_API_KEY=你的apikey
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen-plus
QWEN_EMBEDDING_MODEL=text-embedding-v4
QWEN_EMBEDDING_DIMENSIONS=1024
```

说明：

- `DASHSCOPE_API_KEY`：你的阿里云百炼 / DashScope API Key。
- `QWEN_CHAT_MODEL`：聊天模型，默认 `qwen-plus`。
- `QWEN_EMBEDDING_MODEL`：embedding 模型，默认 `text-embedding-v4`。
- `QWEN_EMBEDDING_DIMENSIONS`：embedding 维度，默认 `1024`。

如果没有填写 API Key，项目仍可运行，但会使用本地简易 embedding 和检索结果展示，不会调用千问模型生成正式回答。

## 2. 放入文档

把需要构建索引的文件放到：

```text
data/input_docs/
```

示例：

```text
data/input_docs/example.pdf
data/input_docs/manual.docx
data/input_docs/notes.md
```

## 3. 构建索引

在项目根目录执行：

```powershell
python -m src.app build-index
```

构建流程：

```text
文件检测 -> 转 PDF -> 解析 PDF -> 文本切片 -> 生成 embedding -> 保存向量索引
```

输出文件：

```text
storage/converted_pdfs/   # DOCX/Markdown 转换后的 PDF
storage/parsed_texts/     # PDF 解析出的文本
storage/chunks.json       # 文本块和元数据
storage/index/vectors.json # 向量索引
```

## 4. 提问

构建索引后，可以直接提问：

```powershell
python -m src.app ask "这份文档主要讲什么？"
```

也可以进入交互模式：

```powershell
python -m src.app shell
```

交互模式会先构建索引，然后反复输入问题。输入 `exit`、`quit` 或 `q` 退出。

## 5. 构造 PDF 评测数据集

项目里已经提供了一套内置中文 PDF 评测集生成脚本：

```powershell
python -B scripts\build_sample_pdf_eval_dataset.py
```

这个脚本会生成：

```text
data/input_docs/RAG架构基础.pdf
data/input_docs/PDF评测数据集规范.pdf
data/input_docs/千问配置指南.pdf
storage/eval/pdf_eval_dataset.jsonl
```

`pdf_eval_dataset.jsonl` 中每一行都是一条中文评测样本，包含问题、标准答案和证据片段。

先放入 PDF 文档并构建索引：

```powershell
python -m src.app build-index
```

然后生成评测数据集：

```powershell
python -m src.eval_dataset --output storage/eval/pdf_eval_dataset.jsonl --questions-per-chunk 2 --max-chunks 100
```

参数说明：

- `--output`：评测集输出路径。
- `--questions-per-chunk`：每个文本块生成多少个问题。
- `--max-chunks`：最多使用多少个文本块生成评测数据。

输出格式是 JSONL，每行是一条评测样本：

```json
{
  "id": "example-1-1",
  "source": "data/input_docs/example.pdf",
  "pdf_path": "data/input_docs/example.pdf",
  "chunk_id": 1,
  "question": "问题",
  "answer": "标准答案",
  "evidence": "答案依据"
}
```

如果已配置千问 API Key，评测问题和答案会由千问聊天模型基于文本块生成；如果没有配置 Key，则只会生成基础 fallback 样本。

## 6. 评测这套 PDF 数据集

评测前先构建索引：

```powershell
python -B -m src.app build-index
```

然后运行评测脚本：

```powershell
python -B scripts\evaluate_pdf_dataset.py 3
```

命令最后的 `3` 表示 `top_k=3`，也就是每个问题检索前 3 个最相关文本块。

评测脚本会读取：

```text
storage/eval/pdf_eval_dataset.jsonl
storage/index/vectors.json
storage/chunks.json
```

它会对每条评测样本执行：

```text
读取问题 -> 生成问题向量 -> 查询向量索引 -> 返回 top_k 文本块 -> 检查命中情况
```

当前评测指标：

- `源文档命中率`：标准答案所在 PDF 是否出现在 top_k 检索结果中。
- `证据片段命中率`：标准证据句子是否出现在 top_k 检索文本中。

评测报告会写入：

```text
storage/eval/pdf_eval_report.json
```

示例输出：

```text
评测样本数: 9
Top-3 源文档命中率: 100.00%
Top-3 证据片段命中率: 100.00%
评测报告: storage/eval/pdf_eval_report.json
```

注意：这套评测首先衡量“检索是否找到了正确证据”。如果配置了千问 API，还可以进一步评测生成答案是否与 `answer` 字段一致；当前脚本先做检索侧评测，便于快速定位索引、切片、embedding 或向量检索的问题。

## 7. 常用命令

```powershell
# 生成内置中文 PDF 评测集
python -B scripts\build_sample_pdf_eval_dataset.py

# 构建索引
python -B -m src.app build-index

# 单次提问
python -B -m src.app ask "你的问题"

# 交互式问答
python -B -m src.app shell

# 基于已有索引生成模型评测数据集
python -m src.eval_dataset --output storage/eval/pdf_eval_dataset.jsonl --questions-per-chunk 2 --max-chunks 100

# 评测内置中文 PDF 数据集
python -B scripts\evaluate_pdf_dataset.py 3
```
