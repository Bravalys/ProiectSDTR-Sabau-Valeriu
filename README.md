# ProiectSDTR-Sabau-Valeriu

Descriere: Proiectul consta in crearea unui sistem de securitate folosind: o camera web cu rolul a prelua imagini dintr-o incapere si de a detecta miscarile produse, o placa de dezvoltare Raspberry Pi 4 ( varianta cu 4 GB RAM ) unde va fi instalat OpenCV pentru a procesa imaginile de la camera web si pentru a transmite datele procesate catre o baza de date, platforma de dezvoltare de la google: Firebase unde avem baza de date si pentru a transmite notificari pe telefon, un telefon care sa aiba sistemul de operare Android care receptioneaza mesajele trimise de pe platforma Firebas. Raspberry Pi si telefonul vor comunica cu exteriorul prin Wi-Fi.

1. MotionDetection.py  reprezinta elementul software care ruleaza pe Raspberry Pi si actioneaza camera web, prelucreaza imaginiile preluate de camera web si transmite mai departe prin Wi-Fi catre Firebase datele prelucrate.

2. Time_of_movements.csv  reprezinta fisierul unde se salveaza fiecare inceput de detectie a miscarii, mai exact: Data si Ora.
