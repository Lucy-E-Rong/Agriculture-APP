# Agriculture Lab Image Dataset Requirements

This document defines the engineering requirements for image data collected by the agriculture lab for FarmScout. The goal is to create a dataset that can support VLM fine-tuning, LoRA experiments, classification-head training, model evaluation, and app feature testing.

The lab should define the agricultural diagnosis categories and experimental design. This document focuses only on the data format, image quality, labeling consistency, metadata, delivery structure, and usage rights needed by the app and model engineering team.

## Collection Targets

Use phased targets so the team can validate the data pipeline before committing to a large collection effort.

| Phase | Image Count | Purpose |
| --- | ---: | --- |
| Pilot | 1,000-2,000 | Validate image quality, label format, upload flow, and early AI evaluation. |
| MVP feasibility | 3,000-5,000 | Test API-based analysis and initial local model experiments. |
| Trainable local model | 15,000-50,000 | Support meaningful VLM fine-tuning, LoRA, or classification-head training. |
| Commercial robustness | 50,000-100,000+ | Improve generalization across locations, devices, lighting, crops, and batches. |

The exact category list should come from the lab. For the first pilot, collect healthy samples plus the 3-5 highest-priority issue categories.

## Image Requirements

- Accepted formats: JPG, PNG, or HEIC. JPG is preferred for delivery.
- Minimum resolution: 1024 x 1024 pixels.
- Original phone or camera images are preferred.
- Do not apply filters, beauty effects, stickers, annotations, or color edits.
- Do not compress images heavily before delivery.
- The crop subject should be clear and visible.
- Include realistic mobile-app variation, not only ideal lab photos.

Useful variation includes:

- Different lighting conditions.
- Different shooting distances.
- Different angles.
- Different phone or camera devices.
- Different growth stages.
- Different collection dates and batches.
- Different greenhouse areas or experimental locations.

## Capture Protocol

For each plant or sample, collect a small set of related images when possible:

- One top-view image.
- One side-view image.
- One to three close-up images of visible symptoms or relevant crop areas.
- Optional environment or location context image.

Repeated images of the same plant are valuable, especially across multiple days. If the same plant or sample is photographed multiple times, all related images must share a stable `plant_id` or `sample_id`.

## Required Metadata

Deliver a `labels.csv` file where each row corresponds to one image.

Minimum required fields:

```csv
image_id,file_name,sample_id,plant_id,crop_name,variety,growth_stage,capture_date,greenhouse_id,location_id,condition_label,severity_score,annotation_confidence,annotated_by,annotation_date,notes
```

Field expectations:

| Field | Requirement |
| --- | --- |
| `image_id` | Unique image identifier. The lab may provide this, or engineering can generate it. |
| `file_name` | Exact image file name in the delivered `images/` folder. |
| `sample_id` | Stable ID for the sample or experimental unit. |
| `plant_id` | Stable ID for the plant when available. |
| `crop_name` | Crop name. |
| `variety` | Variety or cultivar when available. |
| `growth_stage` | Lab-defined growth stage. |
| `capture_date` | Date the image was captured. |
| `greenhouse_id` | Greenhouse, room, or facility identifier. |
| `location_id` | More specific location if available, such as section, table, or row. |
| `condition_label` | Lab-defined primary condition label. |
| `severity_score` | Numeric severity score from 0 to 5. |
| `annotation_confidence` | `low`, `medium`, or `high`. |
| `annotated_by` | Expert, technician, or annotator identifier. |
| `annotation_date` | Date the label was created or confirmed. |
| `notes` | Optional free-text context. |

## Labeling Rules

Use a fixed label schema for each dataset batch.

- Provide a `label_schema.json` file with every allowed label and its meaning.
- Include a schema version, such as `label_schema_v1`.
- Avoid duplicate spellings for the same class.
- Avoid mixing multiple names for the same condition.
- Avoid mixing Chinese and English labels inside the same schema unless both are explicitly mapped.
- Support `primary_label` and `secondary_label` if one image can contain multiple issues.
- Use `unknown` when the image cannot be confidently labeled.
- Use `mixed` only when the lab intentionally defines a mixed-condition class.

Recommended severity scale:

| Score | Meaning |
| ---: | --- |
| 0 | Healthy or no visible issue. |
| 1 | Very mild or early signal. |
| 2 | Mild. |
| 3 | Moderate. |
| 4 | Severe. |
| 5 | Critical, crop loss, or near unrecoverable. |

If the lab already has a different scoring system, include the scoring definition in the dataset README so engineering can map it consistently.

## Optional Advanced Annotation

Advanced annotation is not required for the first pilot, but it is useful for later model training.

| Level | Annotation Type | Use Case |
| --- | --- | --- |
| Level 1 | Image-level label | Fastest option. Suitable for early classification and VLM evaluation. |
| Level 2 | Bounding boxes | Useful for training detection models and locating visible problem areas. |
| Level 3 | Segmentation masks | Most detailed option. Useful for precise affected-area modeling. |

Recommended approach:

- Start with Level 1 for the first pilot.
- Add Level 2 bounding boxes for the most important or most common categories.
- Consider Level 3 only after the label schema and model goals are stable.

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

If possible, reserve one independent test set from a different date, batch, greenhouse, or device group. This helps measure whether the model works outside the exact data used for training.

## Delivery Format

Deliver each batch as a folder with this structure:

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

## Data Rights Checklist

Before using the dataset for model development, confirm whether the images and labels may be used for:

- AI model training.
- AI model evaluation.
- App product testing.
- Long-term storage.
- Commercial product use.
- Derivative model creation.
- Anonymized demos, reports, or presentations.

Any restrictions should be documented in the batch README or a separate data agreement.

## Suggested First Pilot

The first pilot should focus on validating the end-to-end data workflow rather than maximizing model accuracy.

Recommended pilot scope:

- 1,000-2,000 images.
- Healthy samples plus 3-5 lab-priority categories.
- Image-level labels.
- Severity score from 0 to 5.
- Stable `sample_id` or `plant_id`.
- A complete `labels.csv`.
- A fixed `label_schema.json`.

After the pilot, the engineering team should review image quality, label consistency, metadata completeness, and model evaluation results before scaling collection.
