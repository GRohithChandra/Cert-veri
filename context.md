# Cert-veri project context

**Evidence labels:** `[STATED]` means directly present in the repository or prior conversation; `[INFERRED]` means a source-based deduction, with its basis given; `[NOT DECIDED]` means no evidence was available. This document describes the inspected source; it does not claim that runtime behavior has been tested.

## 1. PROJECT SNAPSHOT

- **Assigned project title:** [NOT DECIDED] The supplied value was the placeholder `[PASTE YOUR TITLE HERE]`; no presentation or project brief was present in the tracked files.
- **Counterpart project title:** [NOT DECIDED] The supplied value was the placeholder `[PASTE THE OTHER TITLE HERE]`.
- **Name displayed in the UI:** [STATED] “CertChain Portal,” used in the page title and home-page navigation in [`templates/index.html`](./templates/index.html).
- **Plain-language summary:** [INFERRED] This is a Flask web application for an administrator to register students and issue certificate records, students to log in and view their certificate-related files and QR code, and unauthenticated verifiers to check a certificate hash against an Ethereum-compatible smart contract. Basis: routes in [`app.py`](./app.py), templates under [`templates/`](./templates/), and [`contract/Certificate.sol`](./contract/Certificate.sol).
- **Problem being addressed:** [STATED] The home page describes certificate issuance and verification as blockchain-backed and says certificates should be tamper-proof and verifiable by employers. [NOT DECIDED] No presentation text or problem statement was available to establish the exact problem framing or claimed need.
- **Target users:** [STATED] The UI has administrator, student, and employer/verifier-facing flows. [INFERRED] The institution is represented by the admin account rather than by a separate institution/issuer entity, because issuance is an admin route and there is no other issuer role in the code.
- **Exact presentation objectives:** [NOT DECIDED] No slides, speaker notes, proposal, or exact presentation objectives were found in the repository or prior conversation.
- **Conversation context:** [STATED] Previous discussion established that the configured Ganache Desktop instance started successfully despite a µWS native-module warning and fallback to a regular Node.js implementation. No source changes were requested or made during that discussion.

## 2. SCOPE

- **Implemented source scope:** [STATED] Flask-rendered pages and routes for admin login, student registration, certificate issuance, admin records, student login/portal/logout, and public certificate verification; MongoDB persistence; local upload/QR file handling; and a Web3.py connection to a Solidity certificate registry.
- **Certificate file generation:** [STATED] Admins upload an existing PDF and student photo. The application generates a QR-code PNG containing the certificate hash; it does not generate the certificate PDF itself.
- **Explicitly out of scope:** [NOT DECIDED] No explicit in-scope/out-of-scope document was found. The absence of a feature in source is recorded in relevant sections but is not treated as an explicit project decision.
- **Counterpart comparison assumptions:** [NOT DECIDED] The counterpart title and project description are unavailable, so no counterpart-specific scope or architecture is assumed.
- **External-system assumptions:** [STATED] The code expects MongoDB and an Ethereum JSON-RPC endpoint (defaulting to local Ganache). [INFERRED] Admin certificate issuance can proceed without MongoDB, but student login and persistence-backed views depend on MongoDB; this follows from the route logic.
- **Verification responsibility:** [STATED] The application itself includes a verifier page and `/verify` route. There is no source evidence that verification is delegated to another project or service.

## 3. ACTORS AND USER FLOWS

### Administrator

- **Capabilities:** [STATED] Login; register a student; issue a certificate; view student and certificate records; logout. Source: [`app.py`](./app.py), [`templates/admin_login.html`](./templates/admin_login.html), and [`templates/dashboard.html`](./templates/dashboard.html).
- **Authentication:** [STATED] `GET/POST /admin/login` compares submitted username and password to literal values `admin` and `admin123`. A successful login sets `session["admin"] = True`. This is not a database-backed admin account.
- **Registration flow:** [STATED] Open admin login → submit username/password → successful login redirects to `/admin/dashboard` → submit the registration form with `student_id`, `name`, `email`, `password`, `department`, `grad_year`, and `cgpa` → app rejects a duplicate student ID or writes the student record to MongoDB → redirect to `/admin/records`.
- **Certificate issuance flow:** [STATED] From the dashboard, submit `student_id`, `name`, `department`, `cgpa`, `passing_year`, `distinction`, `cert_pdf`, and `student_photo` → app checks that contract/Web3 are available and both files exist → saves the PDF and photo under `static/uploads` → computes a SHA-256 hash → invokes `issueCertificate` from the first Ganache account → waits for a receipt → creates a QR PNG → if MongoDB is available, upserts a certificate record and creates a default student account if none exists → redirects to records.
- **Records flow:** [STATED] Open `/admin/records` while logged in → app reads all documents from the `students` and `certificates` collections when MongoDB is connected → dashboard shows student and certificate tables and file/QR links.
- **Logout:** [STATED] `GET /admin/logout` removes the `admin` key from the session and redirects to `/`. The route itself does not check that the caller is logged in.

### Student / certificate recipient

- **Capabilities:** [STATED] Sign in, view profile details and an issued certificate hash, transaction hash, QR image, PDF and photo links, download the QR image, and log out.
- **Authentication:** [STATED] `POST /student/login` searches MongoDB for a case-insensitive exact student ID and matching password. Successful login stores `session["student_id"]`.
- **Flow:** [STATED] Submit student ID and password from the home page → successful login redirects to `/student/portal` → app loads the student document and certificate by student ID → render the student portal. If no certificate record exists, the page says the certificate has not been issued. Logout uses `GET /student/logout`.
- **Default credentials for an auto-created account:** [STATED] When a certificate is issued and no student record exists, the app creates a student document with email `<lowercase student_id>@college.edu` and password `123`.

### Employer / verifier / public visitor

- **Capabilities:** [STATED] Open the verifier page without logging in; enter a hash, upload a QR image through the browser UI, or scan a QR code with a camera; view a valid/invalid result.
- **Authentication:** [STATED] No authentication check is applied to `/verify`.
- **Flow:** [STATED] Enter a certificate hash or use the QR scan UI → browser fills the hash input and submits the form for QR scans → backend calls `verifyCertificate(hash)` on the loaded contract → show returned student name, ID, department, and issue date if valid; otherwise show a failure message.
- **Public visitor:** [STATED] The home page links to certificate verification and admin login and presents a student login form. [INFERRED] A visitor who does not log in can reach the public verification route because it has no session guard.

### Other roles

- **Separate institution/issuer, wallet holder, auditor, or system operator:** [NOT DECIDED] No separate actor account or workflow for these roles is present in the inspected source.

## 4. SYSTEM ARCHITECTURE

- **Frontend:** [STATED] HTML templates rendered by Flask/Jinja, shared stylesheet `static/styles.css`, and browser-side `html5-qrcode` loaded from `https://unpkg.com/html5-qrcode`.
- **Backend:** [STATED] A single Flask application in [`app.py`](./app.py) serves pages and handles form submissions.
- **Blockchain:** [STATED] Web3.py connects to an HTTP JSON-RPC endpoint, default `http://127.0.0.1:7545`, and uses the ABI in `contract/Certificate_abi.json` plus `CONTRACT_ADDRESS` to bind to a deployed contract.
- **Database:** [STATED] PyMongo connects to MongoDB, default `mongodb://localhost:27017/cert_verify_db`; selected database is `cert_verify_db`, with `students` and `certificates` collections.
- **File storage:** [STATED] Uploaded certificate PDFs and student photos are saved under `static/uploads`; QR PNGs are saved under `static/qrcodes`. Both paths are served through Flask's static-file handling.
- **Contract deployment:** [STATED] [`deploy_contract.py`](./deploy_contract.py) compiles `contract/Certificate.sol`, writes the ABI JSON, deploys to the configured Ganache RPC endpoint, and prints the resulting address.

### End-to-end flows

**Certificate issuance**

```text
Admin browser form
  -> Flask POST /admin/issue_certificate
  -> local PDF/photo files + SHA-256 certificate hash
  -> Web3.py HTTP JSON-RPC
  -> Ganache -> CertificateRegistry.issueCertificate(...)
  -> transaction receipt / transaction hash
  -> local QR PNG containing the hash
  -> MongoDB certificate upsert + optional student auto-creation
  -> admin records page
```

- [STATED] The chain call occurs before QR generation and MongoDB update; these operations are not enclosed in a shared transaction.
- [STATED] If MongoDB is unavailable, issuance still attempts the chain transaction and QR generation, while the certificate/student database writes are skipped.

**Student portal**

```text
Student browser form
  -> Flask POST /student/login
  -> MongoDB students lookup
  -> session["student_id"]
  -> GET /student/portal
  -> MongoDB student + certificate lookup
  -> rendered profile, QR, and static-file links
```

**Certificate verification**

```text
Verifier browser: type hash / scan QR
  -> hash submitted to Flask POST /verify
  -> Web3.py calls CertificateRegistry.verifyCertificate(hash)
  -> result data from chain
  -> optional MongoDB lookup by cert_hash for PDF/photo filenames
  -> rendered VALID or INVALID result
```

- [STATED] Verification uses a read-only contract call; it does not submit a blockchain transaction.
- [INFERRED] MongoDB is used only to enrich a valid verification result with local file links; the chain response supplies validity and the main identity fields.

## 5. BLOCKCHAIN LAYER

### Platform, network, provider, and costs

- **Platform:** [STATED] Solidity/Ethereum Virtual Machine-compatible contract, deployed through Ganache and accessed using Web3.py.
- **Network:** [STATED] The previous Ganache startup screenshot showed an Ethereum-flavor Ganache Desktop instance at `127.0.0.1:7545`, `network_id` 5777, `hardfork` `"merge"`, 10 accounts, `default_balance_ether` 100, `gasLimit` 6,721,975, and `gasPrice` 20,000,000,000 wei. The screenshot showed “Ganache started successfully” and “Waiting for requests.”
- **Production network:** [NOT DECIDED] No mainnet, public testnet, or production deployment is identified in source or conversation.
- **Why selected:** [NOT DECIDED] The code defaults to local Ganache, but no explicit rationale for choosing it was documented.
- **Consensus assumptions:** [NOT DECIDED] No consensus mechanism or consensus security assumptions are described. The inspected deployment configuration is a local Ganache development chain.
- **Gas/cost:** [STATED] Contract calls use Ganache account-based transactions and do not supply a gas value in Python's `.transact({"from": ...})` call. The screenshot reports a local gas price and gas limit. [NOT DECIDED] No real-network gas budget or fee analysis is documented.
- **Provider/wallet:** [STATED] Python `web3` 6.20.0 with `Web3.HTTPProvider`; no MetaMask, ethers.js, or web3.js integration appears in the source.
- **Transaction account:** [STATED] Deployment and issuance use `w3.eth.accounts[0]`. The active contract sets `owner = msg.sender` in its constructor, so the deployment account is the contract owner.
- **µWS message:** [STATED] Prior conversation's Ganache log showed it could not load `uws_win32_x64_87.node`, fell back to the Node.js implementation with a performance warning, and nevertheless started successfully. This message concerns Ganache's optional Node.js WebSocket implementation, not a Solidity compile error.

### Active deployment contract: `contract/Certificate.sol`

- **Contract name/language:** [STATED] `CertificateRegistry`, Solidity, source pragma `^0.8.0`; deployment script explicitly installs and compiles with solc `0.8.0`.
- **State variable:** [STATED] `address public owner`.
- **Struct:** [STATED] `Certificate { string studentId; string studentName; string department; string certHash; uint256 timestamp; bool isValid; }`.
- **Mapping:** [STATED] `mapping(string => Certificate) public certificates`, keyed by certificate hash string. The public mapping generates a getter.
- **Constructor:** [STATED] `constructor()` sets `owner` to `msg.sender`.
- **Modifier:** [STATED] `onlyOwner()` requires `msg.sender == owner` and reverts with `"Only owner/admin can perform this action"`.
- **Issue function:** [STATED] `issueCertificate(string memory _studentId, string memory _studentName, string memory _department, string memory _certHash) public onlyOwner`. It rejects an already-valid hash with `"Certificate hash already exists"`, stores the details, block timestamp, and `isValid: true`, then emits `CertificateIssued`.
- **Verify function:** [STATED] `verifyCertificate(string memory _certHash) public view returns (bool isValid, string memory studentId, string memory studentName, string memory department, uint256 timestamp)`. It returns values from the mapping entry; an unset hash returns default values, including `false`.
- **Event:** [STATED] `CertificateIssued(string indexed certHash, string studentId, string studentName, uint256 timestamp)`.
- **Permissions:** [STATED] Only the owner can issue; verification is public. There are no additional Solidity roles in this contract.
- **Revocation/expiry:** [STATED] The active contract has no revoke, expire, or ownership-transfer function.

### Other contract source

- **Root-level source:** [STATED] [`Certificate.sol`](./Certificate.sol) also declares `CertificateRegistry`, but it is a different implementation from `contract/Certificate.sol`. `deploy_contract.py` explicitly compiles the latter, so the root-level file is not selected by that deployment script.
- **Root-level state:** [STATED] `address public owner`; private `mapping(string => Certificate) certificates`; struct fields `bytes32 hash`, `address issuer`, `uint256 issuedAt`, `bool revoked`.
- **Root-level functions:** [STATED] `constructor()` sets owner; `transferOwnership(address newOwner) external onlyOwner`; `storeCertificate(string memory certId, bytes32 hash) external onlyOwner`; `revokeCertificate(string memory certId) external onlyOwner`; `getCertificateHash(string memory certId) external view returns (bytes32)`; `isRevoked(string memory certId) external view returns (bool)`; and `exists(string memory certId) external view returns (bool)`.
- **Root-level events:** [STATED] `CertificateStored(string certId, bytes32 hash, address indexed issuer, uint256 timestamp)`; `CertificateRevoked(string certId, address indexed issuer, uint256 timestamp)`; `OwnerTransferred(address indexed previousOwner, address indexed newOwner)`.
- **Deployment/use status:** [INFERRED] It is not used by the application's deployment path because the deployment script reads `contract/Certificate.sol`, and the checked-in ABI matches the `contract/` version. Whether it was an earlier/discarded implementation is [NOT DECIDED].

### On-chain and off-chain data

- **On-chain:** [STATED] Certificate hash, student ID, student name, department, block timestamp, validity boolean, owner address, and issue event are represented by the active contract.
- **Off-chain MongoDB:** [STATED] Student profiles and certificate metadata, including CGPA, passing year, distinction, transaction hash, file names, QR filename, and issue date.
- **Off-chain local files:** [STATED] PDF, photo, and QR PNG files are stored in the application's local `static` folders.
- **Reason for split:** [NOT DECIDED] No explicit data-placement rationale is documented. [INFERRED] The contract stores text/hash metadata rather than file bytes because the contract interface accepts student text and a hash, not file content.
- **Contract address:** [NOT DECIDED] A deployment script prints a dynamic address and asks the operator to place it in `.env`; the actual address value was not recorded in this document.

## 6. CERTIFICATE GENERATION

- **PDF generation:** [STATED] No PDF-generation library or PDF template is implemented. The admin supplies an existing PDF file.
- **Uploaded inputs:** [STATED] `student_id`, `name`, `department`, `cgpa`, `passing_year`, `distinction`, `cert_pdf`, and `student_photo`. The dashboard marks all but `distinction` as required in HTML; the backend explicitly checks for the PDF and photo but does not show server-side validation of the other fields.
- **Hash function:** [STATED] `generate_cert_hash(student_id, student_name, department, file_bytes) -> str` in [`utils.py`](./utils.py) strips the three text values, concatenates them in the order student ID + name + department without separators, appends the PDF bytes to the SHA-256 input, and returns a lowercase hexadecimal digest.
- **Not included in hash:** [STATED] The code does not pass CGPA, passing year, distinction, photo bytes, or filename to `generate_cert_hash`.
- **Blockchain record fields:** [STATED] Student ID, name, department, the hash, timestamp, and `isValid` are sent/stored by the active contract.
- **QR code:** [STATED] `make_qr_code(cert_hash, output_path)` uses the `qrcode` package with `version=1`, `box_size=10`, `border=4`, black fill, and white background; the QR payload is the hash. Output name is `<student_id>_qr.png` under `static/qrcodes`.
- **Upload file handling:** [STATED] Filenames are built from the student ID, a `_cert_` or `_photo_` marker, and the original filename, then passed through Werkzeug `secure_filename`; stored in `static/uploads`.
- **Multiple/bulk issuance:** [STATED] The route processes one certificate per request. [NOT DECIDED] No bulk-issuance workflow or explicit statement about planned bulk support was found.
- **Unique ID scheme:** [STATED] No separate generated certificate ID is used by this flow; the SHA-256 hash is used as the contract mapping key. MongoDB certificate upsert is keyed by `student_id`.
- **Storage location:** [STATED] Uploaded files and generated QR files are local application static folders; no IPFS, S3, or cloud object-store integration appears in tracked source.

## 7. CERTIFICATE VALIDATION

- **Methods exposed in the UI:** [STATED] Manual hash entry, upload a QR-code image, and live camera QR scan. The page does not offer certificate-PDF upload, student-ID lookup, or wallet lookup.
- **Browser QR handling:** [STATED] `templates/verify.html` loads unversioned `html5-qrcode` from unpkg. For a selected image, browser JavaScript runs `scanFile`, puts decoded text into the hash field, and submits the form. For live scan, `Html5QrcodeScanner` is configured with `fps: 10` and `qrbox: 250`, then submits the decoded text.
- **Backend QR handling:** [STATED] `/verify` also has code to decode a submitted `qr_file` using Pillow and `pyzbar`. [INFERRED] The visible file input has no `name="qr_file"` and the browser-side code submits the decoded hash rather than the file, so the normal UI path does not appear to send a `qr_file` field for that backend branch.
- **Algorithm:** [STATED] Trim submitted hash → optionally replace it with a decoded QR value if backend receives `qr_file` → require nonempty hash, loaded contract, and connected Web3 provider → call `verifyCertificate(hash)` → if returned `isValid` is true, build a valid result; otherwise build invalid result. If MongoDB is connected, look up a certificate document by `cert_hash` to supply optional PDF/photo links.
- **Valid result displayed:** [STATED] “VERIFICATION SUCCESSFUL (GENUINE RECORD),” student name, student roll number, department, issue date, and optional PDF/photo links.
- **Invalid result displayed:** [STATED] “VERIFICATION FAILED (INVALID / FORGERY)” plus a message. Messages cover unregistered hash, blockchain/network unavailable or no hash, and caught verification errors.
- **Result states:** [STATED] The application exposes `VALID` and `INVALID`. [NOT DECIDED] No distinct UI result states for revoked, expired, or not found are implemented in the active contract/app flow.
- **Tamper detection:** [INFERRED] A verifier can compare a supplied certificate hash to the registered blockchain hash only if they provide the hash from the issued record/QR; this route does not accept a PDF and recompute its hash. The code does not prove that the presented PDF bytes correspond to the registered hash during verification.
- **Revocation and expiry:** [STATED] Neither is supported in the active contract/app verification path. The root-level alternative contract has revocation functions, but the app's deploy script does not use it.
- **Reissuance:** [STATED] The active contract prevents issuing a duplicate currently-valid hash. [INFERRED] A different hash for the same student may be issued as a new chain record, while MongoDB upserts by `student_id`, replacing the single stored certificate document for that student; old chain records are not revoked by this code.

## 8. BACKEND

- **Language/framework:** [STATED] Python with Flask, using server-rendered Jinja templates. Dependencies are listed in [`requirements.txt`](./requirements.txt).
- **Folder structure:** [STATED] Root-level `app.py`, `deploy_contract.py`, `utils.py`, and `Certificate.sol`; active deployment contract and ABI under `contract/`; HTML under `templates/`; stylesheet under `static/`. No separate `routes/`, `models/`, or API package is present in the tracked tree.
- **Response style:** [STATED] Routes render HTML pages, use redirects and Flask flash messages; no JSON REST response interface is implemented in the inspected routes.

### Endpoint inventory

| Method and path | Request fields / input | Authentication | Behavior and response |
|---|---|---|---|
| [STATED] `GET /` | None | [STATED] Public | [STATED] Renders `index.html` in the logged-out state. |
| [STATED] `GET, POST /admin/login` | [STATED] POST form: `username`, `password` | [STATED] Login endpoint | [STATED] Exact hard-coded credential match sets admin session and redirects to dashboard; mismatch flashes “Invalid Admin Credentials”; renders `admin_login.html`. |
| [STATED] `GET /admin/logout` | None | [STATED] No explicit guard | [STATED] Removes `admin` from session and redirects to `/`. |
| [STATED] `GET /admin/dashboard` | None | [STATED] Requires `session["admin"]` | [STATED] Redirects to login if absent; otherwise renders dashboard overview. |
| [STATED] `POST /admin/register_student` | [STATED] `student_id`, `name`, `email`, `password`, `department`, `grad_year`, `cgpa` | [STATED] Requires admin session and MongoDB | [STATED] Duplicate ID flashes warning and redirects to dashboard; DB-offline flashes an error; otherwise inserts student and redirects to `/admin/records`. |
| [STATED] `POST /admin/issue_certificate` | [STATED] `student_id`, `name`, `department`, `cgpa`, `passing_year`, `distinction`, files `cert_pdf`, `student_photo` | [STATED] Requires admin session; also requires loaded contract and connected Web3 for issuance | [STATED] Writes files, computes hash, submits issue transaction, generates QR, optionally updates MongoDB, flashes status, and redirects to records or dashboard on handled errors. |
| [STATED] `GET /admin/records` | None | [STATED] Requires admin session | [STATED] Reads students/certificates if MongoDB is available and renders dashboard records tab. |
| [STATED] `POST /student/login` | [STATED] `student_id`, `password` | [STATED] Login endpoint; MongoDB required | [STATED] Case-insensitive exact ID plus password lookup; success stores student ID in session and redirects to portal; failures flash and redirect to `/`. |
| [STATED] `GET /student/portal` | Session student ID | [STATED] Requires a student session and MongoDB | [STATED] Loads student and certificate; renders portal, or clears stale session / redirects with a flash message. |
| [STATED] `GET /student/logout` | None | [STATED] No explicit guard | [STATED] Removes `student_id` from session and redirects to `/`. |
| [STATED] `GET, POST /verify` | [STATED] POST form `cert_hash`; optional backend field `qr_file` | [STATED] Public | [STATED] Calls contract read function and renders verifier page with `VALID` or `INVALID` result. |

- **Middleware/framework wiring:** [STATED] Flask's `session`, `request`, `flash`, `redirect`, `url_for`, and `render_template` are used. [NOT DECIDED] No separately configured middleware stack is documented.
- **Blockchain integration:** [STATED] `Web3.HTTPProvider` uses `GANACHE_URL` or default local URL with a 2-second request timeout. At module initialization, the app loads the ABI/address-bound contract if the ABI exists, the node is connected, and `CONTRACT_ADDRESS` is set; `admin_account` becomes `w3.eth.accounts[0]`.
- **MongoDB connection behavior:** [STATED] At module initialization, the app calls `server_info()` with `serverSelectionTimeoutMS=2000`; connection exceptions are printed and the app continues with `mongo_connected=False` and collection variables set to `None`.

## 9. DATABASE AND STORAGE

- **Database:** [STATED] MongoDB accessed by PyMongo. Default URI is `mongodb://localhost:27017/cert_verify_db`; selected DB is `cert_verify_db`.
- **Collection `students`:** [STATED] Fields inserted by admin registration: `student_id`, `name`, `email`, `password`, `department`, `grad_year`, `cgpa`, `created_at`. Auto-created student documents use the same fields, with generated email and default password.
- **Collection `certificates`:** [STATED] Fields written by issuance: `student_id`, `name`, `department`, `cgpa`, `passing_year`, `distinction`, `cert_hash`, `tx_hash`, `cert_pdf`, `student_photo`, `qr_code`, and `issue_date`.
- **Indexes/constraints:** [STATED] No explicit MongoDB index or unique constraint setup is present. Duplicate student ID is checked with a query before insert; certificate records are upserted by student ID.
- **Blockchain data:** [STATED] The active mapping stores certificate identity/hash/timestamp/validity details as described in Section 5.
- **File storage:** [STATED] PDFs and photos in `static/uploads`; QR PNGs in `static/qrcodes`. `.gitignore` excludes these folders. No cloud storage, IPFS, or S3 usage was found in the tracked files.
- **Data retention/backups:** [NOT DECIDED] No retention, backup, or deletion policy was found.

## 10. FRONTEND

- **Framework/libraries:** [STATED] Flask/Jinja HTML templates; plain CSS in `static/styles.css`; browser QR functionality from `html5-qrcode` loaded from unversioned `https://unpkg.com/html5-qrcode`. No frontend framework or package manifest is present.
- **Home/student page (`templates/index.html`):** [STATED] Displays “CertChain Portal,” links to verification and admin login, student login form, and—when logged in—student name, roll number, department, CGPA, certificate QR, hash, transaction hash, PDF link, photo link, and logout. If the student has no certificate record it displays a notice.
- **Admin login (`templates/admin_login.html`):** [STATED] Username/password form.
- **Admin dashboard (`templates/dashboard.html`):** [STATED] Overview tab contains student registration and certificate issuance forms; records tab displays registered student and certificate tables, with PDF/photo/QR links.
- **Verifier page (`templates/verify.html`):** [STATED] Manual hash input, QR-image file input, camera scanner, and valid/invalid result card. Valid results display identity fields and optional file links.
- **Navigation/state:** [STATED] Navigation uses Flask-generated endpoint links. Admin/student login state is carried in Flask session and used to choose rendered page state. No client-side global application state manager appears.
- **Visual design:** [STATED] Shared dark-themed stylesheet defines colors, responsive CSS grid, cards, buttons, forms, badges, and tables.

## 11. AUTHENTICATION, SECURITY AND PRIVACY

- **Admin authentication:** [STATED] Hard-coded username `admin` and password `admin123`; session flag is `session["admin"] = True`.
- **Student authentication:** [STATED] Student ID/password match against MongoDB. The inspected code stores and compares the password directly; no password hash function is applied.
- **Session signing key:** [STATED] Code reads `SECRET_KEY` from environment and otherwise uses literal fallback `fallback_secret_key_123`. [STATED] The `.env` file contains names `PORT`, `MONGO_URI`, `GANACHE_URL`, and `CONTRACT_ADDRESS`; `SECRET_KEY` is not among those observed keys. The `.env` values are intentionally not reproduced here.
- **Role checks:** [STATED] Admin session is checked on dashboard, student registration, issuance, and records routes. Student portal checks student session. Verification is public. Logout routes have no explicit authentication guard.
- **Blockchain issuer permission:** [STATED] Active contract's `onlyOwner` modifier restricts issuance to owner; app supplies `w3.eth.accounts[0]`.
- **Private key handling:** [STATED] No private key or external wallet signing is used by the application code; transactions are sent through the Ganache node using its account list.
- **Personal data:** [STATED] Student ID, name, and department are written on-chain in clear text in the active contract; MongoDB includes email, password, department, graduation year, and CGPA; local static storage keeps PDF and photo. [INFERRED] Anyone with access to the chain can read the on-chain public state, and static files may be served by the web app if their paths are known.
- **Input/file controls:** [STATED] Client-side form fields use HTML `required`, PDF/image `accept` hints, and filenames pass through `secure_filename`. [STATED] The inspected issuance route does not show server-side content-type, PDF signature, image-content, or file-size validation.
- **Other safeguards:** [STATED] Web3 and Mongo connection attempts use two-second timeouts in the Flask app. [NOT DECIDED] No CSRF protection, rate limiting, audit policy, deployment TLS, compliance standard, or formal threat model is documented.
- **Threats addressed/unsupported:** [INFERRED] The hash plus chain registration is intended to make issued records checkable for tampering; code has owner-only issuance and duplicate-hash prevention. [STATED] No active-contract revocation, expiry, or wallet-based signer authentication flow is present. [NOT DECIDED] Key-compromise response and privacy/compliance requirements are not documented.

## 12. COMPLETE TECH STACK TABLE

| Layer | Technology | Version | Purpose | Why chosen |
|---|---|---|---|---|
| [STATED] Backend language | Python | [NOT DECIDED] Not pinned in tracked manifest | Flask app and deployment utility | [NOT DECIDED] |
| [STATED] Web framework | Flask | `3.0.3` | Routes, sessions, templates, flash messages | [NOT DECIDED] |
| [STATED] Database driver | PyMongo | `4.8.0` | MongoDB connection and document operations | [NOT DECIDED] |
| [STATED] Blockchain client | `web3` (Web3.py) | `6.20.0` | JSON-RPC connection, contract calls, transaction receipts | [NOT DECIDED] |
| [STATED] Solidity compiler interface | `py-solc-x` | `2.0.2` | Installs/uses solc from Python deployment script | [STATED] Script calls `install_solc("0.8.0")`; choice rationale [NOT DECIDED] |
| [STATED] Contract language/compiler | Solidity / solc | pragma `^0.8.0`; deployment solc `0.8.0` | Certificate registry contract | [NOT DECIDED] |
| [STATED] Local EVM/RPC | Ganache Desktop (from prior screenshot) | [NOT DECIDED] Version not shown | Local Ethereum-compatible chain, JSON-RPC on port 7545 | [NOT DECIDED] |
| [STATED] Environment loading | `python-dotenv` | `1.0.1` | Load `.env` into process environment | [NOT DECIDED] |
| [STATED] QR generation | `qrcode` | `7.4.2` | Create QR PNG for hash | [NOT DECIDED] |
| [STATED] Image processing | Pillow | `10.4.0` | Open QR image for backend decoding | [NOT DECIDED] |
| [STATED] QR decoding | `pyzbar` | `0.1.9` | Decode optional backend-submitted QR image | [NOT DECIDED] |
| [STATED] HTTP/WSGI utility | Werkzeug | `3.0.3` | Flask dependency; `secure_filename` used | [NOT DECIDED] |
| [STATED] Browser QR library | `html5-qrcode` | [NOT DECIDED] CDN URL is unversioned | QR image/camera scan in verifier page | [NOT DECIDED] |
| [STATED] Frontend rendering | HTML/Jinja + CSS | [NOT DECIDED] No independent version pinned | Rendered forms, tables, scanner UI | [NOT DECIDED] |
| [STATED] Database server | MongoDB | [NOT DECIDED] Server version not specified | Student and certificate document persistence | [NOT DECIDED] |
| [STATED] Runtime/deployment platform | [NOT DECIDED] | [NOT DECIDED] | No host/container/runtime setup specified | [NOT DECIDED] |

## 13. DELIVERABLES

| Deliverable | Status | Evidence |
|---|---|---|
| [STATED] Flask source application | Implemented in source; runtime verification not established | [`app.py`](./app.py), templates and utilities are tracked. |
| [STATED] Solidity contract source | Implemented in source | [`contract/Certificate.sol`](./contract/Certificate.sol); a separate root-level alternative is also tracked. |
| [STATED] Contract ABI | Present | [`contract/Certificate_abi.json`](./contract/Certificate_abi.json). |
| [STATED] Deployment script | Present | [`deploy_contract.py`](./deploy_contract.py). |
| [STATED] Dependency list | Present | [`requirements.txt`](./requirements.txt). |
| [NOT DECIDED] Presentation, report, project documentation, demo video, hosted link, test report, or other promised submission | No status can be assigned | No such plan or deliverable evidence in tracked files or prior conversation. |
| [NOT DECIDED] Whether the prototype has been demonstrated or accepted | Unknown | No runtime acceptance evidence supplied. |

## 14. IMPLEMENTATION STATUS AND TIMELINE

- **Implemented in tracked source:** [STATED] Flask route and template flows; MongoDB connection and document operations; SHA-256 hash utility; local PDF/photo save; QR generation; Web3 contract deployment and calls; active Solidity registry; verifier QR scanner UI.
- **Static evidence versus runtime:** [INFERRED] The above is “implemented in source,” not proof that all flows run correctly end-to-end; no test suite or runtime report is present in the tracked files.
- **Partially implemented / caveats:** [STATED] Certificate issuance depends on an available contract and Ganache connection. Mongo persistence is conditional. [INFERRED] Normal QR image scanning is handled in the browser because the input does not declare a backend `qr_file` field.
- **Planned but not started:** [NOT DECIDED] No roadmap or planned feature list was found.
- **Milestones/deadlines:** [NOT DECIDED] No timeline or deadlines were supplied.
- **Team-member work division:** [NOT DECIDED] No authorship/work split was documented.
- **Project tree evidence:** [STATED] Tracked files are `.gitignore`, `Certificate.sol`, `app.py`, `contract/Certificate.sol`, `contract/Certificate_abi.json`, `deploy_contract.py`, `requirements.txt`, `static/styles.css`, four templates, and `utils.py`. Untracked local `.env`, virtual environments, uploaded media, and generated files are not treated as tracked deliverables.

## 15. TESTING AND DEPLOYMENT PLAN

Not Required (as specified in the request).

## 16. DIFFERENTIATORS AND NOVELTY CLAIMS

- **UI wording:** [STATED] The home page calls the system “Blockchain Certificate Verification” and describes it as “Decentralized certificate issuance and verification powered by Ethereum smart contracts. Permanent, tamper-proof, and instantly verifiable by employers.” This is page copy, not evidence that these claims were evaluated or presented.
- **Verifier copy:** [STATED] The verifier labels valid records “GENUINE RECORD” and invalid results “INVALID / FORGERY.”
- **Presentation novelty claims:** [NOT DECIDED] No presentation was available, so exact claims attributed to the presenter cannot be quoted.
- **Comparative/novelty evidence:** [NOT DECIDED] No comparison against existing systems, literature, or the counterpart project was present in the inspected sources.

## 17. KNOWN LIMITATIONS, RISKS AND OPEN QUESTIONS

- **[STATED] Single active contract has no revocation or expiry function.** Verification only considers the stored `isValid` flag.
- **[STATED] Personal details are written on-chain.** Student ID, name, and department are stored as contract strings.
- **[STATED] Passwords are stored in MongoDB in directly comparable form.** No password hashing is shown in source.
- **[STATED] Admin credentials are hard-coded.** The app's fallback Flask secret key is also a literal in source.
- **[STATED] Persistence is optional in parts of the app.** MongoDB offline handling prevents student login/registration; issuance can continue while skipping Mongo writes.
- **[INFERRED] Cross-system issuance is not atomic.** The blockchain transaction, QR-file generation, and MongoDB persistence happen in sequence without a compensating rollback. A later failure could leave a chain record without matching local/DB artifacts.
- **[INFERRED] One Mongo certificate document per student can hide older issuance.** The upsert key is `student_id`; the contract key is hash and does not revoke earlier entries.
- **[STATED] Verification does not upload/re-hash the PDF.** It checks a submitted hash; it does not independently compare a presented certificate PDF with the chain.
- **[INFERRED] QR backend decode branch may not be used by the current form.** The input has no `name="qr_file"` while browser JavaScript decodes and submits the hash.
- **[STATED] Root-level `Certificate.sol` differs from the active `contract/Certificate.sol`.** Deployment script selects only the `contract/` copy.
- **[STATED] Application runs with `debug=True` when started directly.** The configured port is `PORT` or `5000`.
- **[STATED] Uploaded files are saved in the web application's static directory.** No cloud/object storage mechanism is present in the inspected source.
- **[STATED] Previous Ganache warning:** Missing/incompatible optional µWS native binary caused a fallback to Node.js; Ganache still reported successful startup. [NOT DECIDED] The Ganache Desktop version and Node.js build version were not provided.
- **[NOT DECIDED]** Production deployment, TLS, backups, privacy rules, secret rotation, account custody, and chain migration plans were not documented.

## 18. OVERLAP SELF-CHECK

- **Counterpart title:** [NOT DECIDED] The counterpart title remains `[PASTE THE OTHER TITLE HERE]`; therefore, a project-specific overlap conclusion cannot be made.
- **Generic certificate-platform comparison:** [INFERRED] If the counterpart is also a digital certificate issuance/verification project, student/recipient records, issuing authority workflow, certificate hash or identifier, verifier flow, and certificate metadata are likely comparison points. This is conditional on a title/description not currently available; it is not a claim about the friend's project.
- **Features only this project is evidenced to cover:** [NOT DECIDED] Cannot determine “only my project” features without the counterpart's requirements or implementation. The current project's concrete implementation evidence is listed in Section 19.
- **Assumptions about counterpart systems:** [NOT DECIDED] No counterpart architecture, storage, chain, roles, or division of responsibility is assumed.

## 19. FEATURE INVENTORY TABLE

| Feature | Status | Layer | Actor | Would counterpart also need it? |
|---|---|---|---|---|
| [STATED] Admin login with fixed credentials | Implemented in source | Backend/frontend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Student registration | Implemented in source | Backend/DB/frontend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Student login | Implemented in source | Backend/DB/frontend | Student | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Student portal/profile view | Implemented in source | Backend/DB/frontend | Student | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Admin certificate issuance form | Implemented in source | Frontend/backend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Upload existing PDF and student photo | Implemented in source | Backend/local files/frontend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] SHA-256 hash of student ID + name + department + PDF bytes | Implemented in source | Backend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] On-chain certificate issue transaction | Implemented in source | On-chain/backend | Admin/issuer | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Owner-only contract issuance | Implemented in source | On-chain | Contract owner/admin account | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] QR PNG generation carrying hash | Implemented in source | Backend/local files | Student/verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Manual hash verification | Implemented in source | Frontend/backend/on-chain | Public verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] QR image selection and browser-side scan | Implemented in source | Frontend | Public verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Live camera QR scan | Implemented in source | Frontend | Public verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Backend QR image decode branch | Implemented in source; normal form path not shown to submit its expected field | Backend | Public verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] `VALID` / `INVALID` verification results | Implemented in source | Backend/frontend/on-chain | Public verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Student/certificate MongoDB records | Implemented in source | Database/backend | Admin/student | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Local static storage for PDFs/photos/QRs | Implemented in source | Other (filesystem) | Admin/student/verifier | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Admin records page | Implemented in source | Backend/database/frontend | Admin | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Contract revocation and expiry in active path | Not implemented in active contract/app | On-chain/backend | Not applicable | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] Bulk certificate issuance | Not evidenced | Backend/frontend | Not applicable | [NOT DECIDED] Counterpart scope unknown. |
| [STATED] PDF generation from a template | Not implemented in inspected source | Other | Not applicable | [NOT DECIDED] Counterpart scope unknown. |

## 20. UNANSWERED QUESTIONS

- [NOT DECIDED] What is the assigned title of this project, and what is the counterpart project title?
- [NOT DECIDED] What exact problem statement, objectives, scope, and novelty claims were spoken or written in the presentation?
- [NOT DECIDED] What does the counterpart project actually build, and which overlap areas did the evaluator identify?
- [NOT DECIDED] Is the root [`Certificate.sol`](./Certificate.sol) an earlier implementation, a planned future contract, or unused/stray code?
- [NOT DECIDED] Has the active contract been deployed in the current Ganache workspace? If so, what is its current address and does the configured address match?
- [NOT DECIDED] Which Ganache Desktop version and Node.js version produced the µWS warning?
- [NOT DECIDED] Which Python version and MongoDB server version are intended/supported?
- [NOT DECIDED] Are certificates intended to be revocable, expire, be reissued, or support multiple certificates per student?
- [NOT DECIDED] Is the current local-file storage and public static serving the intended deployment arrangement?
- [NOT DECIDED] What privacy, credential, or institution authorization requirements were specified?
- [NOT DECIDED] What was actually promised for final deliverables, and what deadlines, milestones, team-member responsibilities, and demonstration status apply?
- [NOT DECIDED] Are there additional tests, reports, presentation slides, diagrams, or project notes outside the tracked repository that should be treated as authoritative?

## 21. RAW EXTRAS

- [STATED] Tracked tree contains no README, `.env.example`, package manifest, test file, slide/deck, or project-specific documentation file. The tracked dependency manifest is [`requirements.txt`](./requirements.txt).
- [STATED] The local `.env` is ignored by `.gitignore`; only its variable names were inspected for this document (`PORT`, `MONGO_URI`, `GANACHE_URL`, `CONTRACT_ADDRESS`). Its values are intentionally not included.
- [STATED] The app also reads `SECRET_KEY`; if it is absent from the process environment, it uses the source-code fallback described in Section 11.
- [STATED] `deploy_contract.py` writes generated ABI JSON to `contract/Certificate_abi.json` and prints the address plus the admin account; the script asks the operator to copy the address into `.env` as `CONTRACT_ADDRESS`.
- [STATED] The active contract's generated ABI is checked in at [`contract/Certificate_abi.json`](./contract/Certificate_abi.json) and contains the constructor, `CertificateIssued` event, public `certificates` getter, `issueCertificate`, `owner` getter, and `verifyCertificate`.
- [STATED] The admin UI's certificate fields include CGPA, passing year, and distinction, but those values are not parameters to the active contract's `issueCertificate`; they are written to MongoDB when Mongo is connected.
- [STATED] The student portal displays the transaction hash and blockchain hash from MongoDB, while the verifier's identity and timestamp come from the contract response.
- [STATED] Previous conversation focused on interpreting the Ganache µWS warning; the log indicated a fallback implementation and successful Ganache startup. No source modifications were made as part of that conversation.
- [NOT DECIDED] No external papers, standards, similar products, discarded design documents, or TODO list were found in the tracked source.

---

**Completeness check:** [STATED] All requested sections 1–21 are present. Section 15 is marked “Not Required” as requested; items without available evidence are explicitly marked `[NOT DECIDED]`.
