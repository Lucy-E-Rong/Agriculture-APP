# VLM 图像数据集采集与模型策略

这份文档用于 FarmScout 项目的图像数据采集和模型路线规划。目标读者包括农业实验室同事和 App/AI 工程侧。

农业团队负责定义作物诊断类别、实验设计、专家标注标准。工程团队需要稳定的图片、metadata、labels、交付格式和数据授权，这样 App 才能支持 zero-shot VLM、few-shot examples、Visual RAG、模型评估，以及未来本地小模型训练。

## 目标

FarmScout 需要逐步支持：

- 使用 API VLM 做早期 App 测试。
- 通过 App 收集结构化图片和标签。
- 让专家复核和修正 AI 结果。
- 用相似历史案例做图像检索，也就是 Visual RAG。
- 后续测试本地 GPU VLM。
- 后续做 LoRA、classification head 或其他 fine-tuning。

第一阶段的目标不是马上训练出完美模型，而是先建立高质量数据管线，让后面训练模型成为可能。

## 不同方法需要的数据量

| 方法 | 最低可用数据量 | 更理想目标 | 主要用途 | 是否需要训练 |
| --- | ---: | ---: | --- | --- |
| Zero-shot API VLM | 0 张标注图 | 50-100 张验证图 | 测试 App 流程和 prompt | 不需要 |
| Few-shot VLM prompting | 20-100 张标注图 | 100-300 张标注图 | 在 prompt 里提供示例 | 不需要 |
| Visual RAG / case retrieval | 100-500 张标注图 | 1,000-5,000 张标注图 | 检索相似案例，提高回答稳定性 | 不需要微调 |
| MVP evaluation dataset | 500-1,000 张标注图 | 1,000-2,000 张标注图 | 判断 AI 输出是否可用 | 不训练，但需要标签 |
| Classification head | 500-2,000 张图 | 3,000-10,000 张图 | 基于 image embeddings 训练轻量分类器 | 需要轻量训练 |
| LoRA / QLoRA VLM tuning | 1,000-5,000 张图 | 10,000-50,000 张图 | 微调开源 VLM 适配农业场景 | 需要 |
| Commercial robustness | 50,000+ 张图 | 100,000+ 张图 | 覆盖不同温室、设备、光照、季节 | 需要训练和评估 |

这些数字是规划范围，不是绝对门槛。标签质量、类别平衡、测试集设计，往往比单纯图片数量更重要。

## 推荐阶段

| 阶段 | 图片数量 | 产出 | 成功标准 |
| --- | ---: | --- | --- |
| Phase 0: App smoke test | 0-50 | 样例图片和 mock/API VLM 输出 | App 扫描流程能跑通 |
| Phase 1: Pilot dataset | 1,000-2,000 | 一批有标签图片 | 图片质量和 metadata 格式验证通过 |
| Phase 2: MVP feasibility | 3,000-5,000 | 评估集 + 初始 RAG 案例库 | API VLM 能输出有用的结构化结果 |
| Phase 3: Local model experiment | 15,000-50,000 | train/validation/test splits | 可以认真测试 classification head 或 LoRA |
| Phase 4: Robust product dataset | 50,000-100,000+ | 多地点、多设备、多季节数据 | 模型能泛化到原始采集条件之外 |

## 图片要求

- 接受格式：JPG、PNG、HEIC。
- 推荐交付格式：JPG。
- 最低分辨率：1024 x 1024。
- 推荐保留手机或相机原图。
- 不要加滤镜、美颜、贴纸、手动画线或颜色编辑。
- 不要在交付前重度压缩。
- 作物主体应清晰可见。
- 要包含真实手机拍摄变化，不只收集理想实验室照片。
- 要包含明显症状，也要包含早期、轻微症状。
- 要包含 healthy control images，也就是健康对照图。

建议覆盖的变化：

- 不同光照条件。
- 不同拍摄距离。
- 不同拍摄角度。
- 不同手机或相机设备。
- 不同生长阶段。
- 不同采集日期和批次。
- 不同温室区域、房间、table、row。
- 不同品种或 cultivar。

## 拍摄协议

如果条件允许，每株植物或每个 sample 采集一组图片：

| 图片类型 | 数量 | 用途 |
| --- | ---: | --- |
| 顶视整株图 | 1 | 看整体状态 |
| 侧视整株图 | 1 | 看结构、萎蔫、生长形态 |
| 症状近景图 | 1-3 | 看可见异常区域 |
| 环境/位置图 | 0-1 | 记录温室、row、table 或周围条件 |

如果同一株植物或同一个 sample 多次拍摄，必须使用稳定的 `plant_id` 或 `sample_id` 关联起来。

多天重复拍摄很有价值，因为可以看到症状发展、恢复或恶化。

## 必需 Metadata

每张图片在 `labels.csv` 里对应一行。

最低字段：

```csv
image_id,file_name,sample_id,plant_id,crop_name,variety,growth_stage,capture_date,greenhouse_id,location_id,condition_label,severity_score,annotation_confidence,annotated_by,annotation_date,notes
```

推荐扩展字段：

```csv
image_id,file_name,batch_id,experiment_id,sample_id,plant_id,crop_name,variety,growth_stage,capture_date,capture_time,greenhouse_id,section_id,table_id,row_id,condition_primary,condition_secondary,severity_score,visible_symptoms,symptom_location,annotation_confidence,diagnosis_method,annotated_by,annotation_date,review_status,notes
```

字段说明：

| 字段 | 要求 |
| --- | --- |
| `image_id` | 唯一图片 ID。 |
| `file_name` | 和 `images/` 文件夹里的图片文件名完全一致。 |
| `batch_id` | 数据交付批次 ID。 |
| `experiment_id` | 实验或 treatment ID，如果有。 |
| `sample_id` | sample 或实验单元的稳定 ID。 |
| `plant_id` | 单株植物 ID，如果有。 |
| `crop_name` | 作物名称。 |
| `variety` | 品种或 cultivar。 |
| `growth_stage` | 生长阶段，由实验室定义。 |
| `capture_date` | 拍摄日期。 |
| `capture_time` | 拍摄时间，可选。 |
| `greenhouse_id` | 温室、房间或 facility ID。 |
| `section_id` | 分区 ID，如果使用。 |
| `table_id` | 栽培台 ID，如果使用。 |
| `row_id` | 行 ID，如果使用。 |
| `condition_primary` | 主要标签，来自实验室定义的 label schema。 |
| `condition_secondary` | 第二标签，用于多问题图片。 |
| `severity_score` | 严重程度，0-5。 |
| `visible_symptoms` | 可见症状，可用短文本或标准词表。 |
| `symptom_location` | 症状位置，例如 outer leaves、tips、edges、whole plant。 |
| `annotation_confidence` | `low`、`medium`、`high`。 |
| `diagnosis_method` | `visual_only`、`lab_test_confirmed`、`grower_confirmed`、`sensor_supported`。 |
| `annotated_by` | 专家、技术员或标注员 ID。 |
| `annotation_date` | 标注日期。 |
| `review_status` | `unreviewed`、`expert_reviewed`、`needs_recheck`、`rejected`。 |
| `notes` | 备注。 |

## 严重程度标准

建议统一使用 0-5：

| 分数 | 含义 |
| ---: | --- |
| 0 | 健康或无可见问题。 |
| 1 | 非常轻微或早期信号。 |
| 2 | 轻度。 |
| 3 | 中度。 |
| 4 | 严重。 |
| 5 | 危急、接近不可恢复或作物损失。 |

如果实验室已有自己的严重程度标准，需要在 dataset README 里写清楚，工程侧再做映射。

## 标注规则

- 每个数据批次必须提供固定的 `label_schema.json`。
- label schema 需要版本号，例如 `label_schema_v1`。
- 同一个类别不要有多个拼写。
- 同一个问题不要混用多个名称。
- 不要在同一个 schema 里混用中文和英文标签，除非明确做映射。
- 一个图片有多个问题时，用 `primary_label` 和 `secondary_label`。
- 不确定时用 `unknown`。
- 只有实验室明确设置混合类别时才用 `mixed`。
- 尽量把“可见症状描述”和“专家诊断结论”分开。

示例 `label_schema.json`：

```json
{
  "schema_version": "label_schema_v1",
  "crop_scope": ["lettuce"],
  "severity_scale": {
    "0": "healthy_or_no_visible_issue",
    "1": "very_mild",
    "2": "mild",
    "3": "moderate",
    "4": "severe",
    "5": "critical"
  },
  "allowed_labels": [
    {
      "id": "healthy",
      "display_name": "Healthy",
      "description": "No visible issue"
    },
    {
      "id": "unknown",
      "display_name": "Unknown",
      "description": "Image cannot be confidently labeled"
    }
  ]
}
```

农业标签由实验室定义。工程侧只要求标签稳定、可版本管理、机器可读取。

## 可选高级标注

第一批数据不一定需要高级标注，但后面会有价值。

| 等级 | 标注类型 | 用途 | 什么时候加 |
| --- | --- | --- | --- |
| Level 1 | Image-level label | 分类、API 评估、RAG 案例库 | 第一批 pilot |
| Level 2 | Bounding boxes | 定位可见异常区域 | 标签稳定后 |
| Level 3 | Segmentation masks | 精确估计受影响区域 | 后期研究/训练 |

推荐路线：

- 第一阶段只做整图标签。
- 对最重要或最常见类别增加 bounding boxes。
- 只有高价值类别再考虑 segmentation。

## Dataset Split

不要按图片随机切分。因为同一株植物可能有多张近似图片，如果随机切分，会导致 train/test 泄漏。

推荐按这些 key 切分：

- `plant_id`
- `sample_id`
- `batch_id`
- `greenhouse_id`
- `experiment_id`

推荐比例：

| Split | Percentage |
| --- | ---: |
| Train | 70% |
| Validation | 15% |
| Test | 15% |

最好保留一个独立测试集，来自不同日期、批次、温室或设备，用来测试模型是否真的能泛化。

## 交付格式

每个数据批次按文件夹交付：

```text
dataset_batch_001/
  images/
    IMG_0001.jpg
    IMG_0002.jpg
    IMG_0003.jpg
  labels.csv
  label_schema.json
  README.md
```

批次 README 应包含：

- 数据批次名称。
- 采集日期范围。
- 温室、房间、facility ID。
- 使用的手机或相机设备。
- label schema 版本。
- severity scoring 定义。
- 已知限制或异常采集条件。
- 数据使用限制。

## 数据授权 Checklist

使用数据前，需要确认图片和标签是否允许用于：

- AI model training。
- AI model evaluation。
- App product testing。
- 长期存储。
- 商业产品使用。
- derivative model creation，也就是训练出的衍生模型。
- 匿名 demo、报告或展示。
- 通过外部 API provider 处理图片。
- 使用云服务做存储或计算。

任何限制都应写进 batch README 或单独的数据协议。

## 设备建议

最低设备：

- 最近几年的智能手机。
- 稳定网络，用于 App 上传。
- sample/plant ID 命名系统，最好用 QR code 或 barcode。
- spreadsheet 工具，用于 metadata 和 label 录入。

推荐设备：

- 高分辨率手机或相机。
- Color reference card 或 white balance card。
- 简单尺子或 scale marker，用于近景图。
- QR labels，用于 plant/sample ID。
- 稳定光照流程。
- 可选 tripod 或固定拍摄台，用于重复拍摄。

可选环境数据：

- Air temperature。
- Humidity。
- Light intensity 或 PAR。
- CO2。
- Water temperature。
- EC。
- pH。
- Irrigation frequency。
- Nutrient formula 或 treatment group。
- Days after transplant。

这些传感器数据不是第一批必须项，但后续会帮助模型判断原因。

## API VLM vs Local Model

| 能力 | API VLM | Local GPU VLM | iPhone 本地模型 |
| --- | --- | --- | --- |
| Zero-shot analysis | 强 | 取决于模型 | 通常有限 |
| Few-shot prompting | 强 | 可以 | 有限 |
| Visual RAG | 强 | 强，如果 server 支持 | 通常不推荐 |
| Structured JSON output | 强 | 可以通过 prompt/control 实现 | 有限 |
| Fine-tuning | 取决于 provider | 适合 | 不适合训练 |
| 隐私控制 | 数据会离开本地环境 | 更可控 | 强，但模型很小 |
| 成本 | 按 API 调用付费 | GPU/服务器成本 | 手机电量和性能成本 |
| 搭建复杂度 | 低 | 中到高 | 高 |
| 最适合第一阶段 | MVP 和评估 | 后续自定义部署 | 离线轻量功能 |

推荐产品路线：

```text
先用 API VLM
收集图片和专家修正
建立 Visual RAG 案例库
在 GPU server 上训练/评估本地模型
当本地模型足够好时，再用于降低成本、增强隐私和专业化
```

不建议一开始把 VLM 放到 iPhone 上。对这个 App 更合理的架构是：

```text
iPhone App
  -> Python FastAPI backend
    -> API VLM or local GPU VLM
```

## 服务器配置建议

当前 MVP：

| 组件 | 最低配置 | 推荐配置 |
| --- | --- | --- |
| Python backend | 2 CPU cores, 4 GB RAM | 2-4 CPU cores, 8 GB RAM |
| Database | Supabase Postgres | Supabase Postgres with backups |
| Image storage | Supabase Storage | Supabase Storage or S3-compatible storage |
| API VLM | OpenAI/Claude/Gemini-style API | 可配置 provider abstraction |

本地 GPU VLM inference：

| 模型大小 | 最低 GPU | 更好 GPU | 说明 |
| --- | --- | --- | --- |
| Small VLM, 2B-4B | 8-12 GB VRAM | 16 GB VRAM | 适合实验，推理能力有限 |
| Medium VLM, 7B-8B | 16 GB VRAM | 24 GB VRAM | 本地 server 比较好的平衡点 |
| Larger VLM, 13B+ | 24 GB VRAM | 48 GB+ VRAM | 更贵，推理能力更强 |

推荐 server stack：

- Python FastAPI，作为 App-facing API。
- vLLM、Transformers 或模型专用 serving stack，用于 local VLM。
- PostgreSQL/Supabase 存 metadata。
- Object storage 存图片。
- Vector database 或 pgvector 存 image embeddings。
- Background worker 做 embedding generation 和 batch evaluation。

## Engineering Notes

这一节主要给程序员/工程侧看。

### 推荐数据架构

原始图片和 metadata 分开存。

```text
Supabase Storage / S3
  org/{org_id}/scans/{scan_id}.jpg

Postgres
  scans
  crops
  growing_rows
  image_annotations
  model_outputs
  expert_reviews
  image_embeddings
```

每次 AI 输出和专家修正都要保留，不要覆盖。需要记录 model name、prompt version、provider、latency、cost estimate、raw response。

### 建议模型输出 Schema

```json
{
  "stress_level": "none|low|medium|high|critical",
  "severity_score": 0,
  "confidence": 0.0,
  "diagnosis": "string",
  "visible_symptoms": ["string"],
  "affected_area": ["string"],
  "detected_issues": ["string"],
  "recommendations": ["string"],
  "needs_human_review": false,
  "uncertainty_reason": "string"
}
```

### Zero-shot Evaluation

在频繁改 prompt 前，先建立一个小的专家标注评估集。

需要跟踪：

- JSON validity rate。
- 和专家标签的一致率。
- severity score error。
- false high-risk rate。
- false healthy rate。
- human review rate。
- latency。
- cost per scan。

### Few-shot Prompting

Few-shot 可以包含文本示例、图片示例或检索到的案例。示例要短、代表性强。不要塞太多示例，因为 VLM context 昂贵，而且可能稀释当前图片的重要性。

### Visual RAG

推荐 Visual RAG 流程：

```text
new image
  -> image embedding model
  -> vector search
  -> retrieve top-k similar labeled images
  -> send current image + case summaries to VLM
  -> return structured JSON
```

可选 embedding 模型：

- CLIP/SigLIP-style image encoders。
- DINO-style vision encoders。
- Provider embedding APIs，前提是数据授权允许。

需要存：

- `embedding_model`
- `embedding_version`
- `image_id`
- `vector`
- `label_summary`
- `expert_review_status`

### Active Learning

尽早加入 `needs_human_review` 流程。优先让专家复核：

- 低 confidence 结果。
- 高 severity 结果。
- API VLM 和 local model 结果不一致。
- unknown 或 mixed conditions。
- 和已有案例不相似的新视觉模式。

Active Learning 通常比随机收图更能提高数据效率。

### Local Model Options

本地 GPU 可做：

- Open-source VLM inference，用于结构化诊断。
- Vision encoder + classification head，用于快速筛查。
- Grounding/detection model，用于定位可见异常区域。
- Segmentation model，用于估计受影响面积。

没有在独立 expert-labeled test set 上验证前，不要把 local VLM 当成可靠结果。

### Training Readiness Checklist

开始 LoRA 或 fine-tuning 前，需要：

- 稳定 label schema。
- 至少一个专家复核 validation set。
- train/validation/test 没有图片泄漏。
- 每个目标类别有足够样本。
- severity scale 一致。
- 商业和数据授权明确。
- 已记录 zero-shot API baseline。
- 已记录 Visual RAG baseline。

### MVP Recommendation

FarmScout MVP 优先做：

```text
API VLM + structured JSON
image upload and storage
expert correction workflow
small evaluation set
Visual RAG case library
active learning queue
```

等 App 收集到足够多有标签、有专家复核的数据后，再认真做本地模型训练。
