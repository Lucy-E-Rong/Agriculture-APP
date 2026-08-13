# VLM Dataset Collection and Model Strategy

This document defines the image dataset requirements and model strategy for FarmScout. It is written for both agriculture collaborators and the app engineering team.

The agriculture team should own the crop diagnosis categories, experimental design, and expert labeling decisions. The engineering team needs consistent images, metadata, labels, delivery formats, and data rights so the app can support zero-shot VLM analysis, few-shot examples, image retrieval, model evaluation, and future local model training.

## Goals

FarmScout should support the following stages:

- API-based VLM analysis for early app testing.
- Structured image and label collection through the app.
- Expert review and correction of AI results.
- Image retrieval using similar historical cases.
- Future local GPU VLM experiments.
- Future LoRA, classification-head, or other fine-tuning workflows.

The first goal is not to train a perfect model immediately. The first goal is to build a high-quality data pipeline that makes later model training possible.

## Dataset Size by Method

| Method | Minimum Useful Data | Better Target | Main Purpose | Training Required |
| --- | ---: | ---: | --- | --- |
| Zero-shot API VLM | 0 labeled images | 50-100 validation images | Test app flow and prompt quality | No |
| Few-shot VLM prompting | 20-100 labeled images | 100-300 labeled images | Provide examples in prompts | No |
| Visual RAG / case retrieval | 100-500 labeled images | 1,000-5,000 labeled images | Retrieve similar cases for better answers | No model fine-tuning required |
| MVP evaluation dataset | 500-1,000 labeled images | 1,000-2,000 labeled images | Measure whether AI output is usable | No, but labels required |
| Classification head | 500-2,000 images | 3,000-10,000 images | Train a lightweight classifier on image embeddings | Yes, light training |
| LoRA / QLoRA VLM tuning | 1,000-5,000 images | 10,000-50,000 images | Adapt an open-source VLM to the lab domain | Yes |
| Commercial robustness | 50,000+ images | 100,000+ images | Generalize across locations, devices, crops, lighting, seasons | Yes, plus evaluation |

These numbers are planning ranges, not hard rules. Label quality, category balance, and test-set design matter more than raw image count.

## Recommended Phases

| Phase | Image Count | Output | Success Criteria |
| --- | ---: | --- | --- |
| Phase 0: App smoke test | 0-50 | Sample images and mock/API VLM output | App scan flow works end to end |
| Phase 1: Pilot dataset | 1,000-2,000 | Labeled image batch | Image quality and metadata format are validated |
| Phase 2: MVP feasibility | 3,000-5,000 | Evaluation set plus early RAG case library | API VLM can produce useful structured results |
| Phase 3: Local model experiment | 15,000-50,000 | Training/validation/test splits | Classification head or LoRA experiments become meaningful |
| Phase 4: Robust product dataset | 50,000-100,000+ | Multi-location, multi-device, multi-season data | Model generalizes outside the original collection conditions |

## Image Requirements

- Accepted formats: JPG, PNG, or HEIC.
- Preferred delivery format: JPG.
- Minimum resolution: 1024 x 1024 pixels.
- Original phone or camera images are preferred.
- Avoid filters, beauty effects, stickers, manual annotations, or color edits.
- Avoid heavy compression before delivery.
- The crop subject should be clear and visible.
- Include realistic mobile-app variation, not only ideal lab photos.
- Include both obvious and early/mild symptoms.
- Include healthy control images.

Useful variation:

- Different lighting conditions.
- Different shooting distances.
- Different angles.
- Different phone or camera devices.
- Different growth stages.
- Different collection dates and batches.
- Different greenhouse areas, rooms, tables, or rows.
- Different varieties or cultivars when applicable.

## Capture Protocol

For each plant or sample, collect a small set of related images when possible:

| Image Type | Count | Purpose |
| --- | ---: | --- |
| Top-view whole plant | 1 | Overall plant condition |
| Side-view whole plant | 1 | Structure, wilting, growth pattern |
| Symptom close-up | 1-3 | Visible issue area |
| Context image | 0-1 | Greenhouse, row, table, or surrounding condition |

If the same plant or sample is photographed multiple times, all related images must share a stable `plant_id` or `sample_id`.

Repeated images over multiple days are valuable because they show progression, recovery, or worsening.

## Required Metadata

Each image should have one row in `labels.csv`.

Minimum required fields:

```csv
image_id,file_name,sample_id,plant_id,crop_name,variety,growth_stage,capture_date,greenhouse_id,location_id,condition_label,severity_score,annotation_confidence,annotated_by,annotation_date,notes
```

Recommended extended fields:

```csv
image_id,file_name,batch_id,experiment_id,sample_id,plant_id,crop_name,variety,growth_stage,capture_date,capture_time,greenhouse_id,section_id,table_id,row_id,condition_primary,condition_secondary,severity_score,visible_symptoms,symptom_location,annotation_confidence,diagnosis_method,annotated_by,annotation_date,review_status,notes
```

Field definitions:

| Field | Requirement |
| --- | --- |
| `image_id` | Unique image identifier. |
| `file_name` | Exact image file name in the delivered `images/` folder. |
| `batch_id` | Dataset delivery batch identifier. |
| `experiment_id` | Lab experiment or treatment identifier, if available. |
| `sample_id` | Stable ID for the sample or experimental unit. |
| `plant_id` | Stable ID for the plant, if available. |
| `crop_name` | Crop name. |
| `variety` | Variety or cultivar. |
| `growth_stage` | Lab-defined growth stage. |
| `capture_date` | Date image was captured. |
| `capture_time` | Optional capture time. |
| `greenhouse_id` | Greenhouse, room, or facility identifier. |
| `section_id` | Section identifier, if used. |
| `table_id` | Table identifier, if used. |
| `row_id` | Row identifier, if used. |
| `condition_primary` | Main label from the lab-defined schema. |
| `condition_secondary` | Optional second label when multiple issues are present. |
| `severity_score` | Numeric severity score from 0 to 5. |
| `visible_symptoms` | Short text or controlled terms describing visible symptoms. |
| `symptom_location` | Where symptoms appear, such as outer leaves, tips, edges, whole plant. |
| `annotation_confidence` | `low`, `medium`, or `high`. |
| `diagnosis_method` | `visual_only`, `lab_test_confirmed`, `grower_confirmed`, or `sensor_supported`. |
| `annotated_by` | Expert, technician, or annotator identifier. |
| `annotation_date` | Date label was created or confirmed. |
| `review_status` | `unreviewed`, `expert_reviewed`, `needs_recheck`, or `rejected`. |
| `notes` | Optional free-text context. |

## Severity Scale

Use a consistent severity scale across each dataset batch.

| Score | Meaning |
| ---: | --- |
| 0 | Healthy or no visible issue. |
| 1 | Very mild or early signal. |
| 2 | Mild. |
| 3 | Moderate. |
| 4 | Severe. |
| 5 | Critical, crop loss, or near unrecoverable. |

If the lab already uses a different severity scale, include the scoring definition in the dataset README so engineering can map it consistently.

## Labeling Rules

- Provide a fixed `label_schema.json` file for each dataset batch.
- Include a schema version, such as `label_schema_v1`.
- Avoid duplicate spellings for the same class.
- Avoid mixing multiple names for the same condition.
- Avoid mixing Chinese and English labels inside the same schema unless both are explicitly mapped.
- Use `primary_label` and `secondary_label` when one image contains multiple issues.
- Use `unknown` when the image cannot be confidently labeled.
- Use `mixed` only when the lab intentionally defines a mixed-condition class.
- Separate visual symptom description from expert diagnosis when possible.

Example `label_schema.json` shape:

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

The lab should define the agricultural labels. The engineering team only needs them to be stable, versioned, and machine-readable.

## Optional Advanced Annotation

Advanced annotation is not required for the first pilot, but it becomes useful later.

| Level | Annotation Type | Use Case | When to Add |
| --- | --- | --- | --- |
| Level 1 | Image-level label | Classification, API evaluation, RAG case library | First pilot |
| Level 2 | Bounding boxes | Localizing visible issue areas | After labels stabilize |
| Level 3 | Segmentation masks | Precise affected-area modeling | Later research/training |

Recommended approach:

- Start with Level 1 labels.
- Add bounding boxes for the most important or most common categories.
- Add segmentation only for high-value categories where precise affected area matters.

## Dataset Split Requirements

Do not split the dataset randomly by image when the same plant or sample has multiple photos. That can leak near-duplicate examples into train and test sets.

Preferred split keys:

- `plant_id`
- `sample_id`
- `batch_id`
- `greenhouse_id`
- `experiment_id`

Recommended split:

| Split | Percentage |
| --- | ---: |
| Train | 70% |
| Validation | 15% |
| Test | 15% |

If possible, reserve one independent test set from a different date, batch, greenhouse, or device group.

## Delivery Format

Each dataset batch should be delivered as a folder:

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

The batch README should include:

- Dataset batch name.
- Collection date range.
- Source greenhouse, room, or facility identifiers.
- Camera or phone devices used when known.
- Label schema version.
- Severity scoring definition.
- Known limitations or unusual collection conditions.
- Data usage restrictions, if any.

## Data Rights Checklist

Before using the dataset for product or model development, confirm whether the images and labels may be used for:

- AI model training.
- AI model evaluation.
- App product testing.
- Long-term storage.
- Commercial product use.
- Derivative model creation.
- Anonymized demos, reports, or presentations.
- Sharing with external model providers through API calls.
- Sharing with cloud infrastructure providers for storage or processing.

Any restrictions should be documented in the batch README or a separate data agreement.

## Equipment Recommendations

Minimum equipment:

- Recent smartphone with a good camera.
- Stable internet connection for app upload.
- Consistent naming or QR/barcode system for sample and plant IDs.
- Spreadsheet tool for metadata and label entry.

Recommended equipment:

- Phone or camera capable of high-resolution images.
- Color reference card or white balance reference card.
- Simple scale marker or ruler for close-up images.
- QR labels for plant/sample IDs.
- Stable lighting reference procedure.
- Optional tripod or fixed capture station for repeated imaging.

Optional sensor/environment data:

- Air temperature.
- Humidity.
- Light intensity or PAR.
- CO2.
- Water temperature.
- EC.
- pH.
- Irrigation frequency.
- Nutrient formula or treatment group.
- Days after transplant.

These sensor fields are not required for the first pilot, but they can improve later diagnosis and model analysis.

## API VLM vs Local Model

| Capability | API VLM | Local GPU VLM | Local iPhone Model |
| --- | --- | --- | --- |
| Zero-shot analysis | Strong | Depends on model | Usually limited |
| Few-shot prompting | Strong | Possible | Limited |
| Visual RAG | Strong | Strong if server supports it | Usually not recommended |
| Structured JSON output | Strong | Possible with prompt/control | Limited |
| Fine-tuning | Provider-dependent | Strong option | Not practical for training |
| Privacy control | Data leaves server/app environment | More controllable | Strong, but model size limited |
| Cost | Pay per API use | GPU/server cost | Device compute and battery |
| Setup complexity | Low | Medium to high | High |
| Best first use | MVP and evaluation | Later custom deployment | Offline lightweight features |

Recommended product path:

```text
Start with API VLM
Collect images and expert corrections
Build Visual RAG case library
Train/evaluate local models on GPU server
Use local VLM for cost/privacy/specialization when it is good enough
```

Do not start by putting a VLM directly on iPhone. For this app, the better architecture is:

```text
iPhone App
  -> Python FastAPI backend
    -> API VLM or local GPU VLM
```

## Server Configuration Guidance

For the current MVP:

| Component | Minimum | Recommended |
| --- | --- | --- |
| Python backend | 2 CPU cores, 4 GB RAM | 2-4 CPU cores, 8 GB RAM |
| Database | Supabase Postgres | Supabase Postgres with backups |
| Image storage | Supabase Storage | Supabase Storage or S3-compatible object storage |
| API VLM | OpenAI/Claude/Gemini-style API | Configurable provider abstraction |

For local GPU VLM inference:

| Model Size | Minimum GPU | Better GPU | Notes |
| --- | --- | --- | --- |
| Small VLM, 2B-4B | 8-12 GB VRAM | 16 GB VRAM | Good for experiments, limited reasoning |
| Medium VLM, 7B-8B | 16 GB VRAM | 24 GB VRAM | Better tradeoff for local server |
| Larger VLM, 13B+ | 24 GB VRAM | 48 GB+ VRAM | More expensive, stronger reasoning |

Suggested server stack:

- Python FastAPI for app-facing API.
- vLLM, Transformers, or model-specific serving stack for local VLM.
- PostgreSQL/Supabase for metadata.
- Object storage for images.
- Vector database or pgvector for image embeddings.
- Background worker for embedding generation and batch evaluation.

## Engineering Notes

This section is primarily for the app/model engineering team.

### Recommended Data Architecture

Store raw images separately from metadata:

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

Keep every AI response and expert correction. Do not overwrite model outputs. Store model name, prompt version, provider, latency, cost estimate, and raw response.

### Suggested Model Output Schema

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

### Zero-Shot Evaluation

Create a small expert-labeled evaluation set before changing prompts heavily.

Track:

- JSON validity rate.
- Label agreement with expert.
- Severity score error.
- False high-risk rate.
- False healthy rate.
- Human review rate.
- Latency.
- Cost per scan.

### Few-Shot Prompting

Few-shot prompting can include text examples, image examples, or retrieved cases. Keep examples short and representative. Do not include too many examples because VLM context is expensive and may dilute the current image.

### Visual RAG

Recommended Visual RAG flow:

```text
new image
  -> image embedding model
  -> vector search
  -> retrieve top-k similar labeled images
  -> send current image + case summaries to VLM
  -> return structured JSON
```

Useful embedding candidates:

- CLIP/SigLIP-style image encoders.
- DINO-style vision encoders.
- Provider embedding APIs if available and acceptable for data rights.

Store:

- `embedding_model`
- `embedding_version`
- `image_id`
- `vector`
- `label_summary`
- `expert_review_status`

### Active Learning

Add a `needs_human_review` workflow early. Prioritize expert review for:

- Low confidence predictions.
- High severity predictions.
- Disagreement between API VLM and local model.
- Unknown or mixed conditions.
- New visual patterns not similar to existing cases.

This improves data efficiency more than collecting random images.

### Local Model Options

Local GPU options can include:

- Open-source VLM inference for structured diagnosis.
- Vision encoder plus classification head for fast screening.
- Grounding/detection model for visible issue localization.
- Segmentation model for affected area estimation.

Do not treat local VLM output as reliable until it has been evaluated on a held-out expert-labeled test set.

### Training Readiness Checklist

Before LoRA or fine-tuning:

- Stable label schema.
- At least one expert-reviewed validation set.
- No image leakage across train/validation/test.
- Enough examples per target class.
- Consistent severity scale.
- Clear commercial/data rights permission.
- Baseline zero-shot API results recorded.
- Baseline Visual RAG results recorded.

### MVP Recommendation

For FarmScout MVP, prioritize:

```text
API VLM + structured JSON
image upload and storage
expert correction workflow
small evaluation set
Visual RAG case library
active learning queue
```

Delay local model training until the app has collected enough labeled and reviewed data.
