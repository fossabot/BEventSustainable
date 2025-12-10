import pytest
import time
import os
from codecarbon import EmissionsTracker

# Importiamo la funzione "CPU-intensive" dal tuo progetto.
# Questa funzione è stata scelta perché rappresenta un carico computazionale puro (algoritmo di filtraggio),
# ideale per misurare l'efficienza del codice Python indipendentemente dal database o dalla rete.
from BEvent_app.GestioneEvento.GestioneEventoService import filtrare_servizi_per_fornitore


# =================================================================================================
# SEZIONE 1: MOCKING E GENERAZIONE DATI SINTETICI
# =================================================================================================
# In questa sezione creiamo oggetti "finti" (Mock) che simulano la struttura del database.
# OBIETTIVO GREEN: Evitare di accendere il database reale durante i micro-benchmark riduce
# drasticamente l'overhead energetico del test stesso ("Green Testing").

class MockFornitore:
    """Classe Mock per simulare un oggetto Fornitore senza dipendenze dal DB."""

    def __init__(self, id_fornitore):
        self.id = str(id_fornitore)


class MockServizio:
    """Classe Mock per simulare un oggetto Servizio senza dipendenze dal DB."""

    def __init__(self, id_servizio, id_fornitore_associato):
        self._id = str(id_servizio)
        self.fornitore_associato = str(id_fornitore_associato)


def genera_dati_stress():
    """
    Genera un dataset massivo in memoria per stressare l'algoritmo.
    Crea 1.000 fornitori e 10.000 servizi.
    """
    print("\n[SETUP] Generazione dataset sintetico (10k servizi)...")

    # Generiamo 1.000 fornitori univoci
    lista_fornitori = [MockFornitore(i) for i in range(1000)]

    # Generiamo 10.000 servizi
    lista_servizi = []
    for i in range(10000):
        # Logica di distribuzione:
        # Usiamo il modulo % 2000 per assegnare i servizi.
        # Poiché i fornitori sono solo 1000 (ID 0-999), metà dei servizi (ID 1000-1999)
        # non troveranno corrispondenza. Questo costringe l'algoritmo di filtro a lavorare davvero.
        fornitore_id = i % 2000
        lista_servizi.append(MockServizio(i, fornitore_id))

    return lista_servizi, lista_fornitori


# Eseguiamo la generazione una volta sola all'avvio del modulo di test
SERVIZI_MOCK, FORNITORI_MOCK = genera_dati_stress()


# =================================================================================================
# SEZIONE 2: TEST DI EFFICIENZA ALGORITMICA (OPS)
# =================================================================================================
# Questo test utilizza la libreria `pytest-benchmark`.
# OBIETTIVO: Misurare la velocità pura e il Throughput (Operazioni Per Secondo).
# Un alto numero di OPS indica un codice ottimizzato che spreca pochi cicli di clock.

def test_benchmark_filtro_servizi(benchmark):
    """
    Benchmark di velocità per l'algoritmo di filtraggio.
    Il risultato sarà una tabella statistica (Min, Max, Mean, OPS).
    """
    # La fixture 'benchmark' esegue la funzione target migliaia di volte,
    # calcolando statistiche precise al microsecondo.
    risultato = benchmark(filtrare_servizi_per_fornitore, SERVIZI_MOCK, FORNITORI_MOCK)

    # Assert funzionale: verifichiamo che il filtro abbia lavorato correttamente
    # e non abbia restituito una lista vuota per errore.
    assert len(risultato) > 0


# =================================================================================================
# SEZIONE 3: TEST DI IMPATTO ENERGETICO (JOULE/CO2)
# =================================================================================================
# Questo test utilizza la libreria `CodeCarbon`.
# OBIETTIVO: Misurare il consumo energetico reale (Watt/Joule) della CPU sotto sforzo.
# Poiché una singola esecuzione è troppo veloce per essere misurata dai sensori hardware,
# eseguiamo la funzione in un loop continuo per 5 secondi ("Soak Micro-Test").

def test_energy_profile_filtro_servizi():
    """
    Profilazione energetica dell'algoritmo.
    Esegue la funzione in loop per 5 secondi per permettere a CodeCarbon
    di rilevare il consumo energetico della CPU tramite sensori RAPL/PowerMetrics.
    """
    # Configura CodeCarbon per salvare il report 'emissions.csv' nella cartella corrente
    output_dir = os.getcwd()

    tracker = EmissionsTracker(
        project_name="Micro_Benchmark_Filter",
        measure_power_secs=0.1,  # Campionamento ad alta frequenza (ogni 0.1s)
        save_to_file=True,
        output_dir=output_dir
    )

    tracker.start()  # Inizio misurazione

    start_time = time.time()
    iterazioni = 0
    duration = 5  # Durata dello stress test in secondi

    print(f"\n[ENERGY] Avvio stress test CPU per {duration} secondi...")

    # Ciclo di carico continuo
    while time.time() - start_time < duration:
        # Chiamata alla funzione target
        filtrare_servizi_per_fornitore(SERVIZI_MOCK, FORNITORI_MOCK)
        iterazioni += 1

    emissioni = tracker.stop()  # Fine misurazione e salvataggio CSV

    # Stampa dei risultati a video per feedback immediato
    print(f"[ENERGY] Test completato.")
    print(f" -> Iterazioni totali: {iterazioni}")
    print(f" -> Throughput medio: {iterazioni / duration:.2f} iter/s")
    print(f" -> Emissioni CO2 stimate: {emissioni} kg")


# --- AGGIUNTA PER CONFRONTO (Sotto al codice esistente) ---

# Funzione "Lenta" (Simuliamo come era il codice PRIMA dell'ottimizzazione)
def filtrare_servizi_inefficiente(servizi_non_filtrati, fornitori_filtrati):
    """
    Versione NON OTTIMIZZATA dell'algoritmo.
    Usa una lista invece di un set. La ricerca 'in list' è O(N),
    rendendo l'algoritmo complessivo O(N*M) (molto lento).
    """
    # Lista semplice (NO Set)
    ids_list = [f.id for f in fornitori_filtrati]

    servizi_filtrati = []
    for servizio in servizi_non_filtrati:
        # Questa riga è lenta: cerca linearmente nella lista ogni volta
        if servizio.fornitore_associato in ids_list:
            servizi_filtrati.append(servizio)
    return servizi_filtrati


# Benchmark della versione Lenta
def test_benchmark_filtro_slow(benchmark):
    risultato = benchmark(filtrare_servizi_inefficiente, SERVIZI_MOCK, FORNITORI_MOCK)
    assert len(risultato) > 0


# Benchmark PEDANTIC (Precisione Massima per la versione veloce)
def test_benchmark_filtro_pedantic(benchmark):
    """
    Esegue il benchmark in modalità 'Pedantic' per controllare esattamente
    rounds e iterazioni, utile per micro-misurazioni stabili.
    """
    benchmark.pedantic(
        filtrare_servizi_per_fornitore,
        args=(SERVIZI_MOCK, FORNITORI_MOCK),
        iterations=10,
        rounds=50
    )