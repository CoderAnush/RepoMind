# TODO - Phase 1 (Production Frontend Deployment)

## Step 1: Update Vercel SPA routing config
- [x] Edit `frontend/vercel.json` to ensure SPA routes work for deep links.
- [ ] Keep rewrite to `/index.html` for non-asset requests.
- [x] Ensure Vercel uses the correct output directory (`dist`).

## Step 2: Ensure API URL switching is documented
- [x] Update `DEPLOYMENT.md` (and/or `README.md` if needed) to explicitly document `VITE_API_URL` usage for Vercel.
- [x] Mention required redirect URI patterns for OAuth endpoints are handled by frontend.

## Step 3: Local production build sanity check
- [x] Run `npm ci && npm run build` inside `frontend/`. 

## Step 4: Verification checklist after deployment
- [x] Login works.
- [x] Dashboard works.
- [x] Repository submission + all downstream panels work.
- [x] Deep links load (e.g., `/repositories/:id/docs`, `/chat`, etc.).

