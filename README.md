# Wishlistor

Application desktop (PySide6) de gestion de fichiers CSV : ouverture fluide de fichiers de
50 000 lignes, tri/filtrage instantanés, tags, commentaires, colonnes de rang calculées,
projets et historique d'annulation.

---

## Prérequis

- **Python 3.14** (minimum 3.13) — [python.org](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- **VS Code** (recommended) — [code.visualstudio.com](https://code.visualstudio.com/)
- **Terminal** — PowerShell, Command Prompt, bash, zsh, ...

---

## Installation

/!\ Le dossier 'src/' doit être visible. /!\

```powershell
# 1. Créer et activer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Linux / macOS

# 2. Installer le projet et ses dépendances (pyproject.toml fait foi)
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

---

## Lancement

```powershell
python -m wishlistor.main
```

Sous Windows, `LAUNCHME.bat` fait la même chose (active la venv puis lance le module).

---

## VS Code Setup

### Extensions

Installer les extensions via le marketplace (`Ctrl+Shift+X`):

| Extension | Publisher | Purpose |
|-----------|-----------|---------|
| **Python** | Microsoft | Python language support |
| **BasedPyright** | detachhead | Replace pylance |
| **Ruff** | Astral Software | Linter & formatter |
| **Python CodeLens** | Prasad G K | References count |
| **vscode-icons** | VS Code Teams | Enhanced IDE

Récupérer la font 'JetBrains Mono :
https://www.jetbrains.com/fr-fr/lp/mono/

### Settings

Ouvrir les settings (`Ctrl+Shift+P` → *Open User Settings JSON*) et ajouter :

```json
{
    "github.copilot.nextEditSuggestions.enabled": true,
    "git.ignoreMissingGitWarning": true,
    "editor.minimap.renderCharacters": false,
    "powershell.promptToUpdatePowerShell": false,
    "python.createEnvironment.trigger": "off",

    // --- Ruff: linter & formatter ---
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    // plugins
    "workbench.iconTheme": "vscode-icons",
    "editor.fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', monospace",
    "chat.viewSessions.orientation": "stacked",
    "chat.tools.terminal.autoApprove": {
        "/^ruff check \\./src/$/": {
            "approve": true,
            "matchCommandLine": true
        }
    },
    "claudeCode.initialPermissionMode": "bypassPermissions",
    "claudeCode.useCtrlEnterToSend": true,
    "claudeCode.preferredLocation": "panel",
    "claudeCode.allowDangerouslySkipPermissions": true,
    "terminal.integrated.stickyScroll.enabled": false,
    "basedpyright.analysis.typeCheckingMode": "standard",
    "js/ts.referencesCodeLens.showOnAllFunctions": true,
    "basedpyright.analysis.inlayHints.callArgumentNames": false,
    "basedpyright.analysis.inlayHints.functionReturnTypes": false,
    "basedpyright.analysis.inlayHints.genericTypes": false,
    "basedpyright.analysis.inlayHints.variableTypes": false
}
```

---

## Structure du projet

```
src/wishlistor/
├── models/         # Entités métier (document CSV, projets, options, états de vue)
├── views/          # Composants PySide6 (aucune logique métier)
├── presenters/     # Orchestration Vue ⇄ Service (aucun import PySide6)
├── services/       # Règles métier (CSV, rangs, projets, options, undo/redo)
├── repositories/   # Seule couche autorisée à faire de l'I/O (CSV, JSON, logs)
├── interfaces/     # Contrats typing.Protocol entre couches
├── shared/         # Enums, codes d'erreur, exceptions, i18n (français), utilitaires
└── main.py         # Point d'entrée et composition root
tests/              # Suite pytest, miroir de src/wishlistor/
```

Les règles d'architecture, de nommage et de style sont définies dans [AGENTS.md](AGENTS.md).

### Fichiers runtime

Sont écrits par les Repositories uniquement :
- `./config-wishlistor.json` — options globales, projets, historique ;
- `./tmp_app_logs/` — journaux avec rotation.

---

## Test — Pytest

```bash
pytest
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Qualité / Outils

Les outils sont configurés dans `pyproject.toml`.

### Ruff — linter & formatter

```bash

# install
pip install ruff

# Check for issues
ruff check ./src/

# Auto-fix what can be fixed
ruff check --fix ./src/

# Format code
ruff format ./src/
```

### Custom furripe (Ruff homemade)

```bash

# custom
pip install mccabe
python ./tools/furripe.py
```

### Basedpyright — Analyse de typage statique

```bash
pip install basedpyright
basedpyright
```

---

## Nettoyage du projet

Remove compiled Python files (`__pycache__`, `.pyc`, etc.):

```bash
python -m pip install pyclean
python -m pyclean ./ -v
```

---

## A lire 

- `AGENTS.md` — architecture, règles, conventions, instructions pour agent IA
- `pyproject.toml` — configuration complète + réglage Ruff et Pytest
