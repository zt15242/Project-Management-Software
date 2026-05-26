# PPT 模板填充系统 - 基于现有模板

## 🎯 目标

使用 1PPT.com 等网站的现成 PPTX 模板，AI 自动：
1. 识别模板结构
2. 填充 AI 生成的内容
3. 替换图片为 AI 生成的图片

## 📊 技术方案

### 1. 模板解析与识别

```python
# backend/utils/ppt_template_parser.py
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

class PPTTemplateParser:
    """PPT 模板解析器"""
    
    def __init__(self, template_path: str):
        self.prs = Presentation(template_path)
        self.structure = self.analyze_structure()
    
    def analyze_structure(self) -> dict:
        """分析模板结构"""
        structure = {
            "total_slides": len(self.prs.slides),
            "slides": []
        }
        
        for idx, slide in enumerate(self.prs.slides):
            slide_info = {
                "index": idx,
                "layout_name": slide.slide_layout.name,
                "placeholders": [],
                "text_boxes": [],
                "images": [],
                "shapes": []
            }
            
            # 识别占位符
            for shape in slide.shapes:
                if shape.is_placeholder:
                    slide_info["placeholders"].append({
                        "type": shape.placeholder_format.type,
                        "name": shape.name,
                        "text": shape.text if hasattr(shape, 'text') else None
                    })
                
                # 识别文本框
                elif shape.has_text_frame:
                    slide_info["text_boxes"].append({
                        "name": shape.name,
                        "text": shape.text,
                        "left": shape.left,
                        "top": shape.top,
                        "width": shape.width,
                        "height": shape.height
                    })
                
                # 识别图片
                elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    slide_info["images"].append({
                        "name": shape.name,
                        "left": shape.left,
                        "top": shape.top,
                        "width": shape.width,
                        "height": shape.height
                    })
            
            structure["slides"].append(slide_info)
        
        return structure
    
    def get_fillable_areas(self, slide_index: int) -> dict:
        """获取可填充区域"""
        slide_info = self.structure["slides"][slide_index]
        
        return {
            "title": self._find_title_area(slide_info),
            "content": self._find_content_areas(slide_info),
            "images": slide_info["images"]
        }
    
    def _find_title_area(self, slide_info: dict):
        """查找标题区域"""
        # 优先查找标题占位符
        for ph in slide_info["placeholders"]:
            if "title" in ph["name"].lower():
                return ph
        
        # 查找最大的文本框
        text_boxes = slide_info["text_boxes"]
        if text_boxes:
            return max(text_boxes, key=lambda x: x["height"])
        
        return None
    
    def _find_content_areas(self, slide_info: dict):
        """查找内容区域"""
        content_areas = []
        
        # 查找内容占位符
        for ph in slide_info["placeholders"]:
            if "content" in ph["name"].lower() or "body" in ph["name"].lower():
                content_areas.append(ph)
        
        # 查找其他文本框
        for tb in slide_info["text_boxes"]:
            if tb not in content_areas:
                content_areas.append(tb)
        
        return content_areas
```

### 2. 内容填充引擎

```python
# backend/utils/ppt_content_filler.py
from pptx import Presentation
from pptx.util import Pt
import io

class PPTContentFiller:
    """PPT 内容填充器"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.parser = PPTTemplateParser(template_path)
    
    async def fill_content(
        self, 
        ai_content: dict,
        use_ai_images: bool = True
    ) -> str:
        """
        填充内容到模板
        
        Args:
            ai_content: AI 生成的内容
                {
                    "title": "PPT标题",
                    "slides": [
                        {
                            "title": "页面标题",
                            "content": ["要点1", "要点2"],
                            "image_description": "图片描述"
                        }
                    ]
                }
            use_ai_images: 是否使用 AI 生成图片
        """
        # 加载模板
        prs = Presentation(self.template_path)
        
        # 填充每一页
        for idx, slide_content in enumerate(ai_content["slides"]):
            if idx >= len(prs.slides):
                break  # 超出模板页数
            
            slide = prs.slides[idx]
            fillable = self.parser.get_fillable_areas(idx)
            
            # 填充标题
            if fillable["title"]:
                self._fill_title(slide, fillable["title"], slide_content["title"])
            
            # 填充内容
            if fillable["content"]:
                self._fill_content(slide, fillable["content"], slide_content["content"])
            
            # 替换图片
            if use_ai_images and fillable["images"]:
                await self._replace_images(
                    slide, 
                    fillable["images"], 
                    slide_content.get("image_description", "")
                )
        
        # 保存
        output_path = f"output_{int(time.time())}.pptx"
        prs.save(output_path)
        return output_path
    
    def _fill_title(self, slide, title_area, text: str):
        """填充标题"""
        for shape in slide.shapes:
            if shape.name == title_area["name"]:
                if shape.has_text_frame:
                    shape.text = text
                    # 保持原有字体样式
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True
                break
    
    def _fill_content(self, slide, content_areas, content_list: list):
        """填充内容"""
        if not content_areas:
            return
        
        # 使用第一个内容区域
        content_area = content_areas[0]
        
        for shape in slide.shapes:
            if shape.name == content_area["name"]:
                if shape.has_text_frame:
                    tf = shape.text_frame
                    tf.clear()  # 清空原有内容
                    
                    # 添加新内容
                    for item in content_list:
                        p = tf.add_paragraph()
                        p.text = f"• {item}"
                        p.level = 0
                break
    
    async def _replace_images(
        self, 
        slide, 
        image_areas: list, 
        description: str
    ):
        """替换图片为 AI 生成的图片"""
        from utils.gemini_image import get_image_generator
        
        # 生成图片
        image_gen = get_image_generator()
        
        # 获取 AI 配置
        db = get_database()
        ai_config = await db.ai_configs.find_one({"is_enabled": True})
        
        if not ai_config:
            return
        
        # 为每个图片区域生成图片
        for img_area in image_areas:
            try:
                # 生成图片
                image_bytes = await image_gen.generate_ppt_slide_image(
                    slide_data={
                        "title": "",
                        "content": [],
                        "image_description": description,
                        "layout": "full"
                    },
                    theme_color="#1e3a8a",
                    style="professional",
                    ai_config=ai_config
                )
                
                if image_bytes:
                    # 替换图片
                    self._replace_image_in_slide(
                        slide, 
                        img_area, 
                        io.BytesIO(image_bytes)
                    )
            except Exception as e:
                print(f"[Template Filler] 图片替换失败: {str(e)}")
    
    def _replace_image_in_slide(self, slide, img_area, image_stream):
        """在幻灯片中替换图片"""
        # 找到原图片并删除
        for shape in slide.shapes:
            if shape.name == img_area["name"]:
                # 记录位置和大小
                left = shape.left
                top = shape.top
                width = shape.width
                height = shape.height
                
                # 删除原图片
                sp = shape.element
                sp.getparent().remove(sp)
                
                # 添加新图片
                slide.shapes.add_picture(
                    image_stream,
                    left, top,
                    width=width,
                    height=height
                )
                break
```

### 3. 完整的工作流程

```python
# backend/routers/ppt_service.py
@router.post("/generate-from-template")
async def generate_ppt_from_template(
    topic: str,
    template_id: str,
    project_id: str = None,
    use_ai_images: bool = True,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    从模板生成 PPT
    
    Args:
        topic: PPT 主题
        template_id: 模板 ID
        use_ai_images: 是否使用 AI 生成图片
    """
    # 1. 获取模板文件
    template = await db.ppt_templates.find_one({"_id": ObjectId(template_id)})
    if not template:
        raise HTTPException(404, "模板不存在")
    
    template_path = template["file_path"]
    
    # 2. AI 生成内容
    from routers.ai_assistant import generate_ppt_content
    ai_content = await generate_ppt_content(topic, project_id)
    
    # 3. 填充内容到模板
    filler = PPTContentFiller(template_path)
    output_path = await filler.fill_content(ai_content, use_ai_images)
    
    # 4. 返回文件
    return {
        "file_url": f"/uploads/ppt/{os.path.basename(output_path)}",
        "file_name": f"{topic}.pptx"
    }
```

### 4. 模板管理

```python
# backend/routers/ppt_templates.py
@router.post("/upload")
async def upload_template(
    file: UploadFile,
    name: str,
    category: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    上传 PPT 模板
    
    支持从 1PPT.com 下载的 .pptx 文件
    """
    # 保存文件
    template_dir = os.path.join(settings.UPLOAD_DIR, "templates")
    os.makedirs(template_dir, exist_ok=True)
    
    file_path = os.path.join(template_dir, f"{int(time.time())}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 解析模板结构
    parser = PPTTemplateParser(file_path)
    structure = parser.structure
    
    # 生成缩略图
    thumbnail_path = await generate_thumbnail(file_path)
    
    # 保存到数据库
    template_doc = {
        "name": name,
        "category": category,
        "file_path": file_path,
        "thumbnail": thumbnail_path,
        "structure": structure,
        "total_slides": structure["total_slides"],
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "downloads": 0
    }
    
    result = await db.ppt_templates.insert_one(template_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "模板上传成功"
    }

@router.get("/")
async def get_templates(
    category: str = None,
    page: int = 1,
    page_size: int = 12
):
    """获取模板列表"""
    query = {}
    if category:
        query["category"] = category
    
    templates = await db.ppt_templates.find(query)\
        .skip((page - 1) * page_size)\
        .limit(page_size)\
        .to_list(page_size)
    
    total = await db.ppt_templates.count_documents(query)
    
    return {
        "templates": templates,
        "total": total,
        "page": page,
        "page_size": page_size
    }
```

## 🎨 前端界面

### 模板库页面

```vue
<template>
  <div class="template-library">
    <h2>PPT 模板库</h2>
    
    <!-- 分类筛选 -->
    <div class="categories">
      <el-button 
        v-for="cat in categories" 
        :key="cat"
        :type="selectedCategory === cat ? 'primary' : ''"
        @click="selectedCategory = cat"
      >
        {{ cat }}
      </el-button>
    </div>
    
    <!-- 模板网格 -->
    <div class="template-grid">
      <div 
        v-for="template in templates" 
        :key="template.id"
        class="template-card"
        @click="selectTemplate(template)"
      >
        <img :src="template.thumbnail" />
        <div class="template-info">
          <h4>{{ template.name }}</h4>
          <p>{{ template.total_slides }} 页</p>
          <el-tag>{{ template.category }}</el-tag>
        </div>
      </div>
    </div>
    
    <!-- 上传模板 -->
    <el-button type="primary" @click="showUploadDialog = true">
      上传模板
    </el-button>
    
    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传 PPT 模板">
      <el-form>
        <el-form-item label="模板名称">
          <el-input v-model="uploadForm.name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category">
            <el-option label="工作汇报" value="工作汇报" />
            <el-option label="商业计划" value="商业计划" />
            <el-option label="产品发布" value="产品发布" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板文件">
          <el-upload
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".pptx"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadTemplate">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

## 🚀 使用流程

### 用户视角

1. **下载模板**
   - 从 1PPT.com 下载喜欢的模板
   - 或使用系统内置模板

2. **上传模板**（可选）
   - 点击"上传模板"
   - 填写模板信息
   - 上传 .pptx 文件

3. **生成 PPT**
   - 输入主题："项目进展汇报"
   - 选择模板
   - 勾选"使用 AI 图片"
   - 点击生成

4. **等待完成**
   - AI 生成内容（30秒）
   - AI 生成图片（5-10分钟）
   - 自动填充到模板

5. **下载使用**
   - 下载生成的 PPT
   - 在 PowerPoint 中打开
   - 完美！

## 📦 依赖库

```bash
pip install python-pptx  # PPT 处理
pip install Pillow       # 图片处理
```

## 🎯 优势

相比手动编辑：
- ✅ **节省时间** - 5-10分钟 vs 2-3小时
- ✅ **专业模板** - 使用 1PPT.com 的设计
- ✅ **AI 内容** - 自动生成专业内容
- ✅ **AI 图片** - Gemini 生成匹配图片
- ✅ **一键完成** - 全自动流程

---

**这个方案更实用！您觉得如何？我可以立即开始实现！** 🚀
