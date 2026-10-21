# My hotdog 🌭

Gra 3D o opiece nad jamnikiem na Androida. Działa w przeglądarce (folder `web`) i jako aplikacja APK (folder `android`).

Grafika 3D jest rysowana własnym, małym silnikiem WebGL wbudowanym w `web/index.html`, więc gra nie potrzebuje żadnych bibliotek z internetu i działa offline.

## Co jest w repozytorium

| Folder / plik | Do czego |
|---|---|
| `web/index.html` | Cała gra |
| `web/config.js` | Adres bazy Firebase do gry we dwoje |
| `android/` | Aplikacja Android, która wyświetla grę |
| `android/apk-version.txt` | Numer wersji APK (zmieniany tylko przy zmianach w `android/`) |
| `.github/workflows/build.yml` | Automatyczne budowanie APK i publikacja gry |
| `firebase-rules.json` | Reguły do wklejenia w Firebase |

## Pierwsze uruchomienie (jednorazowo)

1. Utwórz na GitHubie **publiczne** repozytorium, np. `my-hotdog`, i wrzuć do niego wszystkie pliki z tej paczki (razem z ukrytym folderem `.github`).
2. W repozytorium wejdź w **Settings → Pages** i w polu **Source** wybierz **GitHub Actions**.
3. Wejdź w zakładkę **Actions** i uruchom **Build My hotdog** (albo po prostu zrób dowolny commit).
4. Po kilku minutach APK będzie w zakładce **Releases** jako `my-hotdog.apk`. Pobierz go na telefon i zainstaluj (telefon zapyta o zgodę na instalację z nieznanego źródła).

## Gra we dwoje (Firebase)

1. Wejdź na https://console.firebase.google.com, utwórz projekt (np. `my-hotdog`). Analytics możesz wyłączyć.
2. W menu: **Build → Realtime Database → Create database**, lokalizacja **europe-west1**, tryb **locked**.
3. Zakładka **Rules**: wklej zawartość `firebase-rules.json` i kliknij **Publish**.
4. Skopiuj adres bazy z góry zakładki **Data** (wygląda jak `https://my-hotdog-xxxxx-default-rtdb.europe-west1.firebasedatabase.app`) i wklej go w `web/config.js` w polu `firebaseUrl`.
5. Zrób commit. Gra na telefonach zaktualizuje się sama.

Plan darmowy Firebase (Spark) w zupełności wystarcza.

## Jak działają automatyczne aktualizacje

- **Zmiany w grze (`web/`)**: po każdym pushu GitHub publikuje grę na GitHub Pages. Aplikacja przy każdym otwarciu sprawdza, czy jest nowa wersja, pobiera ją i od razu przeładowuje grę. Postęp zostaje. Nie trzeba instalować nowego APK.
- **Zmiany w aplikacji (`android/`)**: zwiększ liczbę w `android/apk-version.txt` (np. z 1 na 2). Po buildzie aplikacja na telefonie pokaże okno „Nowa wersja My hotdog” z przyciskiem do pobrania nowego APK. Instalujesz ją na starą, postęp zostaje.

APK jest zawsze podpisany tym samym kluczem (`android/keystore/myhotdog.jks`), dzięki czemu nowe wersje instalują się na stare. Nie usuwaj tego pliku. Jeśli zgubisz klucz, trzeba będzie odinstalować starą aplikację (a z nią zapis gry).

## Ustawienia gry do zmiany

Na początku skryptu w `web/index.html`:

- `GROW_H` – po ilu godzinach szczeniak staje się młody i dorosły (domyślnie 24 i 72),
- `DATES_FOR_PUPPY` – ile randek do szczeniaka (3),
- `DATE_COOLDOWN_MIN` – przerwa między randkami w minutach (20),
- `EXTRA_DOG_PRICE` – cena adopcji kolejnego jamnika (150).

Szczeniaki z randek rodzą się tylko z pary piesek i suczka.

## Modele jamników (paczka Unity)

Jamniki w grze to siatki z pliku `Jamniki_Pakiet_Unity.zip` (24 warianty OBJ). Paczka nie miała rigów, UV ani tekstur, więc:

- skrypty w `tools/` (`convert.py`, `dump.py`, `obj.py`) rozkładają siatki na części, naprawiają odwrócone ściany, przesuwają oczy na powierzchnię głowy, liczą wagi skinningu do 28 kości i zapisują wynik w `web/index.html` (blok `const DACH=...`),
- skinning liczy się w grze na procesorze (jedna siatka na psa),
- tekstura (włosie, merle, pręgi, srokate łaty, dzik, podpalane znaczenia, wnętrze pyska) jest generowana w shaderze, bez UV,
- animacje (chód, sztuczki, siku itd.) są liczone w kodzie i działają na szkielecie.

W ustawieniach gry można wrócić do klasycznego modelu z kulek i kapsuł.
