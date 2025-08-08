"""
Calculs de coûts et gestion du budget pour l'outil CLI LLM.

Ce module fournit des fonctions pour calculer les coûts des appels API,
estimer les coûts de session et gérer les alertes de budget.
"""

from typing import List, Optional, Tuple
from .schema import Usage, Session, ModelInfo
from .utils import format_cost


# Prix par défaut OpenRouter (par million de tokens) si non disponibles via API
DEFAULT_PRICING = {
    # OpenAI
    "openai/gpt-4": {"prompt": 30.0, "completion": 60.0},
    "openai/gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
    "openai/gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
    
    # Anthropic
    "anthropic/claude-3.5-sonnet": {"prompt": 3.0, "completion": 15.0},
    "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    "anthropic/claude-3-opus": {"prompt": 15.0, "completion": 75.0},
    
    # Modèles gratuits
    "free": {"prompt": 0.0, "completion": 0.0},
}


def calculate_token_cost(
    usage: Usage, 
    pricing_prompt: float, 
    pricing_completion: float
) -> float:
    """
    Calcule le coût d'un usage basé sur les tokens et les prix par million.
    
    Args:
        usage: Objet Usage avec les métriques de tokens
        pricing_prompt: Prix par million de tokens de prompt (USD)
        pricing_completion: Prix par million de tokens de completion (USD)
        
    Returns:
        Coût total en USD
        
    Raises:
        ValueError: Si les prix sont négatifs
    """
    if pricing_prompt < 0 or pricing_completion < 0:
        raise ValueError("Les prix ne peuvent pas être négatifs")
    
    # Calcul: (tokens / 1_000_000) * prix_par_million
    prompt_cost = (usage.prompt_tokens / 1_000_000) * pricing_prompt
    completion_cost = (usage.completion_tokens / 1_000_000) * pricing_completion
    
    return prompt_cost + completion_cost


def estimate_session_cost(session: Session, models_info: List[ModelInfo]) -> float:
    """
    Calcule le coût total estimé d'une session complète.
    
    Args:
        session: Session à analyser
        models_info: Liste des informations de modèles disponibles
        
    Returns:
        Coût total estimé en USD
    """
    # Trouver les informations du modèle utilisé
    model_info = None
    for info in models_info:
        if info.id == session.model:
            model_info = info
            break
    
    # Si pas d'info trouvée, essayer les prix par défaut
    if not model_info or not model_info.pricing_prompt or not model_info.pricing_completion:
        default_pricing = _get_default_pricing(session.model)
        if default_pricing:
            pricing_prompt = default_pricing["prompt"]
            pricing_completion = default_pricing["completion"]
        else:
            # Pas de prix disponible
            return 0.0
    else:
        pricing_prompt = model_info.pricing_prompt
        pricing_completion = model_info.pricing_completion
    
    total_cost = 0.0
    
    # Calculer le coût de chaque tour
    for turn in session.turns:
        if turn.usage:
            turn_cost = calculate_token_cost(
                usage=turn.usage,
                pricing_prompt=pricing_prompt,
                pricing_completion=pricing_completion
            )
            total_cost += turn_cost
    
    return total_cost


def _get_default_pricing(model_id: str) -> Optional[dict]:
    """
    Récupère les prix par défaut pour un modèle donné.
    
    Args:
        model_id: Identifiant du modèle
        
    Returns:
        Dict avec les prix prompt/completion ou None si non trouvé
    """
    # Recherche exacte
    if model_id in DEFAULT_PRICING:
        return DEFAULT_PRICING[model_id]
    
    # Recherche par préfixe pour les modèles similaires
    for pattern, pricing in DEFAULT_PRICING.items():
        if pattern != "free" and model_id.startswith(pattern.split("/")[0]):
            return pricing
    
    # Modèles gratuits (pattern "free" dans le nom)
    if "free" in model_id.lower() or "gratis" in model_id.lower():
        return DEFAULT_PRICING["free"]
    
    return None


def format_budget_status(current_cost: float, budget_max: Optional[float]) -> str:
    """
    Formate le statut du budget avec des couleurs appropriées.
    
    Args:
        current_cost: Coût actuel en USD
        budget_max: Budget maximum en USD ou None si pas de limite
        
    Returns:
        Chaîne formatée avec couleurs (utilise des codes ANSI)
    """
    cost_str = format_cost(current_cost)
    
    if budget_max is None:
        return f"Budget: {cost_str} (no limit)"
    
    budget_str = format_cost(budget_max)
    percentage = (current_cost / budget_max) * 100 if budget_max > 0 else 0
    
    # Déterminer la couleur basée sur le pourcentage
    if percentage < 70:
        color_code = "\033[32m"  # Vert
    elif percentage < 90:
        color_code = "\033[33m"  # Orange/Jaune
    else:
        color_code = "\033[31m"  # Rouge
    
    reset_code = "\033[0m"  # Reset couleur
    
    return f"Budget: {color_code}{cost_str} / {budget_str} ({percentage:.0f}%){reset_code}"


def get_budget_warning(current_cost: float, budget_max: Optional[float]) -> Optional[str]:
    """
    Génère un message d'avertissement si le budget est proche ou dépassé.
    
    Args:
        current_cost: Coût actuel en USD
        budget_max: Budget maximum en USD ou None si pas de limite
        
    Returns:
        Message d'avertissement ou None si tout va bien
    """
    if budget_max is None or budget_max <= 0:
        return None
    
    percentage = (current_cost / budget_max) * 100
    
    if percentage >= 100:
        return f"⚠️  BUDGET DÉPASSÉ! Coût actuel: {format_cost(current_cost)} / Budget: {format_cost(budget_max)}"
    elif percentage >= 80:
        return f"⚠️  Budget bientôt épuisé: {format_cost(current_cost)} / {format_cost(budget_max)} ({percentage:.0f}%)"
    
    return None


def calculate_estimated_cost_per_token(model_info: ModelInfo) -> Tuple[float, float]:
    """
    Calcule le coût estimé par token pour un modèle.
    
    Args:
        model_info: Informations du modèle
        
    Returns:
        Tuple (coût_par_token_prompt, coût_par_token_completion) en USD
    """
    if not model_info.pricing_prompt or not model_info.pricing_completion:
        # Essayer les prix par défaut
        default_pricing = _get_default_pricing(model_info.id)
        if default_pricing:
            prompt_price = default_pricing["prompt"]
            completion_price = default_pricing["completion"]
        else:
            return (0.0, 0.0)
    else:
        prompt_price = model_info.pricing_prompt
        completion_price = model_info.pricing_completion
    
    # Convertir du prix par million au prix par token
    cost_per_prompt_token = prompt_price / 1_000_000
    cost_per_completion_token = completion_price / 1_000_000
    
    return (cost_per_prompt_token, cost_per_completion_token)


def estimate_cost_for_tokens(
    prompt_tokens: int, 
    completion_tokens: int, 
    model_info: ModelInfo
) -> float:
    """
    Estime le coût pour un nombre spécifique de tokens.
    
    Args:
        prompt_tokens: Nombre de tokens de prompt
        completion_tokens: Nombre de tokens de completion
        model_info: Informations du modèle
        
    Returns:
        Coût estimé en USD
    """
    usage = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )
    
    cost_per_prompt, cost_per_completion = calculate_estimated_cost_per_token(model_info)
    
    return calculate_token_cost(
        usage=usage,
        pricing_prompt=cost_per_prompt * 1_000_000,  # Reconvertir au prix par million
        pricing_completion=cost_per_completion * 1_000_000
    )


def get_cost_breakdown(session: Session, models_info: List[ModelInfo]) -> dict:
    """
    Fournit une analyse détaillée des coûts d'une session.
    
    Args:
        session: Session à analyser
        models_info: Liste des informations de modèles
        
    Returns:
        Dictionnaire avec l'analyse détaillée des coûts
    """
    model_info = None
    for info in models_info:
        if info.id == session.model:
            model_info = info
            break
    
    if not model_info:
        # Créer un ModelInfo minimal avec prix par défaut
        default_pricing = _get_default_pricing(session.model)
        if default_pricing:
            model_info = ModelInfo(
                id=session.model,
                pricing_prompt=default_pricing["prompt"],
                pricing_completion=default_pricing["completion"]
            )
        else:
            # Pas de prix disponible
            return {
                "model": session.model,
                "total_cost": 0.0,
                "turns_count": len(session.turns),
                "total_tokens": session.usage_totals.total_tokens if session.usage_totals else 0,
                "pricing_available": False,
                "turns_breakdown": []
            }
    
    cost_per_prompt, cost_per_completion = calculate_estimated_cost_per_token(model_info)
    
    turns_breakdown = []
    total_cost = 0.0
    
    for i, turn in enumerate(session.turns):
        if turn.usage:
            turn_cost = calculate_token_cost(
                usage=turn.usage,
                pricing_prompt=model_info.pricing_prompt or 0.0,
                pricing_completion=model_info.pricing_completion or 0.0
            )
            total_cost += turn_cost
            
            turns_breakdown.append({
                "turn_number": i + 1,
                "prompt_tokens": turn.usage.prompt_tokens,
                "completion_tokens": turn.usage.completion_tokens,
                "total_tokens": turn.usage.total_tokens,
                "cost": turn_cost,
                "cost_formatted": format_cost(turn_cost)
            })
        else:
            turns_breakdown.append({
                "turn_number": i + 1,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "cost_formatted": format_cost(0.0)
            })
    
    return {
        "model": session.model,
        "total_cost": total_cost,
        "total_cost_formatted": format_cost(total_cost),
        "turns_count": len(session.turns),
        "total_tokens": session.usage_totals.total_tokens if session.usage_totals else 0,
        "pricing_available": True,
        "cost_per_prompt_token": cost_per_prompt,
        "cost_per_completion_token": cost_per_completion,
        "turns_breakdown": turns_breakdown,
        "pricing_info": {
            "prompt_price_per_1m": model_info.pricing_prompt or 0.0,
            "completion_price_per_1m": model_info.pricing_completion or 0.0
        }
    }


def compare_model_costs(models_info: List[ModelInfo], token_count: int = 1000) -> List[dict]:
    """
    Compare les coûts entre différents modèles pour un nombre donné de tokens.
    
    Args:
        models_info: Liste des modèles à comparer
        token_count: Nombre de tokens pour la comparaison (défaut: 1000)
        
    Returns:
        Liste de dictionnaires avec les comparaisons de coûts, triée par coût croissant
    """
    comparisons = []
    
    for model in models_info:
        # Estimer le coût (assume 50% prompt, 50% completion)
        prompt_tokens = token_count // 2
        completion_tokens = token_count - prompt_tokens
        
        estimated_cost = estimate_cost_for_tokens(prompt_tokens, completion_tokens, model)
        
        comparisons.append({
            "model_id": model.id,
            "estimated_cost": estimated_cost,
            "cost_formatted": format_cost(estimated_cost),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "pricing_available": bool(model.pricing_prompt and model.pricing_completion),
            "context_length": model.context_length
        })
    
    # Trier par coût croissant
    comparisons.sort(key=lambda x: x["estimated_cost"])
    
    return comparisons