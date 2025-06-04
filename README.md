# Parcial 2 — Arquitectura de microservicios (Flask/FastAPI + RabbitMQ + Traefik)

Sobre los conceptos teóricos, acá están las respuestas a la parte teórica redactas a mano y elaboradas coloquial pero técniicamente:

rabbit MQ es un message-broker, aen español podríamos llamarlo "gestor o repartidor de mensages", en inglés broker es un intermediario que gestiona actividades o procesos para sus clientes, así rabbit gestiona consumidores y productores, y de paso aísla fallos
Una cola es un proceso más organizado de punto-a-punto, mientras que fanout sencillamente entrega copias de un mensaje a todos los consumidores suscritos, cola es mejor para ambientes que requieren seguridad y orden, fanout es mejor para broadcast
¿Qué es una Dead Letter Queue (DLQ) y cómo se configura? Una cola a la que RabbitMQ redirige mensajes que expiran, superan reintentos o son rechazados (con requeue=false.)

Diferencia volumen vs bind-mount: **Volumen:** gestionado por Docker; ruta en /var/lib/docker/volumes; portabilidad y driver plugins. **Bind mount:** ruta real del host; refleja permisos y estructura del host. Ej.: - ./src:/app/src.
**Efecto de network_mode: host** : El contenedor comparte la pila de red del host: mismos puertos, IP y tablas. Pros: latencia mínima; Contras: sin aislamiento puede chocar con puertos ocupados en Mac/Windows.

Traefik
Rol en microservicios	Reverse proxy / API Gateway: auto-descubre servicios (como labels), balancea carga, termina TLS, hace path routing, aplica middlewares (rate-limit, auth, …).
**Endpoints TLS automáticos**	Se habilita ACME en la línea de comandos o traefik.yml:
certificatesResolvers.myresolver.acme.tlsChallenge=true y entryPoints.websecure.address=:443. Luego se etiqueta un router: traefik.http.routers.api.tls.certresolver=myresolver. Traefik solicita y renueva los certificados de Let’s Encrypt automáticament

## Evidencias

| Paso | Screenshot |
| --- | --- |
| Contenedores levantados |  ![Screenshot from 2025-06-03 18-46-43](https://github.com/user-attachments/assets/cea75f85-f160-4c53-b62f-2e48e0ce6ab3)
   |
| Llamada exitosa al endpoint |   ![Screenshot from 2025-06-03 18-57-11](https://github.com/user-attachments/assets/05190386-0a43-4b5d-b758-bba710fee90f)
  |
| Archivo creado por el worker |   ![Screenshot from 2025-06-03 19-17-52](https://github.com/user-attachments/assets/7688d862-5d79-4f76-9ed6-758eb9cf8789)
  |
| RabbitMQ dashboard |  ![Screenshot from 2025-06-03 19-30-54](https://github.com/user-attachments/assets/4b279c64-478d-4652-be12-cacb9cb12abe)
   |

---

## Diagrama en mermaid

```mermaid
graph TD
    A[Client<br>(browser / curl)] -->|HTTP :80| T(Traefik)
    T -->|/api → 8000| API[FastAPI<br>service]
    T -->|/monitor → 15672| RMQUI[RabbitMQ<br>Management]

    API -->|AMQP 5672<br>publish message| RMQ[(RabbitMQ<br>broker)]
    RMQ -->|consume| WK[Worker<br>Python script]
    WK -->|write JSON| VOL[[processed_messages<br>(volume)]]

```

La estructura mínima del repo queda así:

```
.
├── api/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── worker/
│   ├── worker.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
└── README.md          ← guía abajo
```

### 2.4 Traefik ⇄ routing

- `PathPrefix("/api")` → contenedor **api** (`POST /api/message`, `GET /api/health`).
  
- `PathPrefix("/monitor")` → GUI de RabbitMQ (originalmente :15672).
  

Todo se declara con **labels** (no se necesita archivo `.toml`).

### 2.5 Extra (bonus) — Monitoreo ligero

- Ya existe `/health` en API (rápido de comprobar con `curl`).
  
- `traefik` y `worker` imprimen logs a *stdout/stderr* → visibles con `docker compose logs`.
  
- Compose heredará *exit codes*; no incluimos *healthchecks* específicos por la instrucción de evitar comprobaciones redundantes.

- **Requisitos**
  
  ```bash
  Docker ≥ 24.0  
  docker compose ≥ 2.27
  ```
  
- **Cómo ejecutar**
  
  ```bash
  git clone <repo>
  cd Parcial2
  docker compose up --build -d
  ```
  
- **Pruebas rápidas**
  
  ```bash
  curl -u admin:secret -X POST http://localhost/api/message \
      -H "Content-Type: application/json" \
      -d '{"hello":"world"}'
  # → {"status":"queued"}
  ```
  
