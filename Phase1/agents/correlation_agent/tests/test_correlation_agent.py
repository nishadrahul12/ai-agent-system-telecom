"""
Tests for CorrelationAgent

Test coverage:
- Data loading (CSV, Excel)
- Correlation calculations
- Model training
- Predictions
- Error handling
"""

import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np

from Phase1.agents.correlation_agent.correlation_agent import CorrelationAgent


class TestCorrelationAgent(unittest.TestCase):
    """Test suite for CorrelationAgent."""
    
    @classmethod
    def setUpClass(cls):
        """Create test data once for all tests."""
        cls.agent = CorrelationAgent()
        
        # Create temporary test CSV
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_csv = os.path.join(cls.temp_dir, "test_data.csv")
        
        # Generate synthetic telecom KPI data
        np.random.seed(42)
        n_samples = 1000
        traffic = np.random.uniform(50, 500, n_samples)
        prb_util = traffic * 0.8 + np.random.normal(0, 20, n_samples)
        drop_rate = traffic * 0.001 + np.random.normal(0, 0.05, n_samples)
        latency = traffic * 0.02 + np.random.normal(0, 5, n_samples)
        
        df = pd.DataFrame({
            "Traffic": traffic,
            "PRB_Utilization": prb_util,
            "Drop_Call_Rate": drop_rate,
            "Latency": latency,
        })
        
        df.to_csv(cls.test_csv, index=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test files."""
        import shutil
        shutil.rmtree(cls.temp_dir)
    
    def test_load_csv(self):
        """Test loading CSV file."""
        success = self.agent.load_data(self.test_csv)
        self.assertTrue(success)
        self.assertIsNotNone(self.agent.df)
        self.assertEqual(len(self.agent.df), 1000)
    
    def test_calculate_correlations(self):
        """Test correlation calculation."""
        self.agent.load_data(self.test_csv)
        corr_results = self.agent.calculate_correlations()
        
        self.assertIn("pearson", corr_results)
        self.assertIn("spearman", corr_results)
        self.assertIn("p_values", corr_results)
        self.assertEqual(len(corr_results["columns"]), 4)
    
    def test_train_models(self):
        """Test model training."""
        results = self.agent.train_models(
            target_col="PRB_Utilization",
            feature_cols=["Traffic", "Drop_Call_Rate"],
            models=["linear", "ridge"]
        )
        
        self.assertIn("linear", results)
        self.assertIn("ridge", results)
        self.assertTrue(results["linear"]["trained"])
        self.assertGreater(results["linear"]["r2_score"], 0)
    
    def test_get_best_model(self):
        """Test best model selection."""
        self.agent.load_data(self.test_csv)  # ← ADD THIS LINE
        self.agent.train_models(
            target_col="Latency",
            feature_cols=["Traffic"],
            models=["linear", "ridge"]
    )

        
        best_name, best_metrics = self.agent.get_best_model()
        self.assertIsNotNone(best_name)
        self.assertIn(best_name, ["linear", "ridge"])
    
    def test_predict(self):
        """Test prediction."""
        self.agent.train_models(
            target_col="Latency",
            feature_cols=["Traffic"],
            models=["linear"]
        )
        
        X_test = pd.DataFrame({"Traffic": [100, 200, 300]})
        predictions = self.agent.predict("linear", X_test)
        
        self.assertEqual(len(predictions), 3)
        self.assertTrue(np.all(np.isfinite(predictions)))
    
    def test_run_method(self):
        """Test main run() method."""
        payload = {
            "file_path": self.test_csv,
            "target_col": "PRB_Utilization",
            "feature_cols": ["Traffic", "Latency"],
            "models": ["linear", "ridge"]
        }
        
        result = self.agent.run(payload)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("correlations", result)
        self.assertIn("models", result)


if __name__ == "__main__":
    unittest.main()
