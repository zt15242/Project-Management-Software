async def process_transcript_with_nlp(speakers: List[SpeakerSegment], ai_config) -> List[SpeakerSegment]:
    """
    使用NLP对转录文本进行处理
    - 文本结构化：分段、标点恢复、口语化修正
    - 语义理解：识别关键信息
    - 多语言支持：处理中英文混合
    """
    try:
        logger.info("开始NLP文本处理...")
        
        # 构建原始转录文本
        raw_transcript = ""
        for segment in speakers:
            speaker_name = segment.speaker_name or "未知说话人"
            raw_transcript += f"{speaker_name}: {segment.text}\n"
        
        # 使用AI进行NLP处理
        nlp_prompt = f"""请对以下会议转录文本进行自然语言处理，优化文本质量：

原始转录文本：
{raw_transcript}

处理要求：
1. **标点恢复**：为缺少标点的句子添加合适的标点符号
2. **分段优化**：根据语义将长句合理分段
3. **口语化修正**：修正口语表达，使其更加书面化和专业
4. **语义连贯**：确保中英文混合内容的语义连贯性
5. **保持原意**：不改变原始内容的含义，只优化表达

请以JSON格式返回处理后的文本，格式如下：
{{
  "processed_segments": [
    {{
      "speaker": "说话人姓名",
      "text": "处理后的文本内容",
      "start_time": 原始开始时间,
      "end_time": 原始结束时间
    }}
  ]
}}

注意：
- 保持原有的说话人信息
- 保持原有的时间戳
- 只优化文本内容
- 必须返回有效的JSON格式
"""
        
        result = await call_ai_api(nlp_prompt, ai_config)
        
        # 解析AI返回的结果
        try:
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                if "processed_segments" in data:
                    # 更新speakers列表
                    processed_speakers = []
                    for i, segment_data in enumerate(data["processed_segments"]):
                        if i < len(speakers):
                            original_segment = speakers[i]
                            # 创建新的segment，使用处理后的文本
                            processed_segment = SpeakerSegment(
                                speaker_id=original_segment.speaker_id,
                                speaker_name=segment_data.get("speaker", original_segment.speaker_name),
                                start_time=segment_data.get("start_time", original_segment.start_time),
                                end_time=segment_data.get("end_time", original_segment.end_time),
                                text=segment_data.get("text", original_segment.text),
                                audio_segment_path=original_segment.audio_segment_path
                            )
                            processed_speakers.append(processed_segment)
                    
                    if processed_speakers:
                        logger.info(f"NLP处理成功，处理了{len(processed_speakers)}个片段")
                        return processed_speakers
                    
        except Exception as parse_error:
            logger.warning(f"NLP结果解析失败: {parse_error}，使用原始文本")
        
        # 如果处理失败，返回原始speakers
        logger.info("NLP处理失败，使用原始转录文本")
        return speakers
        
    except Exception as e:
        logger.error(f"NLP处理出错: {e}")
        # 出错时返回原始speakers
        return speakers
