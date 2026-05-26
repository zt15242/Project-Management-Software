"""
手动完成会议处理脚本
用于处理已转录但未完成后续步骤的会议
"""

import asyncio
from pymongo import MongoClient
from bson import ObjectId
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import MeetingStatus, SpeakerSegment
from utils import get_beijing_time

async def manual_process_meeting(meeting_id: str):
    """手动处理会议"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['project_management']
    
    print(f"开始处理会议: {meeting_id}")
    
    # 获取会议记录
    meeting = db.meetings.find_one({"_id": ObjectId(meeting_id)})
    if not meeting:
        print(f"错误: 会议 {meeting_id} 不存在")
        return
    
    print(f"当前状态: {meeting['status']}")
    print(f"文件路径: {meeting['file_path']}")
    
    # 如果状态是SPEAKER_IDENTIFICATION,说明转录已完成但后续步骤未执行
    # 我们需要重新触发处理
    
    if meeting['status'] == MeetingStatus.SPEAKER_IDENTIFICATION:
        print("检测到转录已完成,但后续步骤未执行")
        print("建议: 在前端点击'重试'按钮重新处理")
    elif meeting['status'] == MeetingStatus.FAILED:
        print(f"会议处理失败: {meeting.get('error_message', '未知错误')}")
        print("建议: 在前端点击'重试'按钮重新处理")
    elif meeting['status'] == MeetingStatus.WAITING_CONFIRMATION:
        print("会议已完成转录,等待用户确认说话人")
        speakers = meeting.get('speakers', [])
        print(f"共 {len(speakers)} 个片段")
        if speakers:
            print(f"第一个片段: {speakers[0].get('text', '')[:50]}...")
    else:
        print(f"当前状态: {meeting['status']}")
    
    client.close()

if __name__ == "__main__":
    meeting_id = "694b8746e449329390e2fb55"  # 你的会议ID
    asyncio.run(manual_process_meeting(meeting_id))
