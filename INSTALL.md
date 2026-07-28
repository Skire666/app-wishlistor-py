
Dossier racine "app-wishlistor-py"
Fichier dans "app-wishlistor-py/src/wishlistor/main.py"

-------------------

0. Se mettre dans l'environnement (important)
.\venv\Scripts\activate

-------------------

1. Installer PyInstaller
pip install pyinstaller

-------------------

2. Se placer à la racine du projet
cd app-wishlistor-py

-------------------

3. Lancer la compilation

```
pyinstaller --noconfirm --onefile --windowed --name wishlistor --paths src src/wishlistor/main.py --icon ".\ress\apps.ico"
```

--paths src : indique à PyInstaller d'ajouter src au chemin de recherche des modules, pour qu'il retrouve bien le package wishlistor si main.py fait des imports du type from wishlistor.timer import Timer
--onefile : un seul .exe
--windowed : pas de console noire derrière ta fenêtre PySide
--name wishlistor : nom de l'exécutable généré

Résultat :
Dossier "build" + " dist"
L'exécutable sera généré dans app-wishlistor-py/dist/wishlistor.exe.

-------------------

Troubleshooting

Si PySide6 pose problème (fenêtre noire/vide, plugin manquant)
```
pyinstaller --noconfirm --onefile --windowed --name wishlistor --paths src --collect-all PySide6 src/wishlistor/main.py
```

Recommandé : passer par un .spec
C'est plus propre de générer un fichier .spec une fois, puis de le versionner :
```
pyi-makespec --onefile --windowed --name wishlistor --paths src src/wishlistor/main.py
```

Va créer un wishlistor.spec à la racine, éditable pour ajouter datas=[...], hiddenimports=[...], etc.
Ensuite tu recompiles simplement avec :

```
pyinstaller wishlistor.spec
```
