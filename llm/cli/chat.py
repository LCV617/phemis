"""
Module de chat interactif pour l'outil CLI LLM.

Ce module implémente la commande `llm chat` qui fournit un REPL interactif
avec streaming des réponses, gestion du budget et commandes internes.
"""

import typer
import signal
import sys
import time
import readline
from typing import Optional, Generator
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

from ..core.session import ChatSession
from ..core.provider_openrouter import (
    OpenRouterProvider, 
    OpenRouterError, 
    OpenRouterAuthError, 
    OpenRouterRateLimitError,
    OpenRouterServerError
)
from ..core.storage import save_session, load_session, StorageError
from ..core.schema import Session, Usage, ModelInfo
from ..core.cost import get_budget_warning, format_budget_status
from ..core.utils import format_duration, format_cost

# Instance console pour l'affichage
console = Console()

# Variables globales pour gérer l'interruption gracieuse
current_session: Optional[ChatSession] = None
provider: Optional[OpenRouterProvider] = None
session_file_path: Optional[str] = None


class ChatInterrupt(Exception):
    """Exception pour gérer l'interruption gracieuse du chat."""
    pass


def signal_handler(signum, frame):
    """Gestionnaire de signal pour Ctrl+C."""
    raise ChatInterrupt()


def format_metadata_footer(
    model: str,
    usage: Optional[Usage] = None,
    latency_ms: Optional[float] = None,
    cost_estimate: Optional[float] = None,
    budget_status: Optional[str] = None
) -> str:
    """
    Formate le footer avec les métadonnées après chaque réponse.
    
    Args:
        model: Nom du modèle utilisé
        usage: Métriques d'usage des tokens
        latency_ms: Latence de la réponse
        cost_estimate: Coût estimé de cette réponse
        budget_status: Status du budget formaté
        
    Returns:
        Footer formaté avec métadonnées
    """
    separator = "─" * 80
    parts = ["assistant", model]
    
    if usage:
        token_info = f"tokens: {usage.prompt_tokens}→{usage.completion_tokens} ({usage.total_tokens})"
        parts.append(token_info)
    
    if latency_ms:
        parts.append(format_duration(latency_ms))
    
    if cost_estimate:
        parts.append(f"~{format_cost(cost_estimate)}")
    
    if budget_status:
        parts.append(budget_status)
    
    footer_text = " | ".join(parts)
    
    return f"\n{separator}\n{footer_text}\n"


def get_budget_color(percentage: Optional[float]) -> str:
    """
    Retourne la couleur Rich appropriée basée sur le pourcentage du budget.
    
    Args:
        percentage: Pourcentage du budget utilisé (0.0 à 1.0+)
        
    Returns:
        Couleur Rich (green, yellow, red)
    """
    if percentage is None:
        return "dim"
    
    if percentage < 0.7:
        return "green"
    elif percentage < 0.9:
        return "yellow"
    else:
        return "red"


def format_budget_status_rich(current_cost: float, budget_max: Optional[float]) -> str:
    """
    Formate le statut du budget avec la couleur Rich appropriée.
    
    Args:
        current_cost: Coût actuel
        budget_max: Budget maximum ou None
        
    Returns:
        String formaté avec couleur Rich
    """
    if budget_max is None:
        return f"budget: {format_cost(current_cost)} (no limit)"
    
    percentage = current_cost / budget_max if budget_max > 0 else 0
    color = get_budget_color(percentage)
    
    budget_text = f"budget: {format_cost(current_cost)}/{format_cost(budget_max)} ({percentage*100:.1f}%)"
    
    if percentage >= 1.0:
        budget_text += " 🚨"
    elif percentage >= 0.8:
        budget_text += " ⚠️"
    
    return f"[{color}]{budget_text}[/{color}]"


def stream_response(provider: OpenRouterProvider, chat_session: ChatSession) -> tuple[str, Optional[Usage], float]:
    """
    Effectue un appel streaming à l'API et affiche la réponse en temps réel.
    
    Args:
        provider: Instance du provider OpenRouter
        chat_session: Session de chat active
        
    Returns:
        Tuple (contenu_complet, usage, latency_ms)
        
    Raises:
        ChatInterrupt: Si l'utilisateur interrompt le streaming
        OpenRouterError: Pour les erreurs API
    """
    start_time = time.time()
    content_buffer = []
    usage = None
    
    try:
        # Préparer les messages pour l'API
        messages_for_api = chat_session.get_messages_for_api()
        
        # Convertir au format attendu par le provider
        from ..core.schema import Message, MessageRole
        api_messages = []
        for msg_dict in messages_for_api:
            role_str = msg_dict["role"]
            if role_str == "system":
                role = MessageRole.SYSTEM
            elif role_str == "user":
                role = MessageRole.USER
            else:
                role = MessageRole.ASSISTANT
            
            api_messages.append(Message(role=role, content=msg_dict["content"]))
        
        # Lancer la requête streaming
        stream_generator = provider.chat_completion(
            messages=api_messages,
            model=chat_session.model,
            stream=True
        )
        
        # Afficher la réponse en temps réel avec Rich Live
        with Live(console=console, refresh_per_second=10) as live:            
            for chunk in stream_generator:
                # Vérifier si l'utilisateur a interrompu
                signal.signal(signal.SIGINT, signal_handler)
                
                # Parser le chunk
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    choice = chunk['choices'][0]
                    
                    if 'delta' in choice and 'content' in choice['delta']:
                        content_piece = choice['delta']['content']
                        if content_piece:
                            # Ne collecter que les nouveaux chunks individuels
                            content_buffer.append(content_piece)
                            
                            # Reconstruire le texte complet depuis les chunks
                            accumulated_text = ''.join(content_buffer)
                            
                            # Afficher le markdown accumulé
                            markdown = Markdown(accumulated_text)
                            live.update(markdown)
                    
                    # Vérifier si c'est la fin
                    if choice.get('finish_reason') is not None:
                        break
                
                # Extraire les métriques d'usage si disponibles
                if 'usage' in chunk:
                    usage_data = chunk['usage']
                    usage = Usage(
                        prompt_tokens=usage_data.get('prompt_tokens', 0),
                        completion_tokens=usage_data.get('completion_tokens', 0),
                        total_tokens=usage_data.get('total_tokens', 0)
                    )
        
        # Calculer la latence
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Assembler le contenu complet
        full_content = ''.join(content_buffer)
        
        return full_content, usage, latency_ms
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Réponse interrompue par l'utilisateur[/yellow]")
        raise ChatInterrupt()
    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Retourner ce qu'on a pu capturer même en cas d'erreur
        partial_content = ''.join(content_buffer)
        if partial_content:
            return partial_content, usage, latency_ms
        else:
            raise e


def handle_internal_command(command: str, args: list, chat_session: ChatSession) -> bool:
    """
    Traite les commandes internes du REPL.
    
    Args:
        command: Commande (sans le ':')
        args: Arguments de la commande
        chat_session: Session active
        
    Returns:
        True si la commande était ':exit' (pour arrêter le REPL)
    """
    global session_file_path
    
    if command == "help":
        help_panel = Panel(
            """[bold]Commandes disponibles:[/bold]

[cyan]:reset[/cyan]           - Vide l'historique (garde le prompt système)
[cyan]:save [filename][/cyan] - Sauvegarde la session (./runs/ par défaut)
[cyan]:exit[/cyan]           - Quitte sans demander sauvegarde
[cyan]:help[/cyan]           - Affiche cette aide

[dim]Tapez votre message directement pour envoyer à l'assistant[/dim]""",
            title="💬 Aide REPL Chat",
            border_style="blue"
        )
        console.print(help_panel)
        
    elif command == "reset":
        chat_session.reset()
        console.print("[green]✓ Historique vidé (prompt système conservé)[/green]")
        
    elif command == "save":
        try:
            if args:
                # Filename spécifié
                filename = args[0]
                if not filename.endswith('.json'):
                    filename += '.json'
                
                # Sauvegarder dans runs/ sauf si chemin absolu
                if not Path(filename).is_absolute():
                    runs_dir = Path("./runs")
                    runs_dir.mkdir(exist_ok=True)
                    save_path = runs_dir / filename
                else:
                    save_path = Path(filename)
            else:
                # Génération automatique du nom
                save_path = "./runs"
            
            # Convertir et sauvegarder
            session = chat_session.to_session()
            actual_path = save_session(session, str(save_path))
            session_file_path = actual_path
            
            console.print(f"[green]💾 Session sauvegardée: {actual_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Erreur lors de la sauvegarde: {e}[/red]")
    
    elif command == "exit":
        return True
    
    else:
        console.print(f"[red]Commande inconnue: :{command}[/red]")
        console.print("[dim]Tapez :help pour voir les commandes disponibles[/dim]")
    
    return False


def show_budget_alert(warning_message: str):
    """
    Affiche une alerte de budget avec Rich.
    
    Args:
        warning_message: Message d'avertissement à afficher
    """
    if "DÉPASSÉ" in warning_message:
        style = "red"
        icon = "🚨"
    else:
        style = "yellow"
        icon = "⚠️"
    
    alert_panel = Panel(
        f"{icon} {warning_message}",
        title="Budget Alert",
        border_style=style
    )
    console.print(alert_panel)


def prompt_save_session(chat_session: ChatSession) -> Optional[str]:
    """
    Demande à l'utilisateur s'il souhaite sauvegarder la session.
    
    Args:
        chat_session: Session à sauvegarder
        
    Returns:
        Chemin du fichier sauvegardé ou None si annulé
    """
    if len(chat_session.turns) == 0:
        return None
    
    try:
        save_choice = Prompt.ask("💾 Save this session?", choices=["y", "N"], default="N")
        
        if save_choice.lower() == "y":
            session = chat_session.to_session()
            save_path = save_session(session, "./runs")
            console.print(f"[green]Session saved to {save_path}[/green]")
            return save_path
    
    except (KeyboardInterrupt, EOFError):
        pass
    
    return None


def start_chat_with_session(loaded_session: Session, resume_path: Optional[str] = None):
    """
    Démarre le chat avec une session pré-chargée (pour la commande resume).
    
    Args:
        loaded_session: Session à reprendre
        resume_path: Chemin du fichier de session (pour updates)
    """
    global current_session, provider, session_file_path
    
    try:
        # Créer le provider
        provider = OpenRouterProvider()
        
        # Convertir la Session en ChatSession
        current_session = ChatSession.from_session(loaded_session)
        session_file_path = resume_path
        
        # Afficher le welcome message avec info de reprise
        console.print(f"[green]📄 Session resumed: {Path(resume_path).name if resume_path else 'loaded'}[/green]")
        console.print(f"Model: [cyan]{current_session.model}[/cyan]")
        console.print(f"Previous turns: [blue]{len(current_session.turns)}[/blue]")
        
        if current_session.usage_totals.total_tokens > 0:
            console.print(f"Previous tokens: [blue]{current_session.usage_totals.total_tokens:,}[/blue]")
        
        if current_session.estimate_usd_total > 0:
            budget_status = format_budget_status_rich(current_session.estimate_usd_total, current_session.budget_max)
            console.print(f"Previous cost: {budget_status}")
        
        console.print("\n[dim]Type :help for commands, :exit to quit.[/dim]")
        console.print()
        
        # Démarrer le REPL
        _run_chat_repl(current_session, provider)
        
    except OpenRouterAuthError as e:
        console.print(f"[red]Authentication error: {e}[/red]")
        console.print("[yellow]Please check your OPENROUTER_API_KEY environment variable[/yellow]")
    except Exception as e:
        console.print(f"[red]Error resuming session: {e}[/red]")


def _run_chat_repl(chat_session: ChatSession, provider: OpenRouterProvider):
    """
    Lance la boucle principale du REPL de chat.
    
    Args:
        chat_session: Session de chat active
        provider: Provider OpenRouter configuré
    """
    global session_file_path
    
    # Configuration de readline pour l'historique des commandes
    try:
        import readline
        readline.set_history_length(1000)
    except ImportError:
        pass
    
    # Installation du gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while True:
            try:
                # Prompt utilisateur avec couleur
                user_input = console.input("[cyan]you>[/cyan] ").strip()
                
                if not user_input:
                    continue
                
                # Vérifier les commandes internes
                if user_input.startswith(':'):
                    command_parts = user_input[1:].split()
                    if not command_parts:
                        continue
                    
                    command = command_parts[0]
                    args = command_parts[1:]
                    
                    should_exit = handle_internal_command(command, args, chat_session)
                    if should_exit:
                        break
                    
                    continue
                
                # Ajouter le message utilisateur
                chat_session.append_user(user_input)
                
                # Effectuer la requête avec streaming
                try:
                    content, usage, latency_ms = stream_response(provider, chat_session)
                    
                    if not content:
                        console.print("[yellow]Réponse vide reçue[/yellow]")
                        continue
                    
                    # Calculer le coût estimé pour cette réponse
                    cost_estimate = None
                    if usage and hasattr(provider, 'estimate_cost'):
                        # Ici on devrait avoir les infos de pricing du modèle
                        # Pour simplifier, on utilise des prix par défaut
                        cost_estimate = provider.estimate_cost(usage, 0.000003, 0.000015)  # Prix approximatifs
                    
                    # Ajouter la réponse à la session
                    chat_session.append_assistant(content, usage, latency_ms)
                    
                    # Mettre à jour le coût total
                    if cost_estimate:
                        chat_session.update_cost_estimate(cost_estimate)
                    
                    # Afficher les métadonnées
                    budget_status = format_budget_status_rich(
                        chat_session.estimate_usd_total, 
                        chat_session.budget_max
                    )
                    
                    metadata_footer = format_metadata_footer(
                        model=chat_session.model,
                        usage=usage,
                        latency_ms=latency_ms,
                        cost_estimate=cost_estimate,
                        budget_status=budget_status
                    )
                    
                    console.print(metadata_footer)
                    
                    # Vérifier les alertes budget
                    budget_warning = chat_session.check_budget()
                    if budget_warning:
                        show_budget_alert(budget_warning)
                    
                    # Auto-sauvegarde si on a un chemin de fichier
                    if session_file_path and len(chat_session.turns) % 5 == 0:  # Sauvegarde toutes les 5 réponses
                        try:
                            session = chat_session.to_session()
                            save_session(session, session_file_path)
                        except Exception as e:
                            console.print(f"[dim]Auto-save failed: {e}[/dim]", style="red")
                
                except ChatInterrupt:
                    # L'utilisateur a interrompu le streaming
                    console.print("\n[yellow]Response interrupted[/yellow]")
                    
                    # Supprimer le message utilisateur non traité
                    if chat_session._current_turn_messages:
                        chat_session._current_turn_messages.clear()
                    
                    continue
                
                except OpenRouterRateLimitError:
                    console.print("[yellow]⏳ Rate limit reached. Waiting 10 seconds...[/yellow]")
                    time.sleep(10)
                    continue
                
                except OpenRouterServerError as e:
                    console.print(f"[red]Server error: {e}[/red]")
                    console.print("[yellow]Retrying in 5 seconds...[/yellow]")
                    time.sleep(5)
                    continue
                
                except OpenRouterError as e:
                    console.print(f"[red]API Error: {e}[/red]")
                    
                    # Supprimer le message utilisateur non traité
                    if chat_session._current_turn_messages:
                        chat_session._current_turn_messages.clear()
                    
                    continue
                
            except (KeyboardInterrupt, EOFError, ChatInterrupt):
                console.print()
                break
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")
                continue
        
    finally:
        # Nettoyage et demande de sauvegarde
        console.print("\n[yellow]Exiting chat...[/yellow]")
        
        try:
            saved_path = prompt_save_session(chat_session)
            if saved_path:
                console.print(f"[green]Session saved to {saved_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error during save: {e}[/red]")
        
        console.print("Goodbye! 👋")


# Fonction principale de chat (sera ajoutée comme commande au main app)
def chat_command(
    model: str = typer.Option(..., "--model", "-m", help="Model ID to use"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    budget_max: Optional[float] = typer.Option(None, "--budget-max", "-b", help="Max budget in USD"),
    resume: Optional[str] = typer.Option(None, "--resume", "-r", help="Resume from session file")
):
    """
    Lance le chat interactif avec un LLM.
    
    Utilise un REPL avec streaming des réponses, gestion du budget
    et commandes internes pour gérer la session.
    """
    global current_session, provider, session_file_path
    
    try:
        # Si mode resume, charger la session existante
        if resume:
            try:
                loaded_session = load_session(resume)
                session_file_path = resume
                start_chat_with_session(loaded_session, resume)
                return
            except StorageError as e:
                console.print(f"[red]Error loading session: {e}[/red]")
                raise typer.Exit(1)
        
        # Créer le provider OpenRouter
        try:
            provider = OpenRouterProvider()
        except OpenRouterAuthError as e:
            console.print(f"[red]Authentication error: {e}[/red]")
            console.print("[yellow]Please set your OPENROUTER_API_KEY environment variable[/yellow]")
            raise typer.Exit(1)
        
        # Créer une nouvelle session
        current_session = ChatSession(
            model=model,
            system=system,
            budget_max=budget_max
        )
        
        # Afficher le welcome message
        welcome_text = Text("Welcome to LLM Chat!", style="bold green")
        console.print(welcome_text)
        console.print(f"Model: [cyan]{model}[/cyan]")
        
        if system:
            system_preview = system[:80] + "..." if len(system) > 80 else system
            console.print(f"System: [dim]{system_preview}[/dim]")
        
        if budget_max:
            console.print(f"Budget: [green]{format_cost(budget_max)}[/green]")
        
        console.print("\n[dim]Type :help for commands, :exit to quit.[/dim]")
        console.print()
        
        # Démarrer le REPL
        _run_chat_repl(current_session, provider)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    chat_app()