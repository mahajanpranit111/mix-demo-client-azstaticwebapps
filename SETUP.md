# Local Setup Guide

> Run the Nuance Mix Demo Client locally using Docker Desktop.  
> **All operations are local** — nothing is deployed to Azure, AKS, or any cloud resource.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Step-by-Step Setup](#step-by-step-setup)
- [Environment Configuration](#environment-configuration)
- [Running the App](#running-the-app)
- [Using the App](#using-the-app)
- [Common Issues & Fixes](#common-issues--fixes)
- [Stopping the App](#stopping-the-app)
- [Changes from Original Repo](#changes-from-original-repo)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Git](https://git-scm.com/downloads) | Any | Clone the repo |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | 20.10+ | Run containers |
| [mkcert](https://github.com/FiloSottile/mkcert) | Any | Generate local SSL certificates |
| [OpenSSL](https://www.openssl.org/) | Any | Create `.pfx` certificate bundle |

### Installing mkcert

**Windows (winget):**
```powershell
winget install FiloSottile.mkcert
```

**Windows (Chocolatey):**
```powershell
choco install mkcert
```

**macOS:**
```bash
brew install mkcert
```

**Linux:**
```bash
brew install mkcert
```

---

## Quick Start

For those who just want to get running fast:

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd mix-demo-client-azstaticwebapps

# 2. Generate SSL certificates
cd resources
mkcert localhost 127.0.0.1 ::1
mkcert -install
# Create a password file (use any password)
echo -n "password123" > .password
# Create .pfx bundle
openssl pkcs12 -export -out certificate.pfx -inkey localhost+2-key.pem -in localhost+2.pem -password file:.password

# 3. Configure your environment
# Edit .env with your Nuance Mix credentials/URLs (or use .preprod_env for preprod)

# 5. Launch
docker-compose up -d

# 6. Wait ~90 seconds for Gatsby to compile, then open:
#    https://localhost:8000/app/
```

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repo-url>
cd mix-demo-client-azstaticwebapps
```

### 2. Generate SSL Certificates

The app runs over HTTPS locally. You need to generate self-signed certificates.

```bash
cd resources

# Generate cert + key for localhost
mkcert localhost 127.0.0.1 ::1

# Install the local CA (so your browser trusts the cert)
mkcert -install
```

This creates two files in `resources/`:
- `localhost+2.pem` (certificate)
- `localhost+2-key.pem` (private key)

### 3. Create Certificate Password & PFX Bundle

The API container needs a `.pfx` certificate bundle.

**macOS/Linux:**
```bash
echo -n "password123" > .password
openssl pkcs12 -export -out certificate.pfx -inkey localhost+2-key.pem -in localhost+2.pem -password file:.password
```

**Windows (PowerShell):**
```powershell
"password123" | Out-File -NoNewline -Encoding ascii .password
openssl pkcs12 -export -out certificate.pfx -inkey "localhost+2-key.pem" -in "localhost+2.pem" -password file:.password
```

Go back to the project root:
```bash
cd ..
```

### 4. Copy Local Settings

The API (Azure Functions) needs a `local.settings.json` file to know which runtime to use:

```bash
cp resources/local.settings.json api/local.settings.json
```

This file tells Azure Functions to use the **Python** runtime. Without it, the container will prompt for a runtime selection and hang.

### 5. Verify Required Files

Before proceeding, confirm these files exist:

```
resources/localhost+2.pem        ← SSL cert
resources/localhost+2-key.pem    ← SSL key
resources/certificate.pfx        ← PFX bundle
resources/.password              ← PFX password
api/local.settings.json          ← Functions runtime config
.env                             ← Environment variables
```

---

## Environment Configuration

### Default Environment (`.env`)

The `.env` file contains the Nuance Mix service URLs and credentials. It is loaded into both containers at startup.

| Variable | Purpose |
|----------|---------|
| `oauth_server_url` | Nuance OAuth2 server URL |
| `oauth_server_token_path` | Token endpoint path (typically `/token`) |
| `base_url_dlgaas` | Dialog as a Service (DLGaaS) API base URL |
| `base_url_nluaas` | Natural Language Understanding (NLUaaS) API base URL |
| `base_url_ttsaas` | Text-to-Speech (TTSaaS) API base URL |
| `base_url_logapi` | Runtime Event Log API base URL |
| `oauth_scope` | OAuth scopes to request |
| `sendgrid_*` | SendGrid email integration (optional) |

### Pre-production Environment (`.preprod_env`)

A separate `.preprod_env` file is provided for pre-production. Update the URLs to match your preprod endpoints.

### Switching Environments

**Default (production):**
```bash
docker-compose up -d
```

**Pre-production:**

*macOS/Linux:*
```bash
ENV_FILE=.preprod_env docker-compose up -d
```

*Windows PowerShell:*
```powershell
$env:ENV_FILE=".preprod_env"; docker-compose up -d
```

> **Note:** No image rebuild is needed when switching environments. Just restart with the new env file.

---

## Running the App

### Start

```bash
docker-compose up -d
```

This starts two containers:

| Container | Service | Port | Description |
|-----------|---------|------|-------------|
| `gatsby-frontend` | app | `https://localhost:8000` | Gatsby/React frontend |
| `az-functions` | api | `https://localhost:7071` | Azure Functions API (Python) |

### Wait for Startup

The **frontend** takes ~60-90 seconds to compile on first start. You can monitor progress:

```bash
docker logs gatsby-frontend --tail 20
```

Look for the message indicating the dev server is ready (e.g., `success Building development bundle`).

The **API** should be ready within ~15-20 seconds. Verify with:

```bash
docker logs az-functions --tail 20
```

Look for lines showing `Successfully processed FunctionLoadRequest` for all functions.

### Access the App

Open **https://localhost:8000** in your browser.

> Your browser may show a certificate warning for the self-signed cert. Click "Advanced" → "Proceed to localhost" to continue.

---

## Using the App

1. **Enter Credentials**: On the Profile/Auth page, enter your Nuance Mix **Client ID** and **Client Secret** (from [Mix Dashboard](https://mix.nuance.com) → Application Credentials).

2. **Configure Session**: Set your **App Model URN**, channel, language, and session timeout.

3. **Start Session**: Click "Start New Session" to begin a dialog with your bot.

4. **Interact**: Type messages or use voice input depending on the simulated experience selected.

---

## Common Issues & Fixes

### 1. `invalid_client` OAuth Error

**Cause:** Your Client ID or Client Secret is invalid or expired.  
**Fix:** Generate new credentials from [Nuance Mix Dashboard](https://mix.nuance.com) → Application Credentials.

### 2. `Response closed without headers`

**Cause:** The app is trying to use gRPC-web directly from the browser to Nuance servers, which fails due to CORS.  
**Fix:** This is already fixed in this branch. The `isGrpcWeb()` function in `dlgaas.js` returns `false`, routing requests through the local API proxy instead.

### 3. API Container Stuck on "Choose option:" Loop

**Cause:** Azure Functions Core Tools v4 prompts for telemetry consent interactively.  
**Fix:** Already fixed. The Dockerfile pre-creates the telemetry consent sentinel file and sets `FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT=1`.

### 4. API Container Fails with Extension Bundle Error

**Cause:** `host.json` referenced an old extension bundle version incompatible with Functions Core Tools v4.  
**Fix:** Already fixed. Updated `host.json` bundle version from `[1.*, 2.0.0)` to `[3.*, 4.0.0)`.

### 5. API Container Selects Wrong Runtime (dotnet instead of Python)

**Cause:** Missing `local.settings.json` in the `api/` directory.  
**Fix:** Run `cp resources/local.settings.json api/local.settings.json` before starting containers.

### 6. `Cannot read properties of null (reading 'length')`

**Cause:** `sessionId` state becomes `null` after an auth error.  
**Fix:** Already fixed with null guard in `dlgaas.js`.

### 7. `Cannot read properties of undefined (reading 'forEach')` on `visualList`

**Cause:** `visualList` is undefined when the REST proxy response doesn't include visual messages.  
**Fix:** Already fixed with null checks in `chat.js`.

### 8. Bot Responses Not Showing in Chat Panel

**Cause:** The REST API proxy returns snake_case field names (`qa_action`, `messages`) but the UI expects gRPC-web format (`qaAction`, `messagesList`).  
**Fix:** Already fixed. A `normalizePayload()` function in `dlgaas.js` converts REST format to gRPC-web format.

---

## Stopping the App

```bash
docker-compose down
```

This stops and removes both containers and the Docker network.

---

## Changes from Original Repo

This branch (`test-pranit`) includes the following changes to make the app run locally on Docker Desktop:

| File | Change | Why |
|------|--------|-----|
| `api/Dockerfile` | Updated `azure-functions-core-tools-3` → `4` | v3 is EOL and no longer available |
| `api/Dockerfile` | Added telemetry opt-out env vars and sentinel file | Prevents interactive prompt that blocks container startup |
| `api/host.json` | Updated extension bundle `[1.*, 2.0.0)` → `[3.*, 4.0.0)` | Required by Functions Core Tools v4 |
| `docker-compose.yml` | Added `FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT` env var | Additional telemetry suppression |
| `docker-compose.yml` | Changed command to `bash -c "yes \| func host start ..."` | Handles any remaining interactive prompts |
| `docker-compose.yml` | Added `stdin_open: false` | Prevents stdin-based prompts |
| `docker-compose.yml` | Made `env_file` configurable via `ENV_FILE` variable | Supports multiple environments (prod, preprod) |
| `app/src/components/dlgaas.js` | `isGrpcWeb()` returns `false` | Routes DLG requests through local HTTP proxy to avoid CORS |
| `app/src/components/dlgaas.js` | Added `normalizePayload()` function | Converts REST API snake_case response to gRPC-web camelCase format |
| `app/src/components/dlgaas.js` | Added null guard for `sessionId.length` | Prevents crash when `sessionId` is null after auth error |
| `app/src/components/chat.js` | Added null checks for `visualList` | Prevents crash when visual messages are undefined |
| `.preprod_env` | New file | Pre-production environment configuration |
| `api/local.settings.json` | Copied from `resources/` | Tells Azure Functions to use Python runtime |
