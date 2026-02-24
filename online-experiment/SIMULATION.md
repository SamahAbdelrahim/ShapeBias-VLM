# Running the web-based experiment (simulation)

Two ways to run the experiment locally:

---

## Option 1: Live Server (static only)

1. In VS Code / Cursor, install the **Live Server** extension if needed.
2. **Right-click** `experiment_scripts/experiment.html` → **Open with Live Server**.

The experiment will load with:
- jsPsych and all assets from `../assets/` (relative to the HTML file).
- A **fallback list of videos** (no Node server), so `/api/videos` is not used; the built-in list (e.g. 1A.mp4, 1B.mp4, …) is used.
- At the end, **data is not saved** (no server). You may see an error about saving; you can ignore it or check the browser console. The Prolific redirect will fail; that’s expected when not using the full server.

Use this for quick UI checks and running through the task flow.

---

## Option 2: Node server (full simulation with API)

1. From the **`online-experiment`** folder:
   ```bash
   npm install
   node pairwise-server.js
   ```
2. Open in the browser: **http://localhost:3020/**  
   You will be redirected to `http://localhost:3020/experiment_scripts/experiment.html`.

With the server running:
- **`/api/videos`** returns the real list of videos from `assets/videos_of_objs/`.
- **`/api/log`** receives trial data. If `mongo_auth.json` is present and MongoDB is running, data is saved there; otherwise data is only logged to the server console.

**MongoDB is optional.** If `mongo_auth.json` is missing or MongoDB is not running, the server still starts and the experiment runs; logs are printed to the console only.

---

## Summary of fixes applied

- **experiment.html**: Asset paths changed from `/general_assets/` to `../assets/`; script changed from `familiar_obj_ratings_openended.js` to `experiment_open_ended.js`.
- **experiment_open_ended.js**: Uses `window.ASSETS_BASE || '../assets'` and `videos_of_objs` for video paths; fallback video list updated to match files in `assets/videos_of_objs/`.
- **pairwise-server.js**: Serves the existing `assets` folder (at `/general_assets` and `/assets`), serves `experiment_scripts`, uses `assets/videos_of_objs` for `/api/videos`, and makes MongoDB optional for local simulation.
