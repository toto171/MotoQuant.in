# Quick Launch Steps — Your Setup

**GitHub:** NITW email, private repo  
**Domain:** motoquant.in on Hostinger  
**Target:** Landing page live by April 15  

---

## Step 1: Create Private GitHub Repo (5 min)

1. Go to https://github.com/new
2. **Repository name:** `motoquant`
3. **Description:** "Physics engine for drag racing prediction"
4. **Visibility:** ⚪ Private
5. **Initialize:** Add `.gitignore` (Python), add README (MIT License optional)
6. Click **Create repository**

Copy the HTTPS URL: `https://github.com/YOUR_NITW_USERNAME/motoquant.git`

---

## Step 2: Push Existing Code to GitHub (10 min)

```bash
cd "Vehicle Dynamics"

# Initialize git (if not already done)
git init
git config user.email "YOUR_NITW_EMAIL@student.nitw.ac.in"
git config user.name "Your Name"

# Add all files
git add .

# First commit
git commit -m "Initial commit: MotoQuant Pro physics engine + landing page"

# Set main branch and connect to GitHub
git branch -M main
git remote add origin https://github.com/YOUR_NITW_USERNAME/motoquant.git
git push -u origin main
```

You'll be prompted for GitHub credentials:
- Username: `YOUR_NITW_USERNAME`
- Password: Use a **Personal Access Token** (not your GitHub password)
  - Go to https://github.com/settings/tokens
  - Create token: "repo" scope, no expiry for now
  - Copy token and paste into prompt

---

## Step 3: Create Next.js Config Files (10 min)

In your project root (`Vehicle Dynamics/`), create these files:

### `package.json`
```json
{
  "name": "motoquant",
  "version": "1.0.0",
  "description": "Physics engine for drag racing prediction",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build && next export",
    "start": "next start"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.383.0"
  },
  "devDependencies": {
    "next": "^14.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### `next.config.js`
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};
module.exports = nextConfig;
```

### `tailwind.config.js`
```javascript
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: { extend: {} },
  plugins: [],
};
```

### `postcss.config.js`
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### `pages/_app.jsx`
```jsx
import LandingPage from '../landing-page.jsx';

export default function App() {
  return <LandingPage />;
}
```

### `vercel.json`
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "out",
  "framework": "nextjs"
}
```

---

## Step 4: Test Locally (5 min)

```bash
# Install dependencies
npm install

# Build
npm run build

# Run dev server
npm run dev
```

Visit `http://localhost:3000` — you should see the landing page.

Press `Ctrl+C` to stop.

---

## Step 5: Push to GitHub (2 min)

```bash
git add pages/ package.json next.config.js tailwind.config.js postcss.config.js vercel.json
git commit -m "Add: Next.js + Vercel deployment config"
git push origin main
```

---

## Step 6: Deploy to Vercel (10 min)

1. Go to https://vercel.com/new
2. **Sign in with GitHub** (authorize if first time)
3. **Import project:** Select `motoquant` repo
4. **Framework:** Next.js (auto-detected)
5. **Root Directory:** Leave blank
6. **Environment:** Leave empty
7. Click **Deploy**

Wait ~2 minutes for build. You'll get a URL like:
```
https://motoquant.vercel.app
```

Test it — landing page should load.

---

## Step 7: Configure Hostinger DNS (10 min active, 24–48 hrs propagation)

### In Vercel:
1. Your project dashboard → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter: `motoquant.in`
4. Copy Vercel's nameservers (you'll see 4 NS records):
   ```
   ns1.vercel-dns.com
   ns2.vercel-dns.com
   ns3.vercel-dns.com
   ns4.vercel-dns.com
   ```

### In Hostinger:
1. Log in to Hostinger account
2. Find your domain → **DNS Management** or **Nameservers**
3. Replace current nameservers with Vercel's 4 nameservers
4. Save changes
5. **Wait 24–48 hours** (DNS propagation)

### Monitor Status:
- Return to Vercel dashboard after ~1 hour
- Domains page should show ✓ **Connected**
- Click domain → **Automatic HTTPS** should enable automatically

---

## Step 8: Verify It's Live (After DNS Propagates)

Once DNS is set:
```bash
# Check DNS propagation
nslookup motoquant.in

# Should return Vercel's IP
# Or use: https://dnschecker.org?domain=motoquant.in
```

Open browser: `https://motoquant.in` → Should load your landing page ✓

---

## Timeline

| Task | Duration | When |
|---|---|---|
| GitHub repo + push | 15 min | Today |
| Local test + config | 15 min | Today |
| Vercel deploy | 10 min | Today |
| DNS setup | 10 min | Today |
| DNS propagation | 24–48 hrs | Background (async) |
| **LIVE** | — | By April 15 |

---

## What to Do While DNS Propagates

**Don't wait!** Work on Phase 2 in parallel:

```bash
# Bulk scrape Japanese Big 4 bikes
python -m motoquant.run scrape --bulk --priority 1

# Check current DB state
python -m motoquant.run db stats

# Expand known_bikes.py with Indian-market bikes
# (See CLAUDE.md for target list)
```

---

## Private Repo Note

Your repo is **private** — GitHub will require auth to pull code. For Phase 3+, when you're ready to share:

- Make public (GitHub → Settings → Danger Zone → Make Public)
- Add open-source license (MIT, already planned)
- Update README with quickstart instructions
- Announce to Indian drag racing community

For now, private is fine — keep it internal until Phase 3 calibration validation is done.

---

## Troubleshooting

**"Can't push to GitHub"**
- Check personal access token is valid (GitHub → Settings → Developer → Tokens)
- Token must have `repo` scope
- Paste full token when prompted (not just part of it)

**"DNS not propagating after 2 hours"**
- Check Vercel domain page — should show status
- Try different DNS checker: https://dnschecker.org
- May take full 48 hours in rare cases

**"Build fails on Vercel"**
- Check build logs in Vercel dashboard (Deployments tab)
- Run `npm run build` locally to replicate error
- Most common: missing `next.config.js` or typo in `package.json`

**"Landing page styling looks broken"**
- Check Tailwind CSS in postcss.config.js
- Vercel should auto-detect Next.js + Tailwind
- Try: clear browser cache / use incognito window

---

## You're Ready!

Once you complete Steps 1–7, you're done with setup. DNS will propagate in the background while you work on Phase 2.

Run Steps 1–6 now (30 min), then Step 7 takes 10 min and waits asyncly.

Questions before you start?
