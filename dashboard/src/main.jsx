import React from 'react';
import { createRoot } from 'react-dom/client';
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  CssBaseline,
  Divider,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ThemeProvider,
  ToggleButton,
  ToggleButtonGroup,
  Toolbar,
  Typography,
  createTheme,
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import SpeedIcon from '@mui/icons-material/Speed';
import MemoryIcon from '@mui/icons-material/Memory';
import BoltIcon from '@mui/icons-material/Bolt';
import TimelineIcon from '@mui/icons-material/Timeline';
import './styles.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1f5fbf' },
    secondary: { main: '#0f8f71' },
    background: { default: '#f5f7fb', paper: '#ffffff' },
    text: { primary: '#172033', secondary: '#5d6980' },
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h4: { fontWeight: 760, letterSpacing: 0 },
    h6: { fontWeight: 720, letterSpacing: 0 },
  },
});

function fmt(value, digits = 2) {
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function MetricTile({ icon, label, value, sub }) {
  return (
    <Paper className="metricTile" variant="outlined">
      <Box className="metricIcon">{icon}</Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5">{value}</Typography>
        <Typography variant="caption" color="text.secondary">
          {sub}
        </Typography>
      </Box>
    </Paper>
  );
}

function BarList({ rows, metric }) {
  const max = Math.max(...rows.map((row) => row[metric]), 1);
  return (
    <Stack spacing={1.5}>
      {rows.map((row) => (
        <Box key={`${row.experiment}-${row.variant}`}>
          <Stack direction="row" justifyContent="space-between" gap={2}>
            <Typography variant="body2" className="barLabel">
              {row.experiment}
            </Typography>
            <Typography variant="body2" fontWeight={700}>
              {fmt(row[metric], 3)}x
            </Typography>
          </Stack>
          <Box className="barTrack">
            <Box
              className={metric.includes('energy') ? 'barFill energy' : 'barFill speed'}
              sx={{ width: `${Math.max(4, (row[metric] / max) * 100)}%` }}
            />
          </Box>
        </Box>
      ))}
    </Stack>
  );
}

function VariantTable({ rows }) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Experiment</TableCell>
            <TableCell>Variant</TableCell>
            <TableCell align="right">Latency Cycles</TableCell>
            <TableCell align="right">Energy pJ</TableCell>
            <TableCell align="right">Speedup</TableCell>
            <TableCell align="right">Energy Eff.</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={`${row.experiment}-${row.variant}`} hover>
              <TableCell>{row.experiment}</TableCell>
              <TableCell>
                <Chip
                  size="small"
                  label={row.variant}
                  color={row.variant.includes('samba') ? 'secondary' : 'default'}
                  variant={row.variant.includes('samba') ? 'filled' : 'outlined'}
                />
              </TableCell>
              <TableCell align="right">{fmt(row.latency_cycles, 0)}</TableCell>
              <TableCell align="right">{fmt(row.energy_pj, 0)}</TableCell>
              <TableCell align="right">{fmt(row.speedup_vs_fixed_adc, 3)}x</TableCell>
              <TableCell align="right">{fmt(row.energy_efficiency_vs_fixed_adc, 3)}x</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function LayerTable({ experiment }) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Layer</TableCell>
            <TableCell>Variant</TableCell>
            <TableCell align="right">Latency</TableCell>
            <TableCell align="right">Movement</TableCell>
            <TableCell align="right">Util.</TableCell>
            <TableCell align="right">ColEx</TableCell>
            <TableCell align="right">RowEx</TableCell>
            <TableCell align="right">Split</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {experiment.top_layers.map((row) => (
            <TableRow key={`${row.layer}-${row.variant}`} hover>
              <TableCell>{row.layer}</TableCell>
              <TableCell>{row.variant}</TableCell>
              <TableCell align="right">{fmt(row.latency_cycles, 0)}</TableCell>
              <TableCell align="right">{fmt(row.movement_cycles, 0)}</TableCell>
              <TableCell align="right">{fmt(row.utilization * 100, 1)}%</TableCell>
              <TableCell align="right">{row.column_swaps}</TableCell>
              <TableCell align="right">{row.row_swaps}</TableCell>
              <TableCell align="right">{row.split_mvmus}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function App() {
  const [data, setData] = React.useState(null);
  const [view, setView] = React.useState(() => {
    const hashView = window.location.hash.replace('#', '');
    return ['headline', 'variants', 'layers'].includes(hashView) ? hashView : 'headline';
  });
  const [selectedRun, setSelectedRun] = React.useState('');

  React.useEffect(() => {
    fetch('/data/dashboard.json')
      .then((response) => response.json())
      .then((payload) => {
        setData(payload);
        setSelectedRun(payload.experiments?.[0]?.run_name ?? '');
      });
  }, []);

  if (!data) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Container sx={{ py: 6 }}>
          <Typography variant="h6">Loading SAMBA results...</Typography>
          <LinearProgress sx={{ mt: 2 }} />
        </Container>
      </ThemeProvider>
    );
  }

  const rows = data.suite.runs;
  const sambaRows = rows.filter((row) => row.variant.includes('samba'));
  const fullResnet = sambaRows.find((row) => row.experiment.startsWith('full_resnet50'));
  const bestSpeed = [...sambaRows].sort(
    (a, b) => b.speedup_vs_fixed_adc - a.speedup_vs_fixed_adc,
  )[0];
  const bestEnergy = [...sambaRows].sort(
    (a, b) => b.energy_efficiency_vs_fixed_adc - a.energy_efficiency_vs_fixed_adc,
  )[0];
  const selectedExperiment =
    data.experiments.find((experiment) => experiment.run_name === selectedRun) ??
    data.experiments[0];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="sticky" color="inherit" elevation={0} className="topbar">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            SAMBA Results Dashboard
          </Typography>
          <Button
            size="small"
            variant="outlined"
            endIcon={<OpenInNewIcon />}
            href="../final_suite/index.html"
          >
            Static Report
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Stack spacing={3}>
          <Paper className="summaryBand" variant="outlined">
            <Stack direction={{ xs: 'column', md: 'row' }} gap={2} alignItems={{ md: 'center' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h4">Sparse IMC Accelerator Evaluation</Typography>
                <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 920 }}>
                  Fixed ADC PUMA baseline, sparse ADC baseline, and SAMBA optimizations compared
                  across microbenchmarks, VGG19, and ResNet50-style workloads.
                </Typography>
              </Box>
              <ToggleButtonGroup
                exclusive
                value={view}
                size="small"
                onChange={(_, next) => {
                  if (next) {
                    setView(next);
                    window.location.hash = next;
                  }
                }}
              >
                <ToggleButton value="headline">Headline</ToggleButton>
                <ToggleButton value="variants">Variants</ToggleButton>
                <ToggleButton value="layers">Layers</ToggleButton>
              </ToggleButtonGroup>
            </Stack>
          </Paper>

          <Box className="metricGrid">
            <MetricTile
              icon={<SpeedIcon />}
              label="Full ResNet50 Speedup"
              value={`${fmt(fullResnet?.speedup_vs_fixed_adc ?? 0, 3)}x`}
              sub="SAMBA vs fixed ADC baseline"
            />
            <MetricTile
              icon={<BoltIcon />}
              label="Full ResNet50 Energy Eff."
              value={`${fmt(fullResnet?.energy_efficiency_vs_fixed_adc ?? 0, 3)}x`}
              sub="Normalized energy efficiency"
            />
            <MetricTile
              icon={<TimelineIcon />}
              label="Best Speedup"
              value={`${fmt(bestSpeed?.speedup_vs_fixed_adc ?? 0, 3)}x`}
              sub={bestSpeed?.experiment ?? 'No run'}
            />
            <MetricTile
              icon={<MemoryIcon />}
              label="Experiments"
              value={String(new Set(rows.map((row) => row.experiment)).size)}
              sub={`${rows.length} variant rows loaded`}
            />
          </Box>

          {view === 'headline' && (
            <Box className="twoCol">
              <Paper className="panel" variant="outlined">
                <Typography variant="h6">SAMBA Speedup</Typography>
                <Divider sx={{ my: 2 }} />
                <BarList rows={sambaRows} metric="speedup_vs_fixed_adc" />
              </Paper>
              <Paper className="panel" variant="outlined">
                <Typography variant="h6">SAMBA Energy Efficiency</Typography>
                <Divider sx={{ my: 2 }} />
                <BarList rows={sambaRows} metric="energy_efficiency_vs_fixed_adc" />
              </Paper>
            </Box>
          )}

          {view === 'variants' && <VariantTable rows={rows} />}

          {view === 'layers' && (
            <Stack spacing={2}>
              <FormControl size="small" sx={{ maxWidth: 420 }}>
                <InputLabel id="run-select">Experiment</InputLabel>
                <Select
                  labelId="run-select"
                  label="Experiment"
                  value={selectedRun}
                  onChange={(event) => setSelectedRun(event.target.value)}
                >
                  {data.experiments.map((experiment) => (
                    <MenuItem key={experiment.run_name} value={experiment.run_name}>
                      {experiment.run_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <LayerTable experiment={selectedExperiment} />
            </Stack>
          )}

          <Paper className="panel" variant="outlined">
            <Typography variant="h6">How to Explain This Result</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              SAMBA is faster because it lowers ADC precision when weights are sparse, avoids
              applying expensive balancing when it does not pay off, and reduces partial-sum
              movement across cores and tiles. These are simulator results, so the correct claim is
              architectural speedup and energy-efficiency improvement, not measured chip silicon.
            </Typography>
          </Paper>
        </Stack>
      </Container>
    </ThemeProvider>
  );
}

createRoot(document.getElementById('root')).render(<App />);
