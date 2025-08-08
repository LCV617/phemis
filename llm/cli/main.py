"""
Point d'entrée principal du CLI LLM.

Application Typer principale avec sous-commandes pour interagir avec l'API OpenRouter.
Gère l'authentification, la gestion des erreurs globales et l'affichage de la version.
"""

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.provider_openrouter import OpenRouterAuthError, OpenRouterError

# Configuration de l'application principale
app = typer.Typer(
    name="llm",
    help="CLI tool for interacting with OpenRouter API",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool):
    """Affiche la version du package et quitte."""
    if value:
        try:
            import importlib.metadata
            version = importlib.metadata.version("llm-cli")
        except ImportError:
            # Fallback pour Python < 3.8
            try:
                import pkg_resources
                version = pkg_resources.get_distribution("llm-cli").version
            except Exception:
                version = "0.1.0"  # Version par défaut
        except Exception:
            version = "0.1.0"  # Version par défaut
        
        console.print(f"llm-cli version {version}")
        raise typer.Exit()


def check_auth():
    """
    Vérifie que la clé API OpenRouter est configurée.
    
    Raises:
        typer.Exit: Si la clé API n'est pas trouvée
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        error_panel = Panel(
            "[red]Erreur: Clé API OpenRouter manquante[/red]\n\n"
            "Veuillez définir votre clé API OpenRouter:\n"
            "[cyan]export OPENROUTER_API_KEY=your_api_key_here[/cyan]\n\n"
            "Obtenez votre clé API sur: https://openrouter.ai/keys",
            title="[red]Configuration requise[/red]",
            border_style="red",
            padding=(1, 1),
        )
        console.print(error_panel)
        raise typer.Exit(1)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", 
        callback=version_callback, 
        help="Show version and exit"
    )
):
    """
    CLI tool for interacting with OpenRouter API.
    
    This tool allows you to chat with various LLM models through OpenRouter,
    manage conversation sessions, and explore available models.
    
    Before using this tool, make sure to set your OpenRouter API key:
    export OPENROUTER_API_KEY=your_api_key_here
    """
    # La vérification d'auth sera faite par chaque sous-commande selon le besoin
    pass


# Gestionnaire d'erreurs global pour les exceptions non gérées
def handle_openrouter_errors(func):
    """Décorateur pour gérer les erreurs OpenRouter de manière uniforme."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OpenRouterAuthError as e:
            error_panel = Panel(
                f"[red]Erreur d'authentification:[/red]\n{str(e)}\n\n"
                "[yellow]Vérifiez votre clé API OpenRouter:[/yellow]\n"
                "[cyan]export OPENROUTER_API_KEY=your_api_key_here[/cyan]",
                title="[red]Authentification échouée[/red]",
                border_style="red",
                padding=(1, 1),
            )
            console.print(error_panel)
            raise typer.Exit(1)
        except OpenRouterError as e:
            error_panel = Panel(
                f"[red]Erreur OpenRouter:[/red]\n{str(e)}",
                title="[red]Erreur API[/red]",
                border_style="red",
                padding=(1, 1),
            )
            console.print(error_panel)
            raise typer.Exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Opération annulée par l'utilisateur[/yellow]")
            raise typer.Exit(0)
        except Exception as e:
            error_panel = Panel(
                f"[red]Erreur inattendue:[/red]\n{str(e)}\n\n"
                "[dim]Si ce problème persiste, veuillez rapporter un bug.[/dim]",
                title="[red]Erreur interne[/red]",
                border_style="red",
                padding=(1, 1),
            )
            console.print(error_panel)
            raise typer.Exit(1)
    
    return wrapper


# Import et ajout des sous-commandes
try:
    from .models import models_app
    app.add_typer(models_app, name="models", help="Manage and explore available models")
except ImportError as e:
    # Gérer les imports optionnels gracieusement pendant le développement
    console.print(f"[yellow]Warning: Could not import models command: {e}[/yellow]")

# Import et ajout des autres sous-commandes
try:
    from .chat import chat_command
    app.command(name="chat", help="Interactive chat with an LLM")(chat_command)
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import chat command: {e}[/yellow]")

try:
    from .ask import ask_app
    app.add_typer(ask_app, name="ask", help="Ask single questions to models")
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import ask command: {e}[/yellow]")

try:
    from .sessions import sessions_app
    app.add_typer(sessions_app, name="sessions", help="Manage conversation sessions")
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import sessions command: {e}[/yellow]")


def cli():
    """Point d'entrée pour la console script."""
    try:
        app()
    except Exception as e:
        # Dernier filet de sécurité pour les erreurs non gérées
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()