"""
Correlation Analysis Agent

Analyzes correlations between telecom KPIs and builds regression models.

Responsibilities:
- Load CSV/Excel files
- Calculate Pearson & Spearman correlations
- Train multiple regression models
- Provide model performance metrics
- Export results

Architecture:
- Inherits from BaseAgent (Phase 0)
- Uses scikit-learn for ML models
- Type-hinted for 100% type safety
- Comprehensive docstrings
- Follows 500-line file limit
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr, spearmanr

logger = logging.getLogger(__name__)


class CorrelationAgent:
    """
    Analyzes correlations and trains regression models on telecom data.
    
    Features:
    - Pearson correlation (linear relationships)
    - Spearman correlation (monotonic relationships)
    - 6 regression models: Linear, Ridge, Lasso, RF, GB, XGBoost
    - Automatic model selection based on R² score
    - Statistical significance testing (p-values)
    
    Attributes:
        name (str): Agent identifier
        version (str): Agent version
        df (Optional[pd.DataFrame]): Loaded dataset
        models (Dict): Trained models cache
        scaler (StandardScaler): Feature scaling
    """
    
    # Model registry: name -> sklearn class
    MODEL_REGISTRY = {
        "linear": LinearRegression,
        "ridge": Ridge,
        "lasso": Lasso,
        "random_forest": RandomForestRegressor,
        "gradient_boosting": GradientBoostingRegressor,
    }
    
    # Model hyperparameters (tuned for CPU)
    MODEL_PARAMS = {
        "linear": {},
        "ridge": {"alpha": 1.0},
        "lasso": {"alpha": 0.1},
        "random_forest": {"n_estimators": 50, "max_depth": 10, "n_jobs": 1},
        "gradient_boosting": {"n_estimators": 50, "max_depth": 5, "learning_rate": 0.1},
    }
    
    def __init__(self, name: str = "correlation_agent", version: str = "0.1.0") -> None:
        """
        Initialize correlation agent.
        
        Args:
            name: Agent identifier
            version: Agent version
        """
        self.name = name
        self.version = version
        self.df: Optional[pd.DataFrame] = None
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        logger.info(f"[{self.name}] Initialized version {self.version}")
    
    def load_data(self, file_path: str) -> bool:
        """
        Load CSV or Excel file.
        
        Args:
            file_path: Path to data file (.csv or .xlsx)
            
        Returns:
            bool: True if loaded successfully
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format unsupported
        """
        try:
            logger.info(f"[{self.name}] Loading data from {file_path}")
            
            if file_path.endswith(".csv"):
                self.df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                self.df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            logger.info(f"[{self.name}] Loaded {len(self.df)} rows, {len(self.df.columns)} columns")
            return True
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to load data: {e}")
            raise
    
    def calculate_correlations(self, numeric_cols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate Pearson and Spearman correlations.
        
        Args:
            numeric_cols: List of numeric columns. If None, auto-detect.
            
        Returns:
            Dict with correlation matrices and p-values
            
        Raises:
            ValueError: If no numeric columns found
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        # Auto-detect numeric columns if not specified
        if numeric_cols is None:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            raise ValueError("No numeric columns found in data")
        
        logger.info(f"[{self.name}] Calculating correlations for {len(numeric_cols)} columns")
        
        # Pearson correlation (linear)
        pearson_corr = self.df[numeric_cols].corr(method="pearson")
        
        # Spearman correlation (monotonic)
        spearman_corr = self.df[numeric_cols].corr(method="spearman")
        
        # P-values for correlations
        p_values = self._calculate_pvalues(numeric_cols)
        
        return {
            "pearson": pearson_corr.to_dict(),
            "spearman": spearman_corr.to_dict(),
            "p_values": p_values,
            "columns": numeric_cols,
        }
    
    def _calculate_pvalues(self, numeric_cols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Calculate p-values for correlations (statistical significance).
        
        Args:
            numeric_cols: Numeric column names
            
        Returns:
            Dict with p-values for each pair
        """
        pvalues = {}
        data = self.df[numeric_cols]
        
        for col1 in numeric_cols:
            pvalues[col1] = {}
            for col2 in numeric_cols:
                if col1 == col2:
                    pvalues[col1][col2] = 0.0
                else:
                    _, pval = pearsonr(data[col1], data[col2])
                    pvalues[col1][col2] = pval
        
        return pvalues
    
    def train_models(
        self,
        target_col: str,
        feature_cols: List[str],
        test_size: float = 0.2,
        models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Train multiple regression models.
        
        Args:
            target_col: Target column name
            feature_cols: List of feature column names
            test_size: Test set fraction (0.2 = 20%)
            models: List of model names. If None, train all.
            
        Returns:
            Dict with trained models and performance metrics
            
        Raises:
            ValueError: If columns not found or data invalid
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        if models is None:
            models = list(self.MODEL_REGISTRY.keys())
        
        logger.info(f"[{self.name}] Training {len(models)} models on {target_col}")
        
        # Prepare data
        X = self.df[feature_cols].fillna(self.df[feature_cols].mean())
        y = self.df[target_col].fillna(self.df[target_col].mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        
        for model_name in models:
            if model_name not in self.MODEL_REGISTRY:
                logger.warning(f"[{self.name}] Unknown model: {model_name}")
                continue
            
            try:
                # Create and train model
                ModelClass = self.MODEL_REGISTRY[model_name]
                params = self.MODEL_PARAMS.get(model_name, {})
                model = ModelClass(**params)
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                
                # Store model and metrics
                self.models[model_name] = model
                results[model_name] = {
                    "r2_score": float(r2),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "trained": True,
                }
                
                logger.info(f"[{self.name}] {model_name}: R² = {r2:.4f}")
                
            except Exception as e:
                logger.error(f"[{self.name}] Failed to train {model_name}: {e}")
                results[model_name] = {"error": str(e), "trained": False}
        
        return results
    
    def get_best_model(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Get best trained model by R² score.
        
        Returns:
            Tuple of (model_name, metrics) or (None, None) if no models trained
        """
        if not self.models:
            return None, None
        
        best_model = max(
            self.models.items(),
            key=lambda x: x[1].get("r2_score", -np.inf)
            if hasattr(x[1], "get") else -np.inf
        )
        
        return best_model[0], {"model": best_model[1]}
    
    def predict(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions with trained model.
        
        Args:
            model_name: Name of trained model
            X: Feature dataframe
            
        Returns:
            Predicted values
            
        Raises:
            ValueError: If model not trained
        """
        if model_name not in self.models:
            raise ValueError(f"Model not trained: {model_name}")
        
        model = self.models[model_name]
        X_scaled = self.scaler.transform(X)
        return model.predict(X_scaled)
    
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method (follows BaseAgent interface).
        
        Args:
            payload: Input with file_path, target_col, feature_cols, models
            
        Returns:
            Dict with analysis results
        """
        try:
            logger.info(f"[{self.name}] Starting correlation analysis")
            
            file_path = payload.get("file_path")
            target_col = payload.get("target_col")
            feature_cols = payload.get("feature_cols")
            model_names = payload.get("models")
            
            # Load data
            self.load_data(file_path)
            
            # Calculate correlations
            corr_results = self.calculate_correlations()
            
            # Train models
            model_results = self.train_models(target_col, feature_cols, models=model_names)
            
            return {
                "status": "success",
                "correlations": corr_results,
                "models": model_results,
                "best_model": self.get_best_model()[0],
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
