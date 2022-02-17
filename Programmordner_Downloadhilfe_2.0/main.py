import json
import os
import requests
import warnings


from bs4 import BeautifulSoup as bs
from PyPDF2 import PdfFileMerger, PdfFileReader


########################################################################################################################
# Dieses Script ermöglicht das automatische Herunterladen von fragmentierten Büchern von "beck-elibrary.de" und        #
# "elibrary.utb.de". Benötigt wird lediglich die URL des Buches.                                                       #
# Es ist funktional und kann an mehreren Stellen verbessert werden. (Multiprocessing, Linkkürzung, etc.)               #
########################################################################################################################


class UserAbort(Exception):
    pass


class NoValidELibrarySelected(Exception):
    pass


def clear():
    os.system('cls')


def download_book(path: str, name: str, url: str):
    supported_sites = {
        'beck-elibrary': get_download_links_beck_elibrary,
        'elibrary.utb': get_download_links_utb_elibrary
    }
    site_selection = None
    if 'beck-elibrary' in url:
        site_selection = supported_sites['beck-elibrary']
    elif 'elibrary.utb' in url:
        site_selection = supported_sites['elibrary.utb']

    if site_selection is None:
        raise NoValidELibrarySelected()

    print(TEXT_MODULES['work_search_chapters'])

    download_links = site_selection(url)
    count = len(download_links)

    print(TEXT_MODULES['success_count_of_found_chapters'].replace('XYZ', str(count)))

    merged_object = PdfFileMerger()
    chap_name = ''
    for i in range(0, count):
        print(TEXT_MODULES['work_loading_chapter'].replace('XYZ', str(i + 1)).replace('ABC', str(count)))
        file_name = name + str(i) + '.pdf'
        with open(file_name, 'wb') as file:
            file.write(requests.get(download_links[i]).content)
        with open(file_name, 'rb') as file:
            merged_object.append(PdfFileReader(file, strict=False, overwriteWarnings=False))
        os.remove(name + str(i) + '.pdf')

    merged_object.write(path + name + '.pdf')
    print(TEXT_MODULES['success_book_downloaded_and_stored'].replace('XYZ', os.path.abspath(path)))


def get_download_links_beck_elibrary(url):
    soup = bs(requests.get(url).text, HTML_PARSER)
    content_links = soup.find_all('li', {'class': 'pl-contents__item--lvl1'})
    links = list()
    # find unique links
    for content_link in content_links:
        soup = bs(str(content_link), HTML_PARSER)
        download_links = soup.find_all('a', {'class': 'pl-contents__link'})

        for i in range(len(download_links)):
            link = str(download_links[i])

            if i >= 1:
                if link[:64] == str(download_links[i - 1])[:64]:
                    continue

            link = download_links[i]['href']  # returns link as string
            pdf_cut = link[11:].find('/') + 11
            pdf_link = TEXT_MODULES['variable_beck_elibrary_url_start'] + link[:pdf_cut] + TEXT_MODULES['variable_beck_elibrary_pdf_extension']

            links.append(pdf_link)

    return links


def get_download_links_utb_elibrary(url):
    site = requests.get(url)
    soup = bs(site.content, 'html.parser')
    subsections = soup.find_all('div', {'class': 'issue-item__title'})
    links = [(url + '/../../../..' + a['href']) for div in subsections for a in div.find_all('a')]

    rtn = []
    count = 1
    for link in links:
        count += 1
        soup = bs(requests.get(link).content, 'html.parser')
        html_download_item = soup.find_all('div', {'class': 'card--shadow mt-4 pdf-download-box'})
        rtn += [(url + '/../../../..' + a['href']) for div in html_download_item for a in div.find_all('a')]
    return rtn


def help_menu():
    print(TEXT_MODULES['help_start'])
    select = input(TEXT_MODULES['enter_help_start'])
    clear()
    if select == "1":
        print(TEXT_MODULES['help_download_book'])
        select = input(TEXT_MODULES['enter_help_download_book_start'])
        clear()
        if select == "1":
            print(TEXT_MODULES['help_download_book_folder_for_book'])

        elif select == "2":
            print(TEXT_MODULES['help_download_book_name_for_book'])

        elif select == "3":
            print(TEXT_MODULES['help_download_book_enter_full_url'])

        else:
            print(TEXT_MODULES['help_no_input'])

    elif select == "2":
        print(TEXT_MODULES['help_main_menu'])

    else:
        print(TEXT_MODULES['help_no_input'])

    input(TEXT_MODULES['enter_help_finish'])


def main_menu():
    print(TEXT_MODULES['main_menu'])
    selection = input(TEXT_MODULES['enter_main_menu'])
    if selection == "1":
        i = 0
        while i == 0:
            path = path_check()
            name = str(input(TEXT_MODULES['enter_book_name']))
            url = url_check()

            download_book(path, name, url)  # TODO: add ThreadPoolExecutor
            if str(input(TEXT_MODULES['enter_additional_book'])).capitalize() != "J":
                i = 1

    elif selection == "3":
        exit()
    else:
        clear()
        help_menu()


def path_check():
    path = '..\\' + input(TEXT_MODULES['enter_folder_for_book'])
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
    url = input(TEXT_MODULES['enter_full_url'])
    status = get_status(url)
    while status != 200 and input(TEXT_MODULES['enter_invalid_url']).capitalize() == 'J':
        url = input(TEXT_MODULES['enter_full_url'])
        status = get_status(url)
    if status == 200:
        return url
    raise UserAbort(TEXT_MODULES['error_no_valid_url'])

HTML_PARSER = 'html.parser'
TEXT_MODULES = {
  "enter_additional_book": "Soll ein weiteres Buch heruntergeladen werden? (j/n)\n",
  "enter_book_name": "Unter welchem Namen soll das Buch gespeichert werden? Hier eingeben:\n",
  "enter_full_url": "Hier die vollständige URL aus dem Browser eingeben:\n",
  "enter_folder_for_book": "In welchem Ordner soll das Buch gespeichert werden: (Enter drücken für den Ordner in dem der Programmordner liegt)\n",
  "enter_help_download_book_start": "\nZu welcher Benutzereingabe haben Sie eine Frage? (1/2/3)\n",
  "enter_help_finish": "\nENTER DRÜCKEN, UM ZUM HAUPTMENÜ ZURÜCKZUGELANGEN.\n",
  "enter_help_start": "\nÜber was möchten Sie mehr wissen? (1/2)\n",
  "enter_invalid_url": "Ungültige URL. Wollen Sie es erneut versuchen? (j/n)\n",
  "enter_main_menu": "\nBitte wählen Sie eine Option: (1/2/3)\n",

  "error_no_valid_url": "Keine gültige URL eingegeben.",
  "error_user_abort": "\nVorgang abgebrochen.",


  "help_download_book":  "\nERKLÄRUNG ZUM AUTOMATISCHEN HERUNTERLADEN VON BÜCHERN\n\nDas Programm leitet Sie durch drei Benutzereingaben:\n 1. In welchem Ordner soll das Buch gespeichert werden?\n 2. Unter welchem Namen soll das Buch gespeichert werden?\n 3. Hier die vollständige URL aus dem Browser eingeben:",
  "help_download_book_enter_full_url":  "\n3. HIER DIE VOLLSTÄNDIGE URL AUS DEM BROWSER EINGEBEN:\n\nDie URL ist die Internetadresse der Hauptseite des Buches auf \"elibrary.utb.de\" oder \"beck-elibrary.de\".\nDie Hauptseite des Buches bietet eine Übersicht über die Unterkapitel und ist die erste Seite, die man sieht, wenn man\nauf einen Buchtitel aus der Suche geklickt hat.\n\nBEISPIEL:\n Sucht man auf \"elibrary.utb.de\" nach \"Kunkel Rechtsgeschichte\", erhält man lediglich ein Buch als Ergebnis.\n Klickt man auf dieses Buch, öffnet sich die Hauptseite des Buches mit der Übersicht über die Unterkapitel.\n Die URL der Hauptseite kann man mit \"Strg+C\" kopieren und mit \"Strg+V\" in die Eingabe des Progammes einsetzen.",
  "help_download_book_folder_for_book":  "\n1. IN WELCHEM ORDNER SOLL DAS BUCH GESPEICHERT WERDEN?\n\nDas Programm setzt voraus, dass der Programmordner im übergeordeneten Ordner liegt, in dem alle Bücherordner liegen.\nWenn keine Eingabe erfolgt (ENTER drücken), wird das Buch in dem Ordner, in dem der Programmordner liegt, gespeichert.\nBei Eingabe eines validen Windows-Ordnernamens (Pfadlänge kürzer 250 Zeichen und Nutzung von \"\\\") wird dieser Ordner\nbenutzt oder erstellt.\n\nBEISPIEL:\n - Liegt der Programmordner (\"Programmordner_Downlaodhilfe_2.0\") im Ordner \"C:\\Uni\\EBooks\" führt das Drücken von ENTER\n   zum Speichern der Unterkapitel im Ordner \"EBooks\".\n - Gibt man den Ordnernamen \"Kunkel Rechtsgeschichte\" ein, speichert das Programm die Unterkapitel unter\n   \"C:\\Uni\\EBooks\\Kunkel Rechtsgeschichte\\\".",
  "help_download_book_name_for_book":  "\n2. UNTER WELCHEM NAMEN SOLL DAS BUCH GESPEICHERT WERDEN?\n\nDas Buch wird als eine PDF in dem vorher gewählten Ordner abgelegt.\n\nBEISPIEL:\n - Wenn ein Buch mit 5 Unterkapiteln unter dem Namen \"Test\" abgespeichert werden soll, ergibt sich also eine PDF mit\n   dem Namen \"Test\".",
  "help_download_book_no_input": "\nKEINE AUSWAHL GETROFFEN. ABBRUCH.\n",
  "help_main_menu": "\nERKLÄRUNG DES HAUPTMENÜS\n\nMit \"Buch herunterladen\" startet das automatische Herunterladen eines Buches.\nMit \"Hilfe\" gelangen Sie in das Hilfemenü.\nMit \"Programm beenden\" beendet sich das Programm.",
  "help_no_input": "\nKEINE AUSWAHL GETROFFEN. ABBRUCH.\n",
  "help_start": "\nHILFE\n\nDas Programm gliedert sich in zwei Hauptbestandteile:\n 1. Buch herunterladen\n 2. Hauptmenü",


  "main_menu": "\nHAUPTMENÜ:\n\n 1) Buch herunterladen\n 2) Hilfe\n 3) Programm beenden",


  "success_book_downloaded_and_stored": "Buch wurde erfolgreich unter XYZ\\ gespeichert",
  "success_count_of_found_chapters": "Es wurden XYZ Kapitel gefunden.",


  "variable_beck_elibrary_pdf_extension": ".pdf?download_chapter_pdf=1&page=1",
  "variable_beck_elibrary_url_start": "https://beck-elibrary.de",

  "welcome_message": "WILLKOMMEN!\n\nMit diesem Tool können Sie automatisiert Bücher von \"elibrary.utb.de\" und \"beck-elibrary.de\" herunterladen.\nHierfür müssen Sie lediglich wissen, wo das Buch gespeichert werden soll und wie die URL von dem Buch ist.\n\nDie Navigation in dem Programm erfolgt über die Tastatur. Geben Sie einfach die gewünschte Option auf der Tastatur ein\nund bestätigen Sie mit der ENTER-Taste.",

  "work_loading_chapter": "Lade Kapitel XYZ/ABC",
  "work_search_chapters": "Suche Kapitel...",
  "work_search_link_for_chapter": "Suche Downloadlink für Kapitel XYZ"
}


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    print(TEXT_MODULES['welcome_message'])
    while True:
        try:
            main_menu()
            clear()
        except UserAbort as e:
            print(str(e) + TEXT_MODULES['error_user_abort'])
