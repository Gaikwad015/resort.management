# Software Requirements Specification (SRS)
## Elara Grand Hotel & Resort — Enterprise Management Platform

**Document Version:** 2.0  
**Target Environment:** Python 3.10+ / Django 4.2 LTS / DRF / Tailwind CSS  
**Security Standard:** OWASP Top 10: 2025 Compliance  
**Last Updated:** October 2026  

---

## 1. System Overview & Objective

The **Elara Grand Hotel & Resort Management Platform** is a full-stack, enterprise-grade hospitality and property management system (PMS) modeled after international 5-star luxury resorts (such as JW Marriott Pune). It integrates front-office operations, guest self-service portals, fine dining and spa wellness, staff scheduling, inventory procurement, event logistics, and financial analytics with zero-trust security architecture.

---

## 2. Hardware Requirements

### 2.1 Server-Side (Host / Cloud Deployment)
| Component | Minimum Specification | Recommended Specification (Production) |
| :--- | :--- | :--- |
| **Processor (CPU)** | Dual-Core 2.0 GHz x86-64 | Quad-Core 3.0 GHz+ (Intel Xeon / AMD EPYC / Apple Silicon) |
| **System Memory (RAM)** | 2 GB RAM | 8 GB – 16 GB DDR4/DDR5 |
| **Storage** | 10 GB available SSD space | 50 GB+ NVMe SSD (for media, logs, and database backups) |
| **Network Interface** | 100 Mbps Ethernet / Broadband | 1 Gbps Dedicated Low-Latency Connection |

### 2.2 Client-Side (User & Staff Devices)
| Component | Minimum Specification |
| :--- | :--- |
| **Supported Devices** | Desktop PCs, Laptops, Tablets (iPad / Android), and Smartphones |
| **Display Resolution** | 1280 × 720 (Desktop) / 375 × 667 (Mobile responsive) |
| **Memory (RAM)** | 2 GB minimum |

---

## 3. Software Requirements

### 3.1 System Environment
| Layer | Specification | Notes |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, Ubuntu 20.04/22.04 LTS, Debian 11/12, or macOS 12+ | Cross-platform compatible |
| **Language Runtime** | **Python 3.10, 3.11, 3.12, or 3.14** | Verified on Python 3.14 preview |
| **Web Framework** | **Django 4.2 LTS** | Enterprise Long Term Support |
| **API Framework** | **Django REST Framework (DRF) 3.14+** | Full RESTful JSON serialization |
| **Database (Dev)** | **SQLite 3.35+** | Bundled with Python standard library |
| **Database (Prod)** | **MySQL 8.0+ / MariaDB 10.5+ / PostgreSQL 14+** | Configured via `DB_ENGINE` in `.env` |
| **Client Browsers** | Google Chrome 90+, Mozilla Firefox 88+, Apple Safari 14+, Microsoft Edge 90+ | Full HTML5, CSS3 Grid, Flexbox, ES6+ support |

---

## 4. Python Package Dependencies Matrix

Below is the definitive catalog of all third-party libraries required by the platform, organized by architectural layer:

| Package Name | Minimum Version | Tested Version | Architectural Role & Purpose | OWASP / Security Relevance |
| :--- | :--- | :--- | :--- | :--- |
| **`Django`** | `>=4.2.0,<5.0` | `4.2.30` | Core MVC/MTV web engine, ORM, URL routing, template rendering, and transaction management. | Built-in CSRF, SQL parameterization, XSS escaping, clickjacking defense. |
| **`djangorestframework`** | `>=3.14.0` | `3.17.2` | REST API views, viewsets, serializers, validators, throttling, and content negotiation. | Enforces strict serializer input validation and fail-closed permissions. |
| **`djangorestframework-simplejwt`** | `>=5.3.0` | `5.5.1` | JSON Web Token (JWT) authentication with token rotation and blacklisting. | A07:2025 Cryptographic stateless session authentication with expiration. |
| **`PyJWT`** | `>=2.8.0` | `2.15.1` | Cryptographic JWT payload encoder and decoder using HMAC-SHA256 signatures. | A04:2025 Cryptographic token verification preventing claim manipulation. |
| **`django-axes`** | `>=6.1.0` | `8.3.1` | IP and username-based login failure tracker, rate limiter, and automatic lockout. | A07:2025 Defends against credential stuffing and brute-force attacks. |
| **`django-csp`** | `>=3.7.0` | `4.0` | Content Security Policy HTTP response header generator. | A02/A05: Prevents Cross-Site Scripting (XSS) and unauthorized script injection. |
| **`django-cors-headers`** | `>=4.3.0` | `4.9.0` | Cross-Origin Resource Sharing middleware for mobile and frontend API clients. | Controls and whitelists authorized cross-domain API calls. |
| **`python-dotenv`** | `>=1.0.0` | `1.2.4` | Loads environment variables from `.env` outside source control. | A02: Prevents hardcoded secret keys, DB passwords, and webhook keys in code. |
| **`Pillow`** | `>=10.0.0` | `12.3.0` | Image processing library for suite photos, dining banners, and guest ID uploads. | Validates image header integrity and handles file resizing. |
| **`mysqlclient`** | `>=2.2.0` | `2.3.0` | High-performance C-based MySQL/MariaDB database driver. | Direct binary bridge to relational database with prepared statement support. |
| **`asgiref`** | `>=3.7.0` | `3.12.1` | ASGI specification standard library for asynchronous handling and sync-to-async bridges. | Core async capability support. |
| **`sqlparse`** | `>=0.5.0` | `0.6.0` | Non-validating SQL parser and formatter used internally by Django. | ORM query compilation support. |
| **`tzdata`** | `>=2024.1` | `2026.5` | IANA time zone database for international date/time conversions. | Standardizes check-in, check-out, and SLA calculations across time zones. |
| **`packaging`** | `>=24.0` | `26.3` | Utilities for package version comparison and software bill of materials (SBOM). | A03:2025 Used by `security_audit` to catalog installed supply chain packages. |

---

## 5. Functional Requirements (FR)

### FR-01: Visual Room and Floor Management (`rooms`)
- **FR-01.1:** System shall group all property rooms by floor with interactive status indicators (Available, Occupied, Cleaning, Maintenance).
- **FR-01.2:** System shall enforce a supervisor cleanliness inspection workflow (`is_inspection_approved`) before a room in `CLEANING` status can become `AVAILABLE`.
- **FR-01.3:** System shall provide a transaction-safe room reassignment workflow that preserves existing reservation dates.

### FR-02: Advanced Revenue & Profit Analytics (`analytics`)
- **FR-02.1:** System shall compute live **ADR** (`Total Room Revenue / Occupied Rooms`) and **RevPAR** (`Total Room Revenue / Total Available Rooms`) with zero-division handling.
- **FR-02.2:** System shall aggregate gross revenues across Rooms, Dining Folios, Spa, and Weddings/Events.
- **FR-02.3:** System shall calculate net operating profit by deducting recorded operating expenses and procurement costs.
- **FR-02.4:** System shall generate 7-day and 30-day predictive forecasts based on confirmed reservations and scheduled events.
- **FR-02.5:** System shall stream an RFC 4180-compliant CSV report (`/api/v1/analytics/export/csv/`) for accounting audits.

### FR-03: Guest CRM & Tiered Loyalty (`accounts`)
- **FR-03.1:** System shall assign loyalty tiers (`SILVER`, `GOLD`, `PLATINUM`, `KOHINOOR_VIP`) based on lifetime stays and points balance.
- **FR-03.2:** System shall maintain an immutable, double-entry points ledger (`LoyaltyTransaction`) for earning, redemption, and adjustments.
- **FR-03.3:** System shall persist guest preferences (floor level, bed type, pillow selection, dietary restrictions).

### FR-04: Inventory & Procurement Control (`inventory`)
- **FR-04.1:** System shall track stock movements (`PURCHASE_IN`, `USAGE_OUT`, `WASTAGE_OUT`, `RESTAURANT_OUT`).
- **FR-04.2:** System shall use database row locking (`select_for_update`) to prevent concurrent updates from causing negative stock.
- **FR-04.3:** System shall support multi-item Purchase Orders with approval workflows and automatic stock increment on receipt.

### FR-05: Workforce & Shift Scheduling (`workforce`)
- **FR-05.1:** System shall model departmental hierarchies with assigned department managers.
- **FR-05.2:** System shall reject shift scheduling that creates overlapping shifts for the same staff member on the same date.
- **FR-05.3:** System shall record biometric/digital clock-in and clock-out timestamps with overtime calculation.
- **FR-05.4:** System shall support staff leave requests with manager approval and rejection workflows.

### FR-06: Digital Check-in & Express Checkout (`bookings`)
- **FR-06.1:** System shall provide contactless pre-arrival registration (`GuestPreArrival`) verifying government ID documents before arrival.
- **FR-06.2:** System shall enable real-time posting of incidental folio charges (dining, minibar, spa) to active room folios.
- **FR-06.3:** System shall allow guests to request paperless express checkout, which automatically transitions the room to `CLEANING` and dispatches turnover tasks.

### FR-07: Complaint Management & SLA Escalation (`complaints`)
- **FR-07.1:** System shall assign automatic SLA deadlines based on priority (`URGENT`: 15 min, `HIGH`: 1 hr, `MEDIUM`: 4 hr, `LOW`: 24 hr).
- **FR-07.2:** System shall maintain an append-only audit trail (`ComplaintAudit`) recording every assignment, resolution, and compensation action.

### FR-08: Lost & Found Vault Management (`concierge`)
- **FR-08.1:** System shall register valuables found on premises with vault storage locker locations.
- **FR-08.2:** System shall enforce identity and ownership verification notes before releasing any stored item.

### FR-09: Energy & Sustainability Telemetry (`analytics`)
- **FR-09.1:** System shall track electricity (kWh), water (kL), and natural gas (SCM) meters.
- **FR-09.2:** System shall trigger automated alerts when daily utility consumption exceeds configured safety thresholds.

### FR-10: Transport & Limousine Concierge (`concierge`)
- **FR-10.1:** System shall manage the luxury vehicle fleet and chauffeur assignments.
- **FR-10.2:** System shall support airport pickup/drop-off bookings with flight number tracking.

### FR-11: Weddings & Event Management (`events`)
- **FR-11.1:** System shall maintain ballroom and outdoor amphitheater venue profiles with capacities and daily rental tariffs.
- **FR-11.2:** System shall enforce strict date/time overlap validation to prevent venue double-booking.

### FR-12: Backup & Disaster Recovery (`core`)
- **FR-12.1:** System shall generate timestamped database backups with SHA-256 cryptographic checksum manifests via `backup_database`.
- **FR-12.2:** System shall verify SHA-256 integrity before restoring any backup snapshot via `restore_database`.

### FR-13: Grounded AI Luxury Concierge (`concierge`)
- **FR-13.1:** System shall provide an interactive chat widget grounded in live resort database models (menus, spa services, tariffs, policies) without hallucination.

---

## 6. Non-Functional Requirements (NFR)

| ID | Category | Requirement Specification |
| :--- | :--- | :--- |
| **NFR-01** | **Security (Zero-Trust)** | Every sensitive request shall verify identity, session, role, and resource ownership server-side. No authorization decision shall rely on frontend state. |
| **NFR-02** | **Cryptographic Integrity** | Passwords must use PBKDF2/Argon2. Payment cards must only store masked numbers (last 4 digits). Audit logs must be signed with HMAC-SHA256 checksums. |
| **NFR-03** | **Concurrency & Idempotency** | Room reservations and inventory deductions must use row locking (`select_for_update`) inside atomic database transactions. Duplicate payment submissions must be rejected via idempotency keys. |
| **NFR-04** | **Performance & Latency** | Web pages shall load in < 1.5 seconds. API responses shall return in < 250 ms under normal load. |
| **NFR-05** | **Availability & Recovery** | Database snapshots shall support 100% data recovery within 5 minutes of disaster occurrence. |
| **NFR-06** | **Fail-Closed Boundary** | Unhandled server exceptions shall never leak stack traces to clients. A sanitized error page with an incident correlation ID (`ERR-XXXXX`) must be presented. |

---

## 7. Role-Based Access Control (RBAC) Matrix

The system implements 11 distinct operational roles:

| Role Code | Role Name | System Capabilities |
| :--- | :--- | :--- |
| `SUPER_ADMIN` | Super Administrator | Full unrestricted property control, security threat monitoring, backup restoration, user provisioning. |
| `ADMIN` | General Manager / Admin | Full operational access, financial reports, PO approvals, workforce overrides. |
| `HOTEL_MANAGER` | Hotel Operations Manager | Floor map oversight, room inspections, complaint escalations, occupancy analytics. |
| `RECEPTIONIST` | Front Desk Receptionist | Check-in, check-out, room folio billing, pre-arrival verification, keycard dispatch. |
| `HOUSEKEEPING` | Housekeeping Supervisor | Room status turnover (Cleaning -> Ready), linen replenishment, inspection logs. |
| `RESTAURANT_MANAGER` | F&B / Restaurant Manager | Table reservations, fine dining venue menus, dining room folio posting. |
| `SPA_MANAGER` | Spa & Wellness Director | Spa treatment bookings, therapist schedules, wellness billing. |
| `ACCOUNTANT` | Financial Controller | RevPAR/ADR audit, daily operating expenses, refund approvals, CSV tax reports. |
| `INVENTORY_MANAGER` | Procurement & Storekeeper | Stock adjustments, PO creation and goods receipt, wastage logging, supplier tracking. |
| `EVENT_MANAGER` | Banquet & Wedding Specialist | Ballroom bookings, catering package coordination, event overlap validation. |
| `CUSTOMER` | Resort Guest / Member | Suite bookings, pre-arrival ID upload, express checkout, loyalty points, AI concierge. |

---

## 8. Verification & Test Suite

The platform includes **20 automated test cases** achieving a 100% pass rate:
- **`core.tests_security` (12 tests):** Validates all OWASP Top 10: 2025 categories.
- **`core.tests_enterprise` (8 tests):** Validates floor map workflows, pre-arrival ID verification, express checkout, inventory stock controls, workforce shift overlap detection, event venue overlap prevention, complaint SLA tracking, and grounded AI concierge retrieval.

```powershell
.\venv\Scripts\python.exe manage.py test core.tests_security core.tests_enterprise
# Verification: 20 passed in ~11 seconds (OK)
```
