"""
Module d'utilitaires divers pour l'outil CLI LLM.

Ce module fournit des fonctionnalités utilitaires comme la session HTTP avec retry,
le rendu Markdown, le formatage de durées et coûts, et le parsing SSE.
"""

import json
import re
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from rich.console import Console
from rich.markdown import Markdown


class HTTPError(Exception):
    """Exception pour les erreurs HTTP avec retry."""
    pass


def setup_retry_session() -> requests.Session:
    """
    Configure une session requests avec backoff exponentiel.
    
    Returns:
        Session configurée avec retry automatique
    """
    session = requests.Session()
    
    # Configuration du retry avec tenacity
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ))
    )
    def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
        """Effectue une requête avec retry automatique."""
        # Configuration par défaut
        kwargs.setdefault('timeout', 60)
        
        response = session.request(method, url, **kwargs)
        
        # Vérifier les codes de statut qui nécessitent un retry
        if response.status_code == 429:  # Too Many Requests
            raise requests.exceptions.RequestException(f"Rate limited: {response.status_code}")
        elif 500 <= response.status_code < 600:  # Server errors
            raise requests.exceptions.RequestException(f"Server error: {response.status_code}")
            
        return response
    
    # Remplacer les méthodes de la session
    session.get = lambda url, **kwargs: request_with_retry('GET', url, **kwargs)
    session.post = lambda url, **kwargs: request_with_retry('POST', url, **kwargs)
    session.put = lambda url, **kwargs: request_with_retry('PUT', url, **kwargs)
    session.delete = lambda url, **kwargs: request_with_retry('DELETE', url, **kwargs)
    session.head = lambda url, **kwargs: request_with_retry('HEAD', url, **kwargs)
    session.options = lambda url, **kwargs: request_with_retry('OPTIONS', url, **kwargs)
    session.patch = lambda url, **kwargs: request_with_retry('PATCH', url, **kwargs)
    
    return session


def render_markdown(text: str) -> str:
    """
    Rend le texte Markdown avec coloration syntaxique pour la console.
    
    Args:
        text: Texte Markdown à rendre
        
    Returns:
        Texte formaté pour affichage console
    """
    console = Console(width=80, legacy_windows=False)
    markdown = Markdown(text)
    
    # Capturer la sortie de Rich
    with console.capture() as capture:
        console.print(markdown)
    
    return capture.get()


def format_duration(duration_ms: float) -> str:
    """
    Formate une durée en millisecondes de manière lisible.
    
    Args:
        duration_ms: Durée en millisecondes
        
    Returns:
        Chaîne formatée (ex: "1.23s", "456ms")
    """
    if duration_ms < 1000:
        return f"{duration_ms:.0f}ms"
    else:
        return f"{duration_ms / 1000:.2f}s"


def format_cost(cost_usd: float) -> str:
    """
    Formate un coût en USD de manière lisible.
    
    Args:
        cost_usd: Coût en dollars américains
        
    Returns:
        Chaîne formatée (ex: "$0.0123", "$1.23")
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    elif cost_usd < 1.0:
        return f"${cost_usd:.3f}"
    else:
        return f"${cost_usd:.2f}"


def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse une ligne de Server-Sent Events (SSE).
    
    Args:
        line: Ligne SSE brute
        
    Returns:
        Dictionnaire JSON parsé ou None si la ligne n'est pas parsable
    """
    # Supprimer les espaces en début/fin
    line = line.strip()
    
    # Ignorer les lignes vides et les commentaires
    if not line or line.startswith(':'):
        return None
    
    # Chercher les lignes "data: ..."
    if line.startswith('data: '):
        data_part = line[6:]  # Enlever "data: "
        
        # Ignorer les marqueurs spéciaux
        if data_part == '[DONE]':
            return None
            
        # Essayer de parser le JSON
        try:
            return json.loads(data_part)
        except json.JSONDecodeError:
            return None
    
    # Autres types de lignes SSE (event:, id:, retry:)
    if ':' in line:
        field, value = line.split(':', 1)
        field = field.strip()
        value = value.strip()
        
        if field in ('event', 'id', 'retry'):
            return {field: value}
    
    return None


def calculate_token_cost(usage: Dict[str, int], model_pricing: Dict[str, float]) -> float:
    """
    Calcule le coût d'un appel API basé sur l'usage des tokens et les prix du modèle.
    
    Args:
        usage: Dictionnaire avec prompt_tokens et completion_tokens
        model_pricing: Dictionnaire avec pricing_prompt et pricing_completion (prix par token)
        
    Returns:
        Coût total en USD
    """
    prompt_cost = usage.get('prompt_tokens', 0) * model_pricing.get('pricing_prompt', 0)
    completion_cost = usage.get('completion_tokens', 0) * model_pricing.get('pricing_completion', 0)
    
    return prompt_cost + completion_cost


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale autorisée
        suffix: Suffixe à ajouter si le texte est tronqué
        
    Returns:
        Texte tronqué si nécessaire
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def validate_model_id(model_id: str) -> bool:
    """
    Valide qu'un identifiant de modèle est dans un format acceptable.
    
    Args:
        model_id: Identifiant du modèle à valider
        
    Returns:
        True si l'identifiant est valide
    """
    # Pattern basique: lettres, chiffres, tirets, points, underscores
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$'
    return bool(re.match(pattern, model_id)) and len(model_id) <= 100


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères dangereux.
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier sécurisé
    """
    # Supprimer les caractères dangereux
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Supprimer les espaces multiples et trim
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # S'assurer qu'on a un nom valide
    if not sanitized or sanitized in ('.', '..'):
        sanitized = 'unnamed'
    
    return sanitized


def get_current_timestamp() -> str:
    """
    Retourne un timestamp actuel au format ISO 8601.
    
    Returns:
        Timestamp formaté
    """
    return datetime.utcnow().isoformat() + 'Z'


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    Parse un timestamp ISO 8601 en objet datetime.
    
    Args:
        timestamp_str: Timestamp au format ISO 8601
        
    Returns:
        Objet datetime
        
    Raises:
        ValueError: Si le format timestamp est invalide
    """
    # Gérer les différents formats ISO 8601
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Format de timestamp invalide: {timestamp_str}") from e