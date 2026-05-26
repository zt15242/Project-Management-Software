"""
AI代码分析服务
支持多种AI平台：OpenAI、通义千问、智谱AI、Claude、DeepSeek
"""
import os
import zipfile
import shutil
from typing import Optional
from datetime import datetime
from models import AIAnalysisResult, RiskLevel, DeploymentType, AIProvider
from database import get_database


# ==================== 工具函数 ====================
def normalize_base_url(url: Optional[str]) -> Optional[str]:
    """标准化Base URL，自动去除多余的 /chat/completions 等路径"""
    if not url:
        return None
    url = url.strip()
    if url.endswith('/'):
        url = url[:-1]
    if url.endswith('/chat/completions'):
        url = url[:-len('/chat/completions')]
    return url


# ==================== 规则匹配分析（默认） ====================
async def analyze_with_rules(zip_path: str, deployment_type: DeploymentType, 
                             version: str, compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用规则匹配进行代码分析（不依赖AI）- 基于NEO开发规范"""
    analysis_results = {
        "security_issues": [],
        "performance_issues": [],
        "code_smells": [],
        "version_changes": [],
        "file_analysis": [],
        "suggestions": []
    }
    
    risk_score = 0
    quality_score = 100.0  # 从100分开始扣分
    
    # NEO规范检查项计数
    neo_violations = {
        "package_naming": 0,      # 包名规范
        "class_naming": 0,        # 类命名规范
        "comment_coverage": 0,    # 注释覆盖率
        "code_structure": 0,      # 代码结构
        "hardcode": 0,            # 硬编码
        "logging": 0              # 日志规范
    }
    
    try:
        # 解压并分析文件
        extract_path = zip_path.replace('.zip', '_extracted')
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 遍历所有文件进行分析
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_path)
                
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                
                # 分析文件
                file_info = {
                    "path": rel_path,
                    "size": file_size,
                    "type": os.path.splitext(file)[1]
                }
                
                # 只分析Java代码文件（NEO规范主要针对Java）
                if file.endswith('.java'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            # ========== NEO规范检查 ==========
                            
                            # 1. 包名规范检查
                            package_line = next((line for line in lines if line.strip().startswith('package ')), None)
                            if package_line:
                                package_name = package_line.strip().replace('package ', '').replace(';', '').strip()
                                # 检查是否以 other 开头
                                if not package_name.startswith('other.'):
                                    analysis_results["code_smells"].append({
                                        "file": rel_path,
                                        "issue": f"包名不符合NEO规范：必须以'other.'开头，当前为'{package_name}'",
                                        "severity": "medium",
                                        "line": lines.index(package_line) + 1,
                                        "code_snippet": package_line.strip(),
                                        "suggestion": "包名应遵循 other.[公司标识].[模块] 格式，如 other.xsy.customer"
                                    })
                                    neo_violations["package_naming"] += 1
                                    quality_score -= 5
                            
                            # 2. 类命名规范检查
                            class_pattern = r'(public|private|protected)?\s*(class|interface|enum)\s+(\w+)'
                            import re
                            for line_num, line in enumerate(lines, 1):
                                match = re.search(class_pattern, line)
                                if match:
                                    class_name = match.group(3)
                                    # 检查是否使用大驼峰命名
                                    if not class_name[0].isupper():
                                        analysis_results["code_smells"].append({
                                            "file": rel_path,
                                            "issue": f"类名'{class_name}'不符合大驼峰命名规范",
                                            "severity": "low",
                                            "line": line_num,
                                            "code_snippet": line.strip(),
                                            "suggestion": "类名应使用大驼峰命名法（UpperCamelCase）"
                                        })
                                        neo_violations["class_naming"] += 1
                                        quality_score -= 2
                            
                            # 3. 注释覆盖率检查
                            comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*'))
                            code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*') and not line.strip().startswith('*'))
                            
                            if code_lines > 0:
                                comment_rate = (comment_lines / (comment_lines + code_lines)) * 100
                                
                                if comment_rate < 45:
                                    analysis_results["code_smells"].append({
                                        "file": rel_path,
                                        "issue": f"注释覆盖率过低：{comment_rate:.1f}%（最低要求45%，建议75%以上）",
                                        "severity": "high",
                                        "line": 1,
                                        "code_snippet": f"注释行数: {comment_lines}, 代码行数: {code_lines}",
                                        "suggestion": "增加代码注释，包括类注释、方法注释和关键逻辑注释"
                                    })
                                    neo_violations["comment_coverage"] += 1
                                    quality_score -= 10
                                elif comment_rate < 75:
                                    analysis_results["code_smells"].append({
                                        "file": rel_path,
                                        "issue": f"注释覆盖率偏低：{comment_rate:.1f}%（建议75%以上）",
                                        "severity": "medium",
                                        "line": 1,
                                        "code_snippet": f"注释行数: {comment_lines}, 代码行数: {code_lines}",
                                        "suggestion": "建议提高注释覆盖率到75%以上"
                                    })
                                    quality_score -= 5
                            
                            # 4. 循环嵌套深度检查（NEO规范：不超过5层）
                            for_count = 0
                            max_nesting = 0
                            current_nesting = 0
                            for line in lines:
                                stripped = line.strip()
                                if 'for ' in stripped or 'while ' in stripped:
                                    current_nesting += 1
                                    max_nesting = max(max_nesting, current_nesting)
                                if '}' in stripped:
                                    current_nesting = max(0, current_nesting - 1)
                            
                            if max_nesting > 5:
                                analysis_results["performance_issues"].append({
                                    "file": rel_path,
                                    "issue": f"循环嵌套层数过深（{max_nesting}层），超过NEO规范要求（最多5层）",
                                    "severity": "high",
                                    "line": 1,
                                    "code_snippet": f"最大嵌套层数: {max_nesting}",
                                    "suggestion": "将复杂逻辑抽离为独立方法，使用Map结构优化数据比对"
                                })
                                neo_violations["code_structure"] += 1
                                quality_score -= 8
                            
                            # 5. 硬编码检查（ID、email、状态值）
                            hardcode_patterns = [
                                (r'\.getId\(\)\s*==\s*["\'][\w-]+["\']', "直接使用ID进行比较"),
                                (r'email\s*=\s*["\'][^"\']+@[^"\']+["\']', "硬编码email地址"),
                                (r'status\s*=\s*["\']?\d+["\']?', "硬编码状态值"),
                                (r'status\s*=\s*["\'][^"\']+["\']', "硬编码状态字符串")
                            ]
                            
                            for line_num, line in enumerate(lines, 1):
                                for pattern, desc in hardcode_patterns:
                                    if re.search(pattern, line):
                                        analysis_results["code_smells"].append({
                                            "file": rel_path,
                                            "issue": f"存在硬编码：{desc}",
                                            "severity": "medium",
                                            "line": line_num,
                                            "code_snippet": line.strip()[:100],
                                            "suggestion": "使用常量或配置文件管理，避免硬编码"
                                        })
                                        neo_violations["hardcode"] += 1
                                        quality_score -= 3
                                        break  # 每行只报告一次
                            
                            # 6. 日志规范检查
                            logger_error_count = 0
                            logger_info_count = 0
                            for line in lines:
                                if 'logger.error' in line or 'log.error' in line:
                                    logger_error_count += 1
                                if 'logger.info' in line or 'log.info' in line:
                                    logger_info_count += 1
                            
                            # 检查是否过度使用error级别
                            if logger_error_count > logger_info_count * 2 and logger_error_count > 5:
                                analysis_results["code_smells"].append({
                                    "file": rel_path,
                                    "issue": f"过度使用error级别日志（{logger_error_count}次），建议使用info级别",
                                    "severity": "low",
                                    "line": 1,
                                    "code_snippet": f"error日志: {logger_error_count}次, info日志: {logger_info_count}次",
                                    "suggestion": "NEO规范建议统一使用info级别记录常规日志"
                                })
                                neo_violations["logging"] += 1
                                quality_score -= 2
                            
                            # 7. 代码格式检查（if语句必须有大括号）
                            if_without_brace = 0
                            for line_num, line in enumerate(lines, 1):
                                stripped = line.strip()
                                if stripped.startswith('if ') and not '{' in stripped:
                                    # 检查下一行是否有大括号
                                    if line_num < len(lines):
                                        next_line = lines[line_num].strip()
                                        if not next_line.startswith('{'):
                                            if_without_brace += 1
                            
                            if if_without_brace > 0:
                                analysis_results["code_smells"].append({
                                    "file": rel_path,
                                    "issue": f"发现{if_without_brace}处if语句未使用大括号",
                                    "severity": "low",
                                    "line": 1,
                                    "code_snippet": "if语句应使用大括号包裹执行语句",
                                    "suggestion": "所有if、for、while语句都应使用大括号，即使只有一行代码"
                                })
                                quality_score -= 2
                            
                            # ========== 原有的安全和性能检查 ==========
                            
                            # 检测潜在的安全问题
                            security_issues_found = {
                                'eval': [],
                                'exec': [],
                                'password': []
                            }
                            
                            for line_num, line in enumerate(lines, 1):
                                if 'eval(' in line:
                                    security_issues_found['eval'].append((line_num, line.strip()))
                                
                                if 'exec(' in line:
                                    security_issues_found['exec'].append((line_num, line.strip()))
                                
                                if 'password' in line.lower() and '=' in line and not line.strip().startswith('//'):
                                    security_issues_found['password'].append((line_num, line.strip()))
                            
                            # 只记录每种问题的第一个出现
                            if security_issues_found['eval']:
                                line_num, code = security_issues_found['eval'][0]
                                count = len(security_issues_found['eval'])
                                analysis_results["security_issues"].append({
                                    "file": rel_path,
                                    "issue": f"使用了eval函数{count}次，可能存在代码注入风险",
                                    "severity": "high",
                                    "line": line_num,
                                    "code_snippet": code,
                                    "suggestion": "避免使用eval函数，考虑使用JSON.parse或其他安全的方法"
                                })
                                risk_score += 20
                                quality_score -= 15
                            
                            if security_issues_found['password']:
                                line_num, code = security_issues_found['password'][0]
                                count = len(security_issues_found['password'])
                                analysis_results["security_issues"].append({
                                    "file": rel_path,
                                    "issue": f"可能包含{count}处硬编码的密码",
                                    "severity": "critical",
                                    "line": line_num,
                                    "code_snippet": code,
                                    "suggestion": "使用环境变量或配置文件来管理敏感信息"
                                })
                                risk_score += 30
                                quality_score -= 20
                            
                            # 检测文件大小
                            if len(lines) > 500:
                                analysis_results["code_smells"].append({
                                    "file": rel_path,
                                    "issue": f"文件过大（{len(lines)}行），建议拆分",
                                    "severity": "low",
                                    "line": 1,
                                    "code_snippet": f"文件总行数: {len(lines)}",
                                    "suggestion": "将大文件拆分为多个小文件，每个文件负责单一职责"
                                })
                                quality_score -= 3
                            
                            file_info["lines"] = len(lines)
                            file_info["comment_rate"] = f"{comment_rate:.1f}%" if code_lines > 0 else "0%"
                            
                    except Exception as e:
                        pass
                
                analysis_results["file_analysis"].append(file_info)
        
        # 版本变更分析
        analysis_results["version_changes"].append({
            "type": "version_update",
            "from": compare_version or "未知",
            "to": version,
            "description": f"版本从 {compare_version or '未知'} 更新到 {version}"
        })
        
        # 生成NEO规范相关建议
        if neo_violations["package_naming"] > 0:
            analysis_results["suggestions"].append(f"发现{neo_violations['package_naming']}个包名不符合NEO规范的问题")
        
        if neo_violations["comment_coverage"] > 0:
            analysis_results["suggestions"].append(f"发现{neo_violations['comment_coverage']}个文件注释覆盖率不达标")
        
        if neo_violations["code_structure"] > 0:
            analysis_results["suggestions"].append(f"发现{neo_violations['code_structure']}个代码结构问题（循环嵌套过深）")
        
        if neo_violations["hardcode"] > 0:
            analysis_results["suggestions"].append(f"发现{neo_violations['hardcode']}处硬编码问题，建议使用常量或配置")
        
        # 生成总体建议
        if len(analysis_results["security_issues"]) > 0:
            analysis_results["suggestions"].append("建议修复所有安全问题后再部署")
        
        if len(analysis_results["performance_issues"]) > 0:
            analysis_results["suggestions"].append("建议优化性能问题，提高代码执行效率")
        
        if len(analysis_results["code_smells"]) > 0:
            analysis_results["suggestions"].append("建议重构代码，改善代码质量")
        
        if len(analysis_results["security_issues"]) == 0 and sum(neo_violations.values()) == 0:
            analysis_results["suggestions"].append("代码质量良好，符合NEO开发规范")
        
        # 清理临时文件
        shutil.rmtree(extract_path)
        
    except Exception as e:
        print(f"规则分析代码时出错: {str(e)}")
        analysis_results["suggestions"].append(f"分析过程中出现错误: {str(e)}")
        risk_score = 50
        quality_score = 50.0
    
    # 确保质量分数在合理范围内
    quality_score = max(0, min(100, quality_score))
    
    # 计算风险等级
    if risk_score >= 50 or quality_score < 50:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 30 or quality_score < 70:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 15 or quality_score < 85:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    return AIAnalysisResult(
        risk_level=risk_level,
        code_quality_score=quality_score,
        security_issues=analysis_results["security_issues"],
        performance_issues=analysis_results["performance_issues"],
        code_smells=analysis_results["code_smells"],
        version_changes=analysis_results["version_changes"],
        file_analysis=analysis_results["file_analysis"],
        suggestions=analysis_results["suggestions"],
        analysis_time=datetime.now()
    )


# ==================== OpenAI GPT ====================
async def analyze_with_openai(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                               deployment_type: DeploymentType, version: str, 
                               compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用OpenAI GPT进行代码分析"""
    try:
        from openai import OpenAI
        
        base_url = normalize_base_url(base_url)
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        
        # 读取代码文件
        code_content = await extract_code_content(zip_path)
        
        # 构造提示词
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [
    {{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}
  ],
  "performance_issues": [
    {{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}
  ],
  "code_smells": [
    {{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}
  ],
  "file_analysis": [
    {{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}
  ],
  "suggestions": ["总体建议1", "总体建议2", "总体建议3"]
}}

重要说明：
1. 代码已带行号格式"行号 | 代码内容"，请准确记录行号
2. code_snippet要包含问题代码的前后2-3行上下文，便于定位
3. 每个文件每种问题只记录一次，避免重复
4. line是主要问题行，line_start和line_end是问题范围
5. suggestions必须是简洁的字符串数组
6. file_analysis要包含所有分析的文件"""

        response = client.chat.completions.create(
            model=model or "gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # 解析AI响应并构造结果
        # 这里需要根据实际AI返回格式进行解析
        return await parse_ai_response(response.choices[0].message.content, version, compare_version)
        
    except Exception as e:
        print(f"OpenAI分析失败: {str(e)}")
        # 降级到规则匹配
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== 通义千问 ====================
async def analyze_with_qwen(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                            deployment_type: DeploymentType, version: str, 
                            compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用阿里通义千问进行代码分析"""
    try:
        import dashscope
        from dashscope import Generation
        
        dashscope.api_key = api_key
        
        code_content = await extract_code_content(zip_path)
        
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}],
  "performance_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}],
  "code_smells": [{{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}],
  "file_analysis": [{{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}],
  "suggestions": ["总体建议1", "总体建议2"]
}}

重要：代码已带行号"行号 | 代码"，请准确记录行号和上下文。每个文件每种问题只记录一次。"""

        response = Generation.call(
            model=model or 'qwen-max',
            prompt=prompt
        )
        
        if response.status_code == 200:
            return await parse_ai_response(response.output.text, version, compare_version)
        else:
            raise Exception(f"通义千问API调用失败: {response.message}")
            
    except Exception as e:
        print(f"通义千问分析失败: {str(e)}")
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== 智谱AI ====================
async def analyze_with_zhipu(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                             deployment_type: DeploymentType, version: str, 
                             compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用智谱AI进行代码分析"""
    try:
        from zhipuai import ZhipuAI
        
        client = ZhipuAI(api_key=api_key)
        
        code_content = await extract_code_content(zip_path)
        
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}],
  "performance_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}],
  "code_smells": [{{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}],
  "file_analysis": [{{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}],
  "suggestions": ["总体建议1", "总体建议2"]
}}

重要：代码已带行号"行号 | 代码"，请准确记录行号和上下文。每个文件每种问题只记录一次。"""

        response = client.chat.completions.create(
            model=model or "glm-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return await parse_ai_response(response.choices[0].message.content, version, compare_version)
        
    except Exception as e:
        print(f"智谱AI分析失败: {str(e)}")
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== Claude ====================
async def analyze_with_claude(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                              deployment_type: DeploymentType, version: str, 
                              compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用Anthropic Claude进行代码分析"""
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        code_content = await extract_code_content(zip_path)
        
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}],
  "performance_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}],
  "code_smells": [{{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}],
  "file_analysis": [{{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}],
  "suggestions": ["总体建议1", "总体建议2"]
}}

重要：代码已带行号"行号 | 代码"，请准确记录行号和上下文。每个文件每种问题只记录一次。"""

        message = client.messages.create(
            model=model or "claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return await parse_ai_response(message.content[0].text, version, compare_version)
        
    except Exception as e:
        print(f"Claude分析失败: {str(e)}")
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== DeepSeek ====================
async def analyze_with_deepseek(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                                deployment_type: DeploymentType, version: str, 
                                compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用DeepSeek进行代码分析"""
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url=normalize_base_url(base_url) or "https://api.deepseek.com"
        )
        
        code_content = await extract_code_content(zip_path)
        
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}],
  "performance_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}],
  "code_smells": [{{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}],
  "file_analysis": [{{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}],
  "suggestions": ["总体建议1", "总体建议2"]
}}

重要：代码已带行号"行号 | 代码"，请准确记录行号和上下文。每个文件每种问题只记录一次。"""

        response = client.chat.completions.create(
            model=model or "deepseek-coder",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return await parse_ai_response(response.choices[0].message.content, version, compare_version)
        
    except Exception as e:
        print(f"DeepSeek分析失败: {str(e)}")
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== Google Gemini ====================
async def analyze_with_gemini(zip_path: str, api_key: str, model: str, base_url: Optional[str],
                              deployment_type: DeploymentType, version: str, 
                              compare_version: Optional[str] = None) -> AIAnalysisResult:
    """使用Google Gemini进行代码分析"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        code_content = await extract_code_content(zip_path)
        
        prompt = f"""请分析以下代码包，这是一个{deployment_type.value}的版本{version}发布。

代码内容（已包含行号）：
{code_content}

请从以下几个方面进行分析，并以JSON格式返回结果：
{{
  "security_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体修复建议"}}],
  "performance_issues": [{{"file": "文件路径", "issue": "问题描述", "severity": "high/medium/low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体优化建议"}}],
  "code_smells": [{{"file": "文件路径", "issue": "问题描述", "severity": "low", "line": 实际行号, "line_start": 问题起始行, "line_end": 问题结束行, "code_snippet": "问题代码及上下文（3-5行）", "suggestion": "具体重构建议"}}],
  "file_analysis": [{{"path": "文件路径", "type": "文件类型", "size": 0, "lines": 实际行数}}],
  "suggestions": ["总体建议1", "总体建议2"]
}}

重要：代码已带行号"行号 | 代码"，请准确记录行号和上下文。每个文件每种问题只记录一次。"""

        # 使用Gemini模型
        gemini_model = genai.GenerativeModel(model or 'gemini-pro')
        response = gemini_model.generate_content(prompt)
        
        return await parse_ai_response(response.text, version, compare_version)
        
    except Exception as e:
        print(f"Gemini分析失败: {str(e)}")
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)


# ==================== 工具函数 ====================
async def extract_all_code_files(zip_path: str):
    """提取所有代码文件，返回文件列表"""
    extract_path = zip_path.replace('.zip', '_extracted')
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # 收集所有代码文件
    all_files = []
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.php', '.go', '.ts', '.tsx', '.vue')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    # 添加带行号的完整代码
                    numbered_content = ""
                    for line_num, line in enumerate(lines, 1):
                        numbered_content += f"{line_num:4d} | {line}"
                    
                    all_files.append({
                        'path': rel_path,
                        'content': numbered_content,
                        'lines': len(lines),
                        'size': os.path.getsize(file_path)
                    })
                except Exception as e:
                    print(f"读取文件 {rel_path} 失败: {str(e)}")
    
    return extract_path, all_files


async def analyze_single_file_with_ai(file_info: dict, api_key: str, model: str, 
                                      base_url: Optional[str], provider: AIProvider) -> dict:
    """使用AI分析单个文件"""
    
    # 如果文件太大，只分析前1000行
    content = file_info['content']
    if file_info['lines'] > 1000:
        lines = content.split('\n')
        content = '\n'.join(lines[:1000])
        content += f"\n... (文件共{file_info['lines']}行，仅分析前1000行) ..."
    
    prompt = f"""请分析以下代码文件：

文件: {file_info['path']} (共{file_info['lines']}行)
{'='*60}
{content}

请以JSON格式返回分析结果：
{{
  "security_issues": [{{"issue": "问题描述", "severity": "high/medium/low", "line": 行号, "line_start": 起始行, "line_end": 结束行, "code_snippet": "代码片段（含上下文）", "suggestion": "修复建议"}}],
  "performance_issues": [{{"issue": "问题描述", "severity": "high/medium/low", "line": 行号, "line_start": 起始行, "line_end": 结束行, "code_snippet": "代码片段（含上下文）", "suggestion": "优化建议"}}],
  "code_smells": [{{"issue": "问题描述", "severity": "low", "line": 行号, "line_start": 起始行, "line_end": 结束行, "code_snippet": "代码片段（含上下文）", "suggestion": "重构建议"}}]
}}

重要：
1. 代码已带行号"行号 | 代码"，请准确记录
2. code_snippet包含问题代码前后2-3行上下文
3. 每种问题只记录一次，避免重复"""

    try:
        if provider == AIProvider.OPENAI:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=normalize_base_url(base_url)) if base_url else OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or "gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result_text = response.choices[0].message.content
            
        elif provider == AIProvider.QWEN:
            import dashscope
            from dashscope import Generation
            dashscope.api_key = api_key
            response = Generation.call(model=model or 'qwen-max', prompt=prompt)
            if response.status_code == 200:
                result_text = response.output.text
            else:
                return {"security_issues": [], "performance_issues": [], "code_smells": []}
                
        elif provider == AIProvider.ZHIPU:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or "glm-4",
                messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.choices[0].message.content
            
        elif provider == AIProvider.DEEPSEEK:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=normalize_base_url(base_url) or "https://api.deepseek.com")
            response = client.chat.completions.create(
                model=model or "deepseek-coder",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result_text = response.choices[0].message.content
        
        elif provider == AIProvider.GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel(model or 'gemini-pro')
            response = gemini_model.generate_content(prompt)
            result_text = response.text
        else:
            return {"security_issues": [], "performance_issues": [], "code_smells": []}
        
        # 解析JSON结果
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            data = json.loads(json_match.group(0))
            # 为每个问题添加文件名
            for issue in data.get("security_issues", []):
                issue['file'] = file_info['path']
            for issue in data.get("performance_issues", []):
                issue['file'] = file_info['path']
            for issue in data.get("code_smells", []):
                issue['file'] = file_info['path']
            return data
        else:
            return {"security_issues": [], "performance_issues": [], "code_smells": []}
            
    except Exception as e:
        print(f"分析文件 {file_info['path']} 失败: {str(e)}")
        return {"security_issues": [], "performance_issues": [], "code_smells": []}


async def parse_ai_response(ai_response: str, version: str, compare_version: Optional[str]) -> AIAnalysisResult:
    """解析AI响应并构造标准结果"""
    import json
    import re
    
    # 尝试解析JSON格式的响应
    try:
        # 尝试从响应中提取JSON（AI可能返回带有说明文字的响应）
        json_match = re.search(r'\{[\s\S]*\}', ai_response)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
        else:
            data = json.loads(ai_response)
    except Exception as e:
        print(f"JSON解析失败: {str(e)}, 使用文本解析")
        # 如果不是JSON格式，使用文本解析
        data = {
            "security_issues": [],
            "performance_issues": [],
            "code_smells": [],
            "file_analysis": [],
            "suggestions": [ai_response[:500]] if len(ai_response) > 0 else ["AI分析完成，未返回标准格式"]
        }
    
    # 确保suggestions是字符串数组
    suggestions = data.get("suggestions", [])
    if isinstance(suggestions, str):
        # 如果是字符串，尝试解析或直接作为单个建议
        try:
            suggestions = json.loads(suggestions)
        except:
            suggestions = [suggestions]
    elif not isinstance(suggestions, list):
        suggestions = ["AI分析完成"]
    
    # 确保file_analysis存在
    file_analysis = data.get("file_analysis", [])
    if not file_analysis:
        # 如果AI没有返回file_analysis，尝试从其他字段推断
        file_analysis = []
        seen_files = set()
        for issue in data.get("security_issues", []) + data.get("performance_issues", []) + data.get("code_smells", []):
            if isinstance(issue, dict) and "file" in issue:
                file_path = issue["file"]
                if file_path not in seen_files:
                    seen_files.add(file_path)
                    file_analysis.append({
                        "path": file_path,
                        "type": "unknown",
                        "size": 0,
                        "lines": 0
                    })
    
    # 计算风险等级
    risk_score = len(data.get("security_issues", [])) * 20 + len(data.get("performance_issues", [])) * 10
    
    # 计算分数（扣分制）
    quality_score = 100.0
    quality_score -= len(data.get("security_issues", [])) * 15
    quality_score -= len(data.get("performance_issues", [])) * 5
    quality_score -= len(data.get("code_smells", [])) * 2
    quality_score = max(0, min(100, quality_score))
    
    # 根据分数判定风险等级
    if quality_score < 60:
        risk_level = RiskLevel.CRITICAL
    elif quality_score < 75:
        risk_level = RiskLevel.HIGH
    elif quality_score < 90:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    return AIAnalysisResult(
        risk_level=risk_level,
        code_quality_score=quality_score,
        security_issues=data.get("security_issues", []),
        performance_issues=data.get("performance_issues", []),
        code_smells=data.get("code_smells", []),
        version_changes=[{
            "type": "version_update",
            "from": compare_version or "未知",
            "to": version,
            "description": f"版本从 {compare_version or '未知'} 更新到 {version}"
        }],
        file_analysis=file_analysis,
        suggestions=suggestions,
        analysis_time=datetime.now()
    )


# ==================== 主分析函数 ====================
async def analyze_code_with_ai(zip_path: str, deployment_type: DeploymentType, 
                               version: str, compare_version: Optional[str] = None) -> AIAnalysisResult:
    """
    根据配置的AI平台进行代码分析（分批全量分析每个文件）
    """
    db = get_database()
    
    # 获取启用的AI配置
    ai_config = await db.ai_configs.find_one({"is_enabled": True})
    
    # 如果没有配置或配置为NONE，使用规则匹配
    if not ai_config or ai_config.get("provider") == AIProvider.NONE.value:
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)
    
    provider = AIProvider(ai_config["provider"])
    api_key = ai_config["api_key"]
    model = ai_config.get("model")
    base_url = ai_config.get("base_url")
    
    # 提取所有代码文件
    print(f"开始提取代码文件...")
    extract_path, all_files = await extract_all_code_files(zip_path)
    
    if not all_files:
        shutil.rmtree(extract_path)
        return await analyze_with_rules(zip_path, deployment_type, version, compare_version)
    
    # 分析所有文件（不限制数量）
    files_to_analyze = all_files
    skipped_files = []
    print(f"准备分析所有 {len(files_to_analyze)} 个代码文件")
    
    print(f"开始并发分析 {len(files_to_analyze)} 个代码文件...")
    
    # 限制并发数量，避免过多API调用
    max_concurrent = 3  # 最多同时分析3个文件（降低并发数）
    file_timeout = 45  # 每个文件分析超时45秒（缩短超时时间）
    
    # 汇总所有分析结果
    all_security_issues = []
    all_performance_issues = []
    all_code_smells = []
    all_file_analysis = []
    
    import asyncio
    
    # 分批并发处理文件
    for i in range(0, len(files_to_analyze), max_concurrent):
        batch = files_to_analyze[i:i + max_concurrent]
        batch_num = i // max_concurrent + 1
        total_batches = (len(files_to_analyze) + max_concurrent - 1) // max_concurrent
        
        print(f"正在处理第 {batch_num}/{total_batches} 批文件 ({len(batch)} 个文件)")
        
        # 创建并发任务
        tasks = []
        for file_info in batch:
            task = asyncio.create_task(
                asyncio.wait_for(
                    analyze_single_file_with_ai(file_info, api_key, model, base_url, provider),
                    timeout=file_timeout
                )
            )
            tasks.append((file_info, task))
        
        # 等待当前批次完成
        for file_info, task in tasks:
            try:
                result = await task
                
                # 汇总结果
                all_security_issues.extend(result.get("security_issues", []))
                all_performance_issues.extend(result.get("performance_issues", []))
                all_code_smells.extend(result.get("code_smells", []))
                
                print(f"[OK] 完成: {file_info['path']}")
                
            except asyncio.TimeoutError:
                print(f"[TIMEOUT] 超时: {file_info['path']} (超过{file_timeout}秒)")
            except Exception as e:
                print(f"[ERROR] 失败: {file_info['path']} - {str(e)}")
            
            # 无论成功失败，都记录文件信息
            all_file_analysis.append({
                "path": file_info['path'],
                "type": file_info['path'].split('.')[-1] if '.' in file_info['path'] else 'unknown',
                "size": file_info['size'],
                "lines": file_info['lines']
            })
    
    # 添加跳过的文件信息（仅记录，不分析）
    for file_info in skipped_files:
        all_file_analysis.append({
            "path": file_info['path'],
            "type": file_info['path'].split('.')[-1] if '.' in file_info['path'] else 'unknown',
            "size": file_info['size'],
            "lines": file_info['lines']
        })
    
    # 清理临时文件
    shutil.rmtree(extract_path)
    
    print(f"分析完成！分析了{len(files_to_analyze)}/{len(all_files)}个文件")
    print(f"共发现: 安全问题{len(all_security_issues)}个, 性能问题{len(all_performance_issues)}个, 代码坏味道{len(all_code_smells)}个")
    
    # 计算风险等级
    risk_score = len(all_security_issues) * 20 + len(all_performance_issues) * 10 + len(all_code_smells) * 2
    
    # 计算分数（扣分制）
    quality_score = 100.0
    quality_score -= len(all_security_issues) * 15
    quality_score -= len(all_performance_issues) * 5
    quality_score -= len(all_code_smells) * 2
    quality_score = max(0, min(100, quality_score))

    # 根据分数判定风险等级
    if quality_score < 60:
        risk_level = RiskLevel.CRITICAL
    elif quality_score < 75:
        risk_level = RiskLevel.HIGH
    elif quality_score < 90:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    # 生成建议
    suggestions = []
    if len(all_security_issues) > 0:
        suggestions.append(f"发现 {len(all_security_issues)} 个安全问题，建议优先修复")
    if len(all_performance_issues) > 0:
        suggestions.append(f"发现 {len(all_performance_issues)} 个性能问题，建议优化")
    if len(all_code_smells) > 0:
        suggestions.append(f"发现 {len(all_code_smells)} 个代码坏味道，建议重构")
    
    # 添加分析范围说明
    if len(skipped_files) > 0:
        suggestions.append(f"注意：本次分析了 {len(files_to_analyze)} 个文件，另有 {len(skipped_files)} 个文件未分析（文件数量限制）")
    else:
        suggestions.append(f"已完整分析 {len(files_to_analyze)} 个代码文件")
    
    if not all_security_issues and not all_performance_issues and not all_code_smells:
        suggestions.insert(0, "代码质量良好，未发现明显问题")
    
    return AIAnalysisResult(
        risk_level=risk_level,
        code_quality_score=quality_score,
        security_issues=all_security_issues,
        performance_issues=all_performance_issues,
        code_smells=all_code_smells,
        version_changes=[{
            "type": "version_update",
            "from": compare_version or "未知",
            "to": version,
            "description": f"版本从 {compare_version or '未知'} 更新到 {version}"
        }],
        file_analysis=all_file_analysis,
        suggestions=suggestions,
        analysis_time=datetime.now()
    )

