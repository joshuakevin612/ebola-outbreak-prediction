import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'
import './GlareHover.css'
import { AnimatedContent as Reveal, GlareHover, Magnet } from './ReactBitsMotion.jsx'
import LandingPage from './LandingPage.jsx'

const datasets = ['West Africa (2014-2016)', 'DRC North Kivu / Ituri (2018-2020)']
const symptomFields = [
  ['Fever', 'Headache', 'Fatigue', 'Muscle_Pain', 'Weakness', 'Sore_Throat'],
  ['Chills', 'Loss_of_Appetite', 'Vomiting', 'Diarrhea', 'Nausea', 'Abdominal_Pain'],
  ['Bleeding_Symptoms', 'Skin_Rash', 'Eye_Redness', 'Respiratory_Difficulty'],
]
const exposureFields = [
  ['Contact_With_Patient', 'Travel_History', 'Visited_Outbreak_Region'],
  ['Animal_Exposure', 'Healthcare_Worker', 'Funeral_Attendance'],
  ['Household_Exposure'],
]
const fieldLabels = {
  Muscle_Pain: 'Muscle pain', Loss_of_Appetite: 'Loss of appetite', Abdominal_Pain: 'Abdominal pain',
  Bleeding_Symptoms: 'Bleeding symptoms', Eye_Redness: 'Eye redness', Respiratory_Difficulty: 'Breathing difficulty',
  Contact_With_Patient: 'Contact with Ebola patient', Travel_History: 'Travel history',
  Visited_Outbreak_Region: 'Visited outbreak region', Animal_Exposure: 'Animal exposure',
  Healthcare_Worker: 'Healthcare worker', Funeral_Attendance: 'Funeral attendance',
  Household_Exposure: 'Household exposure',
}
const defaultPatient = {
  Age: 25, Gender: 'Female', Weight_kg: 60, Occupation: 'Healthcare', Region: 'West Africa', Urban_Rural: 'Urban',
  Fever: 0, Body_Temperature: 36.7, Headache: 0, Fatigue: 0, Muscle_Pain: 0, Weakness: 0, Sore_Throat: 0,
  Chills: 0, Loss_of_Appetite: 0, Vomiting: 0, Diarrhea: 0, Nausea: 0, Abdominal_Pain: 0, Bleeding_Symptoms: 0,
  Skin_Rash: 0, Eye_Redness: 0, Respiratory_Difficulty: 0, Dehydration_Level: 1, Blood_Pressure: 120, Heart_Rate: 72,
  Oxygen_Saturation: 99, Contact_With_Patient: 0, Travel_History: 0, Visited_Outbreak_Region: 0, Animal_Exposure: 0,
  Healthcare_Worker: 0, Funeral_Attendance: 0, Household_Exposure: 0, Days_Since_Exposure: 0, Vaccination_Status: 0,
  Immune_Condition: 'Normal', WBC_Count: 7.5, Platelet_Count: 270000, Hemoglobin: 13.5, Viral_Load_Score: 2,
  Symptom_Duration_Days: 1, Time_Since_First_Symptom: 1, Population_Density_Score: 5, Local_Outbreak_Severity: 5,
  Healthcare_Access_Score: 8,
}
const numericFields = {
  Age: ['Age', 0, 120, 1], Weight_kg: ['Weight (kg)', 1, 200, 1], Body_Temperature: ['Temperature (°C)', 30, 45, 0.1],
  Dehydration_Level: ['Dehydration level', 0, 10, 1], Blood_Pressure: ['Blood pressure', 50, 250, 1],
  Heart_Rate: ['Heart rate', 30, 200, 1], Oxygen_Saturation: ['Oxygen saturation (%)', 50, 100, 0.1],
  Days_Since_Exposure: ['Days since exposure', 0, 100, 1], WBC_Count: ['WBC count', 0, 30, 0.1],
  Platelet_Count: ['Platelet count', 0, 600000, 1], Hemoglobin: ['Hemoglobin', 0, 25, 0.1],
  Viral_Load_Score: ['Viral load score', 0, 10, 1], Symptom_Duration_Days: ['Symptom duration (days)', 0, 100, 1],
  Time_Since_First_Symptom: ['Days since first symptom', 0, 100, 1], Population_Density_Score: ['Population density', 0, 10, 1],
  Local_Outbreak_Severity: ['Local outbreak severity', 0, 10, 1], Healthcare_Access_Score: ['Healthcare access', 0, 10, 1],
}

function Icon({ name, size = 18, ...props }) {
  const paths = {
    pulse: <><path d="M2 12h4l3-8 5 16 3-8h5" /></>,
    chart: <><path d="M3 3v18h18" /><path d="m7 14 4-4 4 3 6-7" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" /></>,
    moon: <path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13Z" />,
    arrow: <><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m7 10 5 5 5-5" />,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5M12 15V3" /></>,
    info: <><circle cx="12" cy="12" r="10" /><path d="M12 16v-4m0-4h.01" /></>,
    activity: <path d="M22 12h-4l-3 9L9 3l-3 9H2" />,
    rotate: <><path d="M3 12a9 9 0 0 1 15.36-6.36L21 8" /><path d="M21 3v5h-5M21 12a9 9 0 0 1-15.36 6.36L3 16" /><path d="M3 21v-5h5" /></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>
}

function Input({ name, value, onChange, compact = false }) {
  const [label, min, max, step] = numericFields[name]
  return <label className={`input-field ${compact ? 'compact' : ''}`}><span>{label}</span><input type="number" min={min} max={max} step={step} value={value} onChange={(event) => onChange(name, Number(event.target.value))} /></label>
}

function Select({ label, value, options, onChange }) {
  return <label className="input-field"><span>{label}</span><span className="select-wrap"><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option}>{option}</option>)}</select><Icon name="chevron" size={15} /></span></label>
}

function Toggle({ checked, onChange, children, style }) {
  return <button type="button" className={`switch ${checked ? 'checked' : ''}`} role="switch" aria-checked={checked} onClick={onChange} style={style}><span className="switch-dot" /><span>{children}</span></button>
}

function TrendChart({ data, result = null, hovered = null, onHover = () => {}, onLeave = () => {} }) {
  if (!data?.length) return <div className="chart-empty">Loading outbreak observations…</div>
  const width = 900, height = 260, pad = { x: 18, y: 18 }
  const predictionValues = Object.values(result?.predictions || {}).flat().filter(Number.isFinite)
  const max = Math.max(...data.map((point) => point.value), ...predictionValues, 1)
  const coords = data.map((point, index) => ({ x: pad.x + index * (width - pad.x * 2) / Math.max(data.length - 1, 1), y: height - pad.y - point.value / max * (height - pad.y * 2) }))
  const path = coords.map((point, index) => `${index ? 'L' : 'M'}${point.x},${point.y}`).join(' ')
  const fill = `${path} L${coords.at(-1)?.x},${height} L${coords[0]?.x},${height} Z`
  const forecastPaths = Object.values(result?.predictions || {}).map((prediction) => prediction.map((value, index) => ({
    x: pad.x + (result.historyCases.length + index) * (width - pad.x * 2) / Math.max(data.length - 1, 1),
    y: height - pad.y - (Number.isFinite(value) ? value : 0) / max * (height - pad.y * 2),
  })).map((point, index) => `${index ? 'L' : 'M'}${point.x},${point.y}`).join(' '))
  const activePoint = hovered ? coords[hovered.index] : null
  const inspect = (event) => {
    const box = event.currentTarget.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (event.clientX - box.left) / box.width))
    const index = Math.round(ratio * (data.length - 1))
    const point = data[index]
    if (!point) return
    const container = event.currentTarget.parentElement.getBoundingClientRect()
    onHover({ index, point, x: event.clientX - container.left, y: event.clientY - container.top })
  }
  const moveWithKey = (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return
    event.preventDefault()
    const next = Math.max(0, Math.min(data.length - 1, (hovered?.index ?? 0) + (event.key === 'ArrowRight' ? 1 : -1)))
    const point = data[next]
    const box = event.currentTarget.getBoundingClientRect()
    const container = event.currentTarget.parentElement.getBoundingClientRect()
    onHover({ index: next, point, x: box.left - container.left + (next / Math.max(data.length - 1, 1)) * box.width, y: box.height * (1 - point.value / max) })
  }
  return <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" tabIndex="0" onPointerMove={inspect} onPointerLeave={onLeave} onKeyDown={moveWithKey} aria-label={result ? 'Reported cases and forecast model predictions' : 'Historical reported cases. Hover or use left and right arrow keys to inspect observations.'}>
    {[0.25, 0.5, 0.75].map((row) => <line key={row} x1="0" x2={width} y1={height * row} y2={height * row} className="grid-line" />)}
    {!result && <path d={fill} className="chart-area" />}
    <path key={`${result?.dataset || 'series'}-${data.length}`} d={path} pathLength="1" className="chart-line actual-line" />
    {forecastPaths.map((forecastPath, index) => <path key={index} d={forecastPath} className={`chart-line forecast-line forecast-${index % 3}`} />)}
    {activePoint && <><line x1={activePoint.x} x2={activePoint.x} y1={0} y2={height} className="chart-crosshair" /><circle cx={activePoint.x} cy={activePoint.y} r={6} className="chart-focus-point" /></>}
  </svg>
}

function RiskInputMap({ patient }) {
  const symptomCount = symptomFields.flat().filter((field) => Boolean(patient[field])).length
  const exposureCount = exposureFields.flat().filter((field) => Boolean(patient[field])).length
  const vitalFields = ['Blood_Pressure', 'Heart_Rate', 'Oxygen_Saturation']
  const vitalCount = vitalFields.filter((field) => patient[field] !== '' && Number.isFinite(Number(patient[field]))).length
  const inputs = [
    { label: 'Reported symptoms', count: symptomCount, total: symptomFields.flat().length },
    { label: 'Exposure factors', count: exposureCount, total: exposureFields.flat().length },
    { label: 'Vital signs', count: vitalCount, total: vitalFields.length },
  ]
  return <div className="intake-map" role="group" aria-label={`Patient inputs: ${inputs.map(({ label, count, total }) => `${label} ${count} of ${total}`).join(', ')}`}>
    <div className="intake-map-heading"><span>Patient input profile</span><span>LIVE</span></div>
    <div className="intake-map-rows">{inputs.map(({ label, count, total }) => {
      const activeMarks = count ? Math.max(1, Math.ceil(count / total * 12)) : 0
      return <div className="intake-row" key={label}>
        <span className="intake-label">{label}</span>
        <span className="intake-count" key={count}><strong>{count}</strong><small> / {total}</small></span>
        <span className="intake-marks" role="img" aria-label={`${count} of ${total} recorded`}>{Array.from({ length: 12 }, (_, index) => <i key={index} className={index < activeMarks ? 'lit' : ''} />)}</span>
      </div>
    })}</div>
  </div>
}

function OutbreakTrace({ series, dataset }) {
  const [activeIndex, setActiveIndex] = useState(null)
  const points = useMemo(() => {
    if (!series?.dates?.length || !series?.cases?.length) return []
    const count = Math.min(48, series.dates.length)
    const maximum = Math.max(...series.cases, 1)
    return Array.from({ length: count }, (_, index) => {
      const sourceIndex = Math.round(index * (series.dates.length - 1) / Math.max(count - 1, 1))
      return { date: series.dates[sourceIndex], value: Number(series.cases[sourceIndex]) || 0, x: 12 + index * 416 / Math.max(count - 1, 1), y: 112 - (Number(series.cases[sourceIndex]) || 0) / maximum * 88 }
    })
  }, [series])
  const path = points.map(({ x, y }, index) => `${index ? 'L' : 'M'}${x},${y}`).join(' ')
  const selected = activeIndex === null ? null : points[activeIndex]
  const inspect = (event) => {
    if (!points.length) return
    const bounds = event.currentTarget.getBoundingClientRect()
    const index = Math.round(Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)) * (points.length - 1))
    setActiveIndex(index)
  }
  const moveWithKey = (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key) || !points.length) return
    event.preventDefault()
    const start = activeIndex ?? (event.key === 'ArrowRight' ? -1 : points.length)
    setActiveIndex(Math.max(0, Math.min(points.length - 1, start + (event.key === 'ArrowRight' ? 1 : -1))))
  }
  return <div className="outbreak-trace">
    <div className="trace-heading"><span>Reported cases</span><span>{series ? `${series.observations?.toLocaleString() || points.length} observations` : 'Loading series'}</span></div>
    {points.length ? <svg key={`${dataset}-${series?.start}`} className="trace-chart" viewBox="0 0 440 128" preserveAspectRatio="none" role="img" tabIndex="0" aria-label="Reported Ebola cases across the selected outbreak series. Hover or use the arrow keys to inspect dates." onPointerMove={inspect} onPointerLeave={() => setActiveIndex(null)} onKeyDown={moveWithKey}>
      <line x1="8" x2="432" y1="112" y2="112" className="trace-baseline" />
      <path d={`${path} L428,112 L12,112 Z`} className="trace-area" />
      <path d={path} pathLength="1" className="trace-line" />
      {selected && <><line x1={selected.x} x2={selected.x} y1="10" y2="114" className="trace-cursor" /><circle cx={selected.x} cy={selected.y} r="5.5" className="trace-focus" /></>}
      {!selected && <circle cx={points.at(-1).x} cy={points.at(-1).y} r="4" className="trace-endpoint" />}
    </svg> : <div className="trace-empty">Outbreak series will appear when the research API is ready.</div>}
    <div className="trace-footer"><span>{selected?.date || series?.start || 'Historical series'}</span><strong>{selected ? `${Math.round(selected.value).toLocaleString()} cases` : series ? `Peak ${Math.round(series.peak || 0).toLocaleString()}` : 'No observations'}</strong></div>
  </div>
}

function RiskScreen({ patient, setPatient, apiStatus, animate }) {
  const [result, setResult] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const set = (name, value) => setPatient((current) => ({ ...current, [name]: value }))
  const submit = async (event) => {
    event.preventDefault(); setPending(true); setError(''); setResult(null)
    try {
      const response = await fetch('/api/risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ patient }) })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.error || 'The model could not calculate a score. Check the selected values and try again.')
      setResult(payload.score)
    } catch (reason) { setError(reason.message || 'Could not reach the model. Start the Python API and try again.') }
    finally { setPending(false) }
  }
  return <main className={`screen risk-screen ${animate ? 'mode-enter' : ''}`} key="risk">
    <div className="screen-intro">
      <div><h1>Patient risk</h1><p>Estimate a model score from reported symptoms and exposure history.</p><div className="prototype-note"><Icon name="info" size={16} /><span>Research prototype / not a clinical tool</span></div></div>
      <RiskInputMap patient={patient} />
    </div>
    <form onSubmit={submit}>
      <Reveal className="form-section identity-section" motion="profile">
        <div className="section-heading"><div><h2>Patient profile</h2><p>Use the available information. The model accepts unknown categories.</p></div><span className="section-number">PROFILE</span></div>
        <div className="field-grid four-col">
          <Input name="Age" value={patient.Age} onChange={set} />
          <Select label="Gender" value={patient.Gender} options={['Male', 'Female', 'Transgender', 'Prefer not to say']} onChange={(value) => set('Gender', value)} />
          <Input name="Weight_kg" value={patient.Weight_kg} onChange={set} />
          <Select label="Occupation" value={patient.Occupation} options={['Healthcare', 'Education', 'Agriculture', 'Transportation and Logistics', 'Trade and Commerce', 'Student', 'Public Services', 'Other', 'Unknown']} onChange={(value) => set('Occupation', value)} />
          <Select label="Outbreak region" value={patient.Region} options={['West Africa', 'North Kivu / Ituri (DRC)', 'Central Africa', 'Other / Unknown']} onChange={(value) => set('Region', value)} />
          <Select label="Area" value={patient.Urban_Rural} options={['Urban', 'Rural']} onChange={(value) => set('Urban_Rural', value)} />
        </div>
      </Reveal>

      <Reveal className="form-section symptom-section" motion="symptoms">
        <div className="section-heading"><div><h2>Symptoms</h2><p>Select reported symptoms and set the current severity where known.</p></div><span className="section-number">SIGNS</span></div>
        <div className="symptom-layout">
          <div className="toggle-grid">{symptomFields.flat().map((key, index) => <Toggle key={key} style={{ '--item-index': index }} checked={Boolean(patient[key])} onChange={() => set(key, patient[key] ? 0 : 1)}>{fieldLabels[key] || key.replaceAll('_', ' ')}</Toggle>)}</div>
          <div className="severity-fields"><Input name="Body_Temperature" value={patient.Body_Temperature} onChange={set} /><Input name="Dehydration_Level" value={patient.Dehydration_Level} onChange={set} /><Input name="Symptom_Duration_Days" value={patient.Symptom_Duration_Days} onChange={set} /></div>
        </div>
      </Reveal>

      <Reveal className="form-section split-section" motion="encounter">
        <div><div className="section-heading"><div><h2>Vital signs</h2><p>Measurements in the units used by the training data.</p></div></div><div className="field-grid two-col">{['Blood_Pressure', 'Heart_Rate', 'Oxygen_Saturation'].map((key) => <Input key={key} name={key} value={patient[key]} onChange={set} />)}</div></div>
        <div><div className="section-heading"><div><h2>Exposure history</h2><p>Recent contact and relevant circumstances.</p></div></div><div className="toggle-grid">{exposureFields.flat().map((key, index) => <Toggle key={key} style={{ '--item-index': index }} checked={Boolean(patient[key])} onChange={() => set(key, patient[key] ? 0 : 1)}>{fieldLabels[key]}</Toggle>)}</div><div className="inline-field"><Input name="Days_Since_Exposure" value={patient.Days_Since_Exposure} onChange={set} /></div></div>
      </Reveal>

      <details className="advanced-section"><summary>Additional medical and regional factors <Icon name="chevron" size={16} /></summary><div className="field-grid four-col advanced-grid">
        <Toggle checked={Boolean(patient.Vaccination_Status)} onChange={() => set('Vaccination_Status', patient.Vaccination_Status ? 0 : 1)}>Vaccination recorded</Toggle>
        <Select label="Immune condition" value={patient.Immune_Condition} options={['Normal', 'Compromised', 'Unknown']} onChange={(value) => set('Immune_Condition', value)} />
        {['WBC_Count', 'Platelet_Count', 'Hemoglobin', 'Viral_Load_Score', 'Time_Since_First_Symptom', 'Population_Density_Score', 'Local_Outbreak_Severity', 'Healthcare_Access_Score'].map((key) => <Input key={key} name={key} value={patient[key]} onChange={set} />)}
      </div></details>

      <div className="form-actions"><div className="safety-copy">The score is an experimental model output. It is not a diagnosis or a medically validated probability.</div><Magnet className="primary-magnet"><GlareHover as="button" className="primary-button" type="submit" disabled={pending || !apiStatus}><span>{pending ? 'Calculating score' : 'Calculate risk score'}</span><Icon name={pending ? 'activity' : 'arrow'} size={18} /></GlareHover></Magnet></div>
      {!apiStatus && <p className="inline-error" role="status">Start the project API to calculate a model score.</p>}
      {error && <p className="inline-error" role="alert">{error}</p>}
      {result !== null && <div className="result-panel" aria-live="polite"><div><span>MODEL RISK SCORE</span><strong>{(result * 100).toFixed(2)}<small>%</small></strong><p>Research model output · not for medical decisions</p></div><div className="result-scale"><div className="result-track"><span style={{ width: `${Math.min(Math.max(result * 100, 1), 100)}%` }} /></div><div><span>Lower model score</span><span>Higher model score</span></div></div></div>}
    </form>
  </main>
}

function ForecastScreen({ apiStatus, animate }) {
  const [dataset, setDataset] = useState(datasets[0])
  const [series, setSeries] = useState(null)
  const [testFrac, setTestFrac] = useState(0.2)
  const [maxP, setMaxP] = useState(3)
  const [epochs, setEpochs] = useState(100)
  const [lookback, setLookback] = useState(14)
  const [selectedModels, setSelectedModels] = useState(['naive', 'arima'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [hovered, setHovered] = useState(null)
  useEffect(() => {
    if (!apiStatus) return
    fetch(`/api/series?dataset=${encodeURIComponent(dataset)}`).then((response) => response.json()).then(setSeries).catch(() => setSeries(null))
  }, [dataset, apiStatus])
  const chartData = useMemo(() => {
    if (!result) return series?.dates?.map((date, index) => ({ date, value: series.cases[index] })) || []
    const historic = result.historyCases.map((value, index) => ({ date: result.historyDates[index], value }))
    const future = result.actual.map((value, index) => ({ date: result.dates[index], value }))
    return [...historic, ...future]
  }, [result, series])
  const modelToggle = (name) => setSelectedModels((current) => current.includes(name) ? current.filter((model) => model !== name) : [...current, name])
  const runForecast = async () => {
    setLoading(true); setError(''); setResult(null)
    try {
      const response = await fetch('/api/forecast', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dataset, testFrac, models: selectedModels, maxP, epochs, lookback }) })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.error || 'Forecast could not be calculated.')
      setResult(payload)
    } catch (reason) { setError(reason.message || 'Could not reach the forecast API. Start it and try again.') }
    finally { setLoading(false) }
  }
  const download = (content, filename) => { const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([content], { type: 'text/csv' })); link.download = filename; link.click(); URL.revokeObjectURL(link.href) }
  const actualCsv = () => {
    if (!result) return
    const columns = ['date', 'actual', ...Object.keys(result.predictions)].join(',')
    const rows = result.dates.map((date, index) => [date, result.actual[index], ...Object.values(result.predictions).map((prediction) => prediction[index] ?? '')].join(','))
    download([columns, ...rows].join('\n'), 'ebola-forecast-results.csv')
  }
  return <main className={`screen forecast-screen ${animate ? 'mode-enter' : ''}`} key="forecast">
    <div className="screen-intro forecast-intro">
      <div><h1>Outbreak forecast</h1><p>Compare model projections against reported case counts.</p><div className="prototype-note"><Icon name="info" size={16} /><span>Historical research / experimental forecasts</span></div></div>
      <OutbreakTrace series={series} dataset={dataset} />
    </div>
    <Reveal className="forecast-controls" motion="controls">
      <div className="control-block dataset-control"><span className="control-label">OUTBREAK SERIES</span><div className="dataset-picker">{datasets.map((name) => <GlareHover key={name} as="button" width="100%" height="100%" background="var(--surface)" borderColor="var(--line)" borderRadius="6px" className={`dataset-option ${dataset === name ? 'selected' : ''}`} aria-pressed={dataset === name} onClick={() => { setDataset(name); setResult(null); setLookback(name.includes('West Africa') ? 14 : 6) }} type="button">{name.split(' (')[0]}<small>{name.match(/\((.*?)\)/)?.[1]}</small></GlareHover>)}</div></div>
      <div className="control-divider" />
      <div className="control-block test-control"><label className="control-label" htmlFor="test-frac">HELD-OUT DATA <strong>{Math.round(testFrac * 100)}%</strong></label><input id="test-frac" className="range-control" type="range" min="0.1" max="0.4" step="0.05" value={testFrac} onChange={(event) => setTestFrac(Number(event.target.value))} /><div className="range-labels"><span>10%</span><span>40%</span></div></div>
      <div className="control-divider" />
      <div className="control-block models-control"><span className="control-label">MODELS</span><div className="model-options"><Toggle checked={selectedModels.includes('naive')} onChange={() => modelToggle('naive')}>Naive baseline</Toggle><Toggle checked={selectedModels.includes('arima')} onChange={() => modelToggle('arima')}>ARIMA</Toggle>{apiStatus?.tensorflow && <><Toggle checked={selectedModels.includes('lstm')} onChange={() => modelToggle('lstm')}>LSTM</Toggle><Toggle checked={selectedModels.includes('pooled')} onChange={() => modelToggle('pooled')}>Pooled LSTM</Toggle></>}</div></div>
      <Magnet className="run-magnet"><GlareHover as="button" className="run-button" type="button" disabled={loading || !apiStatus || selectedModels.length === 0} onClick={runForecast}><span>{loading ? 'Running…' : 'Run forecast'}</span><Icon name="arrow" size={17} /></GlareHover></Magnet>
    </Reveal>
    <details className="advanced-section forecast-advanced"><summary>Advanced model settings <Icon name="chevron" size={16} /></summary><div className="advanced-grid field-grid four-col"><label className="input-field"><span>ARIMA p and q search</span><select value={maxP} onChange={(event) => setMaxP(Number(event.target.value))}>{[1, 2, 3, 4].map((value) => <option key={value} value={value}>0 to {value}</option>)}</select></label><label className="input-field"><span>LSTM training epochs</span><input type="number" min="20" max="200" step="10" value={epochs} onChange={(event) => setEpochs(Number(event.target.value))} /></label><label className="input-field"><span>LSTM lookback window</span><input type="number" min="3" max="30" value={lookback} onChange={(event) => setLookback(Number(event.target.value))} /></label></div></details>
    {!apiStatus && <p className="inline-error" role="status">Start the project API to load the outbreak series and run forecasts.</p>}
    {error && <p className="inline-error" role="alert">{error}</p>}

    <Reveal className="trend-section" motion="data">
      <div className="trend-title"><div><h2>{result ? 'Forecast against actual cases' : 'Reported cases over time'}</h2><p>{dataset} / {dataset.includes('West Africa') ? 'Daily reported new cases' : 'Weekly reported new cases'}</p></div><span className="chart-key"><i />Reported cases {result && <><i className="key-forecast" />Model predictions</>}</span></div>
      <div className="chart-shell"><div className="axis-labels"><span>{Math.ceil((series?.peak || Math.max(...chartData.map((point) => point.value), 1)) / 100) * 100} cases</span><span>0</span></div><TrendChart data={chartData} result={result} hovered={hovered} onHover={setHovered} onLeave={() => setHovered(null)} />{hovered && <div className="chart-tooltip" role="status" aria-live="polite" style={{ '--tip-x': `${hovered.x}px`, '--tip-y': `${hovered.y}px` }}><time>{hovered.point.date}</time><strong>{Math.round(hovered.point.value).toLocaleString()} reported cases</strong>{result && hovered.index >= result.historyCases.length && Object.entries(result.predictions).map(([name, values]) => <span key={name}>{values[hovered.index - result.historyCases.length] == null ? '—' : `${name}: ${Math.round(values[hovered.index - result.historyCases.length]).toLocaleString()}`}</span>)}</div>}<div className="chart-dates"><span>{chartData[0]?.date}</span><span>{result?.testStart || chartData[Math.floor(chartData.length / 2)]?.date}</span><span>{chartData.at(-1)?.date}</span></div></div>
      <div className="series-stats"><div><span>OBSERVATIONS</span><strong>{series?.observations?.toLocaleString() || '—'}</strong></div><div><span>DATE RANGE</span><strong>{series ? `${series.start} — ${series.end}` : 'Loading series'}</strong></div><div><span>PEAK NEW CASES</span><strong>{series ? Math.round(series.peak).toLocaleString() : '—'}</strong></div><div><span>TEST PERIOD</span><strong>{result ? `${result.testStart} — ${result.testEnd}` : 'Run forecast to evaluate'}</strong></div></div>
      {series?.adf && <details className="diagnostics"><summary>Stationarity diagnostic <Icon name="chevron" size={15} /></summary><div><span>ADF statistic <strong>{Number(series.adf.stat).toFixed(3)}</strong></span><span>p-value <strong>{Number(series.adf.p_value).toFixed(4)}</strong></span><span>Evidence at 5% <strong>{series.adf.stationary ? 'Present' : 'Not established'}</strong></span></div><p>The Augmented Dickey–Fuller test assesses evidence against a unit root. It does not identify the most accurate model.</p></details>}
    </Reveal>

    {result && <Reveal className="results-section" motion="results">
      <div className="section-heading"><div><h2>Model comparison</h2><p>Lower RMSE and MAE indicate smaller average errors. Higher R² is generally better.</p></div><button className="text-button" type="button" onClick={actualCsv}><Icon name="download" size={16} /> Download CSV</button></div>
      <div className="table-scroll"><table><thead><tr><th>MODEL</th><th>RMSE</th><th>MAE</th><th>R²</th></tr></thead><tbody>{result.metrics.map((row, index) => <tr key={row.model}><td><span className={`model-dot dot-${index % 2}`} />{row.model}</td><td>{row.rmse.toFixed(2)}</td><td>{row.mae.toFixed(2)}</td><td>{row.r2.toFixed(3)}</td></tr>)}</tbody></table></div>
      {Object.entries(result.errors || {}).map(([model, message]) => <p className="inline-error" key={model}>{model}: {message}</p>)}
    </Reveal>}
    <footer className="screen-footnote">These forecasts are experimental. Reporting gaps, case definitions, and data quality affect interpretation. Do not use this research prototype for public health decisions.</footer>
  </main>
}

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) return <main className="screen-stage"><p className="inline-error" role="alert">This section stopped unexpectedly. Refresh the page to restore it.</p></main>
    return this.props.children
  }
}

function App() {
  const [entered, setEntered] = useState(false)
  const [mode, setMode] = useState('risk')
  const [hasSwitched, setHasSwitched] = useState(false)
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('ebolavf-theme') || 'dark' } catch { return 'dark' } })
  const [patient, setPatient] = useState(defaultPatient)
  const [apiStatus, setApiStatus] = useState(null)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('ebolavf-theme', theme) } catch {}
  }, [theme])
  useEffect(() => { fetch('/api/status').then((response) => response.json()).then(setApiStatus).catch(() => setApiStatus(null)) }, [])
  const changeMode = (next) => {
    if (next === mode) return
    setHasSwitched(true)
    setMode(next)
  }
  if (!entered) return <LandingPage theme={theme} onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} apiStatus={apiStatus} onEnter={(next) => { setMode(next); setHasSwitched(false); setEntered(true) }} />
  return <div className={`app-shell ${mode === 'forecast' ? 'is-forecast' : ''}`}>
    <aside className="rail"><button className="brand" type="button" onClick={() => setEntered(false)} aria-label="Return to EbolaVF landing page"><span className="brand-mark"><Icon name="pulse" size={19} /></span><span>EBOLA<span>VF</span></span></button><div className="rail-rule" /><nav className="mode-nav" aria-label="Research tools"><button type="button" className={mode === 'risk' ? 'active' : ''} onClick={(event) => changeMode('risk', event)} aria-current={mode === 'risk' ? 'page' : undefined}><Icon name="pulse" /><span>Patient risk</span><i /></button><button type="button" className={mode === 'forecast' ? 'active' : ''} onClick={(event) => changeMode('forecast', event)} aria-current={mode === 'forecast' ? 'page' : undefined}><Icon name="chart" /><span>Forecasting</span><i /></button></nav><div className="rail-bottom"><span className={`connection-dot ${apiStatus ? 'online' : ''}`} /><span>{apiStatus ? 'MODEL API READY' : 'MODEL API OFFLINE'}</span></div></aside>
    <div className="workspace"><header className="topbar"><div className="topbar-context"><span>RESEARCH WORKSPACE</span><span className="context-divider" /><span>EBOLA OUTBREAK INTELLIGENCE</span></div><div className="topbar-actions"><button type="button" className="back-home" onClick={() => { setEntered(false); window.scrollTo(0, 0) }}><Icon name="arrow" size={16} />Back to home</button><span className="prototype-badge"><i />RESEARCH PROTOTYPE</span><button className="theme-toggle" type="button" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}><Icon name={theme === 'dark' ? 'sun' : 'moon'} size={17} /></button></div></header><div className="mode-switch" role="tablist" aria-label="Choose a research workspace"><button role="tab" aria-selected={mode === 'risk'} className={mode === 'risk' ? 'active' : ''} onClick={() => changeMode('risk')} type="button"><Icon name="pulse" size={16} />Patient risk</button><button role="tab" aria-selected={mode === 'forecast'} className={mode === 'forecast' ? 'active' : ''} onClick={() => changeMode('forecast')} type="button"><Icon name="chart" size={16} />Ebola forecasting</button><span className="tab-indicator" /></div><div id="main" className="screen-stage"><div className="scroll-progress" aria-hidden="true" />{mode === 'risk' ? <RiskScreen patient={patient} setPatient={setPatient} apiStatus={apiStatus} animate={hasSwitched} /> : <ForecastScreen apiStatus={apiStatus} animate={hasSwitched} />}</div></div>
  </div>
}

createRoot(document.getElementById('root')).render(<ErrorBoundary><App /></ErrorBoundary>)
