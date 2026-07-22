
Contexte :
Je suis développeur python et je vais réaliser une application desktop avec PySide6 et python 3.14.

Objectif :
Aide moi à créer le ficheir AGENTS.md qui va servir à cadrer tout le projet.

Consignes :
- Le fichier AGENTS.md se doit d'être qualitatif et respecter les bonnes pratiques en termes de projets, d'architecture et de développements.
- Il est à écrire en anglais, et doit lister les bon usages, et interdire les mauvais.
- Aucun français autorisé (sauf si règle explicite à ce sujet).

Pour t'aider à faire le fichier AGENTS.md, je vais te lister ce que je sais et ce que j'aimerais avoir.
A toi d'extrapoler et consolider pour sortir le fichier AGENTS.md adéquat.

Une fois terminé, vérifie la cohérence, et fait le bilan de ce qu'il est possible d'améliorer.
 
# Description du projet

Nom : Wishlistor
Est un tableur qui permet de manipuler des CSV.
Est basé sur PySide6 et Python 3.14.

# Architecture

Le projet suit l'architecture :
View, Presenter, Service, Repository, Model.

# Organisation du code source

```
src/
├── models/         # Business entities and data structures (domain)
├── views/          # GUI components
├── presenters/     # Orchestration: wires ViewModel callbacks to services
├── repositories/   # Data read/write layer (files, JSON, ...)
├── services/       # Business logic and domain rules
├── interfaces/     # Protocol-based contracts
├── shared/         # Cross-cutting utilities (enums, i18n, helpers)
└── main.py         # Application entry point and composition root
```

### Rôles

Définit les rôles de chaque couche de l'architecture.
Quel couche doit avoir la responsabilité de quoi.
Déterminer comment organiser ou déplacer le code en fonction de la situation.

### MVP + Règles

Définit les règles de chacune des couches.
Ce qu'il peut faire (GOOD), ce qui est interdit (BAD).
Mapping des dépendances : Liste les imports autorisés et dans quel sens.
Ce qu'il peut importer et ce qu'il ne doit jamais importer.

---

## Convention de nommage

| Dossier          | Suffixe         | Example                                   |
|-----------------|---------------------|----------------------------------------|
| `models/`       | `_model.py`         | `vendor_model.py` 					 |
| `services/`     | `_service.py`       | `vendor_service.py`                  |
| `repositories/` | `_repository.py`    | `config_repository.py`                 |
| `presenters/`   | `_presenter.py`     | `executor_presenter.py`                |
| `views/`        | `_view.py`          | `warehouse_edit_view.py`                |
| `interfaces/`   | `i_*.py`            | `i_vendor_view.py`                   |

Cas particulier : dossier 'shared'
- Les fichiers qui regroupent les outils doivent être suffixé '_util.py'.
- Les fichiers qui regroupent les codes d'erreurs doivent être suffixé '_error.py'

Une classe est toujour écrite en PascalCase (ex. `<Module>View`).
Le nom de fichier doit être écrit en snake_case (ex. `warehouse_edit_view.py`).
Lien entre classe et fichier : `warehouse_edit_view.py` → `WarehouseEditView`).

| élément | Convention | Exemple |
|---|---|---|
| Any vars in view | suffix `_var` | `url_var`, `is_busy_var`, `can_submit_var` |
| Capability / boolean Var | `can_<x>` / `is_<x>` | `can_submit`, `is_dirty` |
| Action method (called by View) | imperative verb | `submit()`, `cancel()`, `open_selected()` |
| Presenter binding hook | prefix `bind_` | `bind_submit(cb)`, `bind_rows_changed(cb)` |
| Stored Presenter callback | prefix `_on_` | `self._on_submit` |
| Read-only snapshot type | `<Module>ViewState` (frozen) | `WarehouseEditViewState` |
| Collection row type | `<Thing>RowState` (frozen) | `WarehouseRowState` |

# enum

Tous les enums sont à ranger dans `src/shared/enums/`

Et doivent toujours être préfixé de 'E_' et posséder un état 'E_UNSET' et 'E_UNKNOWN' 

Exemple :

```
class FilterClosedEnum(Enum):
    """Enumerates the modes for determining the URL to open in an OPEN_URL step."""

    E_UNSET = "UNSET"
    E_ENUM1 = "..."
    E_ENUM2 = "..."
    E_ENUM3 = "..."
    E_UNKNOWN = "UNKNOWN"
```

## Python Version

Le projet cible Python 3.14 (et à minima 3.13 et plus)
Python 2 est strictement interdit.

## Environnement & Installation

Définir :
- Environnement virtuel avec 'venv' + activation
- Installer les dépendances (install, requirements).
- Déployer le projet (fichier toml, etc.).
- Comment lancer l'application.
- Nettoyer le projet : python -m pyclean ./ -v
- Basedpyright — static type checking
- Ruff (linter/formatter)

## Fichier temporaire au runtime

| Chemin                          | Description                          |
|-------------------------------|--------------------------------------|
| `./tmp_app_logs/`             | Temporary execution logs             |
| `./config-wishlistor.json`     | Main application configuration       |

---

## Language

| Contenu                   | Language                              | Exemple                                       |
|---------------------------|---------------------------------------|-----------------------------------------------|
| Docstrings                | **English**                           | `"""Load the warehouse from disk."""`          |
| Inline comments           | **English**                           | `# Extract the main result blocks`            |
| Log messages (all levels) | **French**                            | `"Démarrage du vendor pour id=%s"`          |
| Exception messages        | **French**                            | `"vendor introuvable : {id}"`               |
| User-facing strings       | **French** — via `shared/i18n_fra.py` only | `ERROR_TEMPLATES["empty_field"]`         |

`shared/i18n_fra.py` et `shared/errors/*_error.py` sont les fichiers sources à priviléger pour l'affichage français des strings.

# Ordre des imports

Toujours **isort**, forcé via `ruff --select I`:

```python
# 1. Standard library
# 2. Third-party
# 3. Local application
```

Lancer `ruff check --select I --fix` avant de commit.

# Style général des commentaires

- Strictement conforme à **PEP 8**
- **Docstrings** requis pour les classes publiques et les fonctions.
- **Google style**, en **English**.
- **Inline comments** en **English**.

Un Docstring doit toujours être composés de :
- Description
- Args
- Returns
- Raises

# Interfaces

Toutes les interfaces sont définies par `typing.Protocol` dans `interfaces/`.
Ne jamais utiliser `ABC` dans les interfaces.
`ABC` autorisé pour faciliter un binding sur une fonction.

# Dépendance et injection

Ne jamais instancier un Service, un Repository, un Presenter à l'intérieur d'un autre.
Tous les objets concrets sont assemblés une seule fois dans `main.py` et injectés via `init`.

La racine de composition dans `main.py` conserve également une référence à chaque instance afin qu'elle ne soit pas supprimée par le ramasse-miettes
Elle gère également la séquence de suppression des ressources lorsqu'une vue est supprimée.

# L'état partagé

L'application possède 2 classes partagés par tous, via un singleton.
Ces 2 Models sont les seuls a avoir cette particularié.

`AppConfigModel` :
Le Model pour le fichier de configuration. est accessible par tous via un singleton.

`AppStateModel` :
Une classe qui encapsule les informations basiques du cycle de vie global de l'application :
- La view principale actuellement active
- Des flags pour savoir si l'application est : 'is_busy', 'is_loading' et 'is_dirty'. Ces flags sont globaux et fonctionne de concert avec les autres flags (surtout ceux dans la view)

# niveau de log par couche

- Utilise `logging` pour la journalisation.
- Une référence '_logger' par classe.

| Couche        | Niveau    | Cible                                                |
|--------------|------------------|----------------------------------------------------------|
| `Repository` | `DEBUG`          | Low-level I/O details, useful for tracing.               |
| `Service`    | `DEBUG`, `INFO`  | Business flow steps.                                     |
| `Presenter`  | `ERROR`          | Unexpected failures caught before being shown to the user. |
| `View`       | `INFO`           | Bouton principaux.     |

- Toujours utiliser `%s` dans le formattage des logs (pas de f-strings).
- Ne jamais log des données sensibles.
- Toujours log la durée écoulé lorsque l'on clique sur un bouton.

# Gestion des erreurs

Les exceptions : Elle sont à ranger dans le dossier `shared/exceptions/'
Les codes d'erreurs sont à ranger dans `shared/errors/`

L'exception doit rester exceptionnel.
La remonter d'erreur doit privilégier l'utilisation de la classe 'ValidationResult' de `/shared/validation_result.py` et des classes 'ErrorCodeXXX' dans `shared/errors/`

Exemple avec ErrorCodeYYD (qui hérite de 'ErrorCode')

```
class ErrorCodeYYD(ErrorCode):
    """Error codes for YoutubeYubDownload"""

    # wrong
    YYD_1001 = "Vidéo indisponible (impossible à joindre)."
    YYD_1002 = "Vidéo soumis à une restriction d'âge (il faut s'identifier)."

    # ???
    YYD_9999 = "Erreur inconnue."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeYYD | None:
        """Simplify the error message for logging."""

        # when ...
        if excp isinstance [...]:
            return ErrorCodeYYD.YYD_1005

		# no conversion
        return None
```

### Who raises, who catches

Définir selon les couches, qui remonte l'erreur, la gère, l'affiche.

## Tests

Lors de l'ajout d'un tests :
- privilégier un tests unitaires (aka TU) pour tester un élément précis.
- privilégier les tests de non-régression (aka TNR) pour fichier les comportements.
- Ils sont à placer dans `tests/`
- Utilise 'pytest'

# Bonne pratique

Principe de code :
- KISS (Keep it Simple, Stupid)
- SOLID (Single Responsibility, Open/Closed, Liskov’s Substitution, Interface Segregation, Dependency Inversion)

# Code

## Couche 'Repository'

- Seule couche autorisé à pouvoir lire/écrire les données et ouvrir les fichiers.
- En dehors d'un repository, les autres classes ont interdiction de faire des 'open' pour lire un fichier ou une donnée externe.
- Gérer le cache des données et ne pas relire inutilement un fichier ou une donnée externe.

## Couche Model :

Ne jamais avoir une collection de model.
Toujours passer par un model qui encapsule la collection.

Une collection de models (une liste de XXXModel par exemple), doit toujours disposer :
- d'une surcharge pour l'itérateur
- Des properties get/set, et garder les variables en private.
- Des opérations de bases d'un CRUD (create, read, update, delete)
- des opérations pour 'search' ou 'batch' des actions en groupe. 
- Une méthode 'get_default' qui retourne un objet déjà initialisé par défaut.
- Méthode pour 'désérialiser' et 'sérialiser' la collection.
- Méthode 'mark_as_created' et 'mark_as_modified' pour définit les dates de création/modifications.
- Posséder une méthode 'validate(context: object | None = None)' et qui retourne un 'ValidationResult' pour valider l'objet.
- Une méthode 'copy' avec en paramètre un enum [E_BUSINESS, E_TECHNICAL] pour demander une copie fonctionnelle ou une copie technique identique.
- Une méthode 'clear' pour remettre l'instance de la classe à zéro.

Un Model doit toujours disposer :
- d'une variable 'id_xxxx' qui représente un identifiant unique.
- Des properties get/set, et garder les variables en private.
- Posséder une méthode 'validate(context: object | None = None)' et qui retourne un 'ValidationResult' pour valider l'objet.
- Des méthodes 'to_dict', 'from_dict' pour manipuler l'objet et faciliter son interfaçage avec les autres classes.
- Une méthode 'get_default' qui retourne un objet initialisé par défaut.
- Méthode 'mark_as_created' et 'mark_as_modified' pour définit les dates de création/modifications.
- Une méthode 'copy' avec en paramètre un enum [E_BUSINESS, E_TECHNICAL] pour demander une copie fonctionnelle ou une copie technique identique.
- Une méthode 'clear' pour remettre l'instance de la classe à zéro.
- fieldnames -> retourne toutes les clés/attributs (pas les valeurs)

## Couche Service

La couche service doit toujours disposer :
- D'une méthode statique permettant de générer un identifiant unique pour l'entité métier qu'il manipule.

## Couche View

La couche view doit toujours disposer :
- Une méthode 'snapshot' qui permet à la couche 'Presenter' de convertir les données dans la GUI en model exploitable.
- Une méthode 'set_enabled' pour griser le composant.
- Une méthode 'notify_error' qui permet au 'Presenter' de notifier l'erreur (soit afficher une popup, mettre un jour un label, etc.)
- Une méthode 'clear' qui vide les valeurs en mémoire dans la GUI.
- Une méthode 'notify_refresh' qui prends en paramètre un 'context: object' et rafraichit l'IHM en conséquence.
- Un flag 'is_dirty' qui est set à 'True' lorsque l'utilisateur fait une modification en écriture d'une donnée (texte dans un champs libre, choix dans une liste déroulante) et qui change le model.
- Un flag 'is_busy' et qui set à 'True' lorsqu'un calcul est demandé ou que l'utilisateur a déclenché un processus.
- Un flag 'is_loading' qui est set à 'True' lorque l'IHM charge des données ou construit la view, afin de ne pas recalculer en cascade des changements de formulaire et de n'avoir qu'une seule passe en sortie.

Comportements à privilégier
- Chaque bouton cliqué, doit log une ligne dans le journal et indiqué la durée écoulé en milli-sec. 
- Privilégier le chargement lazy pour la view.
- la view doit favoriser la validation en temps réel et maximiser le feedback à l'utilisateur.
