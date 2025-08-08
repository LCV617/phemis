"""
Module de gestion des sessions de conversation via CLI.

Ce module implémente les commandes pour lister, afficher et reprendre des sessions.
Il fournit une interface utilisateur riche avec formatage des tableaux et gestion
complète des erreurs.
"""

import typer
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from ..core.storage import load_session, list_session_files, StorageError
from ..core.cost import estimate_session_cost, get_cost_breakdown
from ..core.utils import format_cost, format_duration, truncate_text
from ..core.schema import Session, ModelInfo

# Instance console pour l'affichage
console = Console()

# App Typer pour les sous-commandes sessions
sessions_app = typer.Typer(name="sessions", help="Manage chat sessions")


def format_session_summary(session: Session) -> dict:
    """
    Formate un résumé des informations clés d'une session.
    
    Args:
        session: Session à analyser
        
    Returns:
        Dictionnaire avec les informations formatées
    """
    # Calculer les statistiques de base
    turns_count = len(session.turns)
    total_tokens = session.usage_totals.total_tokens if session.usage_totals else 0
    
    # Premier et dernier message
    first_exchange = None
    last_exchange = None
    
    if session.turns:
        # Premier échange
        first_turn = session.turns[0]
        if first_turn.messages:
            user_msg = next((msg for msg in first_turn.messages if msg.role == "user"), None)
            assistant_msg = next((msg for msg in first_turn.messages if msg.role == "assistant"), None)
            
            if user_msg and assistant_msg:
                first_exchange = {
                    "user": truncate_message(user_msg.content, 150),
                    "assistant": truncate_message(assistant_msg.content, 150)
                }
        
        # Dernier échange (si différent du premier)
        if turns_count > 1:
            last_turn = session.turns[-1]
            if last_turn.messages:
                user_msg = next((msg for msg in last_turn.messages if msg.role == "user"), None)
                assistant_msg = next((msg for msg in last_turn.messages if msg.role == "assistant"), None)
                
                if user_msg and assistant_msg:
                    last_exchange = {
                        "user": truncate_message(user_msg.content, 150),
                        "assistant": truncate_message(assistant_msg.content, 150)
                    }
    
    return {
        "model": session.model,
        "created_at": session.created_at,
        "system": session.system,
        "turns_count": turns_count,
        "total_tokens": total_tokens,
        "first_exchange": first_exchange,
        "last_exchange": last_exchange,
        "usage_totals": session.usage_totals
    }


def truncate_message(content: str, max_length: int = 100) -> str:
    """
    Tronque un message à une longueur maximale.
    
    Args:
        content: Contenu du message
        max_length: Longueur maximale
        
    Returns:
        Message tronqué avec "..." si nécessaire
    """
    if len(content) <= max_length:
        return content
    
    # Trouver le dernier espace avant la limite pour éviter de couper au milieu d'un mot
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Si l'espace n'est pas trop loin
        truncated = truncated[:last_space]
    
    return truncated + "..."


def calculate_session_stats(session: Session) -> dict:
    """
    Calcule les statistiques détaillées d'une session.
    
    Args:
        session: Session à analyser
        
    Returns:
        Dictionnaire avec les statistiques
    """
    stats = {
        "turns_count": len(session.turns),
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "avg_latency_ms": 0,
        "total_latency_ms": 0
    }
    
    if session.usage_totals:
        stats.update({
            "total_tokens": session.usage_totals.total_tokens,
            "prompt_tokens": session.usage_totals.prompt_tokens,
            "completion_tokens": session.usage_totals.completion_tokens
        })
    
    # Calculer latence moyenne
    latencies = [turn.latency_ms for turn in session.turns if turn.latency_ms is not None]
    if latencies:
        stats["avg_latency_ms"] = sum(latencies) / len(latencies)
        stats["total_latency_ms"] = sum(latencies)
    
    return stats


@sessions_app.command("list")
def list_sessions(runs_dir: str = typer.Option("./runs", "--dir", "-d", help="Directory containing session files")):
    """
    Liste toutes les sessions disponibles avec leurs statistiques.
    
    Affiche un tableau avec le nom de fichier, la date, le modèle,
    le nombre de tours et le coût estimé pour chaque session.
    """
    try:
        # Vérifier/créer le répertoire runs
        runs_path = Path(runs_dir)
        if not runs_path.exists():
            runs_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[yellow]Répertoire {runs_dir} créé[/yellow]")
        
        # Lister les fichiers de session
        session_files = list_session_files(runs_dir)
        
        if not session_files:
            console.print(f"[yellow]Aucune session trouvée dans {runs_dir}[/yellow]")
            console.print("Utilisez 'llm chat' pour créer votre première session.")
            return
        
        # Créer le tableau Rich
        table = Table(title=f"Sessions ({len(session_files)} trouvées)")
        table.add_column("Filename", style="cyan", no_wrap=True)
        table.add_column("Date", style="magenta")
        table.add_column("Model", style="green")
        table.add_column("Turns", justify="right", style="blue")
        table.add_column("Tokens", justify="right", style="blue")
        table.add_column("Est. Cost", justify="right", style="yellow")
        
        successful_loads = 0
        
        for session_file in session_files:
            try:
                # Charger la session pour extraire les métadonnées
                session = load_session(session_file)
                
                # Calculer les statistiques
                stats = calculate_session_stats(session)
                
                # Estimer le coût (utilise les prix par défaut si pas d'infos modèle)
                estimated_cost = session.calculate_total_cost()
                if estimated_cost is None:
                    # Essayer avec les prix par défaut
                    estimated_cost = estimate_session_cost(session, [])
                    if estimated_cost is None:
                        estimated_cost = 0.0
                
                # Formatage des données
                filename = Path(session_file).name
                date_str = session.created_at.strftime("%Y-%m-%d %H:%M")
                model_display = truncate_text(session.model, 20)
                cost_display = format_cost(estimated_cost) if estimated_cost > 0 else "Free"
                
                table.add_row(
                    filename,
                    date_str,
                    model_display,
                    str(stats["turns_count"]),
                    f"{stats['total_tokens']:,}",
                    cost_display
                )
                
                successful_loads += 1
                
            except Exception as e:
                # Ignorer les fichiers corrompus avec un warning
                filename = Path(session_file).name
                console.print(f"[red]Warning: Impossible de charger {filename}: {e}[/red]")
                continue
        
        if successful_loads > 0:
            console.print(table)
            console.print(f"\n[dim]Utilisez 'llm sessions show <filename>' pour plus de détails[/dim]")
        else:
            console.print("[red]Aucune session valide trouvée[/red]")
            
    except StorageError as e:
        console.print(f"[red]Erreur d'accès au stockage: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Erreur inattendue: {e}[/red]")
        raise typer.Exit(1)


@sessions_app.command("show")
def show_session(session_path: str = typer.Argument(..., help="Path to the session file to display")):
    """
    Affiche le résumé détaillé d'une session spécifique.
    
    Montre les informations de base, le premier et dernier échange,
    ainsi que les statistiques d'usage et de coût.
    """
    try:
        # Charger la session
        session = load_session(session_path)
        
        # Calculer les statistiques détaillées
        summary = format_session_summary(session)
        stats = calculate_session_stats(session)
        cost_breakdown = get_cost_breakdown(session, [])
        
        # Titre avec nom de fichier
        filename = Path(session_path).name
        title_text = Text(f"Session: {filename}", style="bold cyan")
        console.print(title_text)
        console.print()
        
        # Panel avec informations principales
        info_content = []
        info_content.append(f"[bold]Model:[/bold] {session.model}")
        info_content.append(f"[bold]Created:[/bold] {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if session.system:
            system_preview = truncate_text(session.system, 60)
            info_content.append(f"[bold]System:[/bold] {system_preview}")
        
        info_content.append(f"[bold]Turns:[/bold] {stats['turns_count']}")
        
        if stats['total_tokens'] > 0:
            info_content.append(
                f"[bold]Total tokens:[/bold] {stats['total_tokens']:,} "
                f"(prompt: {stats['prompt_tokens']:,}, completion: {stats['completion_tokens']:,})"
            )
        
        if cost_breakdown['pricing_available'] and cost_breakdown['total_cost'] > 0:
            info_content.append(f"[bold]Estimated cost:[/bold] {cost_breakdown['total_cost_formatted']}")
        
        if stats['avg_latency_ms'] > 0:
            info_content.append(f"[bold]Avg latency:[/bold] {format_duration(stats['avg_latency_ms'])}")
        
        info_panel = Panel(
            "\n".join(info_content),
            title="Session Information",
            border_style="blue"
        )
        console.print(info_panel)
        console.print()
        
        # Affichage des échanges
        if summary['first_exchange']:
            first_panel_content = []
            first_panel_content.append(f"[bold blue]USER:[/bold blue] {summary['first_exchange']['user']}")
            first_panel_content.append("")
            first_panel_content.append(f"[bold green]ASSISTANT:[/bold green] {summary['first_exchange']['assistant']}")
            
            first_panel = Panel(
                "\n".join(first_panel_content),
                title="💬 First Exchange",
                border_style="green"
            )
            console.print(first_panel)
            console.print()
        
        # Dernier échange si différent du premier
        if summary['last_exchange'] and stats['turns_count'] > 1:
            last_panel_content = []
            last_panel_content.append(f"[bold blue]USER:[/bold blue] {summary['last_exchange']['user']}")
            last_panel_content.append("")
            last_panel_content.append(f"[bold green]ASSISTANT:[/bold green] {summary['last_exchange']['assistant']}")
            
            last_panel = Panel(
                "\n".join(last_panel_content),
                title="💬 Last Exchange",
                border_style="yellow"
            )
            console.print(last_panel)
            console.print()
        
        # Statistiques détaillées si disponibles
        if cost_breakdown['pricing_available'] and len(cost_breakdown['turns_breakdown']) > 0:
            console.print("[bold]Cost Breakdown by Turn:[/bold]")
            
            cost_table = Table(show_header=True, header_style="bold magenta")
            cost_table.add_column("Turn", justify="center")
            cost_table.add_column("Prompt Tokens", justify="right")
            cost_table.add_column("Completion Tokens", justify="right")
            cost_table.add_column("Cost", justify="right")
            
            for turn_info in cost_breakdown['turns_breakdown'][:5]:  # Limiter à 5 tours
                cost_table.add_row(
                    str(turn_info['turn_number']),
                    f"{turn_info['prompt_tokens']:,}",
                    f"{turn_info['completion_tokens']:,}",
                    turn_info['cost_formatted']
                )
            
            if len(cost_breakdown['turns_breakdown']) > 5:
                cost_table.add_row("...", "...", "...", "...")
            
            console.print(cost_table)
            console.print()
        
        # Actions suggérées
        console.print("[dim]Actions disponibles:[/dim]")
        console.print(f"[dim]• Reprendre la session: llm sessions resume {session_path}[/dim]")
        console.print(f"[dim]• Lister toutes les sessions: llm sessions list[/dim]")
        
    except StorageError as e:
        console.print(f"[red]Erreur lors du chargement de la session: {e}[/red]")
        
        # Suggestions en cas d'erreur
        if "introuvable" in str(e).lower():
            runs_path = Path("./runs")
            if runs_path.exists():
                json_files = list(runs_path.glob("*.json"))
                if json_files:
                    console.print("\n[yellow]Sessions disponibles:[/yellow]")
                    for f in json_files[:5]:
                        console.print(f"  • {f.name}")
                    if len(json_files) > 5:
                        console.print(f"  ... et {len(json_files) - 5} autres")
        
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Erreur inattendue: {e}[/red]")
        raise typer.Exit(1)


@sessions_app.command("resume")
def resume_session(session_path: str = typer.Argument(..., help="Path to the session file to resume")):
    """
    Reprend une session existante et lance le mode chat interactif.
    
    Cette commande charge une session sauvegardée et permet de continuer
    la conversation là où elle s'était arrêtée.
    """
    try:
        # Vérifier que le fichier existe
        session_file = Path(session_path)
        if not session_file.exists():
            console.print(f"[red]Fichier de session introuvable: {session_path}[/red]")
            
            # Suggérer des alternatives
            runs_path = Path("./runs")
            if runs_path.exists():
                json_files = list(runs_path.glob("*.json"))
                if json_files:
                    console.print("\n[yellow]Sessions disponibles:[/yellow]")
                    for f in sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                        console.print(f"  • {f.name}")
            
            raise typer.Exit(1)
        
        # Charger la session pour validation
        try:
            session = load_session(session_path)
        except Exception as e:
            console.print(f"[red]Impossible de charger la session: {e}[/red]")
            raise typer.Exit(1)
        
        # Afficher un résumé avant de reprendre
        console.print(f"[green]Reprise de la session: {session_file.name}[/green]")
        console.print(f"Model: {session.model}")
        console.print(f"Tours précédents: {len(session.turns)}")
        
        if session.usage_totals:
            console.print(f"Tokens utilisés: {session.usage_totals.total_tokens:,}")
        
        console.print()
        
        # Importer et lancer le chat avec la session pré-chargée
        try:
            from .chat import start_chat_with_session
            start_chat_with_session(session, session_path)
            
        except ImportError:
            console.print("[yellow]Module de chat non disponible[/yellow]")
            console.print(f"[dim]Session validée: {session_path}[/dim]")
            console.print("[dim]Utilisez 'llm chat --resume <path>' pour reprendre cette session[/dim]")
        except Exception as e:
            console.print(f"[red]Erreur lors du lancement du chat: {e}[/red]")
            console.print(f"[dim]Utilisez 'llm chat --resume {session_path}' pour reprendre cette session[/dim]")
        
    except Exception as e:
        console.print(f"[red]Erreur lors de la reprise: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    # Permet d'exécuter le module directement pour les tests
    sessions_app()