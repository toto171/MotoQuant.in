# MotoQuant Pro — Soft Launch Deployment Guide

## Phase 1: GitHub Repository Setup

### Option A: Create a New GitHub Repository (Recommended for clean separation)

1. **Create repo on GitHub:**
   - Go to https://github.com/new
   - Repo name: `motoquant` (or `motoquant-landing`)
   - Description: "Physics engine for drag racing prediction"
   - Public (open source)
   - Add `.gitignore` (Python), add README, add MIT license

2. **Push existing code:**
   ```bash
   cd "Vehicle Dynamics"
   git init
   git add .
   git commit -m "Initial commit: MotoQuant Pro physics engine"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/motoquant.git
   git push -u origin main
   ```

3. **Add landing page:**
   - The `landing-page.jsx` file is already in this directory
   - For Vercel deployment, we'll create a `/web` subdirectory with Next.js config below

### Option B: Use Existing Repository

If you already have a GitHub repo:
```bash
cd "Vehicle Dynamics"
git add landing-page.jsx DEPLOYMENT.md
git commit -m "Add: soft launch landing page"
git push origin main
```

---

## Phase 2: Vercel Deployment Setup

### 1. Create Next.js Wrapper (Required for Vercel)

Vercel works best with Next.js. Create this minimal setup:

**File: `vercel.json`** (in project root)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "out",
  "framework": "nextjs"
}
```

**File: `pages/_app.jsx`** (create `/pages` folder)
```jsx
import LandingPage from '../landing-page.jsx';

export default function App() {
  return <LandingPage />;
}
```

**File: `package.json`** (update or create)
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
    "@tailwindcss/postcss": "^7.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

**File: `next.config.js`** (in project root)
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
```

**File: `tailwind.config.js`**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

**File: `postcss.config.js`**
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### 2. Install Dependencies Locally

```bash
cd "Vehicle Dynamics"
npm install
npm run build  # Test locally
npm run dev     # View at http://localhost:3000
```

### 3. Push to GitHub

```bash
git add pages/ landing-page.jsx package.json next.config.js tailwind.config.js postcss.config.js vercel.json
git commit -m "Add: Next.js + Vercel deployment setup"
git push origin main
```

---

## Phase 3: Connect Vercel & Deploy

### 1. Link Repository to Vercel

1. Go to https://vercel.com/new
2. Sign in with GitHub (you may need to authorize if first time)
3. Select the `motoquant` repository
4. **Framework Preset:** Next.js (auto-detected)
5. **Root Directory:** leave blank (uses project root)
6. **Environment Variables:** Leave empty for now
7. Click **Deploy**

Vercel will build and deploy automatically. You'll get a URL like `motoquant.vercel.app`.

### 2. Test the Deployment

- Visit the Vercel URL — you should see the landing page
- Check all links work (GitHub, nav links)
- Test responsive design (mobile, tablet, desktop)

---

## Phase 4: Configure Custom Domain (motoquant.in)

### 1. Add Domain to Vercel Project

1. In Vercel dashboard, go to your project → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter: `motoquant.in`
4. Vercel will show you nameserver instructions

### 2. Update Domain DNS (at registrar)

Wherever you purchased motoquant.in (likely Hostinger via GitHub Education pack):

1. Log into your domain registrar account
2. Find **DNS Settings** or **Nameservers**
3. Replace nameservers with Vercel's:
   - `ns1.vercel-dns.com`
   - `ns2.vercel-dns.com`
   - `ns3.vercel-dns.com`
   - `ns4.vercel-dns.com`
4. Save and wait 24–48 hours for DNS propagation

### 3. Verify & Enable HTTPS

- Return to Vercel dashboard → Settings → Domains
- Check status: should show ✓ Connected
- Click on domain → Enable **Automatic HTTPS**
- Vercel manages SSL certificate automatically

---

## What's Live Now

✅ **Landing page:** motoquant.in  
✅ **Physics validation:** Real benchmarks (K5, R1, Hayabusa)  
✅ **GitHub link:** Direct to your repo  
✅ **CTA:** Links to GitHub Quick Start + "Web Simulator Coming Q3 2026"  

---

## Next Steps (Phase 2 Continuation)

While the landing page is live:

1. **Continue Phase 2 remaining items:**
   - Bulk bike scraping (`--priority 1` for Japanese Big 4)
   - Expand known_bikes.py with 30+ hand-curated models
   - Add Indian-market bikes (Pulsar 200NS, Dominar, Hero Xtreme, KTM Duke)

2. **Notify the community:**
   - Tweet/share the landing page link
   - Post in Indian drag racing groups (Reddit, Discord, Narhe forums)
   - "Physics engine validated on real bikes — try the CLI, web simulator coming soon"

3. **Gather feedback:**
   - GitHub issues for bike requests, physics questions
   - Early adopters will help shape Phase 3 calibration pipeline

---

## Troubleshooting

**DNS not propagating:**
- Check at https://dnschecker.org with your domain
- May take 24–48 hours
- Try clearing browser cache / use incognito window

**Build failing on Vercel:**
- Check Vercel build logs (Dashboard → Deployments)
- Common: missing `next.config.js` or package versions
- Run `npm run build` locally to replicate

**Landing page styling broken:**
- Ensure Tailwind CSS is in `globals.css` or imported properly
- Check postcss.config.js references tailwindcss
- Rebuild: `npm run build && npm run dev`

---

## GitHub Education Benefits (NITW Pack)

You have free access to:
- **GitHub Pro** (free for student accounts)
- **Vercel Pro** ($10/month usually, free)
- **Namecheap** domain discounts
- Evaluate requesting **DigitalOcean credits** for Phase 3 backend (FastAPI simulator)

---

## FAQ

**Q: When do we launch the web simulator?**  
A: Phase 3 completion (Dragy GPS import, dyno curve fitting, real-data validation). This landing page is the credibility milestone—soft launch now, full tool by Q3 2026.

**Q: Can I keep the CLI private and only show landing page?**  
A: No—repo should be public (open source). Phase 6 is when you offer commercial licenses. Early credibility comes from transparency.

**Q: Should I password-protect the landing page?**  
A: No. Public visibility drives early adopter interest and GitHub stars.
