from codecarbon import EmissionsTracker
import time

# Configura il tracker per salvare i dati ogni 2 secondi
tracker = EmissionsTracker(project_name="JMeter_Load_Test", measure_power_secs=2)

print("--- AVVIO MONITORAGGIO ENERGETICO ---")
tracker.start()

print(">> ORA AVVIA JMETER (Clicca Play su JMeter) <<")
print("premi CTRL+C in questa finestra QUANDO JMETER HA FINITO.")

try:
    while True:
        time.sleep(1) # Tiene vivo lo script mentre JMeter bombarda il server
except KeyboardInterrupt:
    # Questo succede quando premi Ctrl+C
    tracker.stop()
    print("--- STOP MONITORAGGIO. Dati salvati in emissions.csv ---")