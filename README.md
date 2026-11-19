# Landed ✈️

*Soar to Success.*

**Find opportunities. Build your skills. Land your next role.**

Landed is an AI-assisted job and internship platform built by students in **NC State ACM's Projects Committee**. Instead of jumping between job boards, spreadsheets, and resume files, students can discover opportunities, see how their skills compare with job requirements, set learning goals, and track applications in one place.

Our goal is simple: help students not only find their next opportunity, but also understand how to prepare for it.

## Features

- **AI-assisted job matching:** Explore personalized job recommendations with skill match scores that compare a student's skills with the skills a role calls for. Landed uses a locally run language model through **Ollama** as part of its job-matching workflow.
- **Skill gaps and learning goals:** See which skills are relevant to a position, identify areas to improve, and create learning goals with resources to guide progress.
- **Job discovery:** Browse and filter internships and early-career opportunities collected from public company job boards.
- **Application tracker:** Save opportunities and follow applications through stages such as saved, applied, interviewing, and offer.
- **Resume library:** Upload and organize different versions of a resume. Resume processing supports PDF, Word, and image-based documents, including OCR for scanned files.
- **Priority companies and alerts:** Follow companies of interest, receive notifications about new postings, and configure notification preferences.
- **Personalized profile:** Manage skills, target roles, and job-search preferences to make recommendations more relevant.

## How it works

```text
Public company job boards (Greenhouse)
                |
                v
     Python job collection pipeline
       (filter, clean, deduplicate)
                |
                v
      Supabase / PostgreSQL
  (jobs, users, skills, applications,
       resumes, notifications)
                ^
                |
                v
         Next.js website
       (student experience)
                |
                +----> Resume processing / OCR
                |
                +----> Skill matching and local AI
                       inference via Ollama
```

**Job collection:** A Python pipeline reads public Greenhouse job-board feeds, filters relevant early-career positions, removes duplicates, and updates listings that are no longer available.

**Student data:** Supabase provides PostgreSQL storage, user authentication, and access controls. Row Level Security (RLS) helps ensure that each student can access only their own protected information. Resume files are stored in private Supabase Storage.

**Recommendations and skills:** Landed brings together the student's profile, skills, and job requirements to support matching, skill-gap insights, and learning goals. A locally running model managed through Ollama supports the AI portion of this workflow.

**Resume processing:** The backend reads content from uploaded PDF and Word files, with OCR support for scanned documents, so students can review relevant information before using it to personalize their profiles.

Landed only collects job data from public feeds intended for access, and does not intentionally scrape websites whose terms prohibit it.

## Tech stack

| Area | Tools and technologies |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| UI/UX design | Figma |
| Database | Supabase PostgreSQL |
| Authentication and authorization | Supabase Auth, Row Level Security (RLS) |
| File storage | Supabase Storage |
| Backend and job ingestion | Python |
| AI integration | Locally hosted language model via Ollama |
| Resume processing | Python, PDF/DOCX parsing, Tesseract OCR |
| Job posting source | Greenhouse public Job Board API |
| Collaboration | Git and GitHub |

## Getting started

Landed is currently run locally. The website runs on your computer, while its data is stored in a configured Supabase project. The AI features also require a local Ollama setup.

### Prerequisites

- **Git**: [git-scm.com](https://git-scm.com/)
- **Python 3.11 or newer**: [python.org](https://www.python.org/)
- **Node.js 22 or newer**: [nodejs.org](https://nodejs.org/)
- **Supabase project**: [supabase.com](https://supabase.com/)
- **Ollama** for local AI features: [ollama.com](https://ollama.com/)
- **Tesseract OCR** for scanned/image-based resumes (the setup helper checks for it)

On macOS, use Terminal; on Windows, use PowerShell. Commands below use macOS/Linux syntax unless noted otherwise.

### 1. Clone the repository

```bash
git clone https://github.com/sajeeths1/cs-career-hub.git
cd cs-career-hub
```

The repository is currently named `cs-career-hub` on GitHub. If it is renamed to `landed`, update the clone URL and folder name above accordingly.

### 2. Install dependencies

From the repository root:

**macOS/Linux:**

```bash
python3 setup_project.py
```

**Windows:**

```powershell
python setup_project.py
```

The setup script installs frontend packages and the Python requirements in `backend/worker/.venv` and `backend/resume/.venv`. It also checks for Tesseract OCR and its English language data. Depending on your operating system, installing Tesseract may require a package manager or a manual installation.

To check the environment without installing or changing anything:

```bash
python3 setup_project.py --check
```

On Windows, use `python setup_project.py --check`.

The setup script does **not** configure your Supabase credentials, run database migrations, or download job postings.

### 3. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com/), or use the existing team project if you have been given access.
2. For a **new, empty project**, open the Supabase **SQL Editor** and apply the SQL files in `supabase/migrations/` in filename order. Review the full migration set before applying it; some migrations create private storage buckets and RLS policies in addition to database tables.
3. **For the shared team project, do not rerun migrations that have already been applied.** Coordinate schema changes with the team member responsible for the database.
4. Under **Settings → API Keys**, locate the project's publishable/anon key and the backend-only secret/service-role key.

**Security:** Never expose a Supabase secret/service-role key in frontend code or commit it to GitHub. It can bypass Row Level Security. Only public/publishable credentials belong in `NEXT_PUBLIC_` environment variables.

### 4. Configure environment variables

Create `frontend/.env.local` (you can start with `frontend/.env.local.example`):

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-publishable-or-anon-key
```

To collect jobs, create `backend/worker/.env`:

```dotenv
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-backend-only-secret-key
```

Use your own Supabase project's credentials. Do not commit `.env`, `.env.local`, or other files containing secrets.

### 5. Collect job postings

The database needs job data before the discovery and matching pages will be useful. Run the collection pipeline from its directory.

**macOS/Linux:**

```bash
cd backend/worker
source .venv/bin/activate
python pipeline.py
cd ../..
```

**Windows (PowerShell):**

```powershell
cd backend\worker
.\.venv\Scripts\Activate.ps1
python pipeline.py
cd ..\..
```

The pipeline fetches postings from supported public job-board feeds. Some company feeds may be skipped if they are no longer available.

For more detail on skills and matching behavior, see [skill development](docs/skill_development.md) and [profile personalization](docs/profile_personalization.md).

### 6. Set up local AI with Ollama

Install [Ollama](https://ollama.com/) and make sure its local service is running. Download the model expected by the current backend's Ollama configuration before using AI-assisted matching. The specific model name and configuration may change as the project evolves, so check the backend configuration instead of assuming a particular model.

Useful commands:

```bash
ollama list
ollama serve
```

If the Ollama application is already running its service, you do not need to start another one. Job browsing and application tracking are separate from local AI inference, but Ollama-dependent features require the configured model to be available.

### 7. Run the website

Open a new terminal in the repository root and run:

```bash
cd frontend
npm run dev
```

Then visit **http://localhost:3000**.

To stop the server, press **Ctrl + C**. To start it again, run `npm run dev` inside `frontend/`.

If you pull changes that modify dependencies, rerun the setup script from the repository root:

```bash
python3 setup_project.py
```

On Windows, use `python setup_project.py`.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `python` or `python3` not found | Install Python 3.11+ and reopen your terminal. macOS typically uses `python3`; Windows typically uses `python`. |
| `npm` not found | Install Node.js 22+ and reopen your terminal. |
| `frontend/.env.local` missing or Supabase connection error | Check the Supabase URL and publishable/anon key, then restart the website. |
| No jobs appear | Confirm the database migrations were applied to your Supabase project, then run `backend/worker/pipeline.py`. |
| `Resume parser is unavailable` | Run the setup script again and check `backend/resume/.venv`, the resume requirements, and Tesseract. See [resume setup](docs/resume_parsing.md). |
| Scanned resume cannot be read | Confirm Tesseract and its English language data are installed. |
| Ollama-assisted matching is unavailable | Confirm Ollama is running and that the model expected by the backend is installed. |
| PowerShell blocks `.venv` activation | For the current shell, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then retry. |
| Changes aren't appearing after a pull | Restart `npm run dev` and reload the browser. If necessary, remove `frontend/.next` (generated build cache) and restart. |

## Project structure

```text
cs-career-hub/
├── backend/
│   ├── worker/              # Python job collection and processing
│   └── resume/              # Resume parsing and related dependencies
├── frontend/                # Next.js application
├── supabase/
│   └── migrations/          # Database schema, policies, and storage setup
├── docs/                    # Technical and setup documentation
├── setup_project.py         # Dependency and environment setup helper
└── README.md
```

## Team

Landed was developed by members of **NC State ACM's Projects Committee**.

| Frontend development | Backend development |
| --- | --- |
| Jack Ongstad | Daniel Dong |
| Aanya Tomar | Gloria Kim |
| Atharva Tijare | Sajeeth Sreeman |

The team worked collaboratively on design, development, testing, and integration throughout the semester.
