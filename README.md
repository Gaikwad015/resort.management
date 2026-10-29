# Elara Grand Hotel & Resort — Enterprise Management Platform

A complete, production-grade 5-star Hotel & Resort Management System inspired by world-class luxury properties such as JW Marriott Pune, built with **Django 4.2 LTS, Django REST Framework, and Tailwind CSS**.

This project delivers **12 enterprise modules**, **OWASP Top 10: 2025 security compliance**, a **Zero Trust Architecture**, database-backed transactional integrity, disaster recovery, and interactive hospitality dashboards.

---

## 🏛️ System Architecture & Complete Module Catalog

| Module | Django App | Highlights & Key Capabilities |
| :--- | :--- | :--- |
| **A. Visual Room & Floor Management** | `rooms` | Interactive floor-wise suite map, real-time status indicators (Available, Occupied, Cleaning, Maintenance), room details, room change reassignment workflow, and supervisor inspection approval. |
| **B. Revenue & Profit Analytics** | `analytics` | Real-time calculation of ADR (Average Daily Rate), RevPAR (Revenue per Available Room), Gross Revenue, Operating Expenses, Net Operating Profit, 7/30-day predictive forecasting, and 1-click RFC 4180 CSV export. |
| **C. Guest CRM & Loyalty** | `accounts` | Tiered membership (`SILVER`, `GOLD`, `PLATINUM`, `KOHINOOR_VIP`), automated points ledger, guest profile preferences (pillows, floor, dietary), and anniversary benefits. |
| **D. Inventory & Procurement** | `inventory` | Stock management, low-stock threshold alerts, Purchase Orders with supervisor approval and automated receipt stock increment, negative inventory prevention (`select_for_update`). |
| **E. Workforce & Staff Scheduling** | `workforce` | Department hierarchy, staff profiles, shift scheduling with automatic double-booking conflict detection, biometric clock-in/out attendance, and leave management. |
| **F. Digital Check-in & Express Checkout** | `bookings` | Contactless pre-arrival ID registration, incidental room folio posting (dining, spa, minibar), paperless express departure approval, and automated housekeeping turnover dispatch. |
| **G. Complaints & Service Recovery** | `complaints` | SLA-tracked ticket lifecycle (Urgent 15-min, High 1-hr), priority escalation, department routing, compensation vouchers, and complete audit trail. |
| **H. Lost & Found Management** | `concierge` | Vault registry for guest valuables, location tracking, and verified identity handover workflow. |
| **I. Energy & Sustainability** | `analytics` | Sub-metering for electricity, water, and gas, daily threshold alerts, and green resort cost tracking. |
| **J. Transport & Limousine Fleet** | `concierge` | Portico luxury chauffeur fleet (BMW 730Ld, Mercedes-Benz V-Class, Toyota Vellfire), airport pickup/drop dispatch, and driver assignment. |
| **K. Weddings & Grand Events** | `events` | Grand ballrooms & royal galas, catering plate packages, and automatic date/time overlap prevention to eliminate double-booking. |
| **L. Backup & Disaster Recovery** | `core` | Automated snapshot commands (`backup_database` & `restore_database`), SHA-256 integrity hash verification, and offline tamper-proof storage outside web access. |
| **AI Luxury Guest Concierge** | `concierge` | Grounded resort knowledge engine answering guest inquiries (dining hours, spa treatments, suite tariffs, policies) via a floating widget. |

---

## 🔒 OWASP Top 10: 2025 Security Implementation

| OWASP 2025 Category | Defense Mechanism Implemented in Elara Grand |
| :--- | :--- |
| **A01:2025 - Broken Access Control** | Zero-Trust RBAC with 11 roles, UUIDv4 primary keys (preventing IDOR/BOLA), and `IsOwnerOrStaff` object-level permissions. |
| **A02:2025 - Security Misconfiguration** | Strict Security Headers (CSP, HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff), HttpOnly/SameSite session cookies, and generic error handlers (400, 403, 404, 500). |
| **A03:2025 - Software Supply Chain Failures** | Automated `python manage.py security_audit` command generating `security_sbom.json` cataloging all installed dependencies. |
| **A04:2025 - Cryptographic Failures** | Argon2/PBKDF2-SHA256 password hashing, masked payment records (PCI-DSS safe: only last 4 digits stored), and salt-based HMAC verification. |
| **A05:2025 - Injection** | `AntiInjectionMiddleware` inspecting query strings and request bodies with regex patterns to block SQLi, XSS, and OS command injection with immediate audit logging. |
| **A06:2025 - Insecure Design** | Database row locking (`select_for_update`) inside atomic transactions for reservations and stock deductions; strict state machine transitions. |
| **A07:2025 - Authentication Failures** | Brute-force rate limiting via `django-axes` (lockout after consecutive failures), NIST-compliant password validators, and Step-Up authentication for sensitive administrative actions. |
| **A08:2025 - Software & Data Integrity Failures** | Cryptographic HMAC-SHA256 checksums signed on every `SecurityAuditLog` entry and backup manifest to ensure complete tamper-evidence. |
| **A09:2025 - Security Logging & Alerting** | Centralized `SecurityAuditLog` capturing client IP, user agent, correlation ID, status code, and live threat feed in the Hotel Command Center. |
| **A10:2025 - Mishandling of Exceptional Conditions** | Fail-closed security architecture: unhandled exceptions are caught by a global middleware, generating an incident correlation ID (`ERR-XXXXX`) without leaking server stack traces. |

---

## 🚀 How to Run the Project

### 1. Open Terminal in Project Directory
```powershell
cd d:\resort.management
```

### 2. Activate Virtual Environment & Install Dependencies
```powershell
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows Command Prompt:
venv\Scripts\activate.bat

# Install / verify dependencies from requirements.txt:
pip install -r requirements.txt
```

> **Detailed Specifications:** See the complete [Software Requirements Specification (SRS)](REQUIREMENTS.md) for full hardware, software, functional (FR-01 to FR-13), non-functional, and RBAC matrices.

### 3. Apply Migrations & Seed Luxury Inventory Data
```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed_data
```

### 4. Run the Development Server
```powershell
.\venv\Scripts\python.exe manage.py runserver
```

---

## 🌐 Web Portals & Interfaces

| Portal | URL | Description |
| :--- | :--- | :--- |
| **Luxury Landing Page** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | 5-Star guest portal featuring Suites, Fine Dining, Spa, Weddings, Interactive Booking Modal, and the **AI Concierge widget**. |
| **Hotel Command Center** | [http://127.0.0.1:8000/admin-dashboard/](http://127.0.0.1:8000/admin-dashboard/) | Live RevPAR/ADR KPIs, Floor-Wise Interactive Room Map, Supervisor Cleanliness Approvals, Guest Complaints SLA tracker, and **OWASP 2025 Threat Monitor**. |
| **Guest Sanctuary Dashboard** | [http://127.0.0.1:8000/guest-dashboard/](http://127.0.0.1:8000/guest-dashboard/) | Upcoming stay details, Digital Pre-Arrival ID verification, Express Checkout, Loyalty points ledger, and One-Touch Concierge services. |
| **Django Administration** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | Complete model management with search, filters, and audit logs. |

---

## 🔑 Pre-Seeded Demo Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Super Admin / GM** | `admin@elara.com` | `SecureAdmin123!` | Full access to Hotel Command Center, OWASP Monitor, Financials, and Django Admin |
| **Staff Member** | `staff@elara.com` | `StaffPassword123!` | Front desk, room inspection, and shift operations |
| **Guest (Platinum VIP)** | `guest@elara.com` | `LuxuryGuest123!` | Guest Sanctuary Dashboard, pre-arrival verification, and express checkout |

---

## 🛠️ Management Commands

### 1. Run Automated Security Audit & SBOM Generation
```powershell
.\venv\Scripts\python.exe manage.py security_audit
```
*Outputs: Software Bill of Materials at `security_sbom.json` and verifies cryptographic audit log integrity.*

### 2. Create Secure Timestamped Database Backup
```powershell
.\venv\Scripts\python.exe manage.py backup_database
```
*Creates an integrity-hashed database snapshot with a signed `.manifest.json` inside the protected `backups/` directory.*

### 3. Restore Database with Integrity Verification
```powershell
.\venv\Scripts\python.exe manage.py restore_database --latest --no-input
```
*Verifies the SHA-256 hash against the manifest before restoring to prevent data tampering.*

### 4. Run the Full Test Suite
```powershell
.\venv\Scripts\python.exe manage.py test core.tests_security core.tests_enterprise
```
*Runs all 20 automated tests verifying OWASP 2025 defenses, floor map transitions, express departures, event overlap prevention, and inventory consistency.*

---

## 📚 Viva & Technical Interview Questions & Answers

**Q1: How does the system prevent double-booking of rooms and wedding venues?**  
*Answer:* The system uses **database row-level locking (`select_for_update`)** within atomic transactions (`@transaction.atomic`) for rooms. For event venues, a strict model-level validator queries for any existing confirmed bookings where `start_time < new_end_time` and `end_time > new_start_time`, raising a `ValidationError` if any overlap exists.

**Q2: How does the Zero Trust security model protect guest privacy?**  
*Answer:* We enforce **Object-Level Access Control (OLAC)** on every guest-facing endpoint (such as complaints, pre-arrival, and bookings). Even if an attacker knows another guest's UUID, the backend checks `request.user == obj.user` (or staff verification) and returns a 403 Forbidden.

**Q3: How are financial KPIs like RevPAR and ADR computed?**  
*Answer:* ADR (Average Daily Rate) is calculated as `Total Room Revenue / Number of Occupied Rooms`. RevPAR (Revenue Per Available Room) is calculated as `Total Room Revenue / Total Available Rooms`. Both formulas include zero-division guards to handle empty database states gracefully.

**Q4: How does the AI Concierge avoid hallucinating incorrect resort information?**  
*Answer:* The AI Concierge employs a **grounded retrieval engine** that fetches verified facts directly from the active PostgreSQL/SQLite database models (`RoomType`, `DiningVenue`, `SpaService`, `EventVenue`). It matches queries to specific intents and provides accurate timings, menus, and tariff numbers.
