# Recapitulare LogiFlow WMS și DevOps

Acest document explică pe scurt cum circulă o cerere prin proiect și ce rol au tehnologiile folosite.

## 1. Cererea și codul Python

Un utilizator trimite o cerere HTTP din interfața web sau din `/docs`. FastAPI găsește ruta potrivită, de exemplu `/products` sau `/orders`, apoi Pydantic verifică forma și valorile datelor.

Codul din `app/main.py` coordonează cererea. Logica de depozit — stoc pe locații, recepții, transferuri, picking, împachetare, paleți și camion — este împărțită în module Python din `app/`. Funcțiile din `app/database.py` citesc și modifică datele SQLite.

Pe scurt:

```text
Browser/API → FastAPI route → Pydantic validation → business logic → SQLite
```

Răspunsul HTTP include un status: `200` înseamnă succes la citire sau operație, `201` resursă creată, `409` conflict de business, iar `422` datele cererii nu respectă schema.

## 2. SQLite, Docker și volumele

SQLite este motorul bazei de date. Fișierul `logiflow.db` stochează produsele, locațiile, soldurile, mișcările și comenzile.

- **Dockerfile** descrie cum se construiește imaginea aplicației: Python, dependențe, cod și comanda de pornire Uvicorn.
- **Imaginea Docker** este pachetul pregătit pentru rulare.
- **Containerul** este procesul pornit din acea imagine.
- **Volumul Docker** păstrează fișierul SQLite în afara ciclului de viață al containerului.
- **`compose.yaml`** descrie imaginea, portul, variabilele de mediu și volumul pentru rularea locală.

Astfel, recrearea containerului nu recreează automat baza de date.

## 3. Git și pull request-urile

`main` este linia principală a proiectului. O ramură `feature/...` izolează o schimbare ca să poată fi revizuită.

- `git add` selectează modificările pentru următorul commit.
- `git commit` salvează un punct din istoricul local.
- `git push` trimite ramura pe GitHub.
- Pull request-ul arată diferențele și pornește verificările CI.
- Merge-ul introduce schimbarea în `main`; apoi `git pull` actualizează copia locală.

## 4. CI, scanarea și publicarea imaginii

GitHub Actions rulează testele, construiește imaginea și o scanează cu Trivy. Pentru pull request, verificările arată dacă schimbarea trece cerințele CI. După merge, workflow-ul publică imaginea în GHCR pentru `linux/amd64` și `linux/arm64`.

Tag-ul cu SHA complet identifică versiunea de cod exactă. `latest` este o etichetă mobilă care se actualizează la fiecare publicare; pentru deploy-uri reproductibile, fișierele Compose și Kubernetes folosesc tag-ul SHA.

## 5. Kubernetes

Kubernetes menține starea descrisă în manifestele YAML:

- **Deployment** ține aplicația pornită într-un Pod.
- **Pod** este locul în care rulează containerul aplicației.
- **Service** oferă o adresă stabilă în cluster către Pod.
- **PersistentVolumeClaim (PVC)** cere stocare persistentă și o montează în container.
- **Readiness probe** verifică dacă aplicația poate primi trafic; **liveness probe** verifică dacă procesul răspunde.

`kubectl apply` apropie clusterul de configurația din fișiere. `kubectl rollout status` urmărește actualizarea. `kubectl rollout undo` revine la o revizie anterioară; după rollback, manifestul trebuie actualizat la SHA dorit pentru ca fișierul și clusterul să descrie aceeași versiune.

Clusterul folosit aici rulează local în Docker Desktop. Storage class-ul `hostpath` este pentru exerciții locale.

## 6. Metrici, loguri și alerte

- **metrics-server** furnizează valori curente pentru comenzi ca `kubectl top pods`.
- **Prometheus** colectează metrici Kubernetes.
- **Grafana** afișează dashboarduri și evaluează reguli de alertare.
- **Alloy** descoperă podurile și citește logurile lor.
- **Loki** stochează logurile, pe care le poți căuta din Grafana.

Dashboardul LogiFlow și regulile `LogiFlow HTTP errors` și `LogiFlow memory high` sunt exportate în `k8s/monitoring/grafana/`. Regulile provisionate din fișiere se modifică în Git și apoi se încarcă în Grafana. Datele SMTP sunt locale și nu se comit în Git.

## 7. Terraform, LocalStack și backup

Terraform descrie resursele dorite într-un fișier declarativ. În proiect, providerul AWS gestionează bucketul S3 prin LocalStack, care emulează local API-ul AWS S3. Asta exersează Terraform și operațiile S3 fără a crea un bucket într-un cont AWS real.

Scriptul de backup:

1. Folosește API-ul SQLite pentru a crea un snapshot consistent din baza montată în Pod.
2. Copiază snapshotul pe Mac.
3. Rulează `PRAGMA integrity_check`.
4. Încarcă fișierul în bucketul S3 LocalStack.

Un backup util este unul pentru care s-a verificat și restaurarea, nu doar încărcarea.

## Ce demonstrează proiectul

Proiectul demonstrează un flux complet de învățare: aplicație Python → imagine/container → CI și registry → Kubernetes local → monitorizare și loguri → infrastructură locală declarativă → backup și verificarea restaurării.

Nu este o implementare AWS reală sau un sistem gata de producție. SQLite și PVC-ul local justifică păstrarea unei singure replici a API-ului.
