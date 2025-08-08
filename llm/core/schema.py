"""
Modèles Pydantic pour l'outil CLI LLM.

Ce module contient tous les schémas de données utilisés par l'application,
incluant les modèles pour les messages, sessions, configurations et métriques d'usage.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class MessageRole(str, Enum):
    """Rôles possibles pour un message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Modèle représentant un message dans une conversation."""
    role: MessageRole = Field(..., description="Rôle de l'auteur du message")
    content: str = Field(..., description="Contenu textuel du message")

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        """Valide que le contenu n'est pas vide."""
        if not v or not v.strip():
            raise ValueError("Le contenu du message ne peut pas être vide")
        return v


class Usage(BaseModel):
    """Modèle représentant l'usage des tokens pour un appel API."""
    prompt_tokens: int = Field(..., ge=0, description="Nombre de tokens dans le prompt")
    completion_tokens: int = Field(..., ge=0, description="Nombre de tokens dans la réponse")
    total_tokens: int = Field(..., ge=0, description="Nombre total de tokens utilisés")

    @model_validator(mode='after')
    def validate_total_tokens(self):
        """Valide que total_tokens = prompt_tokens + completion_tokens."""
        expected_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != expected_total:
            raise ValueError(f"total_tokens ({self.total_tokens}) doit égaler prompt_tokens + completion_tokens ({expected_total})")
        return self


class ModelInfo(BaseModel):
    """Modèle représentant les informations d'un modèle LLM."""
    id: str = Field(..., description="Identifiant unique du modèle")
    context_length: Optional[int] = Field(None, ge=1, description="Longueur maximale du contexte en tokens")
    pricing_prompt: Optional[float] = Field(None, ge=0, description="Prix par token de prompt (en USD)")
    pricing_completion: Optional[float] = Field(None, ge=0, description="Prix par token de completion (en USD)")
    description: Optional[str] = Field(None, description="Description du modèle")

    @field_validator('id')
    @classmethod
    def id_not_empty(cls, v):
        """Valide que l'ID du modèle n'est pas vide."""
        if not v or not v.strip():
            raise ValueError("L'ID du modèle ne peut pas être vide")
        return v.strip()


class Turn(BaseModel):
    """Modèle représentant un tour de conversation (user + assistant)."""
    messages: List[Message] = Field(..., min_items=1, description="Messages du tour de conversation")
    usage: Optional[Usage] = Field(None, description="Métriques d'usage pour ce tour")
    latency_ms: Optional[float] = Field(None, ge=0, description="Latence de la réponse en millisecondes")
    cost_estimate: Optional[float] = Field(None, ge=0, description="Estimation du coût pour ce tour en USD")

    @field_validator('messages')
    @classmethod
    def validate_messages_structure(cls, v):
        """Valide la structure des messages dans un tour."""
        if not v:
            raise ValueError("Un tour doit contenir au moins un message")
        
        # Un tour typique devrait avoir un message user suivi d'un message assistant
        # mais on permet plus de flexibilité pour des cas spéciaux
        roles = [msg.role for msg in v]
        
        # Vérifier qu'on n'a pas de messages système dans un tour
        if MessageRole.SYSTEM in roles:
            raise ValueError("Les messages système ne doivent pas être dans un tour de conversation")
            
        return v


class Session(BaseModel):
    """Modèle représentant une session de conversation complète."""
    schema_version: int = Field(default=1, description="Version du schéma de données")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création de la session")
    model: str = Field(..., description="Modèle LLM utilisé pour cette session")
    system: Optional[str] = Field(None, description="Message système pour cette session")
    turns: List[Turn] = Field(default_factory=list, description="Liste des tours de conversation")
    usage_totals: Optional[Usage] = Field(None, description="Usage total cumulé pour toute la session")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées diverses de la session")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}

    @field_validator('model')
    @classmethod
    def model_not_empty(cls, v):
        """Valide que le modèle n'est pas vide."""
        if not v or not v.strip():
            raise ValueError("Le modèle ne peut pas être vide")
        return v.strip()

    @field_validator('created_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse les datetime depuis string ISO 8601."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Format de date invalide, utilisez ISO 8601")
        return v

    def add_turn(self, turn: Turn) -> None:
        """Ajoute un tour à la session et met à jour les totaux d'usage."""
        self.turns.append(turn)
        
        # Mettre à jour les totaux d'usage si disponible
        if turn.usage:
            if self.usage_totals is None:
                self.usage_totals = Usage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            
            self.usage_totals.prompt_tokens += turn.usage.prompt_tokens
            self.usage_totals.completion_tokens += turn.usage.completion_tokens
            self.usage_totals.total_tokens += turn.usage.total_tokens

    def get_all_messages(self) -> List[Message]:
        """Retourne tous les messages de la session dans l'ordre chronologique."""
        messages = []
        
        # Ajouter le message système s'il existe
        if self.system:
            messages.append(Message(role=MessageRole.SYSTEM, content=self.system))
        
        # Ajouter tous les messages des tours
        for turn in self.turns:
            messages.extend(turn.messages)
            
        return messages

    def calculate_total_cost(self) -> Optional[float]:
        """Calcule le coût total estimé de la session."""
        total_cost = 0.0
        has_cost_data = False
        
        for turn in self.turns:
            if turn.cost_estimate is not None:
                total_cost += turn.cost_estimate
                has_cost_data = True
                
        return total_cost if has_cost_data else None


class ChatConfig(BaseModel):
    """Modèle représentant la configuration pour une session de chat."""
    model: str = Field(..., description="Modèle LLM à utiliser")
    system: Optional[str] = Field(None, description="Message système optionnel")
    budget_max: Optional[float] = Field(None, ge=0, description="Budget maximum en USD pour la session")

    @field_validator('model')
    @classmethod
    def model_not_empty(cls, v):
        """Valide que le modèle n'est pas vide."""
        if not v or not v.strip():
            raise ValueError("Le modèle ne peut pas être vide")
        return v.strip()

    @field_validator('system')
    @classmethod
    def system_optional_validation(cls, v):
        """Valide le message système s'il est fourni."""
        if v is not None and not v.strip():
            return None  # Convertir string vide en None
        return v

    def to_session(self) -> Session:
        """Convertit la configuration en une nouvelle session."""
        return Session(
            model=self.model,
            system=self.system,
            meta={"budget_max": self.budget_max} if self.budget_max else {}
        )