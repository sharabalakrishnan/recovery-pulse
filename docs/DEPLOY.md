# Deploying Recovery Pulse

## Try it on your computer
```bash
cd recovery-pulse
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the Check in page, send a check-in, then look at Community pulse.

## Put it online (free)
1. Create a new **public** GitHub repository, for example `recovery-pulse`, with "Add a README" **off**.
2. Upload everything **inside** the `recovery-pulse` folder to the top level of the repository, including the hidden `.streamlit` folder (in Finder press Command + Shift + . to see it). Don't upload `data/pulse.db`.
3. On share.streamlit.io: **Create app** → your repository → branch `main` → main file `app.py` → **Deploy**.
4. Optional: in the app's **Settings → Secrets**, add `ORGANIZER_CODE = "your-code"` so only organizers can change settings.

## Important: saving real check-ins
Streamlit Community Cloud doesn't keep files between restarts, so check-ins saved in SQLite disappear when the app sleeps or redeploys. That's fine for a demo with sample data. For a real town, swap the storage for a hosted database (for example a free Supabase Postgres database or Google Sheets). Only `pulse/storage.py` needs to change.

## Before sharing with a real community
- Ask a local recovery group or city office to review the questions.
- Set the community name, disaster date and neighborhoods in **About → Organizer settings**.
- Remove the sample check-ins.
- Share the Check in page link on flyers, church bulletins and local Facebook groups.
