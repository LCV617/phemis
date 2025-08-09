"""
Provider OpenRouter pour l'outil CLI LLM.

Ce module implémente toutes les interactions avec l'API OpenRouter,
incluant la liste des modèles et les complétions de chat avec support streaming.
"""

import os
import json
import time
from typing import List, Optional, Dict, Any, Iterator, Generator
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .schema import ModelInfo, Message, Usage


class OpenRouterError(Exception):
    """Exception de base pour les erreurs OpenRouter."""
    pass


class OpenRouterAuthError(OpenRouterError):
    """Exception pour les erreurs d'authentification OpenRouter."""
    pass


class OpenRouterRateLimitError(OpenRouterError):
    """Exception pour les erreurs de limitation de taux OpenRouter."""
    pass


class OpenRouterServerError(OpenRouterError):
    """Exception pour les erreurs serveur OpenRouter."""
    pass


class OpenRouterProvider:
    """
    Client pour l'API OpenRouter.
    
    Gère l'authentification, les appels API et les erreurs pour OpenRouter.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1/"
    DEFAULT_TIMEOUT = 60
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        extra_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialise le provider OpenRouter.
        
        Args:
            api_key: Clé API OpenRouter. Si None, utilise OPENROUTER_API_KEY depuis l'environnement
            timeout: Timeout pour les requêtes HTTP en secondes
            extra_headers: Headers supplémentaires à inclure dans les requêtes
            
        Raises:
            OpenRouterAuthError: Si aucune clé API n'est fournie ou trouvée
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise OpenRouterAuthError(
                "Clé API OpenRouter requise. Définissez OPENROUTER_API_KEY ou passez api_key au constructeur."
            )
            
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        
        # Configuration de la session HTTP avec retry automatique
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Construit les headers pour les requêtes API.
        
        Args:
            extra_headers: Headers supplémentaires spécifiques à cette requête
            
        Returns:
            Dictionnaire des headers HTTP
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream; charset=utf-8",
        }
        
        # Ajouter les headers configurés au niveau de la classe
        headers.update(self.extra_headers)
        
        # Ajouter les headers spécifiques à cette requête
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
        
    def _handle_response_error(self, response: requests.Response) -> None:
        """
        Gère les erreurs de réponse HTTP.
        
        Args:
            response: Réponse HTTP à vérifier
            
        Raises:
            OpenRouterAuthError: Pour les erreurs 401
            OpenRouterRateLimitError: Pour les erreurs 429
            OpenRouterServerError: Pour les erreurs 5xx
            OpenRouterError: Pour les autres erreurs
        """
        if response.status_code == 401:
            raise OpenRouterAuthError(
                f"Erreur d'authentification (401): Vérifiez votre clé API OpenRouter"
            )
        elif response.status_code == 429:
            raise OpenRouterRateLimitError(
                f"Limite de taux atteinte (429): Trop de requêtes"
            )
        elif response.status_code >= 500:
            raise OpenRouterServerError(
                f"Erreur serveur OpenRouter ({response.status_code}): {response.text}"
            )
        elif not response.ok:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
            except (json.JSONDecodeError, KeyError):
                error_msg = response.text
            raise OpenRouterError(
                f"Erreur API OpenRouter ({response.status_code}): {error_msg}"
            )
            
    def list_models(self) -> List[ModelInfo]:
        """
        Récupère la liste des modèles disponibles sur OpenRouter.
        
        Returns:
            Liste des informations des modèles
            
        Raises:
            OpenRouterError: En cas d'erreur API
        """
        url = urljoin(self.BASE_URL, "models")
        headers = self._get_headers()
        
        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            self._handle_response_error(response)
            
            data = response.json()
            models = []
            
            for model_data in data.get("data", []):
                # Extraire les informations du modèle
                model_id = model_data.get("id", "")
                context_length = model_data.get("context_length")
                description = model_data.get("description")
                
                # Extraire les prix s'ils existent
                pricing = model_data.get("pricing", {})
                pricing_prompt = None
                pricing_completion = None
                
                if pricing:
                    # Les prix sont généralement en string, les convertir en float
                    prompt_price = pricing.get("prompt")
                    completion_price = pricing.get("completion")
                    
                    if prompt_price is not None:
                        try:
                            pricing_prompt = float(prompt_price)
                        except (ValueError, TypeError):
                            pass
                            
                    if completion_price is not None:
                        try:
                            pricing_completion = float(completion_price)
                        except (ValueError, TypeError):
                            pass
                
                model_info = ModelInfo(
                    id=model_id,
                    context_length=context_length,
                    pricing_prompt=pricing_prompt,
                    pricing_completion=pricing_completion,
                    description=description
                )
                models.append(model_info)
                
            return models
            
        except requests.exceptions.Timeout:
            raise OpenRouterError(f"Timeout lors de la récupération des modèles (>{self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise OpenRouterError(f"Erreur réseau lors de la récupération des modèles: {e}")
            
    def chat_completion(
        self,
        messages: List[Message],
        model: str,
        stream: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        Effectue une complétion de chat via l'API OpenRouter.
        
        Args:
            messages: Liste des messages de la conversation
            model: ID du modèle à utiliser
            stream: Si True, retourne un generator pour le streaming
            extra_headers: Headers supplémentaires pour cette requête
            **kwargs: Paramètres supplémentaires pour l'API OpenRouter
            
        Returns:
            Dict avec la réponse complète si stream=False, 
            Generator[Dict] si stream=True
            
        Raises:
            OpenRouterError: En cas d'erreur API
        """
        url = urljoin(self.BASE_URL, "chat/completions")
        headers = self._get_headers(extra_headers)
        
        # Préparer les messages au format API OpenRouter
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
            
        payload = {
            "model": model,
            "messages": api_messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            if stream:
                return self._chat_completion_stream(url, headers, payload)
            else:
                return self._chat_completion_sync(url, headers, payload)
                
        except requests.exceptions.Timeout:
            raise OpenRouterError(f"Timeout lors de la complétion de chat (>{self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise OpenRouterError(f"Erreur réseau lors de la complétion de chat: {e}")
            
    def _chat_completion_sync(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une complétion de chat synchrone (non-streaming).
        
        Args:
            url: URL de l'endpoint
            headers: Headers HTTP
            payload: Données de la requête
            
        Returns:
            Réponse API complète
        """
        response = self.session.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=self.timeout
        )
        self._handle_response_error(response)
        return response.json()
        
    def _chat_completion_stream(
        self, 
        url: str, 
        headers: Dict[str, str], 
        payload: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Effectue une complétion de chat en streaming.
        
        Args:
            url: URL de l'endpoint
            headers: Headers HTTP
            payload: Données de la requête
            
        Yields:
            Chunks de données de la réponse streaming
        """
        response = self.session.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
            stream=True
        )
        self._handle_response_error(response)
        
        try:
            # Utiliser decode_unicode=False pour gérer l'encoding manuellement
            for line_bytes in response.iter_lines(decode_unicode=False):
                if not line_bytes:
                    continue
                
                # Décoder manuellement en UTF-8
                try:
                    line = line_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # Fallback si le décodage UTF-8 échoue
                    line = line_bytes.decode('iso-8859-1', errors='replace')
                if not line:
                    continue
                    
                # Ignorer les commentaires SSE
                if line.startswith(":"):
                    continue
                    
                # Ignorer les commentaires spécifiques OpenRouter
                if "OPENROUTER PROCESSING" in line:
                    continue
                    
                # Parser les lignes SSE format "data: {json}"
                if line.startswith("data: "):
                    data_str = line[6:]  # Enlever "data: "
                    
                    # Vérifier la fin du stream
                    if data_str.strip() == "[DONE]":
                        break
                        
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        # Ignorer les lignes malformées
                        continue
                        
        except Exception as e:
            raise OpenRouterError(f"Erreur lors du parsing du stream: {e}")
        finally:
            response.close()
            
    def estimate_cost(
        self, 
        usage: Usage, 
        pricing_prompt: Optional[float], 
        pricing_completion: Optional[float]
    ) -> Optional[float]:
        """
        Estime le coût d'un appel API basé sur l'usage et les prix.
        
        Args:
            usage: Métriques d'usage des tokens
            pricing_prompt: Prix par token de prompt (en USD)
            pricing_completion: Prix par token de completion (en USD)
            
        Returns:
            Coût estimé en USD, None si les prix ne sont pas disponibles
        """
        if pricing_prompt is None or pricing_completion is None:
            return None
            
        prompt_cost = usage.prompt_tokens * pricing_prompt
        completion_cost = usage.completion_tokens * pricing_completion
        
        return prompt_cost + completion_cost