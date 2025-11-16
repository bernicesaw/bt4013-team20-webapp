# A Career Path Navigator for Developers

The Career Path Navigator for Developers is an integrated web application designed to help software developers explore potential career paths, analyze industry trends, and receive personalized skill and course recommendations.
Using insights from the Stack Overflow Developer Survey (2020–2025), the platform provides interactive visualizations, an AI-driven recommendation system, and a conversational chatbot to support data-driven career decision-making.

## Quick start

1. Create and activate a virtual environment at project root

```
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Run App
## Run App

First navigate to the app's directory:

```text
bt4013-team20-webapp/
├── myapp/   <-- navigate here!
│   └── ...
├── .gitignore
├── requirements.txt
└── README.md
```

Run the web app with the following command:

```bash
python manage.py runserver
```

The app opens at http://localhost:8000. Create account and sign in to experience the skill adjacency graph and intereact with our chatbot.

## Troubleshooting
- “Scheme 'b''://' is unknown”:
  - Ensure .env is in myapp directory.

## Alternative: Docker Build and Run

To run the webapp inside Docker, navigate to the 'docker' branch first, then:

1. Build the image

```bash
docker build -t team20-webapp .
```

2. Run the container

```bash
docker run -p 8000:8000 team20-webapp
```

3. Access the app

```bash
Visit: http://localhost:8000
```

## Project structure

```
bt4103-team20/
├ dashboard/
│  ├ streamlit_app.py          # Combined entrypoint (One-Year + Multi-Year)
│  ├ one_year_dashboard.py     # 2025 Global Landscape
│  ├ multi_year_dashboard.py   # 2020–2025 Trends
│  └ .streamlit/
│     ├ config.toml            # Local Streamlit configuration
│     └ secrets.toml           # Local secrets (gitignored)
├ data/
│  ├ raw/
│  │  ├ multi_year_survey_*.csv   # Original multi-year survey CSVs
│  │  └ survey_results_pu*.csv    # Original one-year survey CSVs
│  └ processed/
│     ├ multi_year_cleaned_*.csv  # Cleaned / transformed multi-year datasets
│     └ one_year_cleaned_*.csv    # Cleaned / transformed one-year datasets
├ devcontainer/
│  ├ devcontainer.json         # VS Code Dev Container definition
│  └ Dockerfile                # Dev container image
├ notebooks/
│  ├ exploration.ipynb         # Exploratory data analysis
│  └ modeling.ipynb            # Modeling experiments
├ src/
│  ├ data_prep.py              # Data cleaning and feature engineering
│  ├ modeling.py               # Model training utilities
│  └ viz_helpers.py            # Shared plotting / visualization helpers
├ tests/
│  └ test_modeling.py          # Unit tests for modeling utilities
├ .gitignore                   # Git ignore rules
├ pyproject.toml               # Project dependencies and tooling
└ README.md                    # Project overview and usage

```