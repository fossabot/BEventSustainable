#!/usr/bin/env python3
"""
populate_db.py
Script per popolare il DB MongoDB del progetto BEventSustainable
- usa campi compatibili con il codice del progetto
- inserisce un marcatore generated_by per poter cancellare poi i documenti
USO:
    source venv/bin/activate
    pip install pymongo werkzeug
    python scripts/populate_db.py
"""
import random
import string
import datetime
import base64
import os
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash

# --- CONFIGURAZIONE ---
MONGO_URI = "mongodb://localhost:27017/"   # modifica se usi Atlas
DB_NAME = "BEvent"
GENERATED_TAG = "populate_script_v1"

NUM_USERS = 800        # numero utenti da creare
NUM_EVENTS = 300       # numero eventi da creare
EVENT_MIN_SUBS = 10
EVENT_MAX_SUBS = 40
INCLUDE_LARGE_IMAGES = True # True -> crea immagini base64 da ~5MB ciascuna
IMAGE_SIZE_BYTES = 5_000_000   # dimensione immagine finta
# -----------------------

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# COLLEZIONI
COL_UTENTE = db["Utente"]
COL_EVENTO = db["Evento"]
COL_BIGLIETTO = db["Biglietto"]
COL_FEEDBACK = db["Feedback"]
COL_RECENSIONE = db["Recensione"]
COL_SERV_OFF = db["Servizio Offerto"]

# ----------------- FUNZIONI -----------------

def random_string(n=10):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def random_email():
    return random_string(8) + "@example.com"

def gen_large_image_base64(size=IMAGE_SIZE_BYTES):
    data = os.urandom(size)
    return base64.b64encode(data).decode("utf-8")

def create_users(num=NUM_USERS):
    docs = []
    for i in range(num):
        ruolo = random.choice(["1","2","3"])
        nome = random_string(6).capitalize()
        cognome = random_string(7).capitalize()
        data_birth = (datetime.datetime.now() - datetime.timedelta(days=random.randint(20*365,50*365))).strftime("%Y-%m-%d")
        nome_utente = f"{nome.lower()}{random.randint(1,9999)}"
        user_doc = {
            "_id": ObjectId(),
            "nome": nome,
            "cognome": cognome,
            "data_di_nascita": data_birth,
            "email": random_email(),
            "telefono": ''.join(random.choices(string.digits, k=10)),
            "nome_utente": nome_utente,
            "password": generate_password_hash("Password123!", method="pbkdf2:sha256"),
            "Admin": {"isAdmin": ruolo=="1"},
            "Ruolo": ruolo,
            "regione": random.choice(["Lombardia","Lazio","Sicilia","Campania","Toscana"]),
            "generated_by": GENERATED_TAG
        }
        if ruolo == "3":
            user_doc["Fornitore"] = {
                "Descrizione": "Fornitore " + nome,
                "EventiMassimiGiornaliero": random.randint(1,5),
                "Foto": [],
                "Citta": random.choice(["Roma","Milano","Napoli"]),
                "Via": f"Via {random_string(5)}",
                "Partita_Iva": ''.join(random.choices(string.digits, k=11)),
                "isLocation": random.choice([True, False])
            }
        if ruolo == "2":
            user_doc["Organizzatore"] = {"Citta": random.choice(["Roma","Milano","Bari"])}
        docs.append(user_doc)
    if docs:
        res = COL_UTENTE.insert_many(docs)
        print(f"[Users] inseriti {len(res.inserted_ids)} utenti")
    return

def create_events(num=NUM_EVENTS):
    utenti = list(COL_UTENTE.find({"generated_by": GENERATED_TAG}))
    if not utenti:
        print("Nessun utente creato: esegui prima create_users()")
        return []
    eventi = []
    for i in range(num):
        ruolo_evento = random.choice(["1","2"])
        organizer = random.choice(utenti)
        data_evento = (datetime.datetime.now() + datetime.timedelta(days=random.randint(1,365))).strftime("%d-%m-%Y")
        prezzo = round(random.uniform(0,100),2)
        is_pagato = random.choice([True, False])
        biglietti_disponibili = str(random.randint(0,200))
        evento_doc = {
            "_id": ObjectId(),
            "Nome": "Evento " + random_string(6),
            "Descrizione": random_string(150),
            "Data": data_evento,
            "Creatore": organizer["_id"],
            "Ruolo": ruolo_evento,
            "isPagato": is_pagato,
            "EventoPubblico": {
                "BigliettiDisponibili": biglietti_disponibili,
                "Prezzo": str(prezzo)
            },
            "locandina": gen_large_image_base64() if INCLUDE_LARGE_IMAGES else None,
            "regione": organizer.get("regione", "Lazio"),
            "luogo": random.choice(["Auditorium","Sala Grande","Piazza Centrale"]),
            "ora": f"{random.randint(9,22)}:{random.choice(['00','30'])}",
            "biglietti_disponibili": biglietti_disponibili,
            "generated_by": GENERATED_TAG
        }
        eventi.append(evento_doc)
    if eventi:
        res = COL_EVENTO.insert_many(eventi)
        print(f"[Events] inseriti {len(res.inserted_ids)} eventi")
        return res.inserted_ids
    return []

def add_subscriptions(event_ids):
    utenti = list(COL_UTENTE.find({"generated_by": GENERATED_TAG}))
    for ev_id in event_ids:
        count = random.randint(EVENT_MIN_SUBS, EVENT_MAX_SUBS)
        subs = random.sample(utenti, min(count, len(utenti)))
        subs_ids = [u["_id"] for u in subs]
        COL_EVENTO.update_one({"_id": ev_id}, {"$set": {"Iscritti": subs_ids}})
    print("[Subscriptions] aggiunte iscrizioni per eventi")

def create_tickets():
    """Crea Biglietti per gli eventi"""
    eventi = list(COL_EVENTO.find({"generated_by": GENERATED_TAG}))
    utenti = list(COL_UTENTE.find({"generated_by": GENERATED_TAG}))
    tickets = []
    for ev in eventi:
        num_tickets = random.randint(5, 20)
        for _ in range(num_tickets):
            utente = random.choice(utenti)
            ticket = {
                "_id": ObjectId(),
                "Evento_associato": ev["_id"],
                "CompratoDa": utente["_id"],
                "DataEvento": ev["Data"],
                "Dove": ev["luogo"],
                "Ora": ev["ora"],
                "generated_by": GENERATED_TAG
            }
            tickets.append(ticket)
    if tickets:
        COL_BIGLIETTO.insert_many(tickets)
        print(f"[Tickets] inseriti {len(tickets)} biglietti")

def create_reviews_and_feedback():
    eventi = list(COL_EVENTO.find({"generated_by": GENERATED_TAG}))
    recs = []
    for ev in eventi:
        for _ in range(random.randint(1,6)):
            recs.append({
                "_id": ObjectId(),
                "Evento": ev["_id"],
                "Stelle": random.randint(1,5),
                "Commento": random_string(80),
                "generated_by": GENERATED_TAG
            })
    if recs:
        COL_RECENSIONE.insert_many(recs)
        print(f"[Reviews] inserite {len(recs)} recensioni")
    # feedback
    fdocs = []
    for _ in range(int(len(eventi)/10)+1):
        fdocs.append({
            "_id": ObjectId(),
            "Testo": random_string(80),
            "generated_by": GENERATED_TAG
        })
    if fdocs:
        COL_FEEDBACK.insert_many(fdocs)
        print(f"[Feedback] inseriti {len(fdocs)} feedback")

def cleanup_generated():
    """Rimuove i documenti creati con generated_by tag"""
    total = 0
    for coll in [COL_UTENTE, COL_EVENTO, COL_RECENSIONE, COL_FEEDBACK, COL_BIGLIETTO]:
        res = coll.delete_many({"generated_by": GENERATED_TAG})
        print(f"[Cleanup] {res.deleted_count} cancellati in {coll.name}")
        total += res.deleted_count
    print(f"[Cleanup] totale cancellati: {total}")

def create_services():
    """Crea servizi offerti per fornitori"""
    fornitori = list(COL_UTENTE.find({"Ruolo": "3", "generated_by": GENERATED_TAG}))
    services = []
    tipi_servizio = ["Animazione per bambini", "Catering", "Musica Live", "Decorazioni"]
    for forn in fornitori:
        num_services = random.randint(1,3)
        for _ in range(num_services):
            service = {
                "_id": ObjectId(),
                "Descrizione": random_string(50),
                "Tipo": random.choice(tipi_servizio),
                "Prezzo": str(random.randint(50,500)),
                "Quantità": str(random.randint(1,10)),
                "FotoServizio": [],
                "fornitore_associato": forn["_id"],
                "isDeleted": False,
                "isCurrentVersion": None,
                "generated_by": GENERATED_TAG
            }
            services.append(service)
    if services:
        COL_SERV_OFF.insert_many(services)
        print(f"[Servizi Offerti] inseriti {len(services)} servizi")

# ----------------- MAIN -----------------

def main():
    print("Popolazione DB: START")

    # 1. Crea utenti
    create_users()

    # 2. Crea eventi
    event_ids = create_events()

    # 3. Aggiungi iscrizioni agli eventi
    if event_ids:
        add_subscriptions(event_ids)
        # Se hai la funzione create_tickets() la puoi chiamare qui

    # 4. Crea recensioni e feedback
    create_reviews_and_feedback()

    # 5. Crea servizi offerti
    create_services()

    print("Popolazione DB: DONE")
    print("Se vuoi rimuovere i dati: esegui cleanup_generated() alla fine del file o via REPL")


if __name__ == "__main__":
    main()
