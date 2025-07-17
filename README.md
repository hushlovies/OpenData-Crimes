# 🕵️ OpenData-Crimes

Projet d’analyse de données ouvertes sur les crimes à New York, avec un backend Flask, une interface frontend Streamlit, et une base de données MongoDB.

> 📁 Le fichier `NYPD_Complaint_Data_Historic_20250716.csv` est **fourni en pièce jointe zippée (`data/NYPD_Data.zip`)**. Merci de le décompresser manuellement dans le dossier `data/`.

---

## 📁 Structure du projet

```
OpenData-Crimes/
│
├── backend/                # Backend Flask
│   └── app.py
│
├── frontend/               # Frontend Streamlit
│   └── app.py
│
├── scripts/                # Scripts d’importation et d’indexation
│   ├── load_csv_to_mongo.py
│   └── create_indexes.py
│
├── data/                   # Contient le fichier CSV (après extraction)
│   └── NYPD_Complaint_Data_Historic_20250716.csv
│
├── .gitattributes          # Fichier Git LFS (si utilisé)
├── requirements.txt        # Dépendances Python
└── README.md
```

---

## ⚙️ Initialisation du projet

### 🔧 Étapes globales

#### 1. Cloner le dépôt

```bash
git clone https://github.com/hushlovies/OpenData-Crimes.git
cd OpenData-Crimes
```

#### 2. Décompresser le fichier ZIP

Décompresse le fichier `data/NYPD_Data.zip` pour obtenir le fichier CSV dans le dossier `data/`.

---

## 🧪 Mise en place côté backend

#### 1. Activer l’environnement virtuel du backend

```bash
cd backend
source venv/Scripts/activate  # Sous Linux/macOS : source venv/bin/activate
```

#### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 3. Charger le fichier CSV dans MongoDB

```bash
python ../scripts/load_csv_to_mongo.py
```

#### 4. Créer les index MongoDB

```bash
python ../scripts/create_indexes.py
```

#### 5. Lancer le backend

```bash
python app.py
```

Le serveur Flask démarre sur `http://127.0.0.1:5000/`

---

## 📊 Mise en place côté frontend

#### 1. Activer l’environnement virtuel du frontend

```bash
cd frontend
source venv/Scripts/activate  # Sous Linux/macOS : source venv/bin/activate
```

#### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 3. Lancer l’application Streamlit

```bash
streamlit run app.py
```

---

## ✅ Récapitulatif des commandes

```bash
# Frontend
cd frontend
source venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py

# Backend
cd backend
source venv/Scripts/activate
pip install -r requirements.txt
python ../scripts/load_csv_to_mongo.py
python ../scripts/create_indexes.py
python app.py
```