Je démarre un projet. La codebase est à son début.
Seul quelques fichiers génériques sont là.

Lis le fichier @AGENTS.md et respecte ses directives sans exception.
Le présent prompt décrit la spécification fonctionnelle ; en cas de doute technique, AGENTS.md fait foi.

Le but de l'application :
Application Desktop de gestion de CSV en pyside6.
Est proche d'un Excel dans son fonctionnement.

---

# A) Informations sur la GUI

## A.1) Squelette de base

2 parties :
- Barre latérale verticale à gauche, avec dedans 4 boutons : Projet, CSV, Journal, Options. 
- Le reste à droite de l'écran est dédié au contenu principal.

Géométrie de fenêtre au globale :
- Taille minimale : 200×200.
- Persister la taille et la position de la fenêtre pour la prochaine ouverture.

## A.2) Couleurs de bases

C_COLOR_BACKGROUND_MAIN: str = "#1E1E1E"          # Fenêtre principale
C_COLOR_BACKGROUND_SECONDARY: str = "#252526"     # Panneaux, sidebar
C_COLOR_SURFACE: str = "#2D2D30"                  # Cartes, groupes, frames
C_COLOR_BORDER: str = "#3F3F46"                   # Bordures, séparateurs
C_COLOR_BUTTON: str = "#3A6EA5"                   # Boutons principaux
C_COLOR_BUTTON_HOVER: str = "#4B82C3"             # Survol des boutons
C_COLOR_BUTTON_DISABLED: str = "#555555"          # Boutons désactivés
C_COLOR_TEXT_PRIMARY: str = "#F3F3F3"             # Texte principal
C_COLOR_TEXT_SECONDARY: str = "#B8B8B8"           # Texte secondaire
C_COLOR_TEXT_DISABLED: str = "#7A7A7A"            # Texte désactivé
C_COLOR_SUCCESS: str = "#4CAF50"                  # Succès
C_COLOR_ERROR: str = "#E53935"                    # Erreur
C_COLOR_INFO: str = "#2196F3"
C_COLOR_WARNING: str = "#DD9000"
C_COLOR_SELECTION: str = "#264F78"
C_COLOR_INPUT_BACKGROUND: str = "#333337"
C_COLOR_INPUT_BORDER: str = "#4A4A4F"
C_COLOR_LINK: str = "#4FC3F7"
C_COLOR_BLACK_FONT: str = "#000000"

## A.3) Philosophie

Privilégier les **feedbacks inline** (bannière inline, labels d'état, surbrillances, cadre rouge autour du champ en erreur) plutôt que des popups bloquantes. Les popups modales sont réservées aux confirmations destructives (perte de données, écrasement de fichier).

Erreur et avertissement inline :
- Le champs ou le contrôle en erreur est entouré d'un cadre rouge ou orange.
- Une icône d'avertissement ou d'erreur apparait à côté.
- Le survol de l'icône fait apparaitre une info-bulle et permet de connaître la nature du problème.

Raccourcis clavier (uniquement dans le module CSV):
`Ctrl+S` (sauvegarder)
`Ctrl+Z` (annuler)
`Ctrl+Y` (rétablir)
`Ctrl+F` (focus sur le champ de recherche).
`Ctrl+O` (coche le tag:  "A faire" et "Favoris" de la ligne, et passe à la suivante)
`Ctrl+N` (coche le tag : "Ignoré" de la ligne, et passe à la suivante)
`Ctrl+T` (coche le tag : "Terminé" de la ligne, et passe à la suivante)

## A.4) Détails d'implémentation

Pour chaque bouton :
- Positionne déjà une icone placeholder '.\ress\placeholder.png' de 32x32 en attendant les îcones définitives.
- Le chemin doit pouvoir être remplacé facilement pour y mettre la nouvelle icône.
- Toute opérations sur un clique qui prends plus de 250 ms doit afficher un chargement ou une barre de progression.

Chargement ou barre de progression :
Il bloque le cadre ainsi que ses interactions pendant l'opération, mais l'UI reste réactive (repaint, déplacement de fenêtre) car le travail est dans un worker. L'overlay de progression reste affiché **au minimum 250 ms**, même si l'opération est plus rapide, pour éviter un effet de flash.

Les cases à cocher :
- Lors du clique, la zone de la case comme le texte doivent trigger le clique et "cocher" (ou décocher) le composant.

Les tableaux :
- Toutes les colonnes sont triables.
- Le survol d'une ligne mets en surbrillance légère BLEU la ligne.
- Le style du tableau est toujours le même : Colorisation légère de 1 ligne sur 2 (exemple : NOIR, GRIS, NOIR, GRIS, ...)

# B) Feature

## B.1) Feature : Barre latérale verticale

Barre latérale verticale (à gauche) :
4 modules sont listés (1 bouton par module) : "Projet", "CSV", "Journal", "Options"
Prévoir le placeholder pour les icônes.

### Comportement :

Cliquer sur un module ouvre le panneau associé dans le cadre principal.

## B.3) Feature : Module "Projet"

Bouton du module :
"Projet"

Objectif :
- Propose de créer un projet.
- Liste dans un tableau les projets déjà créés.

### Composition :

- **Ligne 1** : Label **Liste des projets**. Aligné à gauche.
- **Ligne 2** : Un séparateur horizontal.
- **Ligne 3** : Bouton **Créer un projet**. Aligné à gauche.
- **Ligne 4** : Un séparateur horizontal.
- **Ligne 5** : Tableau avec la liste des projets. Occupe tout l'espace disponibles. Colonnes : "Nom du projet", "Chemin du CSV", "Date de dernière ouverture", "Taille du fichier (avec unité)", "Disponible ?" (si le fichier est encore disponible ou non). Toutes les colonnes sont triables. Par défaut, est trié par date du plus récent au plus ancien.
- **Ligne 6** Un label qui indique le nombre de lignes disponibles. Est ancré en bas.

### Comportement :

- Le bouton **Créer un projet** ouvre un formulaire de création. Cf. section "B.3.1) **Créer un projet**" pour les détails.
- Un clic dans la liste des projets ouvre le projet.
- Si un projet dans le tableau pointe vers un CSV disparu, l'indiquer visuellement et proposer de le retirer de la liste (bouton "Effacer").
- Par défaut, le module affiché au lancement est **Projet**. Pas de réouverture automatique du dernier projet.
- Lorque le bouton "Effacer" est cliqué, il retire la ligne du projet.
- Une fois les informations remplies, lorsque l'utilisateur clique sur le bouton **Créer**, l'application enregistre le projet, charge le CSV, et redirige vers le module **CSV** avec le fichier affiché.


### B.3.1) **Créer un projet**

Lorsque l'utilisateur crée un nouveau projet, le panneau historique est remplacé par un formulaire inline.

Validation inline champ par champ, en temps réel : le cadre du champ en erreur est coloré en rouge, et une icône d'avertissement apparaît à droite du champ. Le survol de l'icône affiche une infobulle décrivant l'erreur.

Les projets (paramètres, poids, mappings, visibilité et ordre des colonnes) et l'historique des projets ouverts sont stockés dans `./config-wishlistor.json`.

#### B.3.1.1) Cadre 1 et 2


**Cadre 1, occupe 1/3 de la largeur. Aligné à gauche — Cadre **Informations** :
- **Chemin vers le CSV** (obligatoire).
- **Nom du projet** : 1 à 64 caractères.
- **Site web cible** : 1 à 64 caractères.
- **Catégorie du projet** : 1 à 64 caractères.
- **Date de création du projet** : calculée automatiquement.
- **Hauteur de ligne** : hauteur des lignes du tableau CSV, en pixels, entre 10 et 200 (défaut : 50). Appliquée en direct.

**Cadre 2, à gauche, sous **Informations** — **Tags** :**
- **Poids des tags** : un pourcentage par tag (la liste des tags reste figée ; seuls les poids sont modifiables), pré-rempli avec les poids par défaut des Options.

#### B.3.1.2) Cadre 3 : Colonnes

Une fois les informations de base saisies et le CSV lisible : Mapping des colonnes

**Cadre 3, occupe 1/3 de la largeur. Aligné au centre.**
- Le cadre se nomme **Colonnes**
- Est à droite des cadres **Informations** et **Tags**, sur toute la hauteur — **Colonnes** :**

L'utilisateur choisit parmi les colonnes existantes du CSV :
- La **colonne de référence** (défaut proposé : `csv.primary_key` si elle existe, sinon aucune présélection).
- La colonne **date de publication**.
- La colonne **popularité**.
- La colonne **notation**.
- Les **colonnes à indexer pour la recherche** : Lister les colonnes à utiliser pour calculer une string qui index les colonnes choisies et ainsi accélérer filtre et recherche. Par défaut, aucune colonne sélectionnée, l'utilisateur doit en sélectionner 1 minimum. Occupe l'espace restant de haut en bas. En plus des colonnes du CSV, proposer obligatoirement `wsh.owner_tags` et `wsh.owner_comments` et les cochers par défaut (sont des colonnes spéciales, seul excpetion, les autres ne sont pas coché).

Le mapping est modifiable après coup depuis **Options du projet** ; tout changement déclenche le recalcul des colonnes de rang.

#### B.3.1.3) Cadre 4

**Cadre 4, occupe 1/3 de la largeur. Aligné à droite.
- Le cadre se nomme **Affichage**
- Est positionné à droite de **Colonnes**, sur toute la hauteur.
- L'utilisateur choisit les colonnes à afficher, parmi les colonnes du CSV.
- Il est possible de choisir l'ordre (prévoir un bouton HAUT et BAS par lignes, et swap la position lorsque l'on clique dessus)
- Par défaut, aucune n'est sélectionnée hormis `wsh.owner_tags` et `wsh.owner_comments`. L'utilisateur doit en sélectionner 3 minimums.

# B.4) Feature : Module "CSV"

Bouton du module :
"CSV"

Objectif :
- Affiche le tableau du CSV ainsi que des actions pour le manipuler.

### Composition :

- **Ligne 1** : Label "Gestion du CSV". Aligné à gauche.
- **Ligne 2** : Un séparateur horizontal.
- **Ligne 3** :
  ---> Une liste déroulante avec la **Liste des projets** permet de choisir un projet parmi les projets existants (elle affiche les informations de base : "Nom du projet", "Site web", "Catégorie", "Chemin du CSV"). Il n'y a pas de saisie libre. Occupe toute la largeur.
  ---> Un hyperlien **Ouvrir dossier**, positionné à sa droite et permet d'ouvrir le dossier parent du fichier dans l'explorateur du système.
  ---> Un bouton "Options du projet" permet de modifier le projet (actif uniquement si projet chargé). Ancré à droite.
- **Ligne 4** : Un séparateur horizontal.
- **Ligne 5** : Cf. la section "B.4.2) Filtres et recherche"
- **Ligne 6** : Un séparateur horizontal.
- **Ligne 7** :
  ---> Un champ libre pour saisir une **URL à ajouter**. Occupe l'espace libre.
  ---> Un bouton **Ajouter l'URL**
  ---> Un label de vérification.
  ---> Un séparateur de 100 pixels horizontal
  ---> Un bouton **Modifier les tags**
  ---> Un bouton **Modifier le commentaire**.
  ---> Un bouton **Supprimer la ligne**.
- **Ligne 8** : Un séparateur horizontal.
- **Ligne 9** :
  ---> Un label avec le nombre de ligne "Sélectionné".
  ---> Un bouton "Tout sélectionner", pour sélectionner les lignes affichés (ou filtrée).
  ---> Un bouton "Inverser la sélection", pour inverser la sélection des lignes affichés (ou filtrée).
  ---> Un label avec le nombre de ligne "Sélectionné".
  ---> Ancré à droite : un bouton **Gestion des colonnes**
- **Ligne 10** : Cf. la section "B.4.1) Tableau principal"
- **Ligne 11** : Cf. la section "B.4.4) Pieds de page"

Comportement :
- Tant qu'aucun projet n'est ouvert, le module affiche un message inline invitant à ouvrir ou créer un projet.
- Il est possible d'ouvrir un CSV de 3 manières : Module "Projet" -> Suite à la création d'un projet via **Créer un projet**. Module "Projet" -> En cliquant dans la liste des projets disponibles. Module "CSV" -> lorsque l'utilisateur clique sur un des éléments de la liste déroulante **Liste des projets**.
- Changer de projet dans la liste **Liste des projets** déclenche la vérification des modifications non sauvegardées. Cf. section "F) Prévention de la perte de données" pour le détail.
- Lors de la sélection d'un projet dans **Liste des projets**, si celui-ci subit une erreur critique, affiche une popup avec l'erreur dedans.
- Le bouton **Options du projet** permet de modifier le projet courant (formulaire de la section "B.3.1) **Créer un projet**").
- Chacun des **filtres de tags** est actif au démarrage de l'application. Chacun affiche le nombre d'éléments associés. Exemple : **En cours (x456)**.
- Si les boutons **Modifier les tags** et **Modifier le commentaire** sont utilisés, la modification s'applique à toutes les lignes sélectionnées. NOTE : une action de masse compte comme **une seule** action dans l'historique d'annulation. Ils sont actifs uniquement si une ligne ou plusieurs sont sélectionnés.
- À la validation de **URL à ajouter** (soit touche `Entrée` ou bouton **Ajouter l'URL**), vérifier si cette valeur existe déjà dans la **colonne de référence**. La comparaison est **stricte** : égalité exacte, sensible à la casse, sans normalisation. Remonter l'erreur dans le label de vérification dédié le cas échéant. Si elle existe : ne rien ajouter, afficher un feedback inline (**Déjà présent**) et mettre le focus sur la ligne existante. Sinon : ajouter une **nouvelle ligne en mémoire, en fin de tableau** (donc en bas du fichier à la sauvegarde), avec la colonne de référence = l'URL saisie et les autres colonnes vides (puis substitutions du glossaire appliquées). Le fichier passe à l'état **modifié** (le bouton Sauvegarder s'active). Aucune écriture disque immédiate.
- Le bouton **Supprimer la ligne** supprime la ligne et recalcul les rangs.
- Le bouton **Gestion des colonnes** permet de gérer les colonnes à afficher/masquer, et de changer l'ordre (prévoir des boutons HAUT et BAS sur chaque ligne et swap la position. Permettre aussi le drag and drop)

### B.4.1) Tableau principal

Occupe toute la hauteur libre restante de la fenêtre.
Il est possible de modifier une valeur en faisant un double clique sur une cellule.
Une clique simple sur la colonne `wsh.owner_tags` permet de modifier les tags. Cf. section "B.4.3) Logique des tags dans une ligne"
Les colonnes de rang sont calculées par l'application et ne sont jamais éditables.

- **Colonne **Sélection**** tout à gauche, case à cocher centrée (horizontalement et verticalement) : une case par ligne
- Quand au moins une ligne est sélectionnée, les deux actions de masse **Modifier les tags** et **Modifier commentaire** deviennent disponibles.
- **Colonnes** : l'utilisateur ne peut **jamais** créer, renommer ou supprimer de colonne via l'UI. Seule l'application crée des colonnes?
- **Affichage/masquage de colonnes** : via un menu (clic droit sur l'en-tête ou bouton dédié), ou via **Créer un projet**, **Options du projet**. La visibilité est un état d'affichage uniquement, sans effet sur le fichier.
- **Tri** : un clic sur un en-tête trie la colonne ; un second clic inverse le sens ; l'indicateur de tri est visible. Le tri est **intelligent** : si toutes les valeurs non vides d'une colonne sont numériques, tri numérique ; sinon tri alphabétique insensible à la casse. Les cellules vides sont toujours placées en fin de tri. Le tri est un état d'affichage : il ne modifie **jamais** l'ordre des données dans le fichier.
- **Surbrillance** : la ligne cliquée ou trouvée par la recherche est mise en surbrillance.

#### Affichage des cellules

- Si une cellule commence par `data:image/` (data-URI base64, ex. `data:image/png;base64,...`) : décoder et afficher l'**image** dans la cellule à la place du texte (redimensionnée à la hauteur de ligne, ratio préservé), avec cache des pixmaps. Si le décodage échoue, afficher un placeholder **image invalide**.
- Si une cellule contient une URL (commence par `http`) : la rendre **cliquable** (style lien) et ouvrir le navigateur par défaut au clic.
- Si une cellule est un chemin commençant par `C:\`, `D:\`, `E:\`, `F:\`, `G:\` ou `H:\` : rendre le lien cliquable et ouvrir le dossier pointé (remonter une erreur inline s'il n'existe pas ou n'est pas accessible). Linux/macOS non gérés.

### B.4.2) Filtres et recherche

Cette ligne contient de gauche à droite, sur 1 seule ligne :
---> **filtres de tags** sous forme de boutons toggle, un par tag : "Favoris", "A faire", "En cours", "Terminé", "Abandonné", "Archivé", "Ignoré". Un cas spécial "(tags vide)" permet de sélectionner les lignes qui n'ont aucun tag.
---> **filtre libre** : Un champ texte libre avec un bouton "Filtrer" et un bouton "Effacer" pour effacer le filtre.
---> **Champ recherche** : Un champ texte libre avec n compteur affiche l'index de la recherche. Exemple : 1/37. 2 boutons **Précédent** et **Suivant**  permettent de naviguer dans la recherche.

Pour **filtres de tags** :
- lorsqu'il sont actifs, ils sont combinés en **OU** entre eux (une ligne est visible si elle porte au moins un des tags actifs).
- Si aucun filtre "Favoris", "A faire", "En cours", "Terminé", "Abandonné", "Archivé", "Ignoré", alors filtre "(tags vide)" est actif.
- Il est **impossible d'avoir zéro filtre actif** : si l'utilisateur décoche le dernier filtre actif, le filtre spécial "(vide)" est automatiquement activé.

Pour **filtre libre** :
- Est un champ texte libre.
- Le tableau est filtré lorque l'utilisateur clique sur la touche `Entrée` ou sur le bouton "Filtrer".
- Il recherche la sous-chaîne via les **colonnes indexées** définies dans le projet.
- Lorqu'un filtre viens d'être appliqué, un bouton "Effacer" permet d'effacer le filtre libre.
- Le filtre texte manuel est combiné en **ET** avec les **filtres de tags**.

Pour **Champ recherche** :
- Est un champ texte libre.
- Cherche une valeur (sous-chaîne, insensible à la casse, sur les **colonnes indexées**) et met le focus sur la prochaine ligne qui correspond parmi les lignes actuellement affichées (après filtres).
- Un compteur affiche l'index de la recherche. Exemple : 1/37.
- La touche `Entrée` passe à l'occurrence suivante (avec bouclage en fin de tableau).
- La ligne trouvée est mise en surbrillance et scrollée dans la vue.
- Les boutons **Précédent** et **Suivant**  permettent de naviguer dans la recherche.
- Si aucun résultat : Le compteur de recherche est remplacé par un message qui indique "0 trouvé".

### B.4.3) Logique des tags dans une ligne

**Modification des tags et règles de cascade** au cochage.
NOTE : décocher un tag n'a jamais d'effet en cascade.

| Action utilisateur | Tags décochés automatiquement |
|---|---|
| Cocher **Favoris** | aucune |
| Cocher **A faire** | Terminé, Abandonné, Archivé, Ignoré |
| Cocher **En cours** | Terminé, Abandonné, Archivé, Ignoré |
| Cocher **Terminé** | A faire, En cours, Abandonné |
| Cocher **Abandonné** | A faire, En cours, Terminé |
| Cocher **Archivé** | A faire, En cours |
| Cocher **Ignoré** | A faire, En cours, Terminé, Abandonné, Archivé (Favoris n'est jamais décoché) |

Invariants (à vérifier en tests, et à appliquer aussi au nettoyage à la lecture du CSV et aux actions de masse) :
- Aucun tag du groupe actif {A faire, En cours} ne coexiste avec un tag du groupe clos {Terminé, Abandonné, Archivé, Ignoré}.
- Si un tag du groupe {A faire, En cours}, le tag "Favoris" est automatiquement coché.
- "Terminé" et "Abandonné" ne coexistent jamais.
- "Favoris" est compatible avec toute les combinaisons.

### B.4.4) Pied de page

Composé de 3 cadres, de gauche à droite :

**Cadre 1 :**
- Le nombre de lignes **totales**.
- Le nombre de lignes **affichées** (après filtres).
- La date de modification (`mtime`) du fichier sur disque.

**Cadre 2 :**
- Bannière inline, haute de 3 lignes, avec un ascenseur pour en voir plus.
- Liste les WARNINGS et ERRORS rencontrés dans le CSV. Affichage simple (ce n'est pas le journal : composant indépendant, sans persistance).
- Alimentée en temps réel : erreurs et avertissements rencontrés durant la lecture/modification du CSV

**Cadre 3 :**
- Un bouton **Sauvegarder**, grisé tant que le tableau n'a pas été modifié depuis la dernière sauvegarde (ou l'ouverture).
- Si l'utilisateur annule toutes ses modifications (Ctrl+Z jusqu'à l'état propre), le bouton **Sauvegarder** se regrise.
- En dessous, un label **Dernière sauvegarde** suivi d'un champ affichant la date de la dernière sauvegarde effectuée durant la session (`--` si aucune sauvegarde n'a encore été effectuée).

# B.5) Feature : Module "Journal"

Bouton du module :
"Journal"

Objectif :
- Affiche le journal de l'application.

### Composition :

- **Ligne 1** : Label "Journalisation des événements". Aligné à gauche.
- **Ligne 2** : Un séparateur horizontal.
- **Ligne 3** :
---> 5 Cases à cocher pour afficher les différents niveaux de logs "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" avec le nombre de logs. Exemple : ERROR x4.
---> Un hyperling pour ouvrir le dossier des logs.
---> Un bouton **Vider l'affichage**.
- **Ligne 4** : Un séparateur horizontal.
- **Ligne 5** : Tableau avec la liste des logs dans le journal. Colonnes : "Date", "Niveau de logs", "Source", "Message". Sur chaque ligne, un bouton **Copier** est disponible.

### Comportement :

- Par défaut, les niveaux de logs : "DEBUG, INFO, WARNING, ERROR, CRITICAL" sont tous sélectionnés.
- Le but de ce journal est de journaliser les événements clés avec horodatage et niveau
- Le journal de la session, est lecture seule, plus récent en haut.
- Sur chaque ligne, un bouton **Copier** est disponible. Il copie la ligne focus.
- Les fichiers de logs sont écrits dans `./tmp_app_logs/`, avec rotation (5 fichiers max., 2 Mo par fichier).

# B.6) Feature : Module "Options"

Bouton du module : "Options".

Objectif :
Configuration de l'application.

### Composition :

- **Ligne 1** : Label "Paramétrage de l'application". Aligné à gauche.
- **Ligne 2** : Un séparateur horizontal.
- **Ligne 3** :
---> Afficher la dernière date  de sauvegarde des options. 
---> Ancré à droite **Remettre réglage d'usine** permet de réinitialiser la configuration et de la remettre à zéro (tout est vidé, historique des projets inclus). 
- **Ligne 4** : Les options configurable.

1) **Retour en arrière** (nombre d'annulations possibles) : entre 1 et 30 (défaut : 10). L'UI empêche de saisir une valeur invalide et affiche la raison inline.

2) **Poids par défaut des tags** utilisés pour pré-remplir le formulaire de projet. Par défaut, est configuré comme suit :
Tag : Favoris = +20% de N
Tag : A faire = +40% de N
Tag : En cours = +80% de N
Tag : Terminé = -50% de N
Tag : Abandonné = -75% de N
Tag : Archivé = -100% de N
Tag : Ignoré = -100% de N.
Sans tag, la valeur vaut 0.

3) **Colonnes spéciales proposées à l'affichage** : liste à cocher des colonnes spéciales que l'on peut proposer. Par défaut est `wsh.owner_tags`, et `wsh.owner_comments`. Il est possible d'en rajouter ou supprimer.

4) **Valeurs par défaut** des colonnes. Le but est d'avoir une liste dans laquelle on peut ajouter une liste de couple "Nom de la colonne" + "Valeur par défaut". Ces valeurs par défaut sont à ajouter au fichier CSV pour la colonne ciblé. Elle peuvent concerné 3 usages : Ouverture du CSV, Sauvegarde du CSV, Ajouter une URL dans le CSV. Les valeurs par défaut peuvent être statiques ou dynamiques.
Par défaut, le contrôle est déjà alimenté avec :
`__date_created__` = `1900-01-01 00:00:00`
`__date_modified__` = `datetime.now()`
`wsh.rank_1_released` = `Rang(N)`
`wsh.rank_2_popularity` = `Rang(N)`
`wsh.rank_3_notation100` = `Rang(N)`
`wsh.rank_4_owner_tags` = `Rang(N)`

4) **Taille de police** : 12. Appliqué en temps réel.

5) Pouvoir confgurer raccouri et le tag qu'il déclenche :
- `Ctrl+O` (coche le tag "A faire" et "Favoris")
- `Ctrl+N` (coche le tag "Archivé")
- `Ctrl+T` (coche le tag "Terminé")
Les règles de tags et leur logique sont appliqués ici aussi.

### Comportement :

- **Remettre réglage d'usine** : Prévenir l'utilisateur via une confirmation modale avant d'exécuter l'opération.
- Les options globales sont persistées dans **`./config-wishlistor.json`**
- Sauvegarde automatique à chaque modification, écriture atomique.
- Si le fichier est absent ou corrompu, repartir des valeurs par défaut et journaliser un avertissement.
- Les options configurables sont avec validation inline (avec bornes, valeur si vide, etc.)

# Structure indicative du JSON :

```json
{
  "options": {
    "nbr_undo_max": 10,
    "default_tag_weights": {
      "Favoris": +0.20, "A faire": +0.40, "En cours": +0.80,
      "Terminé": -0.50, "Abandonné": -0.75, "Archivé": -1.00, "Ignoré": -1.00
    },
    "special_display_columns": ["wsh.owner_tags", "wsh.owner_comments",
                                 "wsh.rank_1_released", "wsh.rank_2_popularity",
                                 "wsh.rank_3_notation100", "wsh.rank_1234_summed",
                                 "wsh.rank_4_owner_tags"],
    "font_size": 12
  },
  "window": { "width": 1280, "height": 800, "x": 100, "y": 100 },
  "recent_projects": ["<id>"],
  "projects": {
    "<id>": {
      "name": "...", "csv_path": "...", "website": "...", "category": "...",
      "created_at": "ISO-8601", "row_height": 50,
      "tag_weights": { "Favoris": +0.20, "A faire": +0.40, "En cours": +0.80,
                        "Terminé": -0.50, "Abandonné": -0.75, "Archivé": -1.00, "Ignoré": -1.00 },
      "columns": { "primary": "csv.primary_key", "released": "...",
                    "popularity": "...", "scoring": "...", "search_index": ["..."] },
      "last_opened": "ISO-8601",
      "visible_columns": ["..."],
      "column_order": ["..."]
    }
  }
}
```

# C) Contrainte techniques et performance

- Garantir la performance lors de l'ouverture d'un CSV de **100 000 lignes**.
- Garantir la fluidité de l'application lors de l'ajout d'une ligne et du recalcul des rangs.
- Tri et filtrage sont perçus comme instantanés (< 150 ms), scroll fluide.
- Les tableaux doivent être optimisés et tenir la performance lors du filtrage sur **100 000 lignes** lignes.
- Toute lecture et sauvegarde de CSV est déléguée par le Presenter à un worker. L'UI ne gèle jamais.
- Filtre texte et recherche : Pour accélérer le traitement, utiliser une variable qui concatène toutes les colonnes à indexer et ainsi chercher dedans lorsque demande un filtre ou un recherche.
- Images en cellule : mettre en cache les images décodés (ne jamais recalculer/repaindre). La cache autorisé est de 256 Mo au total.
- Mises à jour massives du modèle doivent être encadrées.

# D) Gestion du CSV

## D.1) Format

- Délimiteur : **`;`**, toujours.
- Encodage : **UTF-8** en lecture (tolérer un BOM) et en écriture (sans BOM).
- Quoting : gérer les champs entre guillemets via le module `csv` de la stdlib (quoting minimal à l'écriture, `newline=''`).
- La première ligne est l'en-tête. Un CSV sans en-tête exploitable, ou avec des noms de colonnes dupliqués ou vides, est une erreur (afficher l'erreur dans la bannière inline, ouverture annulée). Un CSV avec en-tête mais zéro ligne de données est valide.

- Toutes les colonnes `__date_*` sont des datetimes : parsing ISO `YYYY-MM-DD hh:mm:ss`. Remonter une alerte si ce n'est pas le cas.
- Toutes les colonnes `wsh.rank_*` sont des `int`, jamais vides.
- **L'utilisateur ne peut jamais créer, renommer ou supprimer de colonne** via l'UI ou la configuration. Seule l'application crée des colonnes.
- Toutes les colonnes de ce tableau sont triables et masquables comme les autres. Elles apparaissent dans le cadre **Affichage** du projet et dans **Gestion des colonnes**.

## D.2) Chargement du fichier

- Si le chemin n'existe pas ou n'est pas lisible : erreur inline, opération annulée.
- Charger **tout** le fichier en mémoire (pas de lecture partielle). Si le fichier dépasse **100 Mo**, afficher un avertissement inline (non bloquant) avant de charger tout.
- Ajouter les colonnes `wsh.owner_tags` et `wsh.owner_comments` si elles sont absentes (elles seront écrites au fichier à la prochaine sauvegarde).
- **colonne de référence** : colonne de référence, définie dans le projet (par défaut `csv.primary_key`). Vérifications à l'ouverture :
  - Si la colonne de référence n'existe pas dans le CSV : erreur inline, proposer d'ouvrir la configuration du projet pour en choisir une autre.
  - Si elle contient des **doublons** ou des **valeurs vides** : erreur inline listant les lignes fautives (numéros de ligne), ouverture annulée. La correction doit être faite dans un éditeur externe.
- Mémoriser le `mtime` et la taille du fichier au chargement : référence pour détecter les modifications externes.
- Afficher l'overlay de progression pendant le chargement.

Vérifications et optimisations :
- Toutes les colonnes qui commencent par `__date_` sont des champs date sous forme de string : les transformer en `datetime` à l'initialisation.
- Toutes les colonnes `wsh.rank_*` sont toujours calculées par l'application. Si une colonne `wsh.rank_*` existe déjà dans le CSV : appliquer la règle du glossaire (remplacement en RAM, disparition à la prochaine sauvegarde).
- Toute autre colonne `__` inconnue du glossaire est **tolérée** (arbitrage propriétaire 2026-07-13 : plus de contrôle de format/glossaire, CSV_1004 n'est plus déclenché).
- La colonne de référence est toujours alimentée : remonter une erreur si une ligne est vide.
- Si une valeur est manquante et qu'une règle de substitution existe, alimenter la valeur.

## D.3) Colonnes ajoutés automatiquement si absente

- `wsh.rank_1_released` : à partir de la colonne mappée **date de publication**. Trier du plus récent vers le plus ancien et numéroter de 1 à N.
- `wsh.rank_2_popularity` : à partir de la colonne mappée **popularité**. Trier du moins populaire au plus populaire (valeur numérique la plus élevée) et numéroter de 1 à N.
- `wsh.rank_3_notation100` : à partir de la colonne mappée **notation**. Trier du plus mauvais au meilleur score (valeur numérique la plus élevée) et numéroter de 1 à N.
- `wsh.rank_4_owner_tags` : soit N le nombre total de lignes du CSV. Poids par défaut (modifiables par projet) :
Tag : Favoris = +20% de N
Tag : A faire = +40% de N
Tag : En cours = +80% de N
Tag : Terminé = -50% de N
Tag : Abandonné = -75% de N
Tag : Archivé = -100% de N
Tag : Ignoré = -100% de N.
Sans tag, la valeur vaut 0
- `wsh.rank_1234_summed` : Est calculé automatiquement avec la somme de `wsh.rank_1_released` + `wsh.rank_2_popularity` + `wsh.rank_3_notation100` + `wsh.rank_4_owner_tags`

Règles de calcul — **aucune cellule des colonnes de rang, ni des colonnes sources utilisées par les rangs, ne doit rester vide** :

- **Valeurs manquantes ou non parsables dans les colonnes sources** :
Au chargement du CSV, à la sauvegarde, ou lors de l'ajout d'une URL, les colonnes vides sont complétés par les **Valeurs par défaut**.
- Le nombre de substitutions est journalisé en WARNING. Ces valeurs complétées font partie des données et seront écrites au fichier à la prochaine sauvegarde (normalisation du fichier).
- **Mapping non défini** : si une colonne mappée (date de publication, populaire, scoring) n'est pas définie dans le projet, ou n'existe pas dans le CSV, toutes les lignes reçoivent la valeur par défaut correspondante. La bannière inline en pied de page invite à compléter la configuration du projet. Aucune colonne de rang ne reste vide.
- **Moment du calcul** : `wsh.rank_1_released`, `wsh.rank_2_popularity`, `wsh.rank_3_notation100` et `wsh.rank_1234_summed` sont recalculés intégralement (toujours après application des substitutions de valeurs vides) : au chargement du fichier, à chaque ajout de ligne via le champ URL, et à l'annulation ou au rétablissement d'un ajout de ligne.

## D.4) Colonne `wsh.owner_tags`

- Les tags sont **hardcodés et figés** : "Favoris", "A faire", "En cours", "Terminé", "Abandonné", "Archivé", "Ignoré".
- Il est **impossible** d'en créer, d'en renommer ou d'en supprimer, que ce soit via l'UI ou la configuration.
- Un clic sur une cellule de cette colonne ouvre le **sélecteur de tags** : une popup légère ancrée à la cellule (pas une boîte de dialogue modale plein écran). Elle affiche les tags, chacun en texte **blanc sur un fond coloré** fixe et distinct. L'utilisateur coche/décoche, avec les règles de cascade (cf. section "B.4.3) Logique des tags dans une ligne"
- Les tags sélectionnés sont affichés dans la cellule sous forme de pastilles colorées.
- **Sérialisation** : à la sauvegarde, la liste des tags d'une cellule est jointe en une seule chaîne, tags séparés par `||` (jamais de `;`, délimiteur du CSV). À la lecture, découpage sur `||` (chaîne vide = aucun tag).
- **Tolérance à la lecture — nettoyage strict** :
  - Un segment qui ne correspond à aucun des tags (donnée étrangère) est **supprimé au chargement**, et un WARNING est journalisé avec le numéro de ligne.
  - Les doublons et segments vides sont supprimés silencieusement.
  - **Résolution des conflits d'invariants** : les segments sont lus de gauche à droite ; le **premier tag lu est prioritaire**. Tout tag ultérieur qui viole un invariant (B.4.3) Logique des tags dans une ligne) avec les tags déjà retenus est supprimé, et un WARNING est journalisé avec le numéro de ligne.
- Si plusieurs lignes sont sélectionnées, la modification des tags en masse devient active et il est possible d'éditer tout le lot en une seule fois (une seule action d'annulation).

### D.5) Sauvegarde

- La sauvegarde **préserve l'ordre original des lignes du fichier**. L'ordre affiché (tri, filtres) n'a aucun impact. Les nouvelles lignes sont écrites à la fin, dans leur ordre d'ajout.
- **L'application normalise le fichier** : les colonnes dont les valeurs ont été substituées sont écrites avec leurs valeurs par défaut.
- **Sauvegarde atomique** : écriture dans un fichier temporaire dans le même dossier, suppression de l'ancien, puis rename du temporaire.
- **Détection de modification externe** : Si le fichier a été modifié ou supprimé entre-temps : ne pas écraser silencieusement ; avertir l'utilisateur et proposer trois choix : **Écraser**, **Enregistrer sous…** (nouvel emplacement, dialogue natif ; met à jour le `csv_path` du projet), **Annuler**.
- Après une sauvegarde réussie : mettre à jour la référence `mtime`/taille, la date affichée dans le pied de page et repasser l'état à **propre** (bouton Sauvegarder regrisé), journaliser l'opération avec sa durée. L'historique d'annulation est conservé.
- Afficher l'overlay de progression pendant la sauvegarde (mêmes règles que le chargement).

---

# E) Historique des actions et annulation

- Historiser les dernières actions d'écriture de l'utilisateur, dans la limite de **Retour en arrière** (défaut : 10).
- Une **action d'écriture** = édition d'une cellule (`wsh.owner_tags` ou `wsh.owner_comments`), une modification de masse (une seule action, quel que soit le nombre de lignes), l'ajout d'une ligne (via le champ URL).
- `Ctrl+Z` annule, jusqu'à **Retour en arrière** fois. Chaque annulation rétablit exactement l'état précédent, y compris le recalcul des colonnes de rang concernées.
- `Ctrl+Y` rétablit une action annulée.
- Lors d'un changement de projet, l'historique d'annulation est vidé (non conservé).

---

# F) Prévention de la perte de données

- Si l'utilisateur change de projet, ou quitte l'application alors que des modifications ne sont pas sauvegardées : afficher une confirmation avec les choix **Sauvegarder**, **Sauvegarder sous…** (nouvel emplacement), **Quitter sans sauvegarder**, **Annuler**.
- Intercepter le `closeEvent` de la fenêtre principale pour couvrir la fermeture par la croix.

## G) Cas limites à couvrir explicitement

- CSV avec en-tête seul (0 ligne de données) : valide, tableau vide.
- CSV vide (0 octet) ou sans en-tête exploitable : erreur inline.
- Noms de colonnes dupliqués ou vides dans l'en-tête : erreur inline.
- Fichier verrouillé ou permissions insuffisantes à la sauvegarde : erreur inline + proposer **Enregistrer sous…**.
- Lignes de longueurs incohérentes (plus ou moins de champs que l'en-tête) : compléter par des valeurs vides ou tronquer, et journaliser un avertissement avec les numéros de ligne.
- Cellule `wsh.owner_tags` contenant des doublons, des segments vides, des tags inconnus ou des combinaisons violant les invariants : nettoyage strict au chargement, premier tag lu prioritaire.
- Ajout d'une URL alors qu'aucune colonne de référence n'est mappée ou que le CSV n'est pas ouvert : champ URL désactivé.
