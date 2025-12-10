import smtplib
from email.mime.text import MIMEText
from ..Utils.Observer import Observer
from .Utente import Utente
from ..Utils import Image


class Fornitore(Utente, Observer):
    """
        Classe che rappresenta un fornitore, derivata dalle classi base Utente e Observer.

        Args:
            user_data (dict): Dati comuni a tutti gli utenti.
            fornitore_data (dict): Dati specifici dei fornitori.

        Attributes:
            descrizione (str): Descrizione del fornitore.
            eventi_max_giornalieri (int): Numero massimo di eventi che il fornitore può gestire al giorno.
            orario_lavoro (str): Orario di lavoro del fornitore.
            foto (list): Elenco di immagini associate al fornitore.
            citta (str): Città del fornitore.
            via (str): Via del fornitore.
            p_Iva (str): Partita IVA del fornitore.
            isLocation (bool): Indica se il fornitore è una location.
        """

    def __init__(self, user_data, fornitore_data):
        """
        Inizializza un nuovo oggetto Fornitore.
        """
        Utente.__init__(self, user_data)
        Observer.__init__(self)

        # Se manca la chiave "Fornitore", evitare crash
        fornitore_info = fornitore_data.get('Fornitore', {})

        # Campi base – sicuri con get()
        self.descrizione = fornitore_info.get('Descrizione', "Non specificato")
        self.eventi_max_giornalieri = fornitore_info.get('EventiMassimiGiornaliero', 0)
        self.orario_lavoro = fornitore_info.get('OrarioDiLavoro', "Non specificato")

        # Lista foto – se mancano, nessun crash
        self.foto = []
        for foto_base64 in fornitore_info.get('Foto', []):
            try:
                immagine = Image.convert_byte_array_to_image(foto_base64)
                self.foto.append(immagine)
            except Exception as e:
                print(f"Errore nella conversione dell'immagine: {str(e)}")

        # Altri campi – sicuri
        self.citta = fornitore_info.get('Citta', "Non specificata")
        self.via = fornitore_info.get('Via', "Non specificata")
        self.p_Iva = fornitore_info.get('Partita_Iva', "Non specificata")
        self.isLocation = fornitore_info.get('isLocation', False)

    def update(self, observable):
        """
               Metodo di callback chiamato quando l'evento osservato è stato annullato.

               Args:
                   observable (Observable): L'oggetto osservato che ha emesso l'evento di annullamento.
               """

        oggetto = "Annullamento dell'evento"
        messaggio_corpo = "L'evento in data " + observable.data + ("è stato annullato! Controlla la tua area fornitore "
                                                                   "per saperne di più! Stiamo avviando le pratiche "
                                                                   "per il rimborso dell'utente :)")
        messaggio = MIMEText(messaggio_corpo, 'plain', 'utf-8')
        messaggio["Subject"] = oggetto

        # Configura la connessione SMTP
        email = smtplib.SMTP("smtp.gmail.com", 587)
        email.ehlo()
        email.starttls()
        email.login("beventc13@gmail.com", "hmbq mcps rmom oiou")

        # Invia l'email
        email.sendmail("beventc13@gmail.com", "simonettidaria@gmail.com", messaggio.as_string())

        # Chiudi la connessione SMTP
        email.quit()
