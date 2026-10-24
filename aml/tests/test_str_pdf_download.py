import os
import sys
import unittest
from fastapi.testclient import TestClient

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
database_dir = os.path.join(root_dir, "database")

if database_dir not in sys.path:
    sys.path.insert(0, database_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import SessionLocal, init_db
from app.models.models import Case

class TestSTRDownload(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)
        db = SessionLocal()
        try:
            case = db.query(Case).filter(Case.case_id == "CASE_TEST_1001").first()
            if not case:
                case = Case(
                    case_id="CASE_TEST_1001",
                    lead_customer_id="CUST_101",
                    title="Test Case for STR Download",
                    priority="HIGH",
                    status="OPEN",
                    meta_risk_score=85.5,
                    correlated_typologies="['Structuring', 'Layering']",
                    summary="Test case summary for PDF generation"
                )
                db.add(case)
                db.commit()
        finally:
            db.close()

    def test_pdf_download_auth(self):
        # 1. Login to get Bearer token
        login_res = self.client.post("/api/v1/auth/login", json={"username": "officer", "password": "officer123"})
        self.assertEqual(login_res.status_code, 200, f"Login failed: {login_res.text}")
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Generate STR report
        gen_res = self.client.post("/api/v1/str/generate", json={"case_id": "CASE_TEST_1001", "narrative_summary": "Test narrative summary for STR PDF download"}, headers=headers)
        self.assertEqual(gen_res.status_code, 200, f"Generate STR failed: {gen_res.text}")
        report_id = gen_res.json()["report_id"]

        # 3. Request PDF without Auth token -> 401
        no_auth_res = self.client.get(f"/api/v1/str/{report_id}/download")
        self.assertEqual(no_auth_res.status_code, 401, "Unauthenticated request should return 401")

        # 4. Request PDF with Auth token -> 200 OK & PDF binary content
        auth_res = self.client.get(f"/api/v1/str/{report_id}/download", headers=headers)
        self.assertEqual(auth_res.status_code, 200, f"Authenticated download failed: {auth_res.text}")
        self.assertEqual(auth_res.headers["content-type"], "application/pdf")
        self.assertGreater(len(auth_res.content), 0, "PDF content should not be empty")

if __name__ == "__main__":
    unittest.main()
