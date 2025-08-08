"""
Commande CLI 'ask' pour poser une question unique à un modèle LLM.

Ce module implémente la commande `llm ask` qui permet d'envoyer une question
à un modèle LLM et d'obtenir une réponse immédiate avec streaming en temps réel.
"""

import json
import time
from typing import Optional, Dict, Any, Generator

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.rule import Rule

from ..core.session import ChatSession
from ..core.provider_openrouter import OpenRouterProvider, OpenRouterError
from ..core.utils import format_duration, format_cost
from ..core.schema import Usage, Message, MessageRole


ask_app = typer.Typer(name="ask", help="Ask a single question to an LLM")


class StreamingResponse:
    """Classe pour gérer la réponse en streaming."""
    
    def __init__(self):
        self.content = ""
        self.usage: Optional[Usage] = None
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
    def add_chunk(self, chunk: str) -> None:
        """Ajoute un chunk de contenu à la réponse."""
        self.content += chunk
        
    def finalize(self, usage: Optional[Usage] = None) -> None:
        """Finalise la réponse avec les métadonnées."""
        self.end_time = time.time()
        if usage:
            self.usage = usage
    
    @property
    def latency_ms(self) -> float:
        """Retourne la latence en millisecondes."""
        end = self.end_time if self.end_time else time.time()
        return (end - self.start_time) * 1000


def extract_usage_from_chunk(chunk: Dict[str, Any]) -> Optional[Usage]:
    """Extrait les informations d'usage d'un chunk de streaming."""
    if 'usage' in chunk and chunk['usage']:
        usage_data = chunk['usage']
        try:
            return Usage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
        except Exception:
            return None
    return None


def extract_content_from_chunk(chunk: Dict[str, Any]) -> str:
    """Extrait le contenu d'un chunk de streaming."""
    choices = chunk.get('choices', [])
    if choices and len(choices) > 0:
        delta = choices[0].get('delta', {})
        return delta.get('content', '')
    return ''


def stream_chat_response(
    provider: OpenRouterProvider,
    messages: list,
    model: str,
    console: Console
) -> StreamingResponse:
    """
    Gère le streaming de la réponse du chat.
    
    Args:
        provider: Instance du provider OpenRouter
        messages: Messages à envoyer à l'API
        model: Identifiant du modèle
        console: Console Rich pour l'affichage
        
    Returns:
        Réponse complète avec métadonnées
    """
    response = StreamingResponse()
    
    try:
        # Démarrer la requête de streaming
        stream = provider.chat_completion(
            messages=messages,
            model=model,
            stream=True
        )
        
        # Traiter chaque chunk
        for chunk in stream:
            # Extraire le contenu
            content = extract_content_from_chunk(chunk)
            if content:
                response.add_chunk(content)
                # Afficher le contenu en temps réel sans nouvelle ligne
                console.print(content, end='', highlight=False)
            
            # Vérifier si c'est le dernier chunk avec les métadonnées
            usage = extract_usage_from_chunk(chunk)
            if usage:
                response.finalize(usage)
                
    except Exception as e:
        response.finalize()
        raise e
    
    # S'assurer qu'on finalise même sans usage explicit
    if response.end_time is None:
        response.finalize()
    
    return response


def format_metadata_footer(
    model: str,
    usage: Optional[Usage],
    latency_ms: float,
    cost_estimate: Optional[float]
) -> str:
    """
    Formate le footer avec les métadonnées de la réponse.
    
    Args:
        model: Identifiant du modèle utilisé
        usage: Métriques d'usage des tokens
        latency_ms: Latence en millisecondes
        cost_estimate: Estimation du coût
        
    Returns:
        Chaîne formatée pour le footer
    """
    parts = [f"Model: {model}"]
    
    if usage:
        token_info = f"{usage.prompt_tokens}→{usage.completion_tokens} ({usage.total_tokens})"
        parts.append(f"Tokens: {token_info}")
    
    parts.append(format_duration(latency_ms))
    
    if cost_estimate is not None:
        parts.append(f"~{format_cost(cost_estimate)}")
    
    return " | ".join(parts)


def get_model_info(provider: OpenRouterProvider, model_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les informations d'un modèle spécifique.
    
    Args:
        provider: Instance du provider OpenRouter
        model_id: Identifiant du modèle
        
    Returns:
        Dictionnaire avec les infos du modèle ou None si non trouvé
    """
    try:
        models = provider.list_models()
        for model_info in models:
            if model_info.id == model_id:
                return {
                    'id': model_info.id,
                    'pricing_prompt': model_info.pricing_prompt,
                    'pricing_completion': model_info.pricing_completion,
                    'context_length': model_info.context_length,
                    'description': model_info.description
                }
        return None
    except Exception:
        return None


def calculate_cost(usage: Optional[Usage], model_info: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Calcule le coût estimé basé sur l'usage et les prix du modèle.
    
    Args:
        usage: Métriques d'usage des tokens
        model_info: Informations du modèle avec les prix
        
    Returns:
        Coût estimé en USD ou None si impossible à calculer
    """
    if not usage or not model_info:
        return None
    
    pricing_prompt = model_info.get('pricing_prompt')
    pricing_completion = model_info.get('pricing_completion')
    
    if pricing_prompt is None or pricing_completion is None:
        return None
    
    # Les prix OpenRouter sont par token, pas par million
    prompt_cost = usage.prompt_tokens * pricing_prompt
    completion_cost = usage.completion_tokens * pricing_completion
    
    return prompt_cost + completion_cost


@ask_app.command()
def ask_question(
    question: str = typer.Argument(..., help="Your question"),
    model: str = typer.Option(..., "--model", "-m", help="Model ID to use"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON format")
) -> None:
    """
    Pose une question unique à un modèle LLM et affiche la réponse.
    
    En mode normal, affiche la réponse en streaming avec métadonnées.
    En mode JSON, retourne une structure complète pour l'intégration dans des scripts.
    """
    console = Console()
    
    try:
        # Initialiser le provider OpenRouter
        provider = OpenRouterProvider()
        
        # Récupérer les informations du modèle pour le calcul des coûts
        model_info = get_model_info(provider, model)
        
        # Créer une session temporaire
        session = ChatSession(model=model, system=system)
        session.append_user(question)
        
        # Préparer les messages pour l'API
        api_messages = []
        for msg_dict in session.get_messages_for_api():
            api_messages.append(Message(
                role=MessageRole(msg_dict['role']),
                content=msg_dict['content']
            ))
        
        if json_output:
            # Mode JSON: réponse complète sans streaming visible
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Generating response...", total=None)
                
                # Faire l'appel API sans streaming pour le mode JSON
                response_data = provider.chat_completion(
                    messages=api_messages,
                    model=model,
                    stream=False
                )
            
            # Extraire les données de la réponse
            choices = response_data.get('choices', [])
            if not choices:
                raise OpenRouterError("No response choices returned from API")
            
            # Extraire le contenu de la réponse, en priorisant le reasoning si content est vide
            message = choices[0].get('message', {})
            response_content = message.get('content', '')
            
            # Si le content est vide ou juste des espaces, utiliser le reasoning
            if not response_content or not response_content.strip():
                response_content = message.get('reasoning', '')
                
            # Si toujours vide, c'est une erreur
            if not response_content or not response_content.strip():
                response_content = "No content returned from the model"
            usage_data = response_data.get('usage', {})
            
            usage = Usage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )
            
            cost_estimate = calculate_cost(usage, model_info)
            
            # Construire la structure JSON
            json_response = {
                "question": question,
                "response": response_content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "latency_ms": 0,  # Non disponible en mode non-streaming
                "estimated_cost_usd": cost_estimate
            }
            
            # Ajouter le système si défini
            if system:
                json_response["system"] = system
            
            # Afficher le JSON
            console.print(json.dumps(json_response, indent=2, ensure_ascii=False))
            
        else:
            # Mode streaming normal
            if not json_output:
                # Afficher la question avec style
                console.print()
                console.print(Text("Question:", style="bold cyan"))
                console.print(Markdown(f"> {question}"))
                console.print()
                console.print(Text("Response:", style="bold green"))
                console.print()
            
            # Démarrer le streaming avec un spinner initial
            with console.status("[bold green]Thinking...", spinner="dots"):
                time.sleep(0.1)  # Petit délai pour l'effet visuel
            
            # Streamer la réponse
            streaming_response = stream_chat_response(
                provider=provider,
                messages=api_messages,
                model=model,
                console=console
            )
            
            # Calculer le coût estimé
            cost_estimate = calculate_cost(streaming_response.usage, model_info)
            
            # Afficher le footer avec les métadonnées
            console.print("\n")  # Nouvelle ligne après la réponse
            console.print(Rule())
            
            footer_text = format_metadata_footer(
                model=model,
                usage=streaming_response.usage,
                latency_ms=streaming_response.latency_ms,
                cost_estimate=cost_estimate
            )
            console.print(Text(footer_text, style="dim"))
            
            # Finaliser la session (optionnel pour une question unique)
            session.append_assistant(
                content=streaming_response.content,
                usage=streaming_response.usage,
                latency_ms=streaming_response.latency_ms
            )
            
    except OpenRouterError as e:
        error_msg = str(e)
        if json_output:
            error_response = {
                "error": error_msg,
                "question": question,
                "model": model
            }
            console.print(json.dumps(error_response, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            
            # Suggestions d'aide selon le type d'erreur
            if "401" in error_msg or "authentication" in error_msg.lower():
                console.print("\n[yellow]💡 Tip:[/yellow] Check your OPENROUTER_API_KEY environment variable")
            elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                console.print(f"\n[yellow]💡 Tip:[/yellow] Use `llm models list` to see available models")
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                console.print("\n[yellow]💡 Tip:[/yellow] Wait a moment and try again")
        
        raise typer.Exit(1)
        
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        if json_output:
            error_response = {
                "error": error_msg,
                "question": question,
                "model": model
            }
            console.print(json.dumps(error_response, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
        
        raise typer.Exit(1)


if __name__ == "__main__":
    ask_app()