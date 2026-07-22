# AGENTS.md — Wishlistor

> **Purpose of this file**: This document is the single source of truth for how code is written, organized, and reviewed in this project. Any agent (human or AI) contributing code MUST comply with every rule below. When a rule says **BAD / FORBIDDEN**, it is non-negotiable.

---

## 1. Project Overview

- **Name**: Wishlistor
- **Description**: A desktop spreadsheet application for manipulating CSV files.
- **UI framework**: **PySide6** (Qt for Python).
- **Language**: Python **3.14** (minimum supported: **3.13**).
- **FORBIDDEN**: Python 2 syntax, `six`, `__future__` compatibility shims, Tkinter, PyQt5/PyQt6, wxPython, or any other GUI toolkit. PySide6 is the only allowed UI framework.

---

## 2. Architecture — MVP (Model / View / Presenter) + Service + Repository

The project follows a strict layered architecture:

```
View  ⇄  Presenter  → →  Service  → →  Repository
                  ↘        ↓            ↓
                    ↘      ↓            ↓
                       Model (shared by all layers)
```

### 2.1 Source layout

The project uses the standard Python **src layout** (`src/wishlistor/` is the importable package):

```
src/
└── wishlistor/
    ├── models/         # Business entities and data structures (domain)
    ├── views/          # GUI components (no business logic)
    ├── presenters/     # Orchestration: wires View callbacks to Services
    ├── repositories/   # Data read/write layer (files, JSON, CSV, ...)
    ├── services/       # Business logic and domain rules
    ├── interfaces/     # Protocol-based contracts
    ├── shared/         # Cross-cutting utilities (enums, i18n, errors, helpers)
    │   ├── enums/          # All application enums
    │   ├── errors/         # ErrorCode classes (*_error.py)
    │   ├── exceptions/     # Custom exception classes
    │   └── i18n_fra.py     # French user-facing strings
    └── main.py         # Application entry point and composition root
```

Tests live outside the source tree:

```
tests/              # pytest test suite (TU + TR)
```

**FORBIDDEN**: double-underscore folder names (`__src__/`, `__tests__/`) — dunder-style names are visually reserved for Python special attributes and break standard packaging conventions.

### 2.2 Layer roles and responsibilities

| Layer | Responsibility | Owns |
|---|---|---|
| **Model** | Pure data + validation. Represents domain entities and their invariants. | State, serialization, validation, identity. |
| **View** | Rendering only. Displays data, collects raw user input, exposes callbacks. **Passive** — it never decides anything. | Widgets, layouts, visual feedback, `snapshot()`. |
| **Presenter** | Orchestration. Reacts to View callbacks, calls Services, pushes results back into the View. | Application flow, error presentation, wiring. |
| **Service** | Business logic and domain rules. Stateless whenever possible. | Computation, transformation, business validation, ID generation. |
| **Repository** | The **only** layer allowed to perform I/O (files, JSON, CSV, network, ...). | Reading, writing, caching, persistence format. |
| **Interfaces** | `typing.Protocol` contracts that decouple layers. | Method signatures only — zero implementation. |
| **Shared** | Cross-cutting concerns with no business logic: enums, error codes, exceptions, i18n, small helpers. | Utilities used by every layer. |

**How to place new code ("Where do I put the code?"):**

- "It draws something / reacts to a click" → `views/`
- "It decides what happens after a click" → `presenters/`
- "It computes, transforms, or applies a business rule" → `services/`
- "It opens, reads, writes, or caches data" → `repositories/`
- "It is a data structure with identity and validation" → `models/`
- "It is a contract between two layers" → `interfaces/`
- "Two or more layers need it and it has no business logic" → `shared/`
- If a class does two of the above at once → **split it**.

### 2.3 Dependency mapping — allowed imports

Dependencies flow **in one direction only**. An arrow means "may import".

| Layer | MAY import | MUST NEVER import |
|---|---|---|
| `views/` | `models/` (read-only state types), `shared/`, `interfaces/`, PySide6 | `presenters/`, `services/`, `repositories/` |
| `presenters/` | `interfaces/`, `models/`, `services/` (via interfaces), `shared/` | `views/` concrete classes (use `i_*_view` Protocols), `repositories/` directly, PySide6 |
| `services/` | `models/`, `repositories/` (via interfaces), `interfaces/`, `shared/` | `views/`, `presenters/`, PySide6 |
| `repositories/` | `models/`, `interfaces/`, `shared/` | `views/`, `presenters/`, `services/`, PySide6 |
| `models/` | `shared/`, `interfaces/` | `views/`, `presenters/`, `services/`, `repositories/`, PySide6 |
| `interfaces/` | `models/`, `shared/`, stdlib `typing` | Any concrete layer implementation |
| `shared/` | stdlib, other `shared/` modules | Everything else — `shared/` sits at the bottom of the dependency graph |
| `main.py` | Everything (composition root) | — |

**GOOD**
- A Presenter depends on `IScrapingView` and `IScrapingService` Protocols.
- A Service receives a Repository through its constructor.
- A View imports a frozen `ScenarioEditViewState` from `models/` to render it.

**BAD / FORBIDDEN**
- A View importing a Service or Repository "just to save time".
- A Service importing PySide6 (e.g., to show a `QMessageBox`).
- A Repository calling a Service (circular logic).
- Two Presenters importing each other.
- Anything in `shared/` importing from `models/`, `services/`, etc.

---

## 3. Naming Conventions

### 3.1 Files and classes

| Folder | File suffix | Example |
|---|---|---|
| `models/` | `_model.py` | `provider_model.py` |
| `services/` | `_service.py` | `scraping_service.py` |
| `repositories/` | `_repository.py` | `config_repository.py` |
| `presenters/` | `_presenter.py` | `executor_presenter.py` |
| `views/` | `_view.py` | `scenario_edit_view.py` |
| `interfaces/` | `i_*.py` prefix | `i_scraping_view.py` |
| `shared/` (utilities) | `_util.py` | `path_util.py` |
| `shared/errors/` | `_error.py` | `csv_error.py` |

- Classes are always **PascalCase**: `<Module>View`, `<Module>Service`, ...
- File names are always **snake_case**.
- File ↔ class mapping is 1:1 and deterministic: `scenario_edit_view.py` → `ScenarioEditView`.
- Interface classes carry the `I` prefix: `i_scraping_view.py` → `IScrapingView`.

### 3.2 Members and identifiers

| Element | Convention | Example |
|---|---|---|
| Any variable bound to a widget in a View | suffix `_var` | `url_var`, `is_busy_var`, `can_submit_var` |
| Capability / boolean flag | `can_<x>` / `is_<x>` | `can_submit`, `is_dirty` |
| Action method (called by the View) | imperative verb | `submit()`, `cancel()`, `open_selected()` |
| Presenter binding hook (exposed by the View) | prefix `bind_` | `bind_submit(cb)`, `bind_rows_changed(cb)` |
| Stored Presenter callback | prefix `_on_` | `self._on_submit` |
| Read-only snapshot type | `<Module>ViewState` (frozen dataclass) | `ScenarioEditViewState` |
| Collection row type | `<Thing>RowState` (frozen dataclass) | `ScenarioRowState` |
| Private attribute | leading underscore | `self._rows` |
| Logger reference | `self._logger` | one per class |

### 3.3 Enums

- **All** enums live in `src/wishlistor/shared/enums/`.
- Every member is prefixed with `E_`.
- Every enum MUST define both `E_UNSET` (initial / not-yet-chosen state) and `E_UNKNOWN` (unrecognized value, e.g., after deserialization of foreign data).

```python
class FilterClosedEnum(Enum):
    """Enumerates the modes for determining the URL to open in an OPEN_URL step."""

    E_UNSET = "UNSET"
    E_MODE_A = "MODE_A"
    E_MODE_B = "MODE_B"
    E_UNKNOWN = "UNKNOWN"
```

**BAD**: defining an enum inside a view/service module, omitting `E_UNSET`/`E_UNKNOWN`, unprefixed members.

---

## 4. Python Version & Tooling

- Target: **Python 3.14**. Minimum: **3.13**. Anything below is FORBIDDEN.
- Use modern typing everywhere: `X | None`, `list[str]`, `Self`, `typing.Protocol`. Never `Optional[X]`, `List[str]`, or `typing.Union`.
- In Python 3.14, `except` without parentheses is valid (PEP 758); you must used `except A, B:` over `except (A, B):`.

### 4.1 Environment & installation

```bash
# 1. Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 2. Install the project and its dependencies (pyproject.toml is the source of truth)
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

# 3. Run the application
python -m wishlistor.main

# 4. Clean the project (bytecode, caches)
python -m pyclean ./ -v
```

- **`pyproject.toml`** is the single source of truth for dependencies, project metadata, and tool configuration (Ruff, basedpyright, pytest). A pinned `requirements.txt` may be generated from it for reproducible deployments, but is never edited by hand.
- **FORBIDDEN**: installing packages globally, editing `requirements.txt` manually, `setup.py`.

### 4.2 Static analysis

| Tool | Role | Command |
|---|---|---|
| **basedpyright** | Static type checking (strict mode) | `basedpyright src/` |
| **Ruff** | Linter + formatter + import sorting | `ruff check --fix . && ruff format .` |
| **Furripe** | Custom Ruff (homemade) | `python ./tools/furripe.py --fix . && python ./tools/furripe.py` |

- Every function signature MUST be fully type-annotated (parameters and return type).
- Code that does not pass basedpyright and Ruff and Furripe MUST NOT be committed.

### 4.3 Import order

Enforced by isort rules through Ruff (`ruff --select I`):

```python
# 1. Standard library
# 2. Third-party
# 3. Local application
```

Run `ruff check --select I --fix` before committing.

---

## 5. Runtime Files

| Path | Description |
|---|---|
| `./tmp_app_logs/` | Temporary execution logs |
| `./config-wishlistor.json` | Main application configuration |

- Only Repositories may read/write these files.
- **FORBIDDEN**: writing runtime files anywhere else, hardcoding absolute paths.

---

## 6. Language Policy

| Content | Language | Example |
|---|---|---|
| Docstrings | **English** | `"""Load the scenario from disk."""` |
| Inline comments | **English** | `# Extract the main result blocks` |
| Log messages (all levels) | **French** | `"Démarrage du scraping pour id=%s"` |
| Exception messages | **French** | `"Provider introuvable : {id}"` |
| User-facing strings | **French** — via `shared/i18n_fra.py` only | `ERROR_TEMPLATES["empty_field"]` |
| Identifiers (classes, methods, variables) | **English** | `load_scenario()` |

- `shared/i18n_fra.py` and `shared/errors/*_error.py` are the **only** sources for French display strings.
- **FORBIDDEN**: hardcoding a French string inside a View, Presenter, or Service; writing docstrings or comments in French; mixing languages within one category.

---

## 7. Comments & Docstrings

- Strictly **PEP 8** compliant.
- Docstrings are **required** for all public classes and functions.
- **Google style**, written in **English**.
- A docstring MUST contain, when applicable:
  - Description
  - `Args:`
  - `Returns:`
  - `Raises:`

```python
def load_scenario(self, scenario_id: str) -> ScenarioModel:
    """Load a scenario from the repository.

    Args:
        scenario_id: Unique identifier of the scenario.

    Returns:
        The fully hydrated scenario model.

    Raises:
        ScenarioNotFoundError: If no scenario matches the identifier.
    """
```

**BAD**: commented-out dead code, comments that paraphrase the code (`i += 1  # increment i`), TODOs without an owner.

---

## 8. Interfaces

- All interfaces are defined with **`typing.Protocol`** and live in `interfaces/`.
- **FORBIDDEN**: using `ABC` / `abc.abstractmethod` to define an interface contract.
- Exception: `ABC` is allowed as a small implementation helper to facilitate binding on a function (e.g., a base class providing a default hook) — never as the published contract between layers.

```python
class IScrapingView(Protocol):
    def snapshot(self) -> ScrapingViewState: ...
    def notify_error(self, message: str) -> None: ...
    def bind_submit(self, callback: Callable[[], None]) -> None: ...
```

---

## 9. Dependency Injection & Composition Root

- **FORBIDDEN**: instantiating a Service, Repository, ViewModel, or Presenter inside another one.
- All concrete objects are assembled **exactly once** in `main.py` (the composition root) and injected through `__init__` parameters.
- The composition root also:
  - keeps a reference to every created instance so it is never garbage-collected;
  - owns the **teardown sequence** when a view is destroyed (disconnect signals, release resources, then drop references — in that order).

**GOOD**
```python
# main.py
config_repository = ConfigRepository()
scraping_service = ScrapingService(config_repository)
scraping_view = ScrapingView()
scraping_presenter = ScrapingPresenter(scraping_view, scraping_service)
```

**BAD**
```python
class ScrapingPresenter:
    def __init__(self) -> None:
        self._service = ScrapingService(ConfigRepository())  # FORBIDDEN
```

---

## 10. Shared Application State

Two classes are shared across the whole application:

### `AppConfigModel`
- Model of `./config-wishlistor.json`.
- Exposed as a **singleton** — the single tolerated exception to the DI rule, because configuration must be readable from anywhere. It remains read-mostly; only its dedicated Repository writes it back.

### `AppStateModel`
- Encapsulates the global application lifecycle:
  - the currently active main View;
  - global flags: `is_busy`, `is_loading`, `is_dirty`.
- These global flags work **in concert** with the per-View flags of the same name: a View flag going `True` propagates to the global flag; the global flag returns to `False` only when no View holds it.
- Injected via the composition root like any other dependency.

---

## 11. Logging

- Use the standard `logging` module. One `self._logger` reference per class:
  `self._logger = logging.getLogger(self.__class__.__name__)`

| Layer | Levels | Target content |
|---|---|---|
| `Repository` | `DEBUG` | Low-level I/O details, useful for tracing. |
| `Service` | `DEBUG`, `INFO` | Business flow steps. |
| `Presenter` | `INFO`, `ERROR` | `INFO`: user actions (button clicks) with elapsed time. `ERROR`: unexpected failures caught before being shown to the user. |
| `View` | — | No logging. Views stay passive; action logging belongs to the Presenter handling the click. |

**Rules**
- Always use `%s` lazy formatting in log calls. **FORBIDDEN**: f-strings or `.format()` inside `logging` calls.
- **FORBIDDEN**: logging sensitive data (credentials, tokens, personal data, full file contents).
- Every main button click MUST produce exactly one log line including the elapsed duration in milliseconds, emitted by the Presenter:
  `self._logger.info("Action 'submit' terminée en %s ms", elapsed_ms)`
- Log messages are written in **French** (see §6).

---

## 12. Error Handling

### 12.1 Where things live

| Artifact | Location |
|---|---|
| Custom exception classes | `shared/exceptions/` |
| Error code classes (`ErrorCodeXXX`) | `shared/errors/` (files suffixed `_error.py`) |
| `ValidationResult` | `shared/validation_result.py` |

### 12.2 Philosophy

- **Exceptions must remain exceptional.** They signal broken invariants and unrecoverable states — never ordinary control flow.
- Expected failures (invalid input, missing entity, business rule violation) are reported through **`ValidationResult`** carrying **`BaseErrorCode`** values, returned as normal values.

Example error code class:

```python
class ErrorCodeYYD(BaseErrorCode):
    """Error codes for YoutubeYubDownload."""

    # wrong
    YYD_1001 = "Vidéo indisponible (impossible à joindre)."
    YYD_1002 = "Vidéo soumise à une restriction d'âge (il faut s'identifier)."
    # ???
    YYD_9999 = "Erreur inconnue."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeYYD | None:
        """Map a raw exception to a known error code, if possible."""
        if isinstance(excp, SomeVendorError):
            return ErrorCodeYYD.YYD_1001
        # no conversion
        return None
```

### 12.3 Who raises, who catches, who displays

| Layer | Raises | Catches | Displays |
|---|---|---|---|
| `Repository` | Technical exceptions (I/O, parsing) wrapped into project exceptions from `shared/exceptions/`. | Vendor/stdlib exceptions, re-raised as project exceptions. Never swallows silently. | Never. |
| `Service` | Business exceptions only when an invariant is truly broken. Returns `ValidationResult` for expected failures. | Repository exceptions it can convert into an `ErrorCode` (via `try_simplify_exception`). | Never. |
| `Presenter` | Nothing (a raise here is a bug). | **Everything.** Last line of defense: catches all exceptions, logs at `ERROR`, converts to a user message. | Decides *what* to show; delegates *how* to the View via `notify_error()`. |
| `View` | Nothing. | Nothing. | Renders the message given by the Presenter (popup, label, ...). |
| `Model` | Nothing from `validate()` — validation returns a `ValidationResult`. | — | Never. |

**FORBIDDEN**
- `except Exception: pass` (silent swallowing) anywhere.
- Raising exceptions for expected business outcomes.
- A View catching exceptions or building error text itself.
- Displaying a raw exception message to the user — always go through `ErrorCode` / `i18n_fra.py`.

---

## 13. Layer Contracts

### 13.1 Repository layer

- The **only** layer allowed to read/write data and open files.
- Outside a Repository, **any** call to `open()`, `pathlib.Path.read_text()`, `json.load()` on files, or any external data access is **FORBIDDEN**.
- Repositories manage a **cache**: never re-read a file or external resource that has not changed. Provide an explicit invalidation method (`invalidate_cache()`).

### 13.2 Model layer

- **FORBIDDEN**: passing around a bare collection of models (`list[XxxModel]`). Always wrap the collection in a dedicated collection model (`XxxCollectionModel`).

**Every Model MUST provide:**
- `id_xxxx`: a unique identifier attribute.
- Private attributes with get/set **properties** (no public bare attributes).
- `validate(context: object | None = None) -> ValidationResult`.
- `to_dict()` / `from_dict()` for serialization and interfacing.
- `get_default()` (classmethod) returning a fully initialized default instance.
- `mark_as_created()` / `mark_as_modified()` maintaining creation/modification timestamps.
- `copy(mode: CopyModeEnum)` where the enum offers `E_BUSINESS` (functional copy, new identity) and `E_TECHNICAL` (identical clone).
- `clear()` resetting the instance to its default state.
- `fieldnames` returning all keys/attribute names (not values).

**Every Collection Model MUST provide, in addition:**
- `__iter__` (and ideally `__len__`, `__getitem__`).
- Private storage with get/set properties.
- Basic **CRUD** operations (create, read, update, delete).
- `search(...)` and batch operations for group actions.
- `serialize()` / `deserialize()` for the whole collection.
- `get_default()`, `mark_as_created()`, `mark_as_modified()`, `validate(context)`, `copy(mode)`, `clear()` — same semantics as a single Model.

### 13.3 Service layer

- Every Service MUST expose a **static method** generating a unique identifier for the business entity it manipulates (e.g., `ScenarioService.generate_id() -> str`).
- Services are stateless whenever possible; state belongs in Models.

### 13.4 View layer

**Every View MUST provide:**
- `snapshot()` — converts the current GUI content into an exploitable state object for the Presenter.
- `set_enabled(enabled: bool)` — greys out / re-enables the component.
- `notify_error(rs: ValidationResult)` — lets the Presenter surface an error (popup, label update, ...).
- `clear()` — empties the in-memory GUI values.
- `notify_refresh(context: object)` — refreshes the UI according to the given context.
- `is_dirty` flag — set to `True` when the user makes a data-changing edit (free text, combo selection, ...).
- `is_busy` flag — set to `True` when a computation is requested or the user triggered a process.
- `is_loading` flag — set to `True` while the UI is loading data or building itself, so cascading form-change recomputations are suppressed and only one final pass happens.

**Preferred behaviors:**
- Every main button click produces one log line with elapsed milliseconds (emitted by the Presenter — see §11).
- Prefer **lazy loading** for Views.
- Maximize **real-time validation** and user feedback (validate on edit, not only on submit).

**FORBIDDEN in a View:**
- Business logic, I/O, threading decisions, direct Service/Repository calls, building error messages, French strings not sourced from `i18n_fra.py`.

---

## 14. Tests

- Framework: **pytest**. Tests live in `tests/`, mirroring the `src/wishlistor/` structure.
- When adding a test:
  - prefer a **unit test (TU)** to verify one precise element in isolation (mock the layer below via its Protocol);
  - prefer a **non-regression test (TR)** to freeze an observed behavior before refactoring or bug-fixing.
- Naming: `test_<module>_<behavior>.py`; test functions read as sentences (`test_validate_returns_error_when_name_is_empty`).
- **FORBIDDEN**: tests that touch the real filesystem outside a `tmp_path` fixture, tests depending on execution order, committing failing/skipped tests without a linked issue.

---

## 15. General Principles

- **KISS** — Keep It Simple, Stupid. The simplest design that works wins.
- **SOLID**:
  - **S**ingle Responsibility — one reason to change per class.
  - **O**pen/Closed — extend via new implementations of Protocols, not by modifying stable code.
  - **L**iskov Substitution — any Protocol implementation must be substitutable.
  - **I**nterface Segregation — small, focused Protocols (`IScrapingView`, not `IEverythingView`).
  - **D**ependency Inversion — depend on `interfaces/`, never on concrete classes across layers.
- **YAGNI** — do not build speculative features or abstractions.
- Prefer composition over inheritance.
- Long-running work MUST NOT block the Qt event loop (see §16).

---

## 16. Qt / PySide6 Rules

### 16.1 Event loop and responsiveness

- There is exactly **one** `QApplication`, created in `main.py` before any widget.
- The Qt event loop MUST never be blocked. **FORBIDDEN**: `time.sleep()`, long synchronous I/O, heavy computation, or busy-wait loops on the UI thread.
- Long-running work is delegated by the **Presenter** to a `QRunnable` worker executed on `QThreadPool.globalInstance()` (or a dedicated pool injected from the composition root). While the worker runs, the View's `is_busy` flag is `True` and interactive widgets are disabled via `set_enabled(False)`.
- **FORBIDDEN**: calling `QApplication.processEvents()` to "unfreeze" the UI — it hides a design problem instead of fixing it.

### 16.2 Threading

- **Widgets are UI-thread only.** Touching any `QWidget` (read or write) from a worker thread is **FORBIDDEN** and causes undefined behavior/crashes.
- Workers communicate results back to the UI thread **exclusively through Qt signals** (define a small `QObject` signal holder on the worker). Cross-thread signal connections use the default `Qt.AutoConnection`, which safely queues the call onto the UI thread.
- A worker never touches a View, a Presenter, or `AppStateModel` directly: it emits `finished(result)` / `failed(error_code)` signals; the Presenter's slot updates the View.
- Prefer `QThreadPool` + `QRunnable` for one-shot tasks; use `QThread` with a moved-to-thread `QObject` only for long-lived background workers. **FORBIDDEN**: subclassing `QThread` to override `run()` with business logic, mixing `threading.Thread` with widget code.

### 16.3 Signals & slots

- Signals/slots are the **only** communication mechanism from asynchronous code to the UI.
- Views expose their widget signals through the `bind_*` hooks defined in §3.2 — the Presenter never connects directly to a private widget (`view._button.clicked.connect(...)` is **FORBIDDEN**; use `view.bind_submit(cb)`).
- Decorate slots with `@Slot(...)` (from `PySide6.QtCore`) with explicit argument types.
- Every `connect()` made outside a View MUST have a matching `disconnect()` in the teardown sequence (see §9), otherwise signals fire on half-destroyed objects.
- **FORBIDDEN**: lambdas capturing `self` in long-lived cross-object connections (leak risk); connecting the same signal/slot pair twice (duplicate invocations).

### 16.4 Widget lifetime & ownership

- Every widget MUST have a parent (Qt's parent-child ownership tree handles destruction). Parentless widgets other than top-level windows are **FORBIDDEN**.
- Destroy widgets with `deleteLater()`, never with `del` or by simply dropping the Python reference — Qt owns the C++ side.
- Teardown order (owned by the composition root, §9): disconnect signals → stop/await workers → `deleteLater()` on the View → drop Python references.
- Never keep a Python reference to a widget whose C++ object may already be deleted (`RuntimeError: Internal C++ object already deleted`). If lifetime is uncertain, check with `shiboken6.isValid()`.

### 16.5 Layouts, models, and UI construction

- Use **layouts** (`QVBoxLayout`, `QGridLayout`, ...) exclusively. **FORBIDDEN**: absolute positioning with `move()` / `setGeometry()` for regular widgets.
- For tabular CSV data, prefer Qt's model/view classes: a `QAbstractTableModel` adapter in `views/` wrapping the frozen `*RowState` snapshots, displayed by a `QTableView`. **FORBIDDEN**: `QTableWidget` with thousands of manually created items (performance), and putting business logic inside a `QAbstractTableModel` subclass — it is a display adapter, nothing more.
- Batch UI updates: wrap bulk changes in `beginResetModel()` / `endResetModel()` (or fine-grained `dataChanged` signals) instead of resetting cell by cell; combine with the View's `is_loading` flag (§13.4) to suppress cascading recomputation.
- Widget object names use `setObjectName()` in snake_case for QSS styling and test targeting.

### 16.6 Qt vs. project conventions

- Qt APIs use camelCase; **project code stays PEP 8 snake_case**. camelCase is tolerated only when overriding Qt virtual methods (`rowCount`, `paintEvent`, ...).
- `QSettings` is **FORBIDDEN** for application configuration — `./config-wishlistor.json` through its Repository (§5, §13.1) is the single configuration mechanism.
- User-visible strings in widgets come from `shared/i18n_fra.py` (§6), never hardcoded, and never from `QObject.tr()` (the project does not use Qt Linguist).
- Timers: use `QTimer` (UI thread) for debouncing real-time validation (§13.4); **FORBIDDEN**: `threading.Timer` in UI code.

---

## 17. Verifying a Change (agents)

- Wishlistor is a native PySide6 desktop application with no headless/automation-friendly mode. Verification MUST be static:
  - `ruff check --fix .` and `ruff format .`
  - `python ./tools/furripe.py --fix . && python ./tools/furripe.py`
  - `basedpyright src/`
  - `pytest`
- A quick `python -c "import <touched module>"` smoke import is fine to catch import-time errors — it is not the same thing as launching the app.
- If a change genuinely needs visual confirmation (layout, colors, wrapping, ...), describe the manual steps for a human to check instead of attempting to drive the GUI.