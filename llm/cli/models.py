"""
Commande 'llm models' pour explorer les modèles disponibles sur OpenRouter.

Cette sous-commande permet de lister et filtrer les modèles LLM disponibles,
avec affichage des informations de prix, contexte et descriptions.
"""

import os
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..core.provider_openrouter import OpenRouterProvider, OpenRouterError, OpenRouterAuthError
from ..core.schema import ModelInfo

# Configuration de la sous-application
models_app = typer.Typer(
    name="models",
    help="Manage and explore available models",
    no_args_is_help=True,
)

console = Console()


def format_context_length(context_length: Optional[int]) -> str:
    """
    Formate la longueur de contexte pour l'affichage.
    
    Args:
        context_length: Longueur de contexte en tokens
        
    Returns:
        Chaîne formatée (ex: "128k", "N/A")
    """
    if context_length is None:
        return "N/A"
    
    if context_length >= 1000000:
        return f"{context_length // 1000000}M"
    elif context_length >= 1000:
        return f"{context_length // 1000}k"
    else:
        return str(context_length)


def format_price(price: Optional[float]) -> str:
    """
    Formate un prix pour l'affichage.
    
    Args:
        price: Prix par token en USD
        
    Returns:
        Chaîne formatée (ex: "$0.15/1M", "N/A")
    """
    if price is None:
        return "N/A"
    
    # Convertir le prix par token en prix par million de tokens
    price_per_million = price * 1000000
    
    if price_per_million < 0.01:
        return f"${price_per_million:.4f}/1M"
    elif price_per_million < 1.0:
        return f"${price_per_million:.3f}/1M"
    else:
        return f"${price_per_million:.2f}/1M"


def truncate_description(description: Optional[str], max_length: int = 50) -> str:
    """
    Tronque une description pour l'affichage dans le tableau.
    
    Args:
        description: Description à tronquer
        max_length: Longueur maximale
        
    Returns:
        Description tronquée avec "..." si nécessaire
    """
    if not description:
        return "N/A"
    
    # Nettoyer la description (supprimer les sauts de ligne multiples)
    clean_desc = " ".join(description.split())
    
    if len(clean_desc) <= max_length:
        return clean_desc
    
    return clean_desc[:max_length-3] + "..."


def filter_models(models: List[ModelInfo], filter_text: Optional[str]) -> List[ModelInfo]:
    """
    Filtre la liste des modèles selon le texte de filtre.
    
    Args:
        models: Liste des modèles à filtrer
        filter_text: Texte de filtre (substring à rechercher dans l'ID)
        
    Returns:
        Liste filtrée des modèles
    """
    if not filter_text:
        return models
    
    filter_lower = filter_text.lower()
    return [
        model for model in models 
        if filter_lower in model.id.lower()
    ]


def create_models_table(models: List[ModelInfo]) -> Table:
    """
    Crée un tableau Rich pour afficher les modèles.
    
    Args:
        models: Liste des modèles à afficher
        
    Returns:
        Table Rich configurée
    """
    table = Table(
        title="Available Models on OpenRouter",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold magenta",
    )
    
    # Ajouter les colonnes
    table.add_column("Model ID", style="green", no_wrap=True, width=25)
    table.add_column("Context", justify="right", style="yellow", width=10)
    table.add_column("Price In", justify="right", style="red", width=12)
    table.add_column("Price Out", justify="right", style="red", width=12)
    table.add_column("Description", style="dim", width=50)
    
    # Trier les modèles par ID alphabétiquement
    sorted_models = sorted(models, key=lambda m: m.id.lower())
    
    # Ajouter les lignes
    for model in sorted_models:
        table.add_row(
            model.id,
            format_context_length(model.context_length),
            format_price(model.pricing_prompt),
            format_price(model.pricing_completion),
            truncate_description(model.description),
        )
    
    return table


@models_app.command("list")
def list_models(
    filter_text: Optional[str] = typer.Option(
        None, "--filter", "-f",
        help="Filter models by substring in model ID"
    ),
    show_details: bool = typer.Option(
        False, "--details", "-d",
        help="Show detailed information for each model"
    )
):
    """
    List available models from OpenRouter.
    
    This command fetches and displays all available models from OpenRouter,
    including their context length, pricing information, and descriptions.
    
    Examples:
        llm models list                    # List all models
        llm models list --filter gpt       # List models containing 'gpt'
        llm models list --filter anthropic # List Anthropic models
        llm models list --details          # Show detailed descriptions
    """
    # Vérifier l'authentification
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        error_panel = Panel(
            "[red]Erreur: Clé API OpenRouter manquante[/red]\n\n"
            "Veuillez définir votre clé API OpenRouter:\n"
            "[cyan]export OPENROUTER_API_KEY=your_api_key_here[/cyan]\n\n"
            "Obtenez votre clé API sur: https://openrouter.ai/keys",
            title="[red]Configuration requise[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)
    
    try:
        # Afficher un indicateur de chargement
        with console.status("[bold green]Récupération des modèles depuis OpenRouter...", spinner="dots"):
            # Créer le provider et récupérer les modèles
            provider = OpenRouterProvider(api_key=api_key)
            all_models = provider.list_models()
        
        # Filtrer les modèles si un filtre est spécifié
        filtered_models = filter_models(all_models, filter_text)
        
        # Vérifier si des modèles ont été trouvés
        if not filtered_models:
            if filter_text:
                console.print(f"[yellow]Aucun modèle trouvé avec le filtre '{filter_text}'[/yellow]")
                console.print(f"[dim]Total de modèles disponibles: {len(all_models)}[/dim]")
            else:
                console.print("[red]Aucun modèle disponible[/red]")
            raise typer.Exit(0)
        
        # Afficher les résultats
        if show_details:
            # Mode détaillé : afficher chaque modèle dans un panel séparé
            for i, model in enumerate(sorted(filtered_models, key=lambda m: m.id.lower())):
                if i > 0:
                    console.print()  # Ligne vide entre les modèles
                
                details = []
                details.append(f"[bold]ID:[/bold] {model.id}")
                details.append(f"[bold]Context:[/bold] {format_context_length(model.context_length)}")
                details.append(f"[bold]Price In:[/bold] {format_price(model.pricing_prompt)}")
                details.append(f"[bold]Price Out:[/bold] {format_price(model.pricing_completion)}")
                
                if model.description:
                    details.append(f"[bold]Description:[/bold]\n{model.description}")
                else:
                    details.append("[bold]Description:[/bold] N/A")
                
                panel = Panel(
                    "\n".join(details),
                    title=f"Model {i+1}/{len(filtered_models)}",
                    border_style="blue",
                    padding=(1, 1),
                )
                console.print(panel)
        else:
            # Mode tableau standard
            table = create_models_table(filtered_models)
            console.print(table)
        
        # Afficher les statistiques
        console.print()
        stats_text = f"[bold green]✓[/bold green] {len(filtered_models)} modèle(s) affiché(s)"
        if filter_text:
            stats_text += f" (filtrés sur '{filter_text}')"
        stats_text += f" sur {len(all_models)} total"
        
        console.print(Panel(
            stats_text,
            border_style="green",
            padding=(0, 1),
        ))
        
    except OpenRouterAuthError as e:
        error_panel = Panel(
            f"[red]Erreur d'authentification:[/red]\n{str(e)}\n\n"
            "[yellow]Vérifiez votre clé API OpenRouter:[/yellow]\n"
            "[cyan]export OPENROUTER_API_KEY=your_api_key_here[/cyan]",
            title="[red]Authentification échouée[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)
        
    except OpenRouterError as e:
        error_panel = Panel(
            f"[red]Erreur lors de la récupération des modèles:[/red]\n{str(e)}\n\n"
            "[dim]Vérifiez votre connexion internet et réessayez.[/dim]",
            title="[red]Erreur API[/red]",
            border_style="red",
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
        )
        console.print(error_panel)
        raise typer.Exit(1)


@models_app.command("info")
def model_info(
    model_id: str = typer.Argument(..., help="Model ID to get detailed information about")
):
    """
    Get detailed information about a specific model.
    
    This command fetches and displays comprehensive information about a single model,
    including all available metadata, pricing, and capabilities.
    
    Examples:
        llm models info openai/gpt-4o-mini
        llm models info anthropic/claude-3-sonnet
    """
    # Vérifier l'authentification
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        error_panel = Panel(
            "[red]Erreur: Clé API OpenRouter manquante[/red]\n\n"
            "Veuillez définir votre clé API OpenRouter:\n"
            "[cyan]export OPENROUTER_API_KEY=your_api_key_here[/cyan]",
            title="[red]Configuration requise[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)
    
    try:
        # Récupérer tous les modèles et chercher celui demandé
        with console.status(f"[bold green]Recherche du modèle '{model_id}'...", spinner="dots"):
            provider = OpenRouterProvider(api_key=api_key)
            all_models = provider.list_models()
        
        # Chercher le modèle spécifique
        target_model = None
        for model in all_models:
            if model.id == model_id:
                target_model = model
                break
        
        if not target_model:
            # Chercher des modèles similaires pour suggestion
            similar_models = [
                model.id for model in all_models
                if model_id.lower() in model.id.lower()
            ]
            
            error_msg = f"[red]Modèle '{model_id}' non trouvé[/red]"
            if similar_models:
                error_msg += "\n\n[yellow]Modèles similaires trouvés:[/yellow]\n"
                for sim_model in similar_models[:5]:  # Limiter à 5 suggestions
                    error_msg += f"  • {sim_model}\n"
            else:
                error_msg += f"\n\n[dim]Utilisez 'llm models list' pour voir tous les modèles disponibles[/dim]"
                
            console.print(Panel(
                error_msg,
                title="[red]Modèle non trouvé[/red]",
                border_style="red",
            ))
            raise typer.Exit(1)
        
        # Afficher les informations détaillées
        details = []
        details.append(f"[bold cyan]Model ID:[/bold cyan] {target_model.id}")
        details.append(f"[bold cyan]Context Length:[/bold cyan] {format_context_length(target_model.context_length)}")
        details.append(f"[bold cyan]Input Price:[/bold cyan] {format_price(target_model.pricing_prompt)}")
        details.append(f"[bold cyan]Output Price:[/bold cyan] {format_price(target_model.pricing_completion)}")
        
        if target_model.description:
            details.append(f"[bold cyan]Description:[/bold cyan]\n{target_model.description}")
        else:
            details.append(f"[bold cyan]Description:[/bold cyan] N/A")
        
        # Calculer des statistiques de coût si les prix sont disponibles
        if target_model.pricing_prompt and target_model.pricing_completion:
            details.append("\n[bold yellow]Cost Estimates (per 1M tokens):[/bold yellow]")
            details.append(f"  • Input: {format_price(target_model.pricing_prompt)}")
            details.append(f"  • Output: {format_price(target_model.pricing_completion)}")
            
            # Estimation pour différents usages typiques
            details.append("\n[bold yellow]Typical Usage Costs:[/bold yellow]")
            
            # Chat simple (1k input, 100 output tokens)
            chat_cost = (1000 * target_model.pricing_prompt + 100 * target_model.pricing_completion)
            details.append(f"  • Simple chat (1k in, 100 out): ${chat_cost:.4f}")
            
            # Document long (10k input, 500 output tokens)
            doc_cost = (10000 * target_model.pricing_prompt + 500 * target_model.pricing_completion)
            details.append(f"  • Long document (10k in, 500 out): ${doc_cost:.4f}")
        
        info_panel = Panel(
            "\n".join(details),
            title=f"[bold green]Model Information: {target_model.id}[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(info_panel)
        
    except OpenRouterAuthError as e:
        error_panel = Panel(
            f"[red]Erreur d'authentification:[/red]\n{str(e)}",
            title="[red]Authentification échouée[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)
        
    except OpenRouterError as e:
        error_panel = Panel(
            f"[red]Erreur API:[/red]\n{str(e)}",
            title="[red]Erreur OpenRouter[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)
        
    except Exception as e:
        error_panel = Panel(
            f"[red]Erreur inattendue:[/red]\n{str(e)}",
            title="[red]Erreur interne[/red]",
            border_style="red",
        )
        console.print(error_panel)
        raise typer.Exit(1)


if __name__ == "__main__":
    models_app()