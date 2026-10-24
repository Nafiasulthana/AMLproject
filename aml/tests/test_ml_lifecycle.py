import os
import sys
import unittest
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

# Ensure root and database directories are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
database_dir = os.path.join(root_dir, "database")
backend_dir = os.path.join(root_dir, "backend")

if database_dir not in sys.path:
    sys.path.insert(0, database_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ml.explainer import AMLExplainer, explainer
from ml.train_model import train_and_save_model
from simulation.simulator import simulator_engine


class TestMLLifecycle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure model is trained once prior to tests
        train_and_save_model()

    def test_01_model_loading_success(self):
        """Verify that existing xgboost_aml.json loads successfully into AMLExplainer."""
        ex = AMLExplainer()
        self.assertIsNotNone(ex.model, "XGBoost model should be loaded successfully.")
        self.assertIsNotNone(ex._shap_explainer, "SHAP TreeExplainer should be initialized.")
        self.assertEqual(len(ex.feature_names), 17)

    def test_02_missing_model_raises_error(self):
        """Verify that missing model file raises FileNotFoundError when raise_if_missing=True."""
        temp_dir = tempfile.mkdtemp()
        try:
            ex = AMLExplainer.__new__(AMLExplainer)
            ex.model_dir = temp_dir
            ex.model = None
            ex._shap_explainer = None
            ex.feature_names = [
                "amount", "z_score_amount", "degree_centrality", "betweenness_centrality",
                "money_retention_ratio", "hop_count", "structuring_flag", "layering_flag",
                "round_trip_flag", "dormant_flag", "smurfing_flag", "high_risk_flag_count",
                "risk_flag_any", "z_score_retention_ratio", "unretained_amount",
                "graph_activity_score", "velocity_pass_through"
            ]

            with self.assertRaises(FileNotFoundError) as ctx:
                ex.load_model(model_dir=temp_dir, raise_if_missing=True)
            
            self.assertIn("XGBoost model not found", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir)

    def test_03_no_startup_training(self):
        """Verify that application startup lifespan loads existing model and DOES NOT retrain."""
        from app.main import lifespan, app
        import asyncio

        with patch("ml.train_model.train_and_save_model") as mock_train:
            with patch("ml.explainer.explainer.load_model") as mock_load:
                async def run_lifespan():
                    async with lifespan(app):
                        pass

                asyncio.run(run_lifespan())

                # Assert train_and_save_model was NOT called
                mock_train.assert_not_called()
                # Assert load_model WAS called with raise_if_missing=True
                mock_load.assert_called_once_with(raise_if_missing=True)

    def test_04_simulator_uses_existing_model_no_retrain(self):
        """Verify that simulator transaction processing scores using existing model without retraining."""
        with patch("ml.train_model.train_and_save_model") as mock_train:
            sample_tx = simulator_engine.generate_single_transaction()
            res = explainer.explain_transaction({
                "amount": sample_tx["amount"],
                "z_score_amount": 0.5,
                "degree_centrality": 3,
                "betweenness_centrality": 0.05,
                "money_retention_ratio": 0.8,
                "hop_count": 2
            })
            
            self.assertTrue(res["model_used"], "Inference should use the pre-loaded XGBoost model.")
            self.assertIn("prediction_probability", res)
            mock_train.assert_not_called()

    def test_05_reproducibility(self):
        """Verify that training twice with seed 42 produces identical metrics."""
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()
        try:
            _, _, metrics1 = train_and_save_model(model_dir=temp_dir1)
            _, _, metrics2 = train_and_save_model(model_dir=temp_dir2)

            self.assertEqual(metrics1["accuracy"], metrics2["accuracy"])
            self.assertEqual(metrics1["precision"], metrics2["precision"])
            self.assertEqual(metrics1["recall"], metrics2["recall"])
            self.assertEqual(metrics1["f1_score"], metrics2["f1_score"])
            self.assertEqual(metrics1["roc_auc"], metrics2["roc_auc"])
            self.assertEqual(metrics1["pr_auc"], metrics2["pr_auc"])
            self.assertEqual(metrics1["tn"], metrics2["tn"])
            self.assertEqual(metrics1["fp"], metrics2["fp"])
            self.assertEqual(metrics1["fn"], metrics2["fn"])
            self.assertEqual(metrics1["tp"], metrics2["tp"])
        finally:
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)

    def test_06_feature_consistency(self):
        """Verify feature list in model metadata matches feature order expected during inference."""
        meta_path = os.path.join(explainer.model_dir, "model_metadata.json")
        self.assertTrue(os.path.exists(meta_path), "model_metadata.json should exist.")
        
        with open(meta_path, "r") as f:
            meta = json.load(f)

        training_features = meta.get("features")
        self.assertEqual(training_features, explainer.feature_names,
                         "Feature order in training metadata must match inference explainer feature_names.")


if __name__ == "__main__":
    unittest.main()
