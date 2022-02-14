import requests as requests
from bs4 import BeautifulSoup as bs
import os
from PyPDF2 import PdfFileMerger, PdfFileReader

########################################################################################################################
# Dieses Script dient dem automatischen Download von Büchern von "https://elibrary.utb.de/".                           #
# Benötigt wird lediglich die URL des Buches.                                                                          #
# Es ist funktional und kann an mehreren Stellen verbessert werden. (Multiprocessing, Linkkürzung, etc.)               #
########################################################################################################################

class UserAbort(Exception):
    pass

def download_book(path, name, url):
    download_links = get_download_links(url)

    count = len(download_links)
    mergedObject = PdfFileMerger()

    chap_name = ''
    for i in range(0, count):
        chap_name = name + '_' + str(i + 1) + '.pdf'
        print('Lade Unterkapitel ' + str(i + 1) + '/' + str(count))
        download_subsection_as_pdf(chap_name, download_links[i])
        # print('Unterkapitel ' + str(i + 1) + '/' + str(count) + ' erfolgreich heruntergeladen')
        mergedObject.append(PdfFileReader(chap_name, 'rb'))
        os.remove('./' + chap_name)
    mergedObject.write(path + name + '.pdf')
    print("Buch wurde erfolreich unter " + os.path.abspath(path) + "\\ gespeichert!")

def get_download_links(url):
    print("Suche Unterkapitel...")
    site = requests.get(url)
    soup = bs(site.content, 'html.parser')
    subsections = soup.find_all('div', {'class': 'issue-item__title'})
    links = [(url + '/../../../..' + a['href']) for div in subsections for a in div.find_all('a')]
    print("Es wurden", len(links), "Unterkapitel gefunden.")
    rtn = []
    count = 1
    for link in links:
        print("Suche Downloadlink für Unterkapitel", count)
        count += 1
        soup = bs(requests.get(link).content, 'html.parser')
        html_download_item = soup.find_all('div', {'class': 'card--shadow mt-4 pdf-download-box'})
        rtn += [(url + '/../../../..' + a['href']) for div in html_download_item for a in div.find_all('a')]
    return rtn

def download_subsection_as_pdf(name, link):
    with open(name, 'wb') as file:
        file.write(requests.get(link).content)


def path_check():
    path = '..\\' + input('In welchem Ordner soll das Buch gespeichert werden: (Enter drücken für den Ordner in dem der Programmordner liegt) ')
    if not os.path.isdir(path):
        os.mkdir(path)
    if path == '..\\':
        return path
    return path + '\\'

def url_check():
    def get_status(url):
        try:
            status = requests.get(url).status_code
        except Exception:
            status = 0
        return status
    url = input("Hier die vollständige URL aus dem Browser eingeben: ")
    status = get_status(url)
    while status != 200 and input("Ungültige URL. Wollen Sie es erneut versuchen? (j/n) ").capitalize() == "J":
        url = input("Hier die vollständige URL aus dem Browser eingeben: ")
        status = get_status(url)
    if status == 200:
        return url
    raise UserAbort("Keine gültige URL eingegeben.")

def clear():
    os.system("cls")

def hilfe_menue():
    print("\nHILFE\n\nDas Programm gliedert sich in zwei Hauptbestandteile:\n 1. Buch herunterladen\n 2. Hauptmenü")
    select = input("\nÜber was möchten Sie mehr wissen? (1/2) ")
    clear()
    if select == "1":
        print("\nERKLÄRUNG ZUM AUTOMATISCHEN HERUNTERLADEN VON BÜCHERN\n")
        print(
            "Das Programm leitet Sie durch drei Benutzereingaben:\n 1. In welchem Ordner soll das Buch gespeichert werden?\n 2. Unter welchem Namen soll das Buch gespeichert werden?\n 3. Hier die vollständige URL aus dem Browser eingeben:")
        select = input("\nZu welcher Benutzereingabe haben Sie eine Frage? (1/2/3) ")
        clear()
        if select == "1":
            print("\n1. IN WELCHEM ORDNER SOLL DAS BUCH GESPEICHERT WERDEN?\n")
            print(
                "Das Programm setzt voraus, dass der Programmordner im übergeordeneten Ordner liegt, in dem alle Bücherordner liegen.")
            print(
                "Wenn keine Eingabe erfolgt (nur Enter drücken), wird das Buch in dem Ordner, in dem der Programmordner liegt, gespeichert.")
            print(
                'Bei Eingabe eines validen Windows-Ordnernamens (Pfadlänge kürzer 250 Zeichen und Nutzung von "\\") wird dieser Ordner benutzt oder erstellt.')
            print('\nBEISPIEL:\n Liegt der Programmordner im Ordner "Uni\EBooks" führt eine leere Eingabe (Enter) zum Speichern der Unterkapitel im Ordner "EBooks".')
            print(' Gibt man den Ordnernamen "Kunkel Rechtsgeschichte" ein, speichert das Programm die Unterkapitel unter "Uni\EBooks\Kunkel Rechtsgeschichte\\".')

        elif select == "2":
            print("\n2. UNTER WELCHEM NAMEN SOLL DAS BUCH GESPEICHERT WERDEN?\n")
            print(
                "Das Buch wird als eine PDF in dem vorher gewählten Ordner abgelegt.")
            print(
                'BEISPIEL:\n Wenn ein Buch mit 5 Unterkapiteln unter dem Namen "Test" abgespeichert werden soll, ergibt sich also eine PDF mit dem Namen "Test".')

        elif select == "3":
            print("\n3. HIER DIE VOLLSTÄNDIGE URL AUS DEM BROWSER EINGEBEN:\n")
            print('Die URL ist die Internetadresse der Hauptseite des Buches auf "elibrary.utb.de".')
            print('Die Hauptseite des Buches bietet eine Übersicht über die Unterkapitel und ist die erste Seite, die man sieht, wenn man auf einen Buchtitel aus der Suche geklickt hat.')
            print('BEISPIEL:\n Sucht man auf "elibrary.utb.de" nach "Kunkel Rechtsgeschichte", erhält man lediglich ein Buch als Ergebnis.\n Klickt man auf dieses Buch, öffnet sich die Hauptseite des Buches mit der Übersicht über die Unterkapitel.')
            print(' Die URL der Hauptseite kann man mit "Strg+C" kopieren und mit "Strg+V" in die Eingabe des Progammes einsetzen.')

        else:
            print("\nKEINE AUSWAHL GETROFFEN. ABBRUCH.\n")

    elif select == "2":
        print("\nERKLÄRUNG DES HAUPTMENÜS\n")
        print('Mit "Buch herunterladen" startet das automatische Herunterladen eines Buches.')
        print('Mit "Hilfe" gelangen Sie in das Hilfemenü.')
        print('Mit "Programm beenden" beendet sich das Programm.')

    else:
        print("\nKEINE AUSWAHL GETROFFEN. ABBRUCH.\n")

    input("\nENTER DRÜCKEN, UM ZUM HAUPTMENÜ ZURÜCKZUGELANGEN.\n")

def main_menu():
    selection = input(
        "\nHAUPTMENÜ:\n\n 1) Buch herunterladen\n 2) Hilfe\n 3) Programm beenden\n\nBitte wählen Sie eine Option: (1/2/3) ")
    if selection == "1":
        path = path_check()
        name = str(input("Unter welchem Namen soll das Buch gespeichert werden? Hier eingeben: "))
        url = url_check()

        download_book(path, name, url)

        if str(input("Soll ein weiteres Buch heruntergeladen werden? (j/n) ")).capitalize() != "J":
            return
    elif selection == "3":
        exit()
    else:
        clear()
        hilfe_menue()


if __name__ == '__main__':
    print(
        'WILLKOMMEN!\n\nMit diesem Tool können Sie automatisiert Bücher von "elibrary.utb.de" herunterladen.\nHierfür müssen Sie lediglich wissen, wo das Buch gespeichert werden soll und wie die URL von dem Buch ist.\n')
    print(
        'Die Navigation in dem Programm erfolgt über die Tastatur. Geben Sie einfach die gewünschte Option auf der Tastatur ein und drücken Sie Enter.')
    while True:
        try:
            main_menu()
            clear()
        except UserAbort as e:
            print(str(e) + "\nVorgang abgebrochen.")
