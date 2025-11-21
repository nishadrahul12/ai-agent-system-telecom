"""
LLM Configuration & Management.

Provides LLM runtime configuration and integration layer:
    - Configuration management (model, parameters, timeouts)
    - Health checks and model availability
    - Caching for LLM responses
    - Fallback and error handling
    - Integration with local runtimes (Ollama, LM Studio)

Status: PREPARED FOR PHASE 1
    - Phase 0: Config only, no actual LLM calls
    - Phase 1: Activate LLM with agent integration

Setup Instructions (for Phase 1):
    1. Install Ollama: https://ollama.ai
    2. Download model: ollama pull mistral (or llama2, neural-chat)
    3. Start Ollama: ollama serve
    4. Verify: curl http://localhost:11434/api/tags
    5. Update config in llm_config.py (uncomment LLM_ENABLED = True)

Usage (Phase 1):
    from orchestrator.llm_config import LLMConfig
    
    llm = LLMConfig()
    response = llm.generate(prompt="Analyze this data: ...", max_tokens=256)
"""

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION (Customize per your environment)
# ============================================================================

# ❌ PHASE 0: LLM disabled (agents work without LLM)
# ✅ PHASE 1: Set to True and ensure Ollama running
LLM_ENABLED = False

# LLM Runtime Configuration
LLM_CONFIG = {
    # Model selection (Phase 1: choose based on your hardware)
    "model": "mistral",  # Options: "mistral", "llama2", "neural-chat", "phi"
    
    # Local runtime endpoint (Ollama or LM Studio)
    "base_url": "http://localhost:11434",  # Ollama default
    # Alternative: "http://localhost:1234"  # LM Studio default
    
    # Model parameters (optimized for i7-8750H)
    "max_tokens": 256,  # CPU-optimized (not 512)
    "temperature": 0.7,  # Creativity (0=deterministic, 1=random)
    "top_p": 0.9,  # Nucleus sampling
    
    # Performance tuning
    "timeout": 60,  # Inference timeout (seconds)
    "request_timeout": 120,  # HTTP request timeout
    
    # Caching
    "cache_enabled": True,
    "cache_size": 5,  # Number of responses to cache
    
    # Fallback
    "use_mock_responses": True,  # Phase 0: Always True
}

# Memory limits
CACHE_MAX_SIZE = 5  # Responses to cache
CACHE_MEMORY_LIMIT = 100 * 1024 * 1024  # 100MB


class LLMCache:
    """
    Simple LLM response cache (in-memory).
    
    Attributes:
        _cache (dict): Cached responses by prompt hash
        _access_count (dict): Access count per cache entry
    """
    
    def __init__(self, max_size: int = CACHE_MAX_SIZE) -> None:
        """
        Initialize cache.
        
        Args:
            max_size (int): Maximum cached responses
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_count: Dict[str, int] = {}
        self.max_size = max_size
        logger.info(f"LLMCache initialized (max_size={max_size})")
    
    def get(self, prompt: str) -> Optional[str]:
        """
        Retrieve cached response.
        
        Args:
            prompt (str): Input prompt
            
        Returns:
            Optional[str]: Cached response if found, None otherwise
        """
        prompt_hash = hash(prompt)
        
        if prompt_hash in self._cache:
            self._access_count[prompt_hash] += 1
            logger.debug(f"Cache hit: {prompt_hash}")
            return self._cache[prompt_hash]["response"]
        
        return None
    
    def put(self, prompt: str, response: str) -> None:
        """
        Cache a response.
        
        Args:
            prompt (str): Input prompt
            response (str): LLM response
        """
        prompt_hash = hash(prompt)
        
        # Evict least-accessed item if cache full
        if len(self._cache) >= self.max_size:
            lru_key = min(self._access_count, key=self._access_count.get)
            del self._cache[lru_key]
            del self._access_count[lru_key]
            logger.debug(f"Cache evicted: {lru_key}")
        
        self._cache[prompt_hash] = {
            "response": response,
            "timestamp": time.time(),
        }
        self._access_count[prompt_hash] = 1
        logger.debug(f"Cache stored: {prompt_hash}")
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        self._access_count.clear()
        logger.info("Cache cleared")


class LLMConfig:
    """
    LLM configuration and management.
    
    Status: PREPARED FOR PHASE 1
        - Phase 0: Mock responses only
        - Phase 1: Activate with real Ollama/LM Studio
    
    Attributes:
        _cache (LLMCache): Response cache
        _config (dict): Runtime configuration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize LLM configuration.
        
        Args:
            config (Optional[Dict]): Override default configuration
        """
        self._config = {**LLM_CONFIG}
        if config:
            self._config.update(config)
        
        self._cache = LLMCache(max_size=self._config.get("cache_size", CACHE_MAX_SIZE))
        
        logger.info(f"LLMConfig initialized (enabled={LLM_ENABLED})")
    
    def is_available(self) -> bool:
        """
        Check if LLM is available.
        
        Returns:
            bool: True if LLM ready (Phase 1) or mock enabled (Phase 0)
        """
        if not LLM_ENABLED:
            logger.debug("LLM disabled (Phase 0)")
            return self._config.get("use_mock_responses", True)
        
        # Phase 1: Check actual LLM availability
        try:
            import requests
            url = f"{self._config['base_url']}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response from LLM.
        
        Phase 0: Returns mock response
        Phase 1: Calls actual LLM (Ollama/LM Studio)
        
        Args:
            prompt (str): Input prompt
            max_tokens (Optional[int]): Max response tokens
            
        Returns:
            str: Generated response
            
        Raises:
            RuntimeError: If LLM unavailable and no mock
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be non-empty string")
        
        max_tokens = max_tokens or self._config.get("max_tokens", 256)
        
        logger.info(f"Generate request: {len(prompt)} chars, max_tokens={max_tokens}")
        
        # Check cache
        if self._config.get("cache_enabled", True):
            cached = self._cache.get(prompt)
            if cached:
                logger.info("Returning cached response")
                return cached
        
        # Phase 0: Mock response
        if self._config.get("use_mock_responses", True):
            response = self._generate_mock_response(prompt, max_tokens)
            if self._config.get("cache_enabled", True):
                self._cache.put(prompt, response)
            return response
        
        # Phase 1: Real LLM call (implement in Phase 1)
        try:
            response = self._call_ollama(prompt, max_tokens)
            if self._config.get("cache_enabled", True):
                self._cache.put(prompt, response)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            if self._config.get("use_mock_responses"):
                logger.warning("Falling back to mock response")
                return self._generate_mock_response(prompt, max_tokens)
            raise RuntimeError(f"LLM unavailable and mock disabled: {e}")
    
    def _generate_mock_response(self, prompt: str, max_tokens: int) -> str:
        """
        Generate mock response (Phase 0).
        
        Args:
            prompt (str): Input prompt
            max_tokens (int): Max tokens
            
        Returns:
            str: Mock response
        """
        mock_responses = [
            "Analysis complete. Found strong correlation (r=0.87) with 95% confidence.",
            "Forecast model converged. Expected trend: +2.3% over next period.",
            "Anomaly detection: 3 outliers identified in dataset. Recommend investigation.",
            "Data processing successful. Generated 15 feature interactions.",
            "Statistical analysis complete. p-value < 0.05 indicates significance.",
        ]
        
        response = mock_responses[hash(prompt) % len(mock_responses)]
        logger.info(f"Mock response: {response[:50]}...")
        return response
    
    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """
        Call actual Ollama LLM (Phase 1 only).
        
        Args:
            prompt (str): Input prompt
            max_tokens (int): Max tokens
            
        Returns:
            str: LLM response
            
        Raises:
            RuntimeError: If Ollama unavailable
            
        NOTE: This is a placeholder. Phase 1 will implement full integration.
        """
        raise NotImplementedError(
            "Ollama integration in Phase 1. For now, use mock responses."
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check LLM system health.
        
        Returns:
            Dict[str, Any]: Health status
        """
        return {
            "enabled": LLM_ENABLED,
            "available": self.is_available(),
            "model": self._config.get("model"),
            "cache_size": len(self._cache._cache),
            "cache_enabled": self._config.get("cache_enabled", True),
            "mock_enabled": self._config.get("use_mock_responses", True),
        }
    
    def clear_cache(self) -> None:
        """Clear response cache."""
        self._cache.clear()
