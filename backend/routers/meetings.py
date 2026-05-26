from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from database import get_database
from models import (
    MeetingCreate, MeetingUpdate, MeetingResponse, MeetingStatus,
    SpeakerSegment, SpeakerConfirmation,
    UserResponse, UserRole
)
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
from utils import get_beijing_time
from config import settings
import os
import aiofiles
import uuid
import mimetypes
import asyncio
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    print("static_ffmpeg not installed, using system ffmpeg")

from logger import logger
from background_task_manager import create_meeting_task

router = APIRouter(prefix="/api/meetings", tags=["会议分析"])

# ... imports ...
# ... imports ...

# ... inside functions ...
SUPPORTED_VIDEO_TYPES = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
SUPPORTED_AUDIO_TYPES = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']


def get_file_type(filename: str) -> str:
    """判断文件类型"""
    ext = os.path.splitext(filename)[1].lower()
    if ext in SUPPORTED_VIDEO_TYPES:
        return "video"
    elif ext in SUPPORTED_AUDIO_TYPES:
        return "audio"
    else:
        return "unknown"


import shutil
import sys

def get_ffmpeg_cmd():
    """获取ffmpeg命令的绝对路径"""
    # 1. 尝试环境变量
    cmd = shutil.which('ffmpeg')
    if cmd:
        return cmd
        
    # 2. 尝试从static_ffmpeg查找
    try:
        import static_ffmpeg
        package_dir = os.path.dirname(static_ffmpeg.__file__)
        if sys.platform == 'win32':
            candidates = [
                os.path.join(package_dir, 'bin', 'win32', 'ffmpeg.exe'),
                os.path.join(package_dir, 'bin', 'ffmpeg.exe'),
            ]
        else:
            candidates = [os.path.join(package_dir, 'bin', 'ffmpeg')]
            
        for p in candidates:
            if os.path.exists(p):
                # 赋予执行权限 (Unix)
                if sys.platform != 'win32':
                    os.chmod(p, 0o755)
                return p
    except:
        pass
        
    return 'ffmpeg'

async def extract_audio_from_video(video_path: str, audio_path: str):
    """从视频中提取音频"""
    try:
        import subprocess
        # 获取ffmpeg路径
        ffmpeg_cmd = get_ffmpeg_cmd()
        logger.info(f"使用FFmpeg路径: {ffmpeg_cmd}")
        logger.info(f"视频路径: {video_path}")
        logger.info(f"音频输出路径: {audio_path}")
        
        # 使用ffmpeg提取音频
        command = [
            ffmpeg_cmd, '-i', video_path,
            '-vn',  # 不包含视频
            '-acodec', 'pcm_s16le',  # 音频编码
            '-ar', '16000',  # 采样率
            '-ac', '1',  # 单声道
            '-y', # 覆盖输出文件
            audio_path
        ]
        
        # 在Windows下使用SelectorEventLoop时不支持子进程，改用同步调用+线程池
        def run_ffmpeg_sync():
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
        result = await asyncio.to_thread(run_ffmpeg_sync)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg执行错误: {result.stderr.decode(errors='ignore')}")
            return False
            
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"音频提取异常: {e}")
        return False


# ==================== 本地Whisper模型代码 (已弃用,改用阿里云API) ====================
# 以下代码已注释,保留用于参考或紧急回退
# 如需使用本地模型,请取消注释并确保已安装 openai-whisper 或 faster-whisper

# # 全局模型缓存
# _whisper_model = None
# _whisper_model_lock = asyncio.Lock()
# _whisper_model_type = None  # 记录使用的模型类型

# def transcribe_with_whisper(audio_path: str):
#     """使用faster-whisper进行转录 (比原版快4-5倍)"""
#     global _whisper_model, _whisper_model_type
#     
#     try:
#         # 优先使用faster-whisper (速度更快)
#         use_faster_whisper = False
#         
#         try:
#             from faster_whisper import WhisperModel
#             
#             # 使用缓存的模型,避免重复加载
#             if _whisper_model is None or _whisper_model_type != "faster":
#                 logger.info(f"正在加载Faster-Whisper模型(small)...")
#                 try:
#                     # 模型选择:
#                     # tiny: 最快(20-30x实时), 准确度较低 (~70%)
#                     # base: 快速(10-15x实时), 准确度中等 (~80%)
#                     # small: 中速(5-8x实时), 准确度较高 (~85%) ⭐ 推荐
#                     # medium: 较慢(2-3x实时), 准确度高 (~90%)
#                     # large: 很慢(1-2x实时), 准确度最高 (~95%)
#                     
#                     # 使用CPU推理,int8量化以提升速度
#                     
#                     # 设置环境变量以使用镜像源(可选)
#                     import os
#                     # os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 国内镜像
#                     
#                     # 使用small模型以提升准确度
#                     _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
#                     _whisper_model_type = "faster"
#                     logger.info(f"Faster-Whisper模型加载完成 (small)")
#                     use_faster_whisper = True
#                 except Exception as download_error:
#                     logger.warning(f"Faster-Whisper模型下载失败: {download_error}")
#                     logger.warning("降级使用原版whisper...")
#                     _whisper_model = None
#                     _whisper_model_type = None
#                     use_faster_whisper = False
#             else:
#                 logger.info(f"使用缓存的Faster-Whisper模型")
#                 use_faster_whisper = True
#             
#             if use_faster_whisper:
#                 # 检测音频时长
#                 import os
#                 file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
#                 estimated_duration_min = file_size_mb / 2  # 粗略估算: 1分钟约2MB
#                 
#                 logger.info(f"开始转录(Faster-Whisper): {audio_path}")
#                 logger.info(f"音频文件大小: {file_size_mb:.1f} MB, 预计时长: {estimated_duration_min:.1f} 分钟")
#                 logger.info(f"预计转录时间: {estimated_duration_min * 0.05:.1f} 分钟 (请耐心等待...)")
#                 
#                 # 转录时添加进度回调
#                 segment_count = 0
#                 segments_list = []
#                 
#                 # 添加中文提示,强制使用简体中文
#                 initial_prompt = "以下是普通话的句子。"  # 提示Whisper使用简体中文
#                 
#                 segments, info = _whisper_model.transcribe(
#                     audio_path, 
#                     beam_size=5,  # 增加beam size以提升准确度(从1改为5)
#                     language="zh",  # 指定中文
#                     vad_filter=True,  # 使用VAD过滤静音
#                     initial_prompt=initial_prompt,  # 添加中文提示
#                     task="transcribe",  # 明确指定转录任务
#                 )
#                 
#                 # 转换为列表格式并显示进度
#                 for segment in segments:
#                     # 转换繁体为简体
#                     text = segment.text
#                     try:
#                         # 尝试使用opencc进行繁简转换
#                         from opencc import OpenCC
#                         cc = OpenCC('t2s')  # 繁体转简体
#                         text = cc.convert(text)
#                     except:
#                         # 如果opencc未安装,跳过转换
#                         pass
#                     
#                     segments_list.append({
#                         "start": segment.start,
#                         "end": segment.end,
#                         "text": text
#                     })
#                     segment_count += 1
#                     # 每处理50个片段输出一次进度
#                     if segment_count % 50 == 0:
#                         logger.info(f"转录进度: 已处理 {segment_count} 个片段, 当前时间点: {segment.end:.1f}秒")
#                 
#                 logger.info(f"转录完成,共 {len(segments_list)} 个片段")
#                 return segments_list
#             
#         except ImportError:
#             logger.warning("未安装faster-whisper,使用原版whisper (速度较慢)")
#         
#         # 降级使用原版whisper
#         if not use_faster_whisper:
#             import whisper
#             
#             if _whisper_model is None or _whisper_model_type != "original":
#                 logger.info(f"正在加载Whisper模型(small)...")
#                 _whisper_model = whisper.load_model("small")  # 使用small模型以提升准确度
#                 _whisper_model_type = "original"
#                 logger.info(f"Whisper模型加载完成 (small)")
#             else:
#                 logger.info(f"使用缓存的Whisper模型")
#             
#             logger.info(f"开始转录(原版Whisper): {audio_path}")
#             
#             # 添加中文提示
#             initial_prompt = "以下是普通话的句子。"
#             result = _whisper_model.transcribe(
#                 audio_path, 
#                 language="zh",
#                 initial_prompt=initial_prompt,
#                 task="transcribe"
#             )
#             
#             # 转换繁体为简体
#             segments = result["segments"]
#             for seg in segments:
#                 try:
#                     from opencc import OpenCC
#                     cc = OpenCC('t2s')
#                     seg["text"] = cc.convert(seg["text"])
#                 except:
#                     pass
#             
#             logger.info(f"转录完成,共 {len(segments)} 个片段")
#             return segments
#             
#     except Exception as e:
#         logger.error(f"Whisper转录失败: {e}")
#         import traceback
#         traceback.print_exc()
#         raise e

# ==================== 阿里云通义千问语音识别API ====================

async def upload_audio_to_public_url(audio_path: str) -> str:
    """
    将音频文件上传到公网可访问的位置,返回公网URL
    - 如果配置了OSS: 上传到云存储并返回公网URL
    - 如果未配置OSS: 使用FastAPI的静态文件服务提供本地URL
    """
    try:
        # 导入OSS工具
        from utils.oss_utils import upload_file_to_oss
        
        # 生成对象名称 (保持目录结构)
        relative_path = os.path.relpath(audio_path, settings.UPLOAD_DIR)
        object_name = f"meetings/{relative_path.replace(os.sep, '/')}"
        
        # 使用OSS工具上传 (会自动判断是否配置了OSS)
        public_url = await upload_file_to_oss(audio_path, object_name)
        
        logger.info(f"音频文件公网URL: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"生成公网URL失败: {e}")
        raise Exception(f"无法生成音频文件的公网访问URL: {str(e)}")


async def submit_dashscope_asr_task(audio_url: str) -> str:
    """
    提交阿里云DashScope ASR转写任务
    返回: task_id
    """
    import httpx
    
    # 从MongoDB获取ASR配置
    db = get_database()
    asr_config = await db.system_config.find_one({"config_type": "asr"})
    
    if not asr_config:
        raise Exception("未配置阿里云DashScope,请在设置中配置ASR")
    
    api_key = asr_config.get("api_key")
    if not api_key:
        raise Exception("未配置阿里云DashScope API Key,请在设置中配置")
    
    base_url = asr_config.get("base_url", "https://dashscope.aliyuncs.com/api/v1")
    model = asr_config.get("model", "qwen3-asr-flash-filetrans")
    
    submit_url = f"{base_url}/services/audio/asr/transcription"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"
    }
    
    payload = {
        "model": model,
        "input": {
            "file_url": audio_url
        },
        "parameters": {
            "channel_id": [0],
            "enable_itn": False  # 不启用逆文本归一化
        }
    }
    
    logger.info(f"提交ASR任务到阿里云: {audio_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(submit_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"提交ASR任务失败: HTTP {response.status_code} - {error_text}")
                raise Exception(f"提交ASR任务失败: {error_text}")
            
            result = response.json()
            output = result.get("output")
            
            if not output or "task_id" not in output:
                logger.error(f"ASR任务提交响应异常: {result}")
                raise Exception(f"ASR任务提交响应格式错误")
            
            task_id = output["task_id"]
            logger.info(f"ASR任务已提交,task_id: {task_id}")
            return task_id
            
    except httpx.RequestError as e:
        logger.error(f"请求阿里云API失败: {e}")
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"提交ASR任务异常: {e}")
        raise


async def query_dashscope_asr_task(task_id: str) -> dict:
    """
    查询阿里云DashScope ASR任务状态和结果
    返回: 任务状态和结果
    """
    import httpx
    
    # 从MongoDB获取ASR配置
    db = get_database()
    asr_config = await db.system_config.find_one({"config_type": "asr"})
    
    if not asr_config:
        raise Exception("未配置阿里云DashScope")
    
    api_key = asr_config.get("api_key")
    if not api_key:
        raise Exception("未配置阿里云DashScope API Key")
    
    base_url = asr_config.get("base_url", "https://dashscope.aliyuncs.com/api/v1")
    query_url = f"{base_url}/tasks/{task_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(query_url, headers=headers)
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"查询ASR任务失败: HTTP {response.status_code} - {error_text}")
                raise Exception(f"查询ASR任务失败: {error_text}")
            
            result = response.json()
            return result
            
    except httpx.RequestError as e:
        logger.error(f"请求阿里云API失败: {e}")
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"查询ASR任务异常: {e}")
        raise


async def poll_dashscope_asr_result(task_id: str, max_wait_seconds: int = 3600) -> list:
    """
    轮询查询阿里云ASR任务结果,直到完成或超时
    返回: segments列表 (格式与Whisper兼容)
    """
    import time
    
    start_time = time.time()
    poll_interval = 3  # 每3秒查询一次
    
    logger.info(f"开始轮询ASR任务结果: {task_id}")
    
    while True:
        # 检查是否超时
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            raise Exception(f"ASR任务超时 (超过{max_wait_seconds}秒)")
        
        # 查询任务状态
        result = await query_dashscope_asr_task(task_id)
        output = result.get("output", {})
        task_status = output.get("task_status", "UNKNOWN")
        
        logger.info(f"ASR任务状态: {task_status} (已等待 {elapsed:.1f}秒)")
        
        if task_status == "SUCCEEDED":
            # 任务成功,解析结果
            logger.info("ASR任务完成,开始解析结果")
            
            # 获取转录结果
            transcription_url = output.get("results", [{}])[0].get("transcription_url")
            if transcription_url:
                # 如果有转录结果URL,下载结果
                import httpx
                async with httpx.AsyncClient() as client:
                    trans_response = await client.get(transcription_url)
                    trans_data = trans_response.json()
            else:
                # 直接从响应中获取结果
                trans_data = output
            
            # 转换为Whisper格式的segments
            segments = []
            transcripts = trans_data.get("transcripts", [])
            
            for item in transcripts:
                sentences = item.get("sentences", [])
                for sentence in sentences:
                    segments.append({
                        "start": sentence.get("begin_time", 0) / 1000.0,  # 毫秒转秒
                        "end": sentence.get("end_time", 0) / 1000.0,
                        "text": sentence.get("text", "").strip()
                    })
            
            logger.info(f"ASR转录完成,共 {len(segments)} 个片段")
            return segments
            
        elif task_status == "FAILED":
            error_msg = output.get("message", "未知错误")
            logger.error(f"ASR任务失败: {error_msg}")
            raise Exception(f"ASR任务失败: {error_msg}")
            
        elif task_status in ["PENDING", "RUNNING"]:
            # 任务进行中,继续等待
            await asyncio.sleep(poll_interval)
            
        else:
            logger.warning(f"未知的任务状态: {task_status}")
            await asyncio.sleep(poll_interval)


async def extract_speaker_audio_segment(audio_path: str, segment: SpeakerSegment, output_path: str):
    """从音频文件中提取指定时间段的片段"""
    try:
        import subprocess
        ffmpeg_cmd = get_ffmpeg_cmd()
        
        # 使用ffmpeg切割音频
        command = [
            ffmpeg_cmd, '-i', audio_path,
            '-ss', str(segment.start_time),  # 开始时间
            '-to', str(segment.end_time),    # 结束时间
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            output_path
        ]
        
        def run_ffmpeg_sync():
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        result = await asyncio.to_thread(run_ffmpeg_sync)
        
        if result.returncode != 0:
            logger.error(f"音频切割失败: {result.stderr.decode(errors='ignore')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"音频切割异常: {e}")
        return False


async def call_ai_api(prompt: str, ai_config: dict) -> str:
    """调用AI接口(支持OpenAI和智谱AI)"""
    import httpx
    
    api_key = ai_config["api_key"]
    base_url = ai_config.get("base_url") or "https://api.openai.com/v1"
    model = ai_config.get("model") or "gpt-3.5-turbo"
    
    # 移除base_url末尾的斜杠(如果有)
    base_url = base_url.rstrip('/')
    
    logger.info(f"调用AI接口: {base_url}, 模型: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": "你是一个专业的会议纪要助手。你必须严格按照JSON格式返回结果，不要包含任何其他文字或markdown标记。"
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}  # 强制返回JSON格式
    }
    
    try:
        # 增加超时时间到120秒,因为会议内容可能很长
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"发送请求到: {base_url}")
            logger.info(f"请求payload大小: {len(str(payload))} 字符")
            
            response = await client.post(f"{base_url}", json=payload, headers=headers)
            
            logger.info(f"AI响应状态码: {response.status_code}")
            
            # 先获取响应文本用于调试
            response_text = response.text
            logger.info(f"AI响应内容长度: {len(response_text)} 字符")
            logger.info(f"AI响应前200字符: {response_text[:200]}")
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"AI API返回错误状态码 {response.status_code}: {response_text}")
                return f"摘要生成失败: API返回错误 {response.status_code}"
            
            # 检查响应是否为空
            if not response_text or len(response_text.strip()) == 0:
                logger.error("AI API返回空响应")
                return "摘要生成失败: API返回空响应"
            
            # 尝试解析JSON
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"JSON解析失败: {json_error}")
                logger.error(f"完整响应文本: {response_text}")
                return f"摘要生成失败: 响应不是有效的JSON格式"
            
            # 检查响应格式
            if "choices" not in data or len(data["choices"]) == 0:
                logger.error(f"AI响应格式错误: {data}")
                return f"摘要生成失败: 响应格式错误"
            
            content = data["choices"][0]["message"]["content"]
            logger.info(f"AI摘要生成成功,长度: {len(content)} 字符")
            return content
            
    except httpx.TimeoutException as e:
        logger.error(f"AI调用超时: {e}")
        return f"摘要生成失败: 请求超时,请稍后重试"
    except httpx.HTTPStatusError as e:
        logger.error(f"AI HTTP错误: {e.response.status_code} - {e.response.text}")
        return f"摘要生成失败: HTTP错误 {e.response.status_code}"
    except httpx.RequestError as e:
        logger.error(f"AI请求错误: {e}")
        return f"摘要生成失败: 网络请求失败 - {str(e)}"
    except Exception as e:
        logger.error(f"AI调用失败: {type(e).__name__} - {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return f"摘要生成失败: {str(e)}"


async def generate_meeting_summary(speakers: List[SpeakerSegment], ai_config) -> str:
    """
    使用AI生成结构化的会议智能纪要（JSON格式）
    """
    try:
        logger.info("开始生成智能会议纪要...")
        # 构建会议内容
        meeting_content = ""
        for segment in speakers:
            speaker_name = segment.speaker_name or "未知说话人"
            time_str = f"({segment.start_time:.1f}s - {segment.end_time:.1f}s)"
            meeting_content += f"{speaker_name} {time_str}: {segment.text}\n"
        
        prompt = f"""请根据以下会议转录内容，生成一份结构化的智能会议纪要。

会议转录内容：
{meeting_content}

请以JSON格式返回，包含以下字段（必须严格按照此JSON结构）：

{{
  "meeting_title": "会议标题（根据内容推测，简短精炼）",
  "meeting_date": "会议日期（从转录内容推测，格式：YYYY-MM-DD，如无法推测则为空字符串）",
  "participants": ["参与者1", "参与者2"],
  "duration": "会议时长（如：约50分钟）",
  "summary": "会议概览（100-200字的简短总结）",
  "key_points": [
    {{
      "title": "要点标题",
      "content": "详细内容",
      "icon": "📋"
    }}
  ],
  "conclusions": [
    {{
      "title": "结论标题",
      "content": "结论内容",
      "type": "decision"
    }}
  ],
  "action_items": [
    {{
      "task": "任务描述",
      "owner": "负责人",
      "deadline": "截止时间",
      "priority": "high"
    }}
  ],
  "discussion_topics": [
    {{
      "topic": "讨论主题",
      "summary": "讨论摘要",
      "decisions": ["决策1", "决策2"]
    }}
  ],
  "risks": [
    {{
      "risk": "风险描述",
      "impact": "影响",
      "mitigation": "缓解措施"
    }}
  ],
  "next_steps": ["下一步行动1", "下一步行动2"]
}}

注意：
1. 必须返回有效的JSON格式，不要包含任何其他文字
2. 如果某个字段无法从转录内容中提取，请返回空数组[]或空字符串""
3. participants字段请从转录中提取所有说话人
4. key_points至少包含3-5个要点
5. icon字段必须使用Unicode Emoji字符（如📝, 📅, 🤝, 💡），绝不要使用文本描述或Shortcode
6. 所有内容必须用中文
"""
        
        result = await call_ai_api(prompt, ai_config)
        
        # 验证返回的是否为有效JSON
        try:
            import json
            json.loads(result)
            logger.info("智能纪要生成成功（JSON格式）")
            return result
        except json.JSONDecodeError:
            logger.warning("AI返回的不是有效JSON，尝试提取JSON部分")
            # 尝试从返回内容中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                json_str = json_match.group(0)
                json.loads(json_str)  # 验证
                logger.info("成功提取JSON内容")
                return json_str
            else:
                logger.error("无法从AI响应中提取有效JSON")
                return f'{{"error": "AI返回格式错误", "raw_content": "{result[:200]}..."}}'
                
    except Exception as e:
        logger.error(f"智能纪要生成失败: {e}")
        return f'{{"error": "生成失败: {str(e)}"}}'


async def process_meeting_file(meeting_id: str):
    """后台任务：处理会议文件"""
    import time
    start_time = time.time()
    logger.info(f"开始后台任务: 处理会议 {meeting_id}")
    db = get_database()
    task_manager = None
    
    try:
        # 获取会议记录
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
        if not meeting:
            logger.error(f"会议 {meeting_id} 不存在")
            return
        
        # 创建后台任务记录
        task_manager = await create_meeting_task(
            meeting_id=meeting_id,
            meeting_title=meeting["title"],
            created_by=meeting["created_by"],
            db=db
        )
        
        file_path = meeting["file_path"]
        file_type = meeting["file_type"]
        logger.info(f"会议文件: {file_path}, 类型: {file_type}")
        
        # 更新状态为处理中
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"status": MeetingStatus.PROCESSING, "updated_at": get_beijing_time()}}
        )
        
        # 1. 提取音频 (如果是视频)
        audio_path = file_path
        if file_type == "video":
            step_start = time.time()
            audio_path = file_path.replace(os.path.splitext(file_path)[1], ".wav")
            logger.info(f"开始提取音频: {file_path} -> {audio_path}")
            success = await extract_audio_from_video(file_path, audio_path)
            if not success:
                raise Exception("音频提取失败")
            step_time = time.time() - step_start
            logger.info(f"音频提取成功 (耗时: {step_time:.2f}秒)")
            if task_manager:
                await task_manager.update_progress(10, "音频提取完成")
        
        # 更新状态为识别中 (这里主要是转录)
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"status": MeetingStatus.SPEAKER_IDENTIFICATION, "updated_at": get_beijing_time()}}
        )
        
        # 2. 使用阿里云DashScope ASR进行转录
        step_start = time.time()
        logger.info(f"开始阿里云ASR转录: {audio_path}")
        
        try:
            # 2.1 生成音频文件的公网URL
            # 检查是否已有audio_url，避免重复上传
            audio_url = meeting.get("audio_url")
            
            if audio_url:
                logger.info(f"使用已存在的音频URL: {audio_url}")
            else:
                audio_url = await upload_audio_to_public_url(audio_path)
                # 保存audio_url到数据库
                await db.meetings.update_one(
                    {"_id": ObjectId(meeting_id)},
                    {"$set": {"audio_url": audio_url}}
                )
                
            if task_manager:
                await task_manager.update_progress(20, "音频URL准备就绪")
            
            # 2.2 提交ASR任务到阿里云
            asr_task_id = await submit_dashscope_asr_task(audio_url)
            logger.info(f"ASR任务已提交: {asr_task_id}")
            
            # 保存task_id到数据库,用于后续查询
            await db.meetings.update_one(
                {"_id": ObjectId(meeting_id)},
                {"$set": {"asr_task_id": asr_task_id, "updated_at": get_beijing_time()}}
            )
            
            if task_manager:
                await task_manager.update_progress(30, "ASR任务已提交,等待处理...")
            
            # 2.3 轮询查询ASR任务结果
            # 在轮询过程中更新后台任务进度
            import time as time_module
            poll_start = time_module.time()
            poll_interval = 2  # 初始轮询间隔2秒
            max_wait = 3600 * 2  # 最多等待2小时
            last_log_time = 0
            
            while True:
                elapsed = time_module.time() - poll_start
                if elapsed > max_wait:
                    raise Exception(f"ASR任务超时 (超过{max_wait}秒)")
                
                # 查询任务状态
                result = await query_dashscope_asr_task(asr_task_id)
                output = result.get("output", {})
                task_status = output.get("task_status", "UNKNOWN")
                
                # 控制日志输出频率 (每30秒或者状态改变时输出)
                current_time = time_module.time()
                if current_time - last_log_time > 30:
                    logger.info(f"ASR任务状态: {task_status} (已等待 {elapsed:.1f}秒)")
                    last_log_time = current_time
                
                # 更新后台任务进度 (30% - 70% 之间)
                # 根据任务时长估算进度，假设平均会议时长30分钟
                estimated_duration = 300 # 估算5分钟处理时间
                progress_percent = min(70, 30 + int((elapsed / estimated_duration) * 40))
                
                if task_manager:
                    # 只有由于状态变化或长时间未更新才更新数据库
                    if current_time - last_log_time < 1: # 利用刚刚更新日志的时间点
                         await task_manager.update_progress(
                            progress_percent, 
                            f"ASR转录中... ({task_status}, 已等待{int(elapsed)}秒)"
                        )
                
                if task_status == "SUCCEEDED":
                    # 任务成功,解析结果
                    logger.info("ASR任务完成,开始解析结果")
                    
                    # 获取转录结果URL
                    # 兼容阿里云不同模型的返回格式 (result vs results)
                    transcription_url = None
                    if "result" in output:
                        transcription_url = output["result"].get("transcription_url")
                    elif "results" in output and len(output["results"]) > 0:
                        transcription_url = output["results"][0].get("transcription_url")
                    
                    trans_data = None
                    if transcription_url:
                        # 如果有转录结果URL,下载结果
                        logger.info(f"下载转录结果: {transcription_url}")
                        import httpx
                        async with httpx.AsyncClient() as client:
                            trans_response = await client.get(transcription_url)
                            trans_data = trans_response.json()
                            logger.info(f"转录结果下载完成, 数据keys: {trans_data.keys()}")
                    else:
                        # 直接从响应中获取结果
                        trans_data = output
                        logger.warning("未找到transcription_url, 尝试直接使用output")
                    
                    # 转换为Whisper格式的segments
                    whisper_segments = []
                    
                    # 尝试从不同位置获取transcripts
                    transcripts = []
                    if "transcripts" in trans_data:
                        transcripts = trans_data["transcripts"]
                    elif "result" in trans_data and "transcripts" in trans_data["result"]:
                        transcripts = trans_data["result"]["transcripts"]
                    elif "results" in trans_data:
                         # 某些格式可能直接在results里
                         pass
                    
                    if not transcripts:
                         logger.warning(f"结果中未找到transcripts字段: {trans_data}")
                    
                    for item in transcripts:
                        sentences = item.get("sentences", [])
                        for sentence in sentences:
                            whisper_segments.append({
                                "start": sentence.get("begin_time", 0) / 1000.0,  # 毫秒转秒
                                "end": sentence.get("end_time", 0) / 1000.0,
                                "text": sentence.get("text", "").strip()
                            })
                    
                    step_time = time.time() - step_start
                    logger.info(f"阿里云ASR转录完成,共 {len(whisper_segments)} 个片段 (耗时: {step_time:.2f}秒)")
                    if task_manager:
                        await task_manager.update_progress(70, "AI转录完成")
                    break
                    
                elif task_status == "FAILED":
                    error_msg = output.get("message", "未知错误")
                    logger.error(f"ASR任务失败: {error_msg}")
                    raise Exception(f"ASR任务失败: {error_msg}")
                    
                elif task_status in ["PENDING", "RUNNING"]:
                    # 任务进行中,继续等待
                    # 动态调整轮询间隔: 前30秒快一点(2s), 之后慢一点(5s), 2分钟后更慢(10s)
                    if elapsed < 30:
                        poll_interval = 2
                    elif elapsed < 120:
                        poll_interval = 5
                    else:
                        poll_interval = 10
                        
                    await asyncio.sleep(poll_interval)
                    
                else:
                    logger.warning(f"未知的任务状态: {task_status}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"阿里云ASR转录异常: {e}")
            raise Exception(f"转录失败: {str(e)}")
        
        # ==================== 本地Whisper转录代码 (已弃用) ====================
        # # 2. 使用Whisper进行转录 (自动分段)
        # step_start = time.time()
        # logger.info(f"开始Whisper转录: {audio_path}")
        # try:
        #     # 必须使用asyncio.to_thread在独立线程中运行，否则会阻塞主事件循环，导致服务器无响应
        #     whisper_segments = await asyncio.to_thread(transcribe_with_whisper, audio_path)
        #     step_time = time.time() - step_start
        #     logger.info(f"Whisper转录完成,共 {len(whisper_segments)} 个片段 (耗时: {step_time:.2f}秒)")
        #     if task_manager:
        #         await task_manager.update_progress(70, "AI转录完成")
        # except ImportError:
        #     logger.error("未安装 openai-whisper 库")
        #     raise Exception("未安装 openai-whisper 库，无法进行转录")
        # except Exception as e:
        #     logger.error(f"转录异常: {e}")
        #     raise Exception(f"转录失败: {str(e)}")
            
            
        # 检查当前会议状态,如果已被用户重置(如再次点击重试),则放弃当前结果
        # 重新获取最新的会议记录
        current_meeting_check = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
        if not current_meeting_check:
            logger.warning(f"会议记录不存在,中止任务: {meeting_id}")
            return
        
        current_status = current_meeting_check["status"]
        logger.info(f"当前会议状态: {current_status}")
        
        if current_status != MeetingStatus.SPEAKER_IDENTIFICATION:
            logger.warning(f"检测到状态变更(当前状态: {current_status}),可能已被重试,中止旧任务: {meeting_id}")
            return


        # 3. 处理分段数据
        step_start = time.time()
        logger.info(f"开始处理 {len(whisper_segments)} 个转录片段...")
        
        speaker_segments = []
        
        for i, seg in enumerate(whisper_segments):
            # Whisper返回的segments包含: id, seek, start, end, text, tokens, temperature, avg_logprob, compression_ratio, no_speech_prob
            start_time = seg["start"]
            end_time = seg["end"]
            text = seg["text"].strip()
            
            segment_obj = SpeakerSegment(
                speaker_id=f"segment_{i+1}", # 暂时无法区分具体说话人,用序号代替
                start_time=start_time,
                end_time=end_time,
                text=text,
                speaker_name=None, # 初始为空,待确认
                audio_segment_path=None  # 跳过音频切割以提升速度
            )
            
            # 跳过音频切割步骤以大幅提升速度
            # 音频切割主要用于前端播放,但对于生成纪要不是必需的
            # 如果需要音频片段,可以取消下面的注释:
            # meeting_dir = os.path.dirname(file_path)
            # segments_dir = os.path.join(meeting_dir, "segments")
            # os.makedirs(segments_dir, exist_ok=True)
            # segment_path = os.path.join(segments_dir, f"segment_{i}.wav")
            # await extract_speaker_audio_segment(audio_path, segment_obj, segment_path)
            # segment_obj.audio_segment_path = segment_path
            
            speaker_segments.append(segment_obj)
        
        step_time = time.time() - step_start
        logger.info(f"片段处理完成 (耗时: {step_time:.2f}秒)")
        
        # 保存转录文本到文件 (重要: 转录完成后必须保存)
        transcript_dir = os.path.join(settings.UPLOAD_DIR, "meetings", meeting["project_id"], "transcripts")
        os.makedirs(transcript_dir, exist_ok=True)
        transcript_file_path = os.path.join(transcript_dir, f"{meeting_id}_transcript.txt")
        
        # 生成转录文本
        transcript_text = ""
        for segment in speaker_segments:
            time_str = f"[{segment.start_time:.1f}s - {segment.end_time:.1f}s]"
            transcript_text += f"{time_str} {segment.text}\n"
        
        # 保存转录文本
        async with aiofiles.open(transcript_file_path, 'w', encoding='utf-8') as f:
            await f.write(transcript_text)
        
        logger.info(f"转录文本已保存: {transcript_file_path}")
        
        # 转录完成后，不自动生成AI纪要，等待用户点击"查看纪要"按钮
        logger.info("转录完成，等待用户点击查看纪要按钮...")
        if task_manager:
            await task_manager.update_progress(90, "转录完成")
        
        # 更新数据库 (保存转录结果，状态设为waiting_confirmation)
        update_data = {
            "status": MeetingStatus.WAITING_CONFIRMATION,  # 等待用户查看纪要
            "speakers": [s.dict() for s in speaker_segments],
            "transcript_file_path": transcript_file_path,  # 转录文本路径
            "updated_at": get_beijing_time()
        }
        
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": update_data}
        )
        
        # 标记任务完成
        if task_manager:
            await task_manager.complete()
        
        total_time = time.time() - start_time
        logger.info(f"✅ 会议处理完成，总耗时: {total_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"处理会议文件失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 标记任务失败
        if task_manager:
            await task_manager.fail(str(e))
        
        total_time = time.time() - start_time
        logger.error(f"❌ 会议处理失败! 总耗时: {total_time:.2f}秒")
        # 更新为失败状态
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {
                "$set": {
                    "status": MeetingStatus.FAILED,
                    "error_message": str(e),
                    "updated_at": get_beijing_time()
                }
            }
        )


@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    project_id: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """上传会议录音/视频"""
    db = get_database()
    
    # 验证项目
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 检查文件类型
    file_type = get_file_type(file.filename)
    if file_type == "unknown":
        raise HTTPException(status_code=400, detail="不支持的文件格式")
    
    # 创建目录
    meeting_dir = os.path.join(settings.UPLOAD_DIR, "meetings", project_id)
    os.makedirs(meeting_dir, exist_ok=True)
    
    # 保存文件
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(meeting_dir, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
        file_size = len(content)
    
    # 创建会议记录
    meeting_doc = {
        "title": title,
        "project_id": project_id,
        "description": description,
        "file_name": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "file_type": file_type,
        "status": MeetingStatus.UPLOADING,
        "speakers": [],
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.meetings.insert_one(meeting_doc)
    meeting_id = str(result.inserted_id)
    
    # 添加后台任务处理文件
    background_tasks.add_task(process_meeting_file, meeting_id)
    
    created_meeting = await db.meetings.find_one({"_id": result.inserted_id})
    
    return MeetingResponse(
        id=str(created_meeting["_id"]),
        title=created_meeting["title"],
        project_id=created_meeting["project_id"],
        description=created_meeting.get("description"),
        file_name=created_meeting["file_name"],
        file_path=created_meeting["file_path"],
        file_size=created_meeting["file_size"],
        file_type=created_meeting["file_type"],
        status=created_meeting["status"],
        speakers=[SpeakerSegment(**s) for s in created_meeting.get("speakers", [])],
        created_by=created_meeting["created_by"],
        created_at=created_meeting["created_at"],
        updated_at=created_meeting["updated_at"]
    )


@router.post("/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """上传分片"""
    # 简单的分片存储, 使用upload_id作为临时文件夹名
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp_chunks", upload_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    chunk_path = os.path.join(temp_dir, f"{chunk_index}")
    async with aiofiles.open(chunk_path, 'wb') as f:
        content = await chunk.read()
        await f.write(content)
        
    return {"status": "success", "chunk_index": chunk_index}


@router.post("/upload/merge", response_model=MeetingResponse)
async def merge_chunks(
    background_tasks: BackgroundTasks,
    upload_id: str = Form(...),
    filename: str = Form(...),
    title: str = Form(...),
    project_id: str = Form(...),
    description: Optional[str] = Form(None),
    total_chunks: int = Form(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """合并分片"""
    db = get_database()
    
    # 验证项目
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id not in project["team_members"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 检查文件类型
    file_type = get_file_type(filename)
    if file_type == "unknown":
        raise HTTPException(status_code=400, detail="不支持的文件格式")
        
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp_chunks", upload_id)
    if not os.path.exists(temp_dir):
        raise HTTPException(status_code=404, detail="分片目录不存在")
        
    # 创建最终目录
    meeting_dir = os.path.join(settings.UPLOAD_DIR, "meetings", project_id)
    os.makedirs(meeting_dir, exist_ok=True)
    
    file_ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(meeting_dir, unique_filename)
    
    # 合并文件
    file_size = 0
    async with aiofiles.open(file_path, 'wb') as target_file:
        for i in range(total_chunks):
            chunk_path = os.path.join(temp_dir, f"{i}")
            if not os.path.exists(chunk_path):
                raise HTTPException(status_code=400, detail=f"分片 {i} 缺失")
            
            async with aiofiles.open(chunk_path, 'rb') as source_file:
                content = await source_file.read()
                await target_file.write(content)
                file_size += len(content)
                
    # 删除分片目录
    import shutil
    shutil.rmtree(temp_dir)
    
    # 创建会议记录
    meeting_doc = {
        "title": title,
        "project_id": project_id,
        "description": description,
        "file_name": filename,
        "file_path": file_path,
        "file_size": file_size,
        "file_type": file_type,
        "status": MeetingStatus.UPLOADING,
        "speakers": [],
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.meetings.insert_one(meeting_doc)
    meeting_id = str(result.inserted_id)
    
    # 添加后台任务处理文件
    background_tasks.add_task(process_meeting_file, meeting_id)
    
    created_meeting = await db.meetings.find_one({"_id": result.inserted_id})
    
    return MeetingResponse(
        id=str(created_meeting["_id"]),
        title=created_meeting["title"],
        project_id=created_meeting["project_id"],
        description=created_meeting.get("description"),
        file_name=created_meeting["file_name"],
        file_path=created_meeting["file_path"],
        file_size=created_meeting["file_size"],
        file_type=created_meeting["file_type"],
        status=created_meeting["status"],
        speakers=[SpeakerSegment(**s) for s in created_meeting.get("speakers", [])],
        created_by=created_meeting["created_by"],
        created_at=created_meeting["created_at"],
        updated_at=created_meeting["updated_at"]
    )


@router.get("/", response_model=List[MeetingResponse])
async def get_meetings(
    project_id: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取会议列表"""
    db = get_database()
    
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    meetings = await db.meetings.find(query).sort("created_at", -1).to_list(length=None)
    
    return [
        MeetingResponse(
            id=str(m["_id"]),
            title=m["title"],
            project_id=m["project_id"],
            description=m.get("description"),
            file_name=m["file_name"],
            file_path=m["file_path"],
            file_size=m["file_size"],
            file_type=m["file_type"],
            duration=m.get("duration"),
            status=m["status"],
            speakers=[SpeakerSegment(**s) for s in m.get("speakers", [])],
            summary_content=m.get("summary_content"),
            summary_file_path=m.get("summary_file_path"),
            error_message=m.get("error_message"),
            created_by=m["created_by"],
            created_at=m["created_at"],
            updated_at=m["updated_at"]
        )
        for m in meetings
    ]


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取会议详情"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    return MeetingResponse(
        id=str(meeting["_id"]),
        title=meeting["title"],
        project_id=meeting["project_id"],
        description=meeting.get("description"),
        file_name=meeting["file_name"],
        file_path=meeting["file_path"],
        file_size=meeting["file_size"],
        file_type=meeting["file_type"],
        duration=meeting.get("duration"),
        status=meeting["status"],
        speakers=[SpeakerSegment(**s) for s in meeting.get("speakers", [])],
        summary_content=meeting.get("summary_content"),
        summary_file_path=meeting.get("summary_file_path"),
        error_message=meeting.get("error_message"),
        created_by=meeting["created_by"],
        created_at=meeting["created_at"],
        updated_at=meeting["updated_at"]
    )


@router.post("/{meeting_id}/confirm-speakers")
async def confirm_speakers(
    meeting_id: str,
    confirmations: List[SpeakerConfirmation],
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """确认说话人姓名"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    # 更新说话人姓名
    speakers = meeting.get("speakers", [])
    for confirmation in confirmations:
        for speaker in speakers:
            if speaker["speaker_id"] == confirmation.speaker_id:
                speaker["speaker_name"] = confirmation.speaker_name
    
    # 更新数据库
    await db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "speakers": speakers,
                "status": MeetingStatus.GENERATING_SUMMARY,
                "updated_at": get_beijing_time()
            }
        }
    )
    
    # 添加后台任务生成摘要
    async def generate_summary_task(meeting_id: str):
        db = get_database()
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
        
        # 获取AI配置
        ai_config = await db.ai_configs.find_one({"is_enabled": True})
        
        # 生成摘要
        speakers = [SpeakerSegment(**s) for s in meeting["speakers"]]
        summary = await generate_meeting_summary(speakers, ai_config)
        
        # 保存摘要文件
        summary_dir = os.path.join(settings.UPLOAD_DIR, "meetings", meeting["project_id"], "summaries")
        os.makedirs(summary_dir, exist_ok=True)
        summary_file_path = os.path.join(summary_dir, f"{meeting_id}_summary.md")
        
        async with aiofiles.open(summary_file_path, 'w', encoding='utf-8') as f:
            await f.write(summary)
        
        # 更新数据库
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {
                "$set": {
                    "summary_content": summary,
                    "summary_file_path": summary_file_path,
                    "status": MeetingStatus.COMPLETED,
                    "updated_at": get_beijing_time()
                }
            }
        )
    
    background_tasks.add_task(generate_summary_task, meeting_id)
    
    return {"message": "说话人确认成功，正在生成摘要..."}


@router.post("/{meeting_id}/retry")
async def retry_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """重新分析会议"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id != meeting["created_by"]:
        project = await db.projects.find_one({"_id": ObjectId(meeting["project_id"])})
        if not project or current_user.id not in project.get("team_members", []):
            raise HTTPException(status_code=403, detail="没有权限")
            
    # 重置状态为处理中，并清除之前的错误信息
    await db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "status": MeetingStatus.UPLOADING, # 重置为初始状态以便process_meeting_file处理
                "error_message": None,
                "updated_at": get_beijing_time()
            }
        }
    )
    
    # 添加后台任务重新处理
    background_tasks.add_task(process_meeting_file, meeting_id)
    
    return {"message": "已开始重新分析"}


@router.post("/{meeting_id}/regenerate-summary")
async def regenerate_summary(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """重新生成AI摘要(使用已保存的转录文本,不重新转录)"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id != meeting["created_by"]:
        project = await db.projects.find_one({"_id": ObjectId(meeting["project_id"])})
        if not project or current_user.id not in project.get("team_members", []):
            raise HTTPException(status_code=403, detail="没有权限")
    
    # 检查是否有转录文本
    if not meeting.get("speakers") or len(meeting.get("speakers", [])) == 0:
        raise HTTPException(status_code=400, detail="没有转录文本,请先完成转录")
    
    # 检查AI配置
    ai_config = await db.ai_configs.find_one({"is_enabled": True})
    if not ai_config:
        raise HTTPException(status_code=400, detail="未配置AI,无法生成摘要")
    
    # 后台任务:重新生成摘要
    async def regenerate_summary_task(meeting_id: str):
        db = get_database()
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
        
        logger.info(f"开始重新生成摘要: {meeting_id}")
        
        # 更新状态为生成中
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"status": MeetingStatus.GENERATING_SUMMARY, "updated_at": get_beijing_time()}}
        )
        
        try:
            # 获取AI配置
            ai_config = await db.ai_configs.find_one({"is_enabled": True})
            
            # 从数据库读取转录片段
            speakers = [SpeakerSegment(**s) for s in meeting["speakers"]]
            
            # 生成摘要
            summary = await generate_meeting_summary(speakers, ai_config)
            
            # 检查摘要是否有效
            if summary and not summary.startswith("摘要生成失败"):
                # 保存摘要文件
                summary_dir = os.path.join(settings.UPLOAD_DIR, "meetings", meeting["project_id"], "summaries")
                os.makedirs(summary_dir, exist_ok=True)
                summary_file_path = os.path.join(summary_dir, f"{meeting_id}_summary.md")
                
                async with aiofiles.open(summary_file_path, 'w', encoding='utf-8') as f:
                    await f.write(summary)
                
                # 更新数据库
                await db.meetings.update_one(
                    {"_id": ObjectId(meeting_id)},
                    {
                        "$set": {
                            "summary_content": summary,
                            "summary_file_path": summary_file_path,
                            "status": MeetingStatus.COMPLETED,
                            "updated_at": get_beijing_time()
                        }
                    }
                )
                logger.info(f"✅ 摘要重新生成成功: {meeting_id}")
            else:
                raise Exception("AI返回了错误信息")
                
        except Exception as e:
            logger.error(f"❌ 摘要重新生成失败: {e}")
            # 恢复为等待确认状态
            await db.meetings.update_one(
                {"_id": ObjectId(meeting_id)},
                {
                    "$set": {
                        "status": MeetingStatus.WAITING_CONFIRMATION,
                        "error_message": f"摘要生成失败: {str(e)}",
                        "updated_at": get_beijing_time()
                    }
                }
            )
    
    background_tasks.add_task(regenerate_summary_task, meeting_id)
    
    return {"message": "正在重新生成摘要,请稍候..."}


@router.post("/{meeting_id}/generate-summary")
async def generate_summary(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """生成AI智能纪要(首次生成,用于转录完成后点击查看纪要按钮)"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id != meeting["created_by"]:
        project = await db.projects.find_one({"_id": ObjectId(meeting["project_id"])})
        if not project or current_user.id not in project.get("team_members", []):
            raise HTTPException(status_code=403, detail="没有权限")
    
    # 检查是否有转录文本
    if not meeting.get("speakers") or len(meeting.get("speakers", [])) == 0:
        raise HTTPException(status_code=400, detail="没有转录文本,请先完成转录")
    
    # 检查AI配置
    ai_config = await db.ai_configs.find_one({"is_enabled": True})
    if not ai_config:
        raise HTTPException(status_code=400, detail="未配置AI,无法生成摘要")
    
    # 后台任务:生成智能纪要
    async def generate_summary_task(meeting_id: str):
        db = get_database()
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
        
        logger.info(f"开始生成智能纪要: {meeting_id}")
        
        # 更新状态为生成中
        await db.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"status": MeetingStatus.GENERATING_SUMMARY, "updated_at": get_beijing_time()}}
        )
        
        try:
            # 获取AI配置
            ai_config = await db.ai_configs.find_one({"is_enabled": True})
            
            # 从数据库读取转录片段
            speakers = [SpeakerSegment(**s) for s in meeting["speakers"]]
            
            # 生成摘要
            summary = await generate_meeting_summary(speakers, ai_config)
            
            # 检查摘要是否有效
            if summary and not summary.startswith("摘要生成失败"):
                # 保存摘要文件
                summary_dir = os.path.join(settings.UPLOAD_DIR, "meetings", meeting["project_id"], "summaries")
                os.makedirs(summary_dir, exist_ok=True)
                summary_file_path = os.path.join(summary_dir, f"{meeting_id}_summary.md")
                
                async with aiofiles.open(summary_file_path, 'w', encoding='utf-8') as f:
                    await f.write(summary)
                
                # 更新数据库
                await db.meetings.update_one(
                    {"_id": ObjectId(meeting_id)},
                    {
                        "$set": {
                            "summary_content": summary,
                            "summary_file_path": summary_file_path,
                            "status": MeetingStatus.COMPLETED,
                            "updated_at": get_beijing_time()
                        }
                    }
                )
                logger.info(f"✅ 智能纪要生成成功: {meeting_id}")
            else:
                raise Exception("AI返回了错误信息")
                
        except Exception as e:
            logger.error(f"❌ 智能纪要生成失败: {e}")
            # 恢复为等待确认状态
            await db.meetings.update_one(
                {"_id": ObjectId(meeting_id)},
                {
                    "$set": {
                        "status": MeetingStatus.WAITING_CONFIRMATION,
                        "error_message": f"摘要生成失败: {str(e)}",
                        "updated_at": get_beijing_time()
                    }
                }
            )
    
    background_tasks.add_task(generate_summary_task, meeting_id)
    
    return {"message": "正在生成智能纪要,请稍候..."}



@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除会议"""
    db = get_database()
    
    try:
        meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的会议ID")
    
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")
    
    # 检查权限
    if current_user.role != UserRole.ADMIN and current_user.id != meeting["created_by"]:
        raise HTTPException(status_code=403, detail="没有权限")
    
    # 删除文件
    try:
        if os.path.exists(meeting["file_path"]):
            os.remove(meeting["file_path"])
        
        # 删除音频片段目录
        meeting_dir = os.path.dirname(meeting["file_path"])
        segments_dir = os.path.join(meeting_dir, "segments")
        if os.path.exists(segments_dir):
            import shutil
            shutil.rmtree(segments_dir)
        
        # 删除摘要文件
        if meeting.get("summary_file_path") and os.path.exists(meeting["summary_file_path"]):
            os.remove(meeting["summary_file_path"])
    except Exception as e:
        print(f"删除文件失败: {e}")
    
    # 删除数据库记录
    await db.meetings.delete_one({"_id": ObjectId(meeting_id)})
    
    return None
