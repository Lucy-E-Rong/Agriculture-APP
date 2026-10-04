import base64
import json
import unittest
from uuid import UUID

import httpx

from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse, PrototypeAnalysisResponse
from app.supabase_persistence import PersistenceError, SupabaseScanStore


def analysis() -> AnalyzeScanResponse:
    return AnalyzeScanResponse(
        crop_is_lettuce=True,
        crop_confidence=0.96,
        image_quality={"usable": True, "issues": [], "retake_guidance": []},
        plant_stress_detected=True,
        stress_level="medium",
        severity_score=3,
        confidence=0.74,
        diagnosis="Visible stress",
        observed_symptoms=[{
            "type": "wilting",
            "location": "outer_leaves",
            "description": "Visible loss of turgor on outer leaves.",
        }],
        possible_causes=[],
        detected_issues=["yellowing"],
        recommendations=["Inspect irrigation"],
        needs_human_review=True,
    )


def request(provider: str = "gemini") -> AnalyzeScanRequest:
    jpeg = b"\xff\xd8compressed-jpeg\xff\xd9"
    return AnalyzeScanRequest(
        image_base64=base64.b64encode(jpeg).decode(),
        image_mime_type="image/jpeg",
        provider=provider,
        language="en",
        location_snapshot={"display": "GH1 · SA · T1 · R1"},
    )


class SupabaseScanStoreTests(unittest.IsolatedAsyncioTestCase):
    def settings(self) -> Settings:
        return Settings(
            _env_file=None,
            supabase_url="https://project.supabase.co",
            supabase_service_role_key="sb_secret_test",
        )

    async def test_success_uploads_before_insert_and_uses_matching_id(self) -> None:
        seen: list[httpx.Request] = []

        def handler(incoming: httpx.Request) -> httpx.Response:
            seen.append(incoming)
            return httpx.Response(201, request=incoming)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await SupabaseScanStore(self.settings(), client).persist_success(
                request(), analysis(), "gemini-test"
            )

        self.assertEqual([item.method for item in seen], ["POST", "POST"])
        self.assertIn("/storage/v1/object/scan-images/demo/", str(seen[0].url))
        row = json.loads(seen[1].content)
        self.assertEqual(row["id"], str(result.scan_id))
        self.assertTrue(row["image_path"].endswith(f"{result.scan_id}.jpg"))
        self.assertEqual(row["analysis_result"]["diagnosis"], row["diagnosis"])
        self.assertEqual(row["status"], "succeeded")
        self.assertEqual(row["data_stage"], "demo")
        self.assertEqual(row["data_purpose"], "user_upload")
        self.assertEqual(row["location_snapshot"], {"display": "GH1 · SA · T1 · R1"})
        self.assertEqual(seen[0].headers["apikey"], "sb_secret_test")
        self.assertNotIn("authorization", seen[0].headers)

    async def test_prototype_is_preserved_in_scan_row(self) -> None:
        seen: list[httpx.Request] = []

        def handler(incoming: httpx.Request) -> httpx.Response:
            seen.append(incoming)
            return httpx.Response(201, request=incoming)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await SupabaseScanStore(self.settings(), client).persist_success(
                request("prototype"), PrototypeAnalysisResponse(
                    response_text="The leaves look droopy; check irrigation."
                ), "gemini-test"
            )

        row = json.loads(seen[1].content)
        self.assertEqual(row["ai_provider"], "prototype")
        self.assertEqual(row["analysis_result"]["response_kind"], "prototype")
        self.assertNotIn("stress_level", row)
        self.assertEqual(result.response_text, "The leaves look droopy; check irrigation.")

    async def test_insert_failure_deletes_the_exact_uploaded_object(self) -> None:
        seen: list[httpx.Request] = []

        def handler(incoming: httpx.Request) -> httpx.Response:
            seen.append(incoming)
            status = 500 if "/rest/v1/scans" in str(incoming.url) else 200
            return httpx.Response(status, request=incoming)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(PersistenceError):
                await SupabaseScanStore(self.settings(), client).persist_success(
                    request(), analysis(), "gemini-test"
                )

        self.assertEqual([item.method for item in seen], ["POST", "POST", "DELETE"])
        upload_path = str(seen[0].url).replace("?", "")
        delete_path = str(seen[2].url).replace("?", "")
        self.assertEqual(upload_path, delete_path)

    async def test_insert_constraint_error_is_safe_and_keeps_diagnostics(self) -> None:
        seen: list[httpx.Request] = []
        sensitive_detail = (
            "Failing row contains (private diagnosis, analysis_result, /9j/image-data, "
            "sb_secret_test)"
        )

        def handler(incoming: httpx.Request) -> httpx.Response:
            seen.append(incoming)
            if "/rest/v1/scans" in str(incoming.url):
                return httpx.Response(
                    400,
                    json={
                        "code": "23514",
                        "message": (
                            'new row violates check constraint "scans_ai_provider_check"'
                        ),
                        "details": sensitive_detail,
                        "hint": "Allow the prototype provider",
                    },
                    request=incoming,
                )
            return httpx.Response(200, request=incoming)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertLogs("farmscout.persistence", level="ERROR") as captured:
                with self.assertRaises(PersistenceError) as raised:
                    await SupabaseScanStore(self.settings(), client).persist_success(
                        request("prototype"), analysis(), "gemini-test"
                    )

        diagnostic = f"{raised.exception} {' '.join(captured.output)}"
        self.assertIn("status=400", diagnostic)
        self.assertIn("23514", diagnostic)
        self.assertIn("scans_ai_provider_check", diagnostic)
        self.assertIn("Allow the prototype provider", diagnostic)
        self.assertIn("[redacted: Supabase error may contain sensitive row data]", diagnostic)
        for secret in (
            "private diagnosis",
            "analysis_result",
            "/9j/image-data",
            "sb_secret_test",
            "authorization",
        ):
            with self.subTest(secret=secret):
                self.assertNotIn(secret.lower(), diagnostic.lower())
        self.assertEqual([item.method for item in seen], ["POST", "POST", "DELETE"])
        self.assertEqual(
            str(seen[0].url).replace("?", ""),
            str(seen[2].url).replace("?", ""),
        )

    def test_non_json_error_body_is_bounded_and_redacts_credentials(self) -> None:
        store = SupabaseScanStore(self.settings())
        body = "Authorization: Bearer private-token " + "x" * 1000
        response = httpx.Response(502, text=body)

        with self.assertLogs("farmscout.persistence", level="ERROR") as captured:
            with self.assertRaises(PersistenceError) as raised:
                store._raise_for_status(response, "Scan row insert failed")

        diagnostic = f"{raised.exception} {' '.join(captured.output)}"
        self.assertIn("status=502", diagnostic)
        self.assertIn("non-JSON", diagnostic)
        self.assertIn("[truncated]", diagnostic)
        self.assertNotIn("private-token", diagnostic)

    async def test_recent_query_enforces_contract_and_limit(self) -> None:
        def handler(incoming: httpx.Request) -> httpx.Response:
            self.assertIn("data_stage=eq.demo", str(incoming.url))
            self.assertIn("data_purpose=eq.user_upload", str(incoming.url))
            self.assertIn("status=eq.succeeded", str(incoming.url))
            self.assertIn("order=created_at.desc", str(incoming.url))
            self.assertIn("limit=10", str(incoming.url))
            return httpx.Response(200, json=[], request=incoming)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            rows = await SupabaseScanStore(self.settings(), client).list_recent(50)
        self.assertEqual(rows, [])

    async def test_detail_signs_private_image_without_selecting_raw_response(self) -> None:
        scan_id = UUID("00000000-0000-0000-0000-000000000123")

        def handler(incoming: httpx.Request) -> httpx.Response:
            if "/rest/v1/scans" in str(incoming.url):
                self.assertNotIn("raw_model_response", str(incoming.url))
                return httpx.Response(
                    200,
                    json=[{
                        "id": str(scan_id),
                        "created_at": "2026-08-21T01:02:03+00:00",
                        "stress_level": "medium",
                        "severity_score": 3,
                        "confidence": 0.74,
                        "diagnosis": "Visible stress",
                        "location_snapshot": {"display": "GH1"},
                        "analysis_result": analysis().model_dump(mode="json"),
                        "image_path": f"demo/2026/08/21/{scan_id}.jpg",
                    }],
                    request=incoming,
                )
            return httpx.Response(
                200,
                json={"signedURL": "/object/sign/scan-images/demo/signed.jpg?token=test"},
                request=incoming,
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            detail = await SupabaseScanStore(self.settings(), client).get_detail(scan_id)
        self.assertEqual(detail.id, scan_id)
        self.assertEqual(
            detail.image_url,
            "https://project.supabase.co/storage/v1/object/sign/scan-images/demo/signed.jpg?token=test",
        )

    async def test_signed_url_normalization_supports_supabase_response_variants(self) -> None:
        cases = [
            (
                {"signedURL": "/object/sign/scan-images/demo/signed.jpg?token=official"},
                "https://project.supabase.co/storage/v1/object/sign/scan-images/demo/signed.jpg?token=official",
            ),
            (
                {"signedUrl": "/storage/v1/object/sign/scan-images/demo/signed.jpg?token=prefixed"},
                "https://project.supabase.co/storage/v1/object/sign/scan-images/demo/signed.jpg?token=prefixed",
            ),
            (
                {"signedURL": "https://cdn.example.test/private.jpg?token=absolute"},
                "https://cdn.example.test/private.jpg?token=absolute",
            ),
        ]

        for payload, expected in cases:
            with self.subTest(payload=payload):
                def handler(incoming: httpx.Request) -> httpx.Response:
                    return httpx.Response(200, json=payload, request=incoming)

                async with httpx.AsyncClient(
                    transport=httpx.MockTransport(handler)
                ) as client:
                    result = await SupabaseScanStore(
                        self.settings(), client
                    )._create_signed_url("demo/signed.jpg")

                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
