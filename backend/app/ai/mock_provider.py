from app.ai.base import AiProviderClient
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


class MockProvider(AiProviderClient):
    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        if request.language == "zh":
            return AnalyzeScanResponse(
                crop_is_lettuce=True,
                crop_confidence=0.96,
                plant_stress_detected=True,
                stress_level="medium",
                severity_score=3,
                confidence=0.74,
                diagnosis="示例分析：该样本显示中度压力迹象。请结合温室位置、近期环境数据和人工观察进行复查。",
                observed_symptoms=[
                    {"type": "leaf_discoloration", "location": "outer leaves", "description": "外层叶片可见轻微黄化。"}
                ],
                possible_causes=[
                    {
                        "category": "irrigation_delivery_to_check",
                        "likelihood": "possible",
                        "reason": "可见轻微黄化，但仅凭图片不能确认供水状态，需要现场检查。",
                    }
                ],
                detected_issues=["sample_result", "moderate_stress"],
                recommendations=["检查该 row 的灌溉供水是否均匀", "查看可用的温室记录", "24 小时内再次扫描"],
                needs_human_review=False,
                human_review_reasons=[],
            )

        return AnalyzeScanResponse(
            crop_is_lettuce=True,
            crop_confidence=0.96,
            plant_stress_detected=True,
            stress_level="medium",
            severity_score=3,
            confidence=0.74,
            diagnosis="Sample analysis: this crop shows moderate stress signals. Review the result with location context, recent environment data, and human inspection.",
            observed_symptoms=[
                {"type": "leaf_discoloration", "location": "outer leaves", "description": "Mild yellowing is visible on outer leaves."}
            ],
            possible_causes=[
                {
                    "category": "irrigation_delivery_to_check",
                    "likelihood": "possible",
                    "reason": "Mild yellowing is visible, but the image cannot confirm water delivery; a field check is needed.",
                }
            ],
            detected_issues=["sample_result", "moderate_stress"],
            recommendations=["Check whether irrigation delivery is even in this row", "Review available greenhouse records", "Scan again within 24 hours"],
            needs_human_review=False,
            human_review_reasons=[],
        )
