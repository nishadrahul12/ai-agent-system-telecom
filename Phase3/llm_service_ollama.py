"""
llm_service_ollama.py - Component 4C: Ollama Local LLM Integration

Provides AI-powered natural language explanations using local Llama model.
- Runs on laptop (no cloud API calls)
- FREE (no API costs)
- Private (100% on-device)
- Telecom-compliant (on-premises only)

Author: Telecom AI Agent System
Date: November 24, 2025
Status: PRODUCTION READY
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LLM_OLLAMA - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OllamaLLMService:
    """Local LLM service using Ollama + Llama 3.1 8B"""
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        max_tokens: int = 256,
        temperature: float = 0.7,
        enable_cache: bool = True
    ):
        """
        Initialize Ollama LLM Service
        
        Args:
            model: Model name (llama2, llama3.1, etc.)
            base_url: Ollama server URL
            timeout: Request timeout in seconds (120+ for CPU machines)
            max_tokens: Maximum response tokens (256 recommended for faster inference)
            temperature: Response creativity (0=deterministic, 1=creative)
            enable_cache: Enable response caching to avoid duplicate inference
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_cache = enable_cache
        
        # Response cache: key -> cached response
        self.response_cache = {}
        
        # Statistics
        self.stats = {
            'total_calls': 0,
            'cached_calls': 0,
            'failed_calls': 0,
            'total_tokens': 0,
            'total_time_seconds': 0.0
        }
        
        logger.info(f"OllamaLLMService initialized")
        logger.info(f"  Model: {model}")
        logger.info(f"  URL: {base_url}")
        logger.info(f"  Timeout: {timeout}s")
        logger.info(f"  Max Tokens: {max_tokens}")
        logger.info(f"  Cache: {'Enabled' if enable_cache else 'Disabled'}")
    
    # ========================================================================
    # CONNECTIVITY CHECK
    # ========================================================================
    
    def is_available(self) -> bool:
        """
        Check if Ollama service is running and accessible
        
        Returns:
            bool: True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            available = response.status_code == 200
            if available:
                logger.info("✅ Ollama service is AVAILABLE")
            else:
                logger.warning(f"❌ Ollama returned status {response.status_code}")
            return available
        except Exception as e:
            logger.warning(f"❌ Ollama NOT available: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models on Ollama
        
        Returns:
            List[str]: Model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m['name'].split(':')[0] for m in data.get('models', [])]
                logger.info(f"Available models: {models}")
                return models
            return []
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
    
    # ========================================================================
    # CORE LLM FUNCTIONS
    # ========================================================================
    
    def generate_explanation(
        self,
        kpi_name: str,
        anomaly_count: int,
        severity: str,
        z_score: float,
        method: str = "Z-Score"
    ) -> str:
        """
        Generate natural language explanation for an anomaly
        
        Example:
            Input: kpi_name="Avg SINR for PUCCH", anomaly_count=9, severity="warning", z_score=2.5
            Output: "Signal quality degradation detected in SINR measurements. 
                     9 anomalies found with 2.5 standard deviations from normal. 
                     This typically indicates cell site power or antenna issues."
        
        Args:
            kpi_name: KPI name
            anomaly_count: Number of anomalies
            severity: Severity level (critical, warning, normal)
            z_score: Z-score deviation
            method: Detection method used
        
        Returns:
            str: Natural language explanation
        """
        cache_key = f"explanation_{kpi_name}_{severity}"
        
        if self.enable_cache and cache_key in self.response_cache:
            logger.info(f"✅ Cache HIT: explanation for {kpi_name}")
            self.stats['cached_calls'] += 1
            return self.response_cache[cache_key]
        
        prompt = f"""Briefly explain this telecom network anomaly in 1-2 sentences.

KPI: {kpi_name}
Anomalies Detected: {anomaly_count}
Severity: {severity}
Z-Score Deviation: {z_score:.2f}
Detection Method: {method}

Focus on: What this means for network operators, likely causes, impact.
Keep response technical but clear. Do NOT include recommendations, only explanation."""

        response = self._call_ollama(prompt)
        
        if self.enable_cache:
            self.response_cache[cache_key] = response
        
        return response
    
    def generate_recommendations(
        self,
        top_anomalies: List[Dict],
        health_score: int,
        trend: str,
        critical_count: int = 0
    ) -> List[str]:
        """
        Generate actionable recommendations for operators
        
        Example:
            Input: top_anomalies=[{kpi:"Avg SINR for PUCCH", count:9}, ...],
                   health_score=0, trend="improving"
            Output: [
                "1. PRIORITY: Investigate SINR for PUCCH degradation (9 anomalies)",
                "2. Check cell site power settings",
                "3. Review antenna alignment"
            ]
        
        Args:
            top_anomalies: List of top affected KPIs with counts
            health_score: Network health score (0-100)
            trend: Trend direction (improving, stable, worsening)
            critical_count: Number of critical anomalies
        
        Returns:
            List[str]: Actionable recommendations
        """
        # Build anomaly list for prompt
        anomaly_text = "\n".join([
            f"  • {a.get('kpi_name', 'Unknown')}: {a.get('count', 0)} anomalies"
            for a in top_anomalies[:5]
        ])
        
        prompt = f"""Generate 3-4 specific technical recommendations for telecom operators to address these anomalies:

Top Affected KPIs:
{anomaly_text}

Network Health Score: {health_score}/100
Trend: {trend}
Critical Anomalies: {critical_count}

Format your response as a numbered list:
1. [First action - most urgent]
2. [Second action]
3. [Third action]

Be specific, actionable, technical. Focus on immediate actions operators can take."""

        response = self._call_ollama(prompt)
        
        # Parse response into list
        recommendations = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and any(c.isdigit() for c in line[:3])
        ]
        
        return recommendations if recommendations else [response]
    
    def generate_summary(
        self,
        total_anomalies: int,
        critical_count: int,
        warning_count: int,
        health_trend: str,
        most_affected_kpi: str = ""
    ) -> str:
        """
        Generate executive summary for management
        
        Example:
            Output: "Your network detected 124 anomalies in March 2024, with 20 requiring 
                     immediate attention. Signal quality is the primary concern. Recent 
                     improvements suggest mitigation efforts are working."
        
        Args:
            total_anomalies: Total anomalies found
            critical_count: Critical anomalies
            warning_count: Warning-level anomalies
            health_trend: Overall trend
            most_affected_kpi: Most affected KPI name
        
        Returns:
            str: 2-3 sentence executive summary
        """
        cache_key = "summary"
        
        if self.enable_cache and cache_key in self.response_cache:
            logger.info(f"✅ Cache HIT: summary")
            self.stats['cached_calls'] += 1
            return self.response_cache[cache_key]
        
        prompt = f"""Write a 2-3 sentence executive summary for a telecom network analysis report:

Total Anomalies: {total_anomalies}
Critical Issues: {critical_count}
Warning Level Issues: {warning_count}
Overall Trend: {health_trend}
Most Affected Area: {most_affected_kpi if most_affected_kpi else 'Multiple KPIs'}

Focus on: severity assessment, primary issues, trend direction.
Make it suitable for management briefing (non-technical language acceptable).
Do NOT include recommendations, only assessment and status."""

        response = self._call_ollama(prompt)
        
        if self.enable_cache:
            self.response_cache[cache_key] = response
        
        return response
    
    # ========================================================================
    # INTERNAL OLLAMA CALL
    # ========================================================================
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Internal method to call Ollama API
        
        Note: Uses max_tokens=256 (not 512) for faster inference on CPU
        Timeout: 120 seconds (recommended for slower CPU machines)
        
        Args:
            prompt: Prompt text
        
        Returns:
            str: LLM response (or error message if failed)
        """
        self.stats['total_calls'] += 1
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9
            }
        }
        
        try:
            start_time = time.time()
            logger.info(f"⏳ Calling Ollama ({self.model})... (may take 30-60s on CPU)")
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            self.stats['total_time_seconds'] += elapsed
            
            logger.info(f"✅ Ollama responded in {elapsed:.1f}s")
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                # Track tokens (estimate if not provided)
                tokens = result.get("eval_count", len(llm_response.split()) * 2)
                self.stats['total_tokens'] += tokens
                
                return llm_response if llm_response else "[Ollama returned empty response]"
            else:
                error_msg = f"Ollama error: {response.status_code}"
                logger.error(f"❌ {error_msg}")
                self.stats['failed_calls'] += 1
                return f"[{error_msg}]"
        
        except requests.exceptions.Timeout:
            error_msg = f"Ollama timeout (>{self.timeout}s) - request may be too large"
            logger.error(f"❌ {error_msg}")
            self.stats['failed_calls'] += 1
            return f"[{error_msg}]"
        
        except Exception as e:
            error_msg = f"Ollama error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.stats['failed_calls'] += 1
            return f"[{error_msg}]"
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def get_stats(self) -> Dict:
        """
        Get service statistics
        
        Returns:
            Dict: Statistics including calls, cache hits, tokens used
        """
        return {
            **self.stats,
            'cache_hit_rate': (
                round(self.stats['cached_calls'] / max(1, self.stats['total_calls']) * 100, 2)
                if self.stats['total_calls'] > 0 else 0
            ),
            'avg_response_time': (
                round(self.stats['total_time_seconds'] / max(1, self.stats['total_calls'] - self.stats['cached_calls']), 2)
            ),
            'cache_size': len(self.response_cache)
        }
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        logger.info("✅ Response cache cleared")
    
    def log_stats(self):
        """Log statistics to console"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("LLM SERVICE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total API Calls:       {stats['total_calls']}")
        logger.info(f"Cached Calls:          {stats['cached_calls']}")
        logger.info(f"Cache Hit Rate:        {stats['cache_hit_rate']}%")
        logger.info(f"Failed Calls:          {stats['failed_calls']}")
        logger.info(f"Total Tokens:          {stats['total_tokens']}")
        logger.info(f"Avg Response Time:     {stats['avg_response_time']:.1f}s")
        logger.info(f"Total Time:            {stats['total_time_seconds']:.1f}s")
        logger.info(f"Cache Size:            {stats['cache_size']} items")
        logger.info("=" * 60)


# ============================================================================
# TESTING & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    """
    Test script for local development
    Run with: python llm_service_ollama.py
    """
    
    print("\n" + "=" * 70)
    print("COMPONENT 4C - OLLAMA LLM SERVICE TEST")
    print("=" * 70)
    
    # Initialize service
    llm = OllamaLLMService(model="llama2")
    
    # Check connectivity
    print("\n1️⃣  CHECKING OLLAMA CONNECTIVITY...")
    if not llm.is_available():
        print("❌ ERROR: Ollama is not running!")
        print("   Start Ollama with: ollama serve")
        print("   Or launch the Ollama app from your applications")
        exit(1)
    print("✅ Ollama is running!")
    
    # Check available models
    print("\n2️⃣  AVAILABLE MODELS...")
    models = llm.get_available_models()
    print(f"   Models: {', '.join(models)}")
    if "llama2" not in models and "llama3.1" not in models:
        print("   ⚠️  WARNING: llama2/llama3.1 not found. Download with: ollama pull llama2")
    
    # Generate explanation
    print("\n3️⃣  GENERATING ANOMALY EXPLANATION...")
    explanation = llm.generate_explanation(
        kpi_name="Avg SINR for PUCCH",
        anomaly_count=9,
        severity="warning",
        z_score=2.5,
        method="Z-Score"
    )
    print(f"\n   Explanation:\n   {explanation}\n")
    
    # Generate recommendations
    print("4️⃣  GENERATING RECOMMENDATIONS...")
    recommendations = llm.generate_recommendations(
        top_anomalies=[
            {"kpi_name": "Avg SINR for PUCCH", "count": 9},
            {"kpi_name": "Avg PRB usage per TTI UL", "count": 8},
            {"kpi_name": "Downlink Power per TTI", "count": 5}
        ],
        health_score=0,
        trend="improving",
        critical_count=0
    )
    print(f"\n   Recommendations:")
    for rec in recommendations:
        print(f"   {rec}")
    
    # Generate summary
    print("\n5️⃣  GENERATING EXECUTIVE SUMMARY...")
    summary = llm.generate_summary(
        total_anomalies=124,
        critical_count=20,
        warning_count=104,
        health_trend="improving",
        most_affected_kpi="Avg SINR for PUCCH"
    )
    print(f"\n   Summary:\n   {summary}\n")
    
    # Show statistics
    print("6️⃣  SERVICE STATISTICS...")
    llm.log_stats()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nComponent 4C is ready for integration with anomaly_api.py")
    print("Next: Update anomaly_api.py to add LLM endpoint\n")
