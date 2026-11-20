# Roadmap LogiFlow WMS și DevOps

Acest roadmap descrie proiectul de la aplicația de depozit până la rulare, livrare, monitorizare și backup. Scopul nu este să memorezi fiecare comandă, ci să poți explica ce problemă rezolvă fiecare etapă, cum verifici rezultatul și cum revii în siguranță.

## Harta generală

```text
Aplicație WMS
    ↓
Teste automate
    ↓
Imagine Docker versionată
    ↓
GitHub Actions: testare → build → scanare → publicare GHCR
    ↓
Docker Compose local sau Kubernetes local
    ↓
Metrici, dashboarduri, loguri și alerte
    ↓
Backup și restaurare prin LocalStack S3 și Terraform
```

## Etapa 1 — Aplicația WMS

**Stare:** funcționalitățile principale sunt implementate.

### Ce face

- API Python cu FastAPI și validare Pydantic.
- Produse cu SKU unic, dimensiuni, greutate și reguli de validare.
- Cutii și planificarea împachetării produselor.
- Paletizare și verificarea încărcării în camion.
- Locații de depozit, solduri pe locații și reguli de identificare a locației.
- Recepții, picking, transferuri și istoric de mișcări de stoc.
- Comenzi și tranziții de stare pentru procesul outbound.
- Interfață web simplă și documentație API la `/docs`.
- SQLite pentru datele aplicației.

### Fluxul unei cereri

```text
Browser sau client HTTP
  → rută FastAPI
  → validare Pydantic
  → logică WMS
  → funcții SQLite
  → răspuns HTTP și status code
```

### Ce trebuie să poți explica

- Diferența dintre rută/API, model Pydantic, logică de business și accesul la baza de date.
- De ce SKU-ul este identificator unic și de ce o cerere invalidă poate primi `422`.
- Când aplicația răspunde cu `200`, `201`, `404`, `409` sau `503`.
- Cum recepția mărește stocul, picking-ul îl scade și transferul mută stocul între locații.
- De ce soldul total al unui produs trebuie să rămână coerent cu soldurile lui pe locații.
- De ce o operație cu mai multe linii poate avea nevoie de tranzacție și rollback.
- De ce împachetarea ține cont de dimensiuni, orientări și greutate, nu doar de volum.

### Comenzi de lucru și verificare

```bash
python -m pytest -q
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

`pytest` verifică comportamentul codului. `/health` confirmă că API-ul răspunde, iar `/ready` confirmă și că aplicația poate interoga baza de date.

## Etapa 2 — Git și colaborarea prin Pull Request

**Stare:** fluxul de lucru pe branch-uri și PR-uri este folosit în proiect.

### Fluxul obișnuit

```bash
git switch main
git pull
git switch -c feature/nume-scurt
# modificări
git status --short --branch
git diff --check
git diff
git add <fișiere>
git diff --cached --stat
git diff --cached --check
git commit -m "Descriere scurtă"
git push -u origin feature/nume-scurt
```

După push se deschide un PR către `main`, se verifică Actions și diff-ul, apoi se face merge. La final, `main` local se actualizează cu `git switch main` și `git pull`.

### Ce trebuie să reții

- Branch-ul izolează o schimbare; commit-ul o salvează în istoric; push-ul o trimite pe remote.
- PR-ul este locul de revizuire și verificare înainte ca schimbarea să ajungă în `main`.
- `git status` arată branch-ul și modificările; `git diff` arată conținutul lor.
- `git add` selectează fișiere pentru commit. Verifică staged diff-ul înainte să comiți.
- Nu comite parole, token-uri, fișiere Terraform state, baze de date locale sau configurații cu secrete.
- Un merge reușit nu actualizează automat checkout-ul local; pentru asta se face `git pull` pe `main`.

## Etapa 3 — Docker și persistența datelor

**Stare:** imagine Docker și rulare locală cu Docker Compose sunt configurate.

### Concepte

- **Dockerfile:** rețeta de build a imaginii.
- **Imagine:** pachet versionat cu runtime-ul, dependențele și codul aplicației.
- **Container:** procesul pornit dintr-o imagine.
- **Port mapping:** leagă un port local de portul din container.
- **Named volume:** păstrează baza SQLite în afara ciclului de viață al containerului.
- **Compose:** descrie serviciile, porturile, mediul și volumele locale.

### Comenzi importante

```bash
docker build -t logiflow-wms:dev .
docker run --rm -p 127.0.0.1:8000:8000 logiflow-wms:dev
docker ps
docker logs --tail 50 <container>
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail 50 api
docker compose down
```

`docker compose down` oprește și elimină containerele și rețeaua Compose, dar păstrează named volume-ul dacă nu ceri explicit ștergerea lui. Comanda `docker compose down -v` șterge și volumele, deci poate șterge baza locală.

### Ce trebuie să poți explica

- De ce rebuild-ul imaginii nu înseamnă automat că datele SQLite dispar.
- De ce portul din stânga al mapării este portul Mac-ului, iar cel din dreapta este portul containerului.
- De ce `127.0.0.1:8000:8000` limitează accesul la localhost-ul Mac-ului.
- Diferența dintre imagine, container și volum.
- De ce containerul poate fi recreat, dar baza trebuie să supraviețuiască în volum.

## Etapa 4 — CI, scanare și publicarea imaginilor

**Stare:** GitHub Actions rulează teste, construiește și scanează imaginea, apoi publică imagini multi-platformă în GHCR după merge pe `main`.

### Fluxul pipeline-ului

1. Checkout al codului.
2. Instalarea dependențelor fixate.
3. Rularea suitei pytest.
4. Build al imaginii Docker.
5. Scanare Trivy; vulnerabilitățile fixabile High/Critical blochează verificarea.
6. După push pe `main`, autentificare cu `GITHUB_TOKEN` și publicare în GHCR.
7. Buildx/QEMU construiesc variante `linux/amd64` și `linux/arm64`.
8. Imaginea primește un tag bazat pe SHA-ul commit-ului și tag-ul mobil `latest`.

### Ce înseamnă

- **CI (Continuous Integration):** verifică automat modificările la PR/push.
- **CD (Continuous Delivery/Deployment):** aici avem publicare automată a imaginii după merge; deploy-ul în clusterul local rămâne manual.
- **GHCR:** registry-ul în care sunt păstrate imaginile.
- **SHA tag:** identifică exact codul construit și permite deploy repetabil.
- **`latest`:** tag comod, dar mobil; poate indica altă imagine în viitor.
- **Trivy:** verifică pachetele din imagine pentru vulnerabilități cunoscute.
- **Buildx și QEMU:** permit construirea de imagini pentru arhitecturi diferite față de runner-ul care face build-ul.

### Cum verifici

- Deschide tab-ul Actions pentru run-ul asociat PR-ului sau commit-ului.
- Verifică separat testele, build-ul, scanarea și publish job-ul.
- Pentru deploy folosește SHA-ul publicat, nu ghici ce conține `latest`.
- Local, verifică existența imaginii cu:

```bash
docker pull ghcr.io/lunguandrei/logiflow-wms:<full-commit-sha>
docker image inspect ghcr.io/lunguandrei/logiflow-wms:<full-commit-sha>
```

## Etapa 5 — Kubernetes local

**Stare:** aplicația rulează într-un cluster single-node Kubernetes din Docker Desktop, cu PVC și probes.

### Obiecte și roluri

- **Deployment:** declară imaginea, replica dorită și strategia de actualizare.
- **Pod:** unitatea în care rulează containerul API.
- **Service:** oferă o adresă stabilă în cluster pentru Pod.
- **PVC:** cere stocare persistentă pentru baza SQLite.
- **Probe:** readiness decide dacă Pod-ul primește trafic; liveness ajută Kubernetes să repornească un container blocat.
- **Namespace:** separă resursele logic, de exemplu `default` și `monitoring`.

### Comenzi pentru aplicație

```bash
kubectl get nodes
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get deployment,pods,service,pvc
kubectl describe pod <pod-name>
kubectl logs <pod-name> --tail=50
kubectl port-forward service/logiflow-wms 8001:8000
kubectl rollout status deployment/logiflow-wms
kubectl rollout history deployment/logiflow-wms
kubectl rollout undo deployment/logiflow-wms
```

Pentru loguri după un restart, folosește `kubectl logs <pod-name> --previous` cât timp logul containerului anterior mai este disponibil.

### Versionare și revenire

1. CI publică tag-ul cu commit SHA.
2. Actualizezi tag-ul în `compose.yaml` și `k8s/deployment.yaml` printr-un PR.
3. Aplici manifestul și urmărești rollout-ul.
4. Dacă versiunea are probleme, faci rollback și verifici serviciul și datele.
5. Actualizezi manifestul Git la SHA-ul pe care ai decis să-l păstrezi și îl aplici din nou, ca Git și clusterul să fie aliniate.

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/logiflow-wms
kubectl rollout undo deployment/logiflow-wms
kubectl get deployment logiflow-wms -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

### Limita importantă a configurației curente

Clusterul este local și are un singur node. `hostpath` nu este storage de cloud. SQLite și o singură replică sunt potrivite pentru proiectul demonstrativ; nu scala API-ul la mai multe replici scriitoare fără să schimbi arhitectura bazei de date și strategia de storage.

## Etapa 6 — Metrici, dashboarduri, loguri și alerte

**Stare:** metrics-server, Prometheus, Grafana, Loki și Alloy sunt instalate local; dashboardul aplicației și reguli pentru erori HTTP și memorie sunt versionate.

### Cine face ce

- **metrics-server:** valori de utilizare curente pentru `kubectl top`; nu este un sistem de istoric/alertare.
- **Prometheus:** colectează și păstrează metrici, cu limbaj de interogare PromQL.
- **Grafana:** dashboarduri, interogări și evaluare de reguli de alertă.
- **Alloy:** descoperă Pod-urile și colectează logurile.
- **Loki:** păstrează și interoghează loguri cu LogQL.
- **Contact point:** stabilește unde se livrează notificarea, de exemplu e-mail.

### Comenzi de operare

```bash
kubectl top pods -l app=logiflow-wms
kubectl get pods -n monitoring
kubectl logs -n monitoring daemonset/alloy --tail=100
kubectl port-forward -n monitoring deployment/monitoring-grafana 3000:3000
helm list -n monitoring
helm status monitoring -n monitoring
```

Grafana, dashboardurile, regulile, Alloy și Loki au configurații în `k8s/monitoring/`. Contact point-ul `logiflow-email` și setările SMTP pot necesita configurare locală. Nu adăuga parole SMTP în Git.

### Ce trebuie să înțelegi

- Metrică numerică și log text sunt semnale diferite.
- Prometheus folosește PromQL; Loki folosește LogQL.
- Un target `DOWN` nu înseamnă automat că aplicația e stricată; identifică ținta, endpoint-ul și cauza.
- O alertă are expresie, prag/condiție, durată și destinație de notificare.
- Dashboardurile/alertele persistente trebuie păstrate în fișiere provisionate, nu doar create în UI.
- `No data` poate indica interval greșit, datasource greșit, metrică/label nepotrivită sau lipsă de loguri.

## Etapa 7 — Backup, restaurare, LocalStack și Terraform

**Stare:** backup-ul SQLite este copiat din Pod, verificat și încărcat în S3-ul emulat local; Terraform descrie bucketul.

### Fluxul backup-ului

1. Scriptul creează snapshot consistent al bazei SQLite din Pod.
2. Snapshot-ul este copiat pe Mac.
3. Se rulează `PRAGMA integrity_check`.
4. Fișierul este încărcat în bucketul S3 din LocalStack.
5. Pentru verificarea restaurării, fișierul este descărcat și comparat/verificat.

### Comenzi reprezentative

```bash
kubectl get pods -l app=logiflow-wms
./scripts/backup-to-localstack.sh
DOCKER_HOST="$(docker context inspect desktop-linux --format '{{.Endpoints.docker.Host}}')" lstk status
DOCKER_HOST="$(docker context inspect desktop-linux --format '{{.Endpoints.docker.Host}}')" lstk aws s3 ls
```

Din `terraform/localstack/`:

```bash
terraform init
terraform plan
terraform apply
terraform state list
```

`terraform plan` arată schimbările propuse; citește atent dacă resurse se creează, se modifică sau se șterg înainte să confirmi `apply`. `.terraform/` și state-ul local nu se comit. Fișierul `.terraform.lock.hcl` se comite pentru a fixa selecțiile provider-ului.

### Ce trebuie să poți demonstra

- Backup valid și restaurabil, nu doar obiect prezent în bucket.
- Hash identic după upload/download, când verifici integritatea transferului.
- `PRAGMA integrity_check` returnează `ok`.
- Știi unde este copia originală, unde este backup-ul și cum ai restaura fără să suprascrii accidental datele curente.
- LocalStack este emulator AWS local; proiectul nu creează resurse în AWS real și nu implică facturare AWS pentru bucketul local.

## Etapa 8 — Documentație și demonstrarea cunoștințelor

**Stare:** README-ul, recapitularea și acest roadmap documentează funcționarea și operarea proiectului.

### Materiale de portofoliu

- README: ce face aplicația, arhitectură, rulare și limitări.
- Recapitularea din `docs/learning-recap.ro.md`: explicația fluxului și a tehnologiilor.
- Roadmap-ul de față: etapele, comenzile și competențele urmărite.
- Capturi sau demo: interfață, API, Actions verde, dashboard Grafana, query Loki și backup restaurat.

### Verificare personală

Pentru fiecare tehnologie, încearcă să explici fără notițe:

1. Ce problemă rezolvă?
2. Ce fișier sau componentă o configurează?
3. Ce comandă o pornește sau o verifică?
4. Ce rezultat aștepți să vezi?
5. Ce verifici dacă eșuează?
6. Cum revii în siguranță?

Nu este necesar să memorezi pe de rost toate fișierele YAML sau comenzile rare. Este important să înțelegi fluxul, să poți citi configurația, să verifici rezultatele și să găsești cauza unei probleme.

## Etapa 9 — Extensii opționale pentru realism

Acestea sunt pași de aprofundare, nu condiții pentru a considera proiectul demonstrativ complet:

- Exersarea unei versiuni reale AWS cu buget/limite de cost, IAM least privilege și resurse șterse după exercițiu.
- Mutarea de la SQLite la PostgreSQL înainte de a demonstra mai multe replici.
- Adăugarea de autentificare/autorizare și gestionare sigură a secretelor.
- Politici de retenție și rotație pentru loguri și backup-uri.
- Probe de restaurare periodice și procedură scrisă de disaster recovery.
- Alertă verificată cap-coadă: declanșare controlată, e-mail primit, apoi rezolvare.
- GitOps sau deployment automat într-un mediu separat, cu aprobare și rollback.
- Scanare continuă a dependențelor și actualizări periodice ale imaginii de bază.

## Checklist de competențe finale

- [ ] Pot urmări o cerere de la browser până la SQLite și înapoi.
- [ ] Pot rula testele și explica ce validează un test relevant.
- [ ] Pot construi imaginea, porni Compose și explica porturile și volumul.
- [ ] Pot citi un workflow GitHub Actions și explica ce îl face să treacă/eșueze.
- [ ] Pot identifica imaginea exactă după tag-ul SHA și o pot promova controlat.
- [ ] Pot inspecta Pod-uri, loguri, probes, PVC-uri și rollout-uri cu `kubectl`.
- [ ] Pot explica metricile față de loguri și găsi datele în Prometheus/Grafana/Loki.
- [ ] Pot face backup, verifica integritatea și demonstra restaurarea.
- [ ] Pot citi un plan Terraform și evita commit-ul de state sau secrete.
- [ ] Pot explica limitele soluției: cluster local single-node, hostpath, SQLite și lipsa unui deploy AWS real.
