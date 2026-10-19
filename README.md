# Community Recovery Pulse

**A one-minute anonymous check-in that shows disaster-recovery organizers which neighborhoods feel most cut off, which strains are piling up, and what help people need most.**

After a flood, hurricane or fire, aid focuses on buildings. People who feel cut off from their neighbors recover more slowly, and isolated neighborhoods are easy to miss. Recovery Pulse gives a town a weekly, privacy-safe read on how connected each neighborhood feels.

Built on [belonginglab](https://pypi.org/project/belonginglab/), an open-source Python library for measuring belonging.

## Screens

| Screen | What it does |
|---|---|
| **Home** | What the app is for, links to each screen, three headline numbers. |
| **Check in** | Residents answer 4 agreement questions, 4 yes/no strains and "what would help". No name or account. People reporting 2+ strains see the Disaster Distress Helpline right away. |
| **Community pulse** | Organizer dashboard: connection score over time (whole community vs. a chosen neighborhood), neighborhood comparison with 90% confidence intervals, how strains stack up, most requested help, strains by neighborhood, CSV download of totals. |
| **Get help** | Disaster Distress Helpline, 988, FEMA, 2-1-1 Texas. |
| **About & privacy** | How the score works, privacy rules, organizer settings. |

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q          # 23 tests
streamlit run app.py
```

The first run fills the database with **sample check-ins for a made-up town (Riverbend, TX)** so the dashboard has something to show. The app labels them as sample data. An organizer removes them under **About → Organizer settings**.

## How it works

### Scoring with belonginglab (`pulse/scoring.py`)
1. Answers are stored under short codes (`q1`–`q8`). `belonginglab.map_variables` renames them to readable names using the schema in `pulse/survey.py`.
2. `belonginglab.compute_belonging_score` standardizes each answer (z-score), applies community weights, sums them and ranks every check-in from 0 to 100. Belonging items count most (+1.0); strains subtract (−0.5 to −0.75).
3. `belonginglab.compare_groups` produces the per-neighborhood summary, which the app extends with confidence intervals and strain rates.

### Added for disaster recovery
- **Strain stacking:** how many of the four strains each person reports at once.
- **90% confidence intervals** on every average.
- **Small-group suppression:** any neighborhood or week with fewer than 10 check-ins is hidden from charts and downloads.
- **3-week rolling averages** for neighborhood trends, so small neighborhoods still reach the privacy minimum.

### Privacy (`pulse/storage.py`)
- No names, emails, addresses, IP addresses or device info are stored.
- Time is stored only as "weeks since the disaster", so answers can't be matched to a person by when they were sent.

## Organizer settings
Community name, type of disaster, disaster date (used to compute weeks), neighborhood list, and removing sample data. To protect settings on a public deployment, add a secret named `ORGANIZER_CODE` in Streamlit Community Cloud (App settings → Secrets):
```toml
ORGANIZER_CODE = "choose-a-code"
```

## Project structure
```
app.py                Navigation
pulse/survey.py       Questions, belonginglab schema and weights
pulse/scoring.py      Scoring, suppression, trends, stacks, needs
pulse/storage.py      SQLite storage and validation
pulse/sample.py       Sample town data
views/                One file per screen; style.py is shared with Texas CareMap
tests/                23 automated tests
```

## Limits
- The connection score describes groups, never individuals, and is not a mental health screening.
- Scores are percentile ranks within the data collected, so 50 is the middle of all check-ins.
- On Streamlit Community Cloud the SQLite file resets when the app restarts. For a real deployment, see `docs/DEPLOY.md`.
