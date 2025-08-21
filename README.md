# AI智能旅游咨询专家系统

基于 ChatGPT 和阿里通义千问的智能旅游咨询系统，支持自然语言对话、旅游目的地推荐、行程规划、景点介绍等功能。

## 功能特点

- **自然语言对话**：基于 ChatGPT 的智能对话能力
- **旅游目的地推荐**：根据用户需求推荐合适的旅游目的地
- **行程规划**：帮助用户制定详细的旅游行程
- **景点介绍**：详细介绍特定景点的特色、最佳游览时间等
- **酒店推荐**：根据预算、位置、设施需求推荐合适的酒店
- **交通建议**：提供到达目的地的最佳交通方式
- **美食推荐**：推荐当地特色美食、餐厅、小吃街等
- **文化体验**：介绍当地文化特色、民俗活动、节日庆典等
- **多用户会话上下文管理**：保持对话连贯性
- **RESTful API 接口**：提供标准化的 API 接口
- **微信接入**：支持微信公众号接入

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入实际配置：

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
python scripts/start_assistant.py

# 或直接使用uvicorn
uvicorn src.ai_smart_assistant.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 验证服务

服务启动后，访问以下地址：

- **API 文档**: http://localhost:8000/docs
- **聊天接口**: http://localhost:8000/chat
- **微信接口**: http://localhost:8000/wechat

## 环境变量配置

### 必需配置

```env
# LLM配置
DEFAULT_LLM_TYPE=gpt4  # 可选: gpt4, gpt5, qianwen

# OpenAI配置（当DEFAULT_LLM_TYPE=gpt4或gpt5时必需）
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-4
OPENAI_GPT5_MODEL_NAME=gpt-5
OPENAI_TEMPERATURE=0.7
# OPENAI_API_BASE=https://api.openai-proxy.org/v1  # 可选：CloseAI代理地址

# 通义千问配置（当DEFAULT_LLM_TYPE=qianwen时必需）
DASHSCOPE_API_KEY=your_dashscope_api_key
QIANWEN_MODEL_NAME=qwen-turbo
QIANWEN_TEMPERATURE=0.7

# 应用配置
APP_NAME=AI智能旅游咨询专家
APP_VERSION=1.0.0
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000
WORKERS=1
```

### 可选配置

```env
# Redis缓存配置
USE_REDIS_CACHE=true
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=xxx

# 企业微信配置
WECOM_CORP_ID=xxx
WECOM_AGENT_ID=xxx
WECOM_AGENT_SECRET=xxx
WECOM_TOKEN=xxx
WECOM_ENCODING_AES_KEY=xxx
```

## API 使用

### 聊天接口

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "我想去云南旅游，有什么推荐吗？",
    "user_id": "user123"
  }'
```

### 微信接口

微信接口支持微信公众号的消息接收和回复，需要在微信公众平台配置相应的URL。

## 项目结构

```
src/ai_smart_traveller/
├── api/                    # API接口
│   ├── chat.py           # 聊天接口
│   └── wechat.py         # 微信接口
├── core/                  # 核心功能
│   ├── agent_builder.py  # Agent构建器
│   ├── app_factory.py    # 应用工厂
│   ├── config.py         # 配置管理
│   ├── llm_factory.py    # LLM工厂
│   ├── logging.py        # 日志配置
│   └── prompts.py        # 提示词配置
├── models/                # 数据模型
│   └── memory_manager.py # 记忆管理器
└── main.py               # 主程序入口
```

## 特色功能

### 智能旅游咨询
- **个性化推荐**：根据用户预算、时间、兴趣等提供个性化旅游建议
- **实时信息**：提供最新的旅游政策、签证要求、疫情防控等信息
- **专业建议**：基于丰富的旅游行业经验，提供专业的旅游咨询

### 多平台接入
- **RESTful API**：标准化的API接口，支持各种客户端接入
- **微信公众号**：支持微信公众号的消息接收和智能回复
- **Web界面**：提供友好的Web聊天界面

### 智能对话
- **上下文记忆**：保持对话连贯性，理解用户意图
- **自然语言理解**：支持自然语言输入，无需特定格式
- **多轮对话**：支持复杂的多轮对话和问题澄清

## 技术架构

- **后端框架**：FastAPI
- **AI模型**：OpenAI GPT-4/5、阿里通义千问
- **对话管理**：LangChain
- **缓存系统**：Redis（可选）
- **日志系统**：结构化日志记录

## 部署说明

### 生产环境部署

```bash
# 使用生产启动脚本
./start_assistant_prod.sh
```

### Docker部署

```bash
# 构建镜像
docker build -t ai-travel-advisor .

# 运行容器
docker run -d -p 8000:8000 --env-file .env ai-travel-advisor
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。
