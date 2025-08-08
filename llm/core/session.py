"""
Gestion des sessions de chat pour l'outil CLI LLM.

Ce module fournit la classe ChatSession qui gère l'état d'une conversation,
incluant l'historique des messages, le suivi des coûts et la gestion du budget.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .schema import Session, Turn, Message, MessageRole, Usage, ModelInfo
from .cost import calculate_token_cost, get_budget_warning


class ChatSession:
    """
    Classe principale pour gérer une session de chat interactive.
    
    Cette classe maintient l'état d'une conversation incluant:
    - L'historique des messages organisé par tours
    - Les métriques d'usage cumulées
    - Le suivi du budget et des coûts
    - La configuration du modèle et du système
    """
    
    def __init__(self, model: str, system: Optional[str] = None, budget_max: Optional[float] = None):
        """
        Initialise une nouvelle session de chat.
        
        Args:
            model: Identifiant du modèle LLM à utiliser
            system: Message système optionnel pour configurer le comportement
            budget_max: Budget maximum en USD pour cette session
        """
        self.model = model.strip()
        self.system = system.strip() if system and system.strip() else None
        self.budget_max = budget_max
        
        # État de la session
        self.turns: List[Turn] = []
        self.usage_totals = Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        self.estimate_usd_total = 0.0
        
        # Turn en cours de construction
        self._current_turn_messages: List[Message] = []
        
        # Validation
        if not self.model:
            raise ValueError("Le modèle ne peut pas être vide")
        if budget_max is not None and budget_max < 0:
            raise ValueError("Le budget doit être positif ou nul")
    
    def append_user(self, content: str) -> None:
        """
        Ajoute un message utilisateur et commence un nouveau tour.
        
        Args:
            content: Contenu du message utilisateur
            
        Raises:
            ValueError: Si le contenu est vide ou si un tour est déjà en cours
        """
        if not content or not content.strip():
            raise ValueError("Le contenu du message utilisateur ne peut pas être vide")
        
        if self._current_turn_messages:
            raise ValueError("Un tour est déjà en cours, terminez-le avec append_assistant()")
        
        # Créer le message utilisateur
        user_message = Message(role=MessageRole.USER, content=content.strip())
        self._current_turn_messages = [user_message]
    
    def append_assistant(
        self, 
        content: str, 
        usage: Optional[Usage] = None, 
        latency_ms: Optional[float] = None
    ) -> None:
        """
        Termine le tour en cours en ajoutant la réponse de l'assistant.
        
        Args:
            content: Contenu de la réponse de l'assistant
            usage: Métriques d'usage optionnelles pour ce tour
            latency_ms: Latence optionnelle de la réponse en millisecondes
            
        Raises:
            ValueError: Si aucun tour n'est en cours ou si le contenu est vide
        """
        if not content or not content.strip():
            # Accepter un contenu vide avec une valeur par défaut plutôt que de lever une erreur
            content = "[Empty response]"
        
        if not self._current_turn_messages:
            raise ValueError("Aucun tour en cours, commencez par append_user()")
        
        # Créer le message assistant
        assistant_message = Message(role=MessageRole.ASSISTANT, content=content.strip())
        self._current_turn_messages.append(assistant_message)
        
        # Calculer l'estimation de coût pour ce tour si usage fourni
        cost_estimate = None
        if usage:
            # Note: On aura besoin des prix du modèle pour calculer le coût exact
            # Pour l'instant on stocke juste l'usage, le coût sera calculé ailleurs
            pass
        
        # Créer le turn complet
        turn = Turn(
            messages=self._current_turn_messages.copy(),
            usage=usage,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate
        )
        
        # Ajouter le turn à l'historique
        self.turns.append(turn)
        
        # Mettre à jour les totaux d'usage
        if usage:
            self.usage_totals.prompt_tokens += usage.prompt_tokens
            self.usage_totals.completion_tokens += usage.completion_tokens
            self.usage_totals.total_tokens += usage.total_tokens
        
        # Réinitialiser le tour en cours
        self._current_turn_messages = []
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """
        Retourne les messages formatés pour l'API du provider.
        
        Returns:
            Liste de dictionnaires représentant les messages pour l'API
        """
        messages = []
        
        # Ajouter le message système s'il existe
        if self.system:
            messages.append({
                "role": "system",
                "content": self.system
            })
        
        # Ajouter tous les messages des tours terminés
        for turn in self.turns:
            for message in turn.messages:
                messages.append({
                    "role": message.role.value,
                    "content": message.content
                })
        
        # Ajouter les messages du tour en cours s'il y en a
        for message in self._current_turn_messages:
            messages.append({
                "role": message.role.value,
                "content": message.content
            })
        
        return messages
    
    def estimate_cost(self, usage: Usage, model_info: ModelInfo) -> float:
        """
        Calcule l'estimation de coût pour un usage donné avec les prix du modèle.
        
        Args:
            usage: Métriques d'usage des tokens
            model_info: Informations du modèle incluant les prix
            
        Returns:
            Coût estimé en USD
        """
        if not model_info.pricing_prompt or not model_info.pricing_completion:
            return 0.0
        
        return calculate_token_cost(
            usage=usage,
            pricing_prompt=model_info.pricing_prompt,
            pricing_completion=model_info.pricing_completion
        )
    
    def update_cost_estimate(self, additional_cost: float) -> None:
        """
        Met à jour l'estimation de coût total de la session.
        
        Args:
            additional_cost: Coût additionnel à ajouter au total
        """
        self.estimate_usd_total += additional_cost
    
    def check_budget(self) -> Optional[str]:
        """
        Vérifie le statut du budget et retourne un avertissement si nécessaire.
        
        Returns:
            Message d'avertissement si le budget est proche/dépassé, None sinon
        """
        if self.budget_max is None:
            return None
        
        return get_budget_warning(self.estimate_usd_total, self.budget_max)
    
    def is_over_budget(self) -> bool:
        """
        Vérifie si le budget est dépassé.
        
        Returns:
            True si le budget est dépassé
        """
        if self.budget_max is None:
            return False
        
        return self.estimate_usd_total >= self.budget_max
    
    def get_budget_percentage(self) -> Optional[float]:
        """
        Calcule le pourcentage du budget utilisé.
        
        Returns:
            Pourcentage utilisé (0.0 à 1.0+) ou None si pas de budget
        """
        if self.budget_max is None or self.budget_max == 0:
            return None
        
        return self.estimate_usd_total / self.budget_max
    
    def reset(self) -> None:
        """
        Vide l'historique et remet les compteurs à zéro.
        
        Garde la configuration (model, system, budget_max) mais efface:
        - L'historique des tours
        - Les métriques d'usage
        - L'estimation de coût total
        """
        self.turns.clear()
        self.usage_totals = Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        self.estimate_usd_total = 0.0
        self._current_turn_messages.clear()
    
    def to_session(self) -> Session:
        """
        Convertit la ChatSession vers un objet Session Pydantic pour la sauvegarde.
        
        Returns:
            Objet Session sérialisable
            
        Raises:
            ValueError: Si un tour est en cours et incomplet
        """
        if self._current_turn_messages:
            raise ValueError(
                "Impossible de sérialiser: un tour est en cours. "
                "Terminez-le avec append_assistant() ou annulez-le avec reset()"
            )
        
        # Préparer les métadonnées
        meta = {}
        if self.budget_max is not None:
            meta["budget_max"] = self.budget_max
        if self.estimate_usd_total > 0:
            meta["estimate_usd_total"] = self.estimate_usd_total
        
        return Session(
            model=self.model,
            system=self.system,
            turns=self.turns.copy(),
            usage_totals=self.usage_totals,
            meta=meta
        )
    
    @classmethod
    def from_session(cls, session: Session) -> 'ChatSession':
        """
        Crée une ChatSession à partir d'un objet Session.
        
        Args:
            session: Objet Session à convertir
            
        Returns:
            Instance ChatSession restaurée
        """
        # Extraire les métadonnées
        budget_max = session.meta.get("budget_max")
        estimate_usd_total = session.meta.get("estimate_usd_total", 0.0)
        
        # Créer l'instance
        chat_session = cls(
            model=session.model,
            system=session.system,
            budget_max=budget_max
        )
        
        # Restaurer l'état
        chat_session.turns = session.turns.copy() if session.turns else []
        chat_session.usage_totals = session.usage_totals or Usage(
            prompt_tokens=0, completion_tokens=0, total_tokens=0
        )
        chat_session.estimate_usd_total = estimate_usd_total
        
        return chat_session
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé de la conversation pour affichage.
        
        Returns:
            Dictionnaire avec les statistiques de la session
        """
        return {
            "model": self.model,
            "system_defined": self.system is not None,
            "turns_count": len(self.turns),
            "total_messages": sum(len(turn.messages) for turn in self.turns),
            "usage_totals": {
                "prompt_tokens": self.usage_totals.prompt_tokens,
                "completion_tokens": self.usage_totals.completion_tokens,
                "total_tokens": self.usage_totals.total_tokens
            },
            "cost_estimate": self.estimate_usd_total,
            "budget_max": self.budget_max,
            "budget_percentage": self.get_budget_percentage(),
            "turn_in_progress": len(self._current_turn_messages) > 0
        }