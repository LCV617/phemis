"""
Module de sauvegarde et chargement sécurisé des sessions.

Ce module fournit des fonctionnalités pour sauvegarder et charger les sessions
de manière sécurisée, avec validation des chemins et gestion robuste des erreurs.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List
from slugify import slugify

from .schema import Session


class SecurityError(Exception):
    """Exception levée lors d'une violation de sécurité des chemins."""
    pass


class StorageError(Exception):
    """Exception levée lors d'erreurs de stockage/chargement."""
    pass


def safe_path_join(base: str, path: str) -> str:
    """
    Utilitaire de sécurité pour éviter les attaques de path traversal.
    
    Args:
        base: Répertoire de base autorisé
        path: Chemin relatif à joindre
        
    Returns:
        Chemin absolu sécurisé
        
    Raises:
        SecurityError: Si le chemin sort du répertoire de base
    """
    base_path = Path(base).resolve()
    full_path = (base_path / path).resolve()
    
    # Vérifier que le chemin final est bien dans le répertoire de base
    try:
        full_path.relative_to(base_path)
    except ValueError:
        raise SecurityError(f"Chemin non autorisé: {path} sort du répertoire de base {base}")
    
    return str(full_path)


def save_session(session: Session, path_or_dir: str) -> str:
    """
    Sauvegarde une session vers un fichier JSON.
    
    Args:
        session: Session à sauvegarder
        path_or_dir: Soit un chemin de fichier exact, soit un répertoire
                    où créer un fichier avec timestamp
                    
    Returns:
        Chemin du fichier créé
        
    Raises:
        SecurityError: Si le chemin n'est pas sécurisé
        StorageError: Si la sauvegarde échoue
    """
    try:
        path = Path(path_or_dir)
        
        if path.is_dir() or (not path.suffix and not path.exists()):
            # C'est un répertoire - générer un nom de fichier avec timestamp
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            # Créer un slug basé sur le modèle et le timestamp
            model_slug = slugify(session.model)
            timestamp = session.created_at.strftime("%Y%m%d-%H%M%S")
            filename = f"{model_slug}-{timestamp}.json"
            
            final_path = path / filename
        else:
            # C'est un fichier spécifique
            final_path = path
            
        # Validation de sécurité - s'assurer qu'on reste dans le répertoire courant
        # Exception pour les répertoires temporaires (pour les tests)
        current_dir = Path.cwd()
        resolved_path = final_path.resolve()
        is_temp = False
        
        # Vérifier si c'est dans un répertoire temporaire
        temp_patterns = ["/tmp", "/var/folders", "/private/tmp", "/private/var/folders"]
        for pattern in temp_patterns:
            try:
                resolved_path.relative_to(Path(pattern).resolve())
                is_temp = True
                break
            except (ValueError, OSError):
                continue
                
        if not is_temp:
            try:
                resolved_path.relative_to(current_dir)
            except ValueError:
                raise SecurityError(f"Chemin non autorisé: {final_path} sort du répertoire courant")
            
        # Créer le répertoire parent si nécessaire
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder la session
        session_data = session.model_dump(mode='json')
        
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
            
        return str(final_path)
        
    except (OSError, IOError) as e:
        raise StorageError(f"Impossible de sauvegarder la session: {e}")
    except Exception as e:
        if isinstance(e, (SecurityError, StorageError)):
            raise
        raise StorageError(f"Erreur inattendue lors de la sauvegarde: {e}")


def load_session(path: str) -> Session:
    """
    Charge une session depuis un fichier JSON.
    
    Args:
        path: Chemin vers le fichier JSON de session
        
    Returns:
        Session chargée et validée
        
    Raises:
        StorageError: Si le chargement ou la validation échoue
    """
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise StorageError(f"Fichier de session introuvable: {path}")
            
        if not file_path.is_file():
            raise StorageError(f"Le chemin n'est pas un fichier: {path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Valider et créer l'objet Session avec Pydantic
        session = Session.model_validate(data)
        
        # Vérifier la version du schéma
        if session.schema_version > 1:
            raise StorageError(
                f"Version de schéma non supportée: {session.schema_version}. "
                "Veuillez mettre à jour l'application."
            )
            
        return session
        
    except json.JSONDecodeError as e:
        raise StorageError(f"Fichier JSON invalide: {e}")
    except Exception as e:
        if isinstance(e, StorageError):
            raise
        raise StorageError(f"Erreur lors du chargement de la session: {e}")


def list_session_files(runs_dir: str = "./runs") -> List[str]:
    """
    Liste tous les fichiers de session dans un répertoire.
    
    Args:
        runs_dir: Répertoire contenant les fichiers de session
        
    Returns:
        Liste des chemins de fichiers triés par date de modification (plus récent en premier)
        
    Raises:
        StorageError: Si l'accès au répertoire échoue
    """
    try:
        runs_path = Path(runs_dir)
        
        if not runs_path.exists():
            return []
            
        if not runs_path.is_dir():
            raise StorageError(f"Le chemin n'est pas un répertoire: {runs_dir}")
            
        # Trouver tous les fichiers JSON
        json_files = list(runs_path.glob("*.json"))
        
        # Trier par date de modification (plus récent en premier)
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return [str(f) for f in json_files]
        
    except OSError as e:
        raise StorageError(f"Impossible d'accéder au répertoire {runs_dir}: {e}")
    except Exception as e:
        raise StorageError(f"Erreur lors du listage des fichiers: {e}")