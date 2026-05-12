# React Material UI Dashboard Guide

## Why Use React + Material UI?

Yes, the results should be shown with a dashboard. Markdown and raw HTML are fine for evidence, but a React + Material UI dashboard is much better for presentation because it clearly shows:

- headline speedup,
- energy-efficiency improvement,
- ablation variants,
- bottleneck layers,
- movement cycles,
- core utilization,
- load-balancing counts.

## Start The Dashboard

```bash
cd /Users/hanumanashikakshintala/Documents/New\ project/samba_imc_accelerator
./scripts/start_results_dashboard.sh
```

Open:

```text
http://127.0.0.1:8088/standalone/
```

## What To Show

1. Show the four metric tiles at the top.
2. Show the `Headline` tab for speedup and energy bars.
3. Show the `Variants` tab to compare fixed ADC, sparse ADC, and SAMBA.
4. Show the `Layers` tab to prove the dashboard is reading real layer-level simulator data.

## React App Version

The project also includes a normal Vite React app in `dashboard/`. This environment currently has Node but no `npm`, so the standalone dashboard is the immediately runnable version. If `npm` is available later:

```bash
cd dashboard
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```
