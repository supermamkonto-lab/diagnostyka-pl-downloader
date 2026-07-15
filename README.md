# Medical Data Collector — Diagnostyka.pl

Automatyczne pobieranie wyników badań (PDF + CDA/XML) z portalu **wyniki.diag.pl**.

---

## 🚀 Szybki Start

### Wymagania
- **Python 3.13+** (zainstalowany)
- **Chrome** (zainstalowany)
- **Połączenie internetowe**

### Instalacja (jednorazowo)

**Opcja 1: Automatyczne menu (POLECANE)**
```bash
cd medical_data_collector
start.cmd
# Kliknij [1] Instalacja/Sprawdzenie → Zainstaluj wszystko
```

**Opcja 2: Ręczna instalacja**
```bash
cd medical_data_collector
pip install -r requirements.txt
python.exe -m playwright install chromium
```

### Uruchomienie

**Opcja 1: Przez menu (POLECANE)**
```bash
start.cmd
```
Następnie wybierz:
- `[3] 🚀 Uruchomienie` → wybrany scenariusz

**Opcja 2: Bezpośrednio z terminala**
```bash
# Pobierz wszystkie wyniki
python.exe run.py collect

# Test: pobierz tylko ostatnie zlecenie
python.exe run.py collect --limit=1

# Pokaż statystykę
python.exe run.py status
```

---

## 🎯 Różne Scenariusze Uruchamiania

### 1. Pierwszy raz — pobierz wszystko
```bash
python.exe run.py collect
```
**Co się dzieje:**
- Otwiera Chrome
- Czeka aż się zalogasz (5 minut)
- Pobiera WSZYSTKIE zlecenia
- Pobiera ALL PDFs + CDAs
- Zapisuje do `DANE_DIAG_PL/`

**Czas:** Zależy od ilości zleceń (100+ zleceń = 30-60 minut)

---

### 2. Test — tylko ostatnie zlecenie
```bash
python.exe run.py collect --limit=1
```
**Używaj aby:**
- Przetestować czy działa
- Sprawdzić czy nazwy plików OK
- Szybko pobrać najnowsze wyniki

**Czas:** ~1-2 minuty

---

### 3. Test — ostatnie 5 zleceń
```bash
python.exe run.py collect --limit=5
```
**Używaj aby:**
- Testować bez pobierania wszystkiego
- Sprawdzić czy CDA się pobiera
- Weryfikacja przed pełną synchronizacją

**Czas:** ~5-10 minut

---

### 4. Pobierz ostatnie 10 zleceń
```bash
python.exe run.py collect --limit=10
```
**Używaj aby:**
- Pobierać tylko świeże wyniki
- Codzienne synchronizacje

---

### 5. Sprawdź status — co już pobrano
```bash
python.exe run.py status
```
**Pokazuje:**
- Ile plików w bazie danych
- Ile pobranych
- Ile czeka na OCR
- Ile importów do MASTER_LAB_DATABASE

**Przykład output:**
```
Portal           Total  Downloaded  OCR done  Imported
diagnostyka_pl   42     42          0         0
```

---

### 6. Odkryj API (dla debugowania)
```bash
python.exe run.py analyze-api
```
**Używaj aby:**
- Analizować ruch sieciowy
- Zrozumieć jakie endpointy API wywołuje portal
- Debugować jeśli coś nie działa

**Co się dzieje:**
1. Otwiera Chrome
2. Czeka aż się zalogasz
3. Nasłuchuje wszystkich API callsów
4. Zapisuje raport do `tools/api_reports/diag_api_capture_*.json`

---

## 🔄 Workflowy

### Workflow 1: Codziennie
```bash
# Porannie — pobierz ostatnie wyniki
python.exe run.py collect --limit=5
```

### Workflow 2: Pełna synchronizacja (jednorazowo)
```bash
# Pierwszy raz — pobierz wszystko
python.exe run.py collect

# Sprawdź czy się powiodło
python.exe run.py status
```

### Workflow 3: Test konfiguracji
```bash
# 1. Zmień config/settings.yaml
# 2. Test ze pojedynczym zleceniem
python.exe run.py collect --limit=1

# 3. Jeśli OK — pełna synchro
python.exe run.py collect

# 4. Sprawdź rezultat
python.exe run.py status
```

### Workflow 4: Troubleshooting
```bash
# 1. Sprawdź status
python.exe run.py status

# 2. Jeśli błędy — analizuj API
python.exe run.py analyze-api

# 3. Sprawdź logi
type logs\*.log

# 4. Retry
python.exe run.py collect --limit=1
```

---

## 📊 Kombinacje Flagi

### Tylko ostatnie zlecenie
```bash
python.exe run.py collect --limit=1
```

### Ostatnie 3 zlecenia
```bash
python.exe run.py collect --limit=3
```

### Ostatnie 20 zleceń
```bash
python.exe run.py collect --limit=20
```

### Wszystkie zlecenia (brak flagi)
```bash
python.exe run.py collect
```

---

## ⏱️ Czasomierze — Co Ile Czasu?

| Sceariusz | Liczba Zleceń | Przybliżony Czas |
|-----------|---------------|------------------|
| `--limit=1` | 1 | 1-2 min |
| `--limit=5` | 5 | 5-10 min |
| `--limit=10` | 10 | 10-20 min |
| `--limit=30` | 30 | 30-45 min |
| Wszystkie (100+) | 100+ | 1-2 godziny |

**Czemu długo?**
- Pobieranie PDFs (każdy kilka MB)
- Pobieranie CDAs (XML)
- Delay 1.5s między requestami (aby nie spamować serwera)
- Retries jeśli sieć się zawiesi

---

## 🎛️ Tuning Wydajności

### Szybciej — mniej delay między requestami
Zmień w `config/settings.yaml`:
```yaml
request_delay_ms: 500      # był 1500 (szybciej ale bardziej agresywnie)
```

### Bardziej niezawodnie — więcej retries
```yaml
max_retries: 5             # był 3 (spróbuj 5 razy zamiast 3)
```

### Bezpieczniej — wolniej
```yaml
request_delay_ms: 3000     # 3 sekundy między requestami
```

---

---

## ⚙️ Konfiguracja (`config/settings.yaml`)

### Ścieżki
```yaml
paths:
  downloads: c:\AI_PROJECTS\LCV_TCM\MEDICAL_DATA_COLLECTOR_DIAGNOSTYKA_PL\DANE_DIAG_PL
  state_db: state/collector.db
  logs: logs
```
**Zmiana:** Edytuj `downloads` aby wskazywał gdzie mają się zapisywać PDFy/CDAs.

### Chrome
```yaml
chrome:
  executable: C:\Program Files\Google\Chrome\Application\chrome.exe
  pwa_app_id: oincohahmilcojpmaimnbgbapfinndnc
  remote_debugging_port: 9222
```
**Zmiana:** Jeśli Chrome jest w innym miejscu, zmień `executable`.

### Portal (wyniki.diag.pl)
```yaml
portals:
  diagnostyka_pl:
    enabled: true
    base_url: https://wyniki.diag.pl
    request_delay_ms: 1500
    max_retries: 3
```
**Zmiana:**
- `request_delay_ms` — czekaj między requestami (aby nie spamować serwera)
- `max_retries` — ile razy spróbować pobrać plik jeśli błąd

### OCR (opcjonalnie)
```yaml
ocr:
  enabled: false
  engine: tesseract
  language: pol+eng
```
**Zmiana:** Ustaw `enabled: true` jeśli chcesz wyciągać tekst z PDFs (wymaga Tesseracta).

---

## 📋 Jak to działa

### 1. Login
```
Program otwiera Chrome
↓
Pokazuje ekran logowania wyniki.diag.pl
↓
TY ręcznie wpisujesz PESEL + hasło
↓
Program czeka aż się zalogasz (max 5 min)
```

**WAŻNE:** Hasło nigdy nie jest zapisywany ani automatyzowany. Login robiłeś ręcznie w przeglądarce.

### 2. Pobieranie listy zleceń
```
Po zalogowaniu program ładuje listę Twoich zleceń
↓
Automatycznie scrolluje aby załadować wszystkie
↓
Zbiera ID każdego zlecenia
```

### 3. Pobieranie dokumentów
```
Dla każdego zlecenia:
  ├─ Pobiera listę dostępnych dokumentów z API
  ├─ Dla każdego dokumentu:
  │  ├─ Pobiera PDF (fileType=1)
  │  └─ Próbuje pobrać CDA/XML (fileType=4, jeśli dostępne)
  └─ Zapisuje z nazwą: RRRR-MM-DD_nazwa_badania.pdf/xml
```

### 4. Nazewnictwo plików
```
Format: RRRR-MM-DD_nazwa_badania.rozszerzenie

Przykłady:
2026-07-14_morfologia.pdf
2026-07-14_morfologia.xml
2026-07-02_APPT_elektrolity.pdf
2026-07-02_APPT_elektrolity.xml
```

Data to **dzień pobrania krwi** (z API), nie czas pobierania przez program.

---

## 💾 Pliki wyjściowe

### Struktura
```
DANE_DIAG_PL\
├── 2026-07-14_morfologia.pdf
├── 2026-07-14_morfologia.xml
├── 2026-07-02_APPT.pdf
├── 2026-07-02_APPT.xml
└── ...
```

### Deduplicacja
Jeśli plik już istnieje na dysku — program go **pomija** (nie pobiera ponownie).

---

## 🔍 Flagi i Opcje

### `--limit=N`
Pobiera tylko N ostatnich zleceń (od najnowszych).

```bash
python.exe run.py collect --limit=1     # Tylko ostatnie zlecenie
python.exe run.py collect --limit=5     # Ostatnie 5 zleceń
python.exe run.py collect               # Wszystkie
```

---

## 📊 Status i Logowanie

### Pokaż statystykę
```bash
python.exe run.py status
```

Wyświetli tabelę:
```
Portal           Total  Downloaded  OCR done  Imported
diagnostyka_pl   42     42          0         0
```

### Logi
Każdy run zapisuje log w: `logs/RRRR-MM-DD_run.log`

Pokaż ostatni log:
```bash
type logs\*.log
```

---

## ⚠️ Ważne dla użytkownika

### 1. Chrome musi być zamknięty
Przed uruchomieniem `collect` **zamknij wszystkie okna Chrome**.
Program otworzy własne okno.

### 2. Login jest ręczny
- Program **nigdy** nie zapisuje hasła
- Login odbywa się w przeglądarce którą widzisz
- Po zalogowaniu się program bierze ciasteczka (JWT tokens)

### 3. Serwer może zablokować
Jeśli pobierasz zbyt szybko (zmniejsz `request_delay_ms`), serwer może zablokować IP.

**Bezpieczne ustawienia:**
```yaml
request_delay_ms: 2000    # 2 sekundy między requestami
max_retries: 5            # Spróbuj 5 razy
```

### 4. Brak internetu
Jeśli utraci się połączenie — program spróbuje 3 razy, potem przejdzie do następnego pliku.

### 5. Pliki CDA mogą być niedostępne
Nie wszystkie wyniki mają CDA. Program gracefully je pomija (bez błędu).

---

## 🛠️ Struktura Programu

```
medical_data_collector/
├── run.py                    ← punkt wejścia (uruchamiaj to)
├── config/settings.yaml      ← konfiguracja
├── requirements.txt          ← zależności Python
│
├── core/                     ← komponenty centralne
│   ├── browser_manager.py    ← launch Chrome
│   ├── session_manager.py    ← login + JWT
│   ├── download_manager.py   ← pobieranie plików
│   └── state_manager.py      ← historia synchro
│
├── database/                 ← baza danych
│   ├── models.py             ← schemat SQLite
│   └── delta_manager.py      ← co nowego pobrać
│
├── portals/                  ← adaptery dla portali
│   ├── base_portal.py        ← interfejs
│   └── diagnostyka_pl.py     ← logika diag.pl
│
├── pipeline/                 ← przetwarzanie
│   ├── ocr_dispatcher.py     ← OCR (opcjonalnie)
│   └── database_updater.py   ← import do master DB
│
└── tools/
    └── api_analyzer.py       ← discovery API (narzędzie)
```

---

## 🐛 Troubleshooting

### "Chrome failed to launch"
**Rozwiązanie:** Sprawdź czy Chrome zainstalowany i zamknięty.
```bash
taskkill /IM chrome.exe /F    # Wymuś zamknięcie Chrome
```

### "Login timeout"
**Rozwiązanie:** Program czeka max 5 minut. Zaloguj się szybciej.

### "Connection refused"
**Rozwiązanie:** Sprawdź czy masz internet i dostęp do wyniki.diag.pl.

### "Permission denied" dla DANE_DIAG_PL
**Rozwiązanie:** Sprawdź czy folder istnieje i masz uprawnienia do zapisu.
```bash
mkdir DANE_DIAG_PL    # Stwórz folder jeśli nie istnieje
```

---

## 📞 Wsparcie

Jeśli coś nie działa:
1. Sprawdź `logs/` ostatni log
2. Spróbuj `--limit=1` do testowania
3. Przeczytaj komunikat błędu w terminalu

---

**Wersja:** 1.0  
**Ostatnia aktualizacja:** 2026-07-14  
**Autor:** Claude Code
