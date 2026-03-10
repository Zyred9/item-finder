"""
配置管理模块
"""
import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "寻物记"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置 - MySQL
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/item_finder?charset=utf8mb4"

    # 文件上传配置
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif"}

    # 百度语音 API（后续使用）
    BAIDU_APP_ID: str = ""
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""

    # DeepSeek API：存的是「环境变量名」，真实 key 从该环境变量里读（可配活）
    DEEPSEEK_ENV_KEY_NAME: str = "XUN_WU_JI_DEEPSEEK_KEY"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # 百炼 Coding Plan（OpenAI 兼容）：存「环境变量名」，真实 key 从该环境变量里读
    # 文档 https://help.aliyun.com/zh/model-studio/coding-plan-quickstart
    CODING_PLAN_ENV_KEY_NAME: str = "XUN_WU_JI_CODING_PLAN_KEY"
    CODING_PLAN_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"
    CODING_PLAN_MODEL: str = "qwen3.5-plus"

    # 百炼 · TTS / Qwen-VL / OCR / Fun-ASR（接口域名为 dashscope.aliyuncs.com，在百炼控制台创建 API Key）
    BAILIAN_API_KEY: str = ""

    # 百炼录音文件识别 ASR：需公网可访问的音频 URL 时使用，填本服务公网地址；本地开发可用 ngrok
    BACKEND_PUBLIC_URL: str = ""

    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    class Config:
        # 通过环境变量 ENV_FILE 指定配置文件，未指定时用 .env（开发）
        env_file = os.environ.get("ENV_FILE", ".env")
        case_sensitive = True


# 创建配置实例
settings = Settings()


def get_deepseek_api_key() -> str:
    """从配置的环境变量名读取 DeepSeek API Key（key 名可配，不写死）。"""
    name = (settings.DEEPSEEK_ENV_KEY_NAME or "").strip()
    if not name:
        return ""
    return (os.environ.get(name) or "").strip()


def get_coding_plan_api_key() -> str:
    """从配置的环境变量名读取 Coding Plan API Key（与 DEEPSEEK_ENV_KEY_NAME 方式一致）。"""
    name = (settings.CODING_PLAN_ENV_KEY_NAME or "").strip()
    if not name:
        return ""
    return (os.environ.get(name) or "").strip()


# 确保必要目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(settings.UPLOAD_DIR / "photos").mkdir(parents=True, exist_ok=True)
(settings.UPLOAD_DIR / "tts").mkdir(parents=True, exist_ok=True)
(settings.UPLOAD_DIR / "voice_temp").mkdir(parents=True, exist_ok=True)