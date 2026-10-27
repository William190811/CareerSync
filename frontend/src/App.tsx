import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowUpRight, BookOpen, Check, ChevronDown, ChevronLeft, ChevronRight, CircleHelp, ExternalLink, RefreshCw, Send, Sparkles, Trash2, X } from 'lucide-react'
import { MarketMetric, Tile, Web3Bento } from './components/ui/web3-bento'

const careers = [
  { name: 'Software engineer', short: 'Software engineering', icon: 'SE', role: 'software engineer', match: ['Computer science', 'Software engineering', 'Computer engineering'] },
  { name: 'AI / ML engineer', short: 'AI and machine learning', icon: 'AI', role: 'AI / ML', match: ['Computer science', 'Mathematics', 'Statistics'] },
  { name: 'Data scientist', short: 'Data science and statistics', icon: 'DS', role: 'data scientist', match: ['Data science', 'Statistics', 'Mathematics'] },
  { name: 'Data engineer', short: 'Data platforms and pipelines', icon: 'DE', role: 'data engineer', match: ['Computer science', 'Data science', 'Information technology'] },
  { name: 'Cybersecurity analyst', short: 'Security and risk', icon: 'CY', role: 'cybersecurity', match: ['Cybersecurity', 'Computer science', 'Information technology'] },
  { name: 'Cloud / DevOps engineer', short: 'Cloud infrastructure', icon: 'CO', role: 'cloud / DevOps', match: ['Computer engineering', 'Information technology', 'Computer science'] },
]
const majors = ['Computer science', 'Software engineering', 'Computer engineering', 'Data science', 'Statistics', 'Mathematics', 'Cybersecurity', 'Information technology']
const starterProfiles: Profile[] = [
  { name: 'Software engineering path', interests: [], subjects: [], career: 'Software engineer', majors: ['Computer science', 'Software engineering', 'Computer engineering'] },
  { name: 'Data and AI path', interests: [], subjects: [], career: 'AI / ML engineer', majors: ['Computer science', 'Mathematics', 'Statistics'] },
  { name: 'Cybersecurity path', interests: [], subjects: [], career: 'Cybersecurity analyst', majors: ['Cybersecurity', 'Computer science', 'Information technology'] },
]
const subjectGuides: Record<string, { topics: string; preparation: string; source: string; url: string }> = {
  'Computer science': { topics: 'Algorithms, programming, systems, data management, security, software engineering, and mathematical foundations.', preparation: 'Check local programming, discrete mathematics, and calculus prerequisites.', source: 'ACM / IEEE-CS / AAAI CS2023', url: 'https://csed.acm.org/' },
  'Software engineering': { topics: 'Software requirements, design, construction, testing, maintenance, and engineering practice.', preparation: 'Check local programming and mathematics prerequisites.', source: 'ACM / IEEE-CS Software Engineering 2014', url: 'https://www.acm.org/binaries/content/assets/education/se2014.pdf' },
  'Computer engineering': { topics: 'Computer architecture, digital systems, embedded computing, software, and hardware interfaces.', preparation: 'Check local mathematics, physics, and programming requirements.', source: 'ACM / IEEE-CS Computer Engineering 2016', url: 'https://www.acm.org/binaries/content/assets/education/ce2016-final-report.pdf' },
  'Data science': { topics: 'Statistical reasoning, computation, data management, modeling, and communicating findings.', preparation: 'Check local calculus, linear algebra, statistics, and programming prerequisites.', source: 'MAA undergraduate Data Science curriculum resources', url: 'https://maa.org/resource/cupm-guide/' },
  'Statistics': { topics: 'Statistical methods and theory, data management, computation, mathematical foundations, and practice.', preparation: 'Check local calculus, linear algebra, and introductory programming requirements.', source: 'American Statistical Association undergraduate guidelines', url: 'https://www.amstat.org/education/curriculum-guidelines-for-undergraduate-programs-in-statistical-science-' },
  'Mathematics': { topics: 'Calculus, algebra, analysis, discrete mathematics, probability, modeling, and applied options.', preparation: 'Check placement and whether the program requires proof-based courses.', source: 'Mathematical Association of America CUPM Guide', url: 'https://maa.org/resource/cupm-guide/' },
  'Cybersecurity': { topics: 'Secure systems, networks, risk, human factors, policy, ethics, and operational processes.', preparation: 'Check local systems, networking, and programming prerequisites.', source: 'ACM / IEEE / AIS / IFIP CSEC2017', url: 'https://cybered.acm.org/' },
  'Information technology': { topics: 'Applied computing, infrastructure, networking, security, systems, user needs, and project work.', preparation: 'Check local programming, networking, and mathematics prerequisites.', source: 'ACM / IEEE IT2017', url: 'https://www.acm.org/binaries/content/assets/education/curricula-recommendations/it2017.pdf' },
}
const questions = ['Which skills appear most in AI roles?', 'How common are remote jobs?', 'Compare data science and software engineering']
const policyColors: Record<string, string> = { remote: '#b0f34b', hybrid: '#b29bed', onsite: '#8c8b98', mixed: '#f1bb8d', not_stated: '#55545e' }
const majorColors = ['#b0f34b', '#a58be8', '#59c995']
type Market = {
  summary: Record<string, number | string>
  coverage: { total: number; processed: number }
  statuses: Record<string, number>
  month_coverage: { month: string; source_posts: number; processed_posts: number }[]
  months: { month: string; posts: number }[]
  skills: { skill: string; mentions: number }[]
  remote: { remote_policy: string; posts: number }[]
  countries: { country: string; posts: number }[]
  salaries: { currency: string; period: string; median_min: number; median_max: number; offers: number }[]
  country_options: string[]
}
type Profile = { name: string; interests: string[]; subjects: string[]; career: string; majors: string[] }
type Post = { item_id: number; month: string; source_url: string; text_plain: string; skills: string[]; seniority: string[]; remote_policy: string }
type Identity = { user: string | null; execution_identity: string }
type QueryResults = { columns: string[]; rows: (string | null)[][] }
const number = (value: unknown) => new Intl.NumberFormat('en').format(Number(value || 0))
const monthName = (value: string) => new Date(`${value}-01T00:00:00`).toLocaleDateString('en', { month: 'short', year: '2-digit' })
async function readApiResponse<T>(response: Response): Promise<T> {
  const body = await response.text()
  let payload: { detail?: string } | T | null = null
  try { payload = body ? JSON.parse(body) as { detail?: string } | T : null } catch { /* Report a readable API error below. */ }
  if (!response.ok) {
    if (!body && response.status >= 500) throw new Error('The dashboard API did not respond. Start the FastAPI backend on port 8001.')
    const detail = payload && typeof payload === 'object' && 'detail' in payload ? payload.detail : null
    throw new Error(typeof detail === 'string' ? detail : 'The dashboard service returned an unreadable response.')
  }
  if (payload === null) throw new Error('The dashboard service returned no data. Start the FastAPI backend on port 8001 and try again.')
  return payload as T
}
function requestError(reason: unknown, fallback: string) {
  if (reason instanceof TypeError) return 'The dashboard API did not respond. Start the FastAPI backend on port 8001.'
  return reason instanceof Error ? reason.message : fallback
}

const pendingReads = new Map<string, Promise<unknown>>()
function getRead<T>(url: string): Promise<T> {
  const existing = pendingReads.get(url)
  if (existing) return existing as Promise<T>
  const request = fetch(url).then(readApiResponse<T>)
  pendingReads.set(url, request)
  request.then(() => {
    if (pendingReads.get(url) === request) pendingReads.delete(url)
  }, () => {
    if (pendingReads.get(url) === request) pendingReads.delete(url)
  })
  return request as Promise<T>
}

export default function App() {
  const [career, setCareer] = useState('')
  const [country, setCountry] = useState('')
  const [period, setPeriod] = useState('all')
  const [seniority, setSeniority] = useState('')
  const [remote, setRemote] = useState('')
  const [market, setMarket] = useState<Market | null>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [postOffset, setPostOffset] = useState(0)
  const [hasMorePosts, setHasMorePosts] = useState(false)
  const [sourceError, setSourceError] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [profilesLoading, setProfilesLoading] = useState(true)
  const [profilesError, setProfilesError] = useState('')
  const [profileName, setProfileName] = useState('')
  const [profileForm, setProfileForm] = useState('')
  const [compare, setCompare] = useState<string[]>([])
  const [frontMajor, setFrontMajor] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [generatedSql, setGeneratedSql] = useState('')
  const [queryResults, setQueryResults] = useState<QueryResults | null>(null)
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    const query = new URLSearchParams()
    if (career) query.set('career', career)
    if (country) query.set('country', country)
    if (seniority) query.set('seniority', seniority)
    if (remote) query.set('remote', remote)
    if (period !== 'all') { query.set('start', `${period}-01`); query.set('end', '2026-10') }
    if (refreshKey) query.set('refresh', String(refreshKey))
    let current = true
    getRead<Market>(`/api/market?${query}`)
      .then(overview => { if (current) { setMarket(overview); setError('') } })
      .catch(reason => { if (current) { setMarket(null); setError(requestError(reason, 'Could not load the market data.')) } })
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [career, country, period, seniority, remote, refreshKey])

  useEffect(() => {
    const query = new URLSearchParams()
    if (career) query.set('career', career)
    if (country) query.set('country', country)
    if (seniority) query.set('seniority', seniority)
    if (remote) query.set('remote', remote)
    if (period !== 'all') { query.set('start', `${period}-01`); query.set('end', '2026-10') }
    let current = true
    getRead<Post[]>(`/api/posts?${query}&limit=6&offset=${postOffset}`)
      .then(rows => { if (current) { setSourceError(''); setPosts(rows.slice(0, 5)); setHasMorePosts(rows.length > 5) } })
      .catch(reason => { if (current) { setSourceError(requestError(reason, 'Could not load source posts.')); setPosts([]); setHasMorePosts(false) } })
    return () => { current = false }
  }, [career, country, period, seniority, remote, postOffset, refreshKey])

  useEffect(() => {
    let current = true
    fetch('/api/profiles').then(readApiResponse<Profile[]>).then(rows => { if (current) { setProfiles(rows); setProfilesError('') } })
      .catch(reason => { if (current) setProfilesError(requestError(reason, 'Could not load demo profiles.')) })
      .finally(() => { if (current) setProfilesLoading(false) })
    return () => { current = false }
  }, [refreshKey])
  useEffect(() => { getRead<Identity>('/api/whoami').then(setIdentity).catch(() => {}) }, [])

  const selectedCareerInfo = careers.find(item => item.name === career)
  const relatedMajors = selectedCareerInfo?.match || []
  const displayedMajors = compare.length ? compare : relatedMajors
  const summary = market?.summary || {}
  const coveragePct = market?.coverage.total ? Math.min(100, Math.round(market.coverage.processed / market.coverage.total * 100)) : 0
  const monthCoverage = useMemo(() => new Map((market?.month_coverage || []).map(row => [row.month, row])), [market])
  const firstMonth = String(summary.first_month || market?.month_coverage?.[0]?.month || '2020-01')
  const lastMonth = String(summary.last_month || market?.months?.at(-1)?.month || 'Latest')
  const topSkills = market?.skills?.slice(0, 5) || []
  const remotePosts = market?.remote?.find(item => item.remote_policy === 'remote')?.posts || 0
  const skillMentions = market?.skills?.reduce((total, item) => total + Number(item.mentions || 0), 0) || 0

  function selectCareer(value: string) { setLoading(true); setError(''); setSourceError(''); setCareer(value); setPostOffset(0) }
  function toggleMajor(major: string) {
    setCompare(current => {
      if (current.includes(major)) return current.filter(value => value !== major)
      if (current.length >= 3) return current
      return [...current, major]
    })
    if (compare.includes(major) || compare.length < 3) setFrontMajor(major)
  }
  function loadProfile(name: string) {
    const profile = profiles.find(value => value.name === name) || starterProfiles.find(value => value.name === name)
    const nextCareer = profile?.career || ''
    setProfileName(name)
    if (nextCareer !== career) setLoading(true)
    setError(''); setSourceError('')
    setCareer(nextCareer)
    setPostOffset(0)
    setCompare(profile?.majors || [])
    setFrontMajor(profile?.majors?.at(-1) || '')
  }
  async function saveProfile() {
    const name = profileForm.trim() || (profiles.some(profile => profile.name === profileName) ? profileName.trim() : '')
    if (!name) { setError('Add a name for this demo profile first.'); return }
    const snapshot = { name, interests: career ? [career] : [], subjects: compare, career, majors: compare }
    try {
      await fetch('/api/profiles', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(snapshot) }).then(readApiResponse<Profile>)
      const saved = await fetch('/api/profiles').then(readApiResponse<Profile[]>)
      setProfiles(saved); setProfilesError(''); setProfileName(name); setProfileForm(''); setError('')
    } catch (reason) { setError(requestError(reason, 'Could not save this profile.')) }
  }
  async function removeProfile() {
    if (!profileName || !window.confirm(`Delete the shared demo profile "${profileName}"?`)) return
    try {
      await fetch(`/api/profiles/${encodeURIComponent(profileName)}`, { method: 'DELETE' }).then(readApiResponse<{ deleted: string }>)
      setProfiles(await fetch('/api/profiles').then(readApiResponse<Profile[]>))
      if (career) setLoading(true)
      setProfileName(''); setCareer(''); setCompare([]); setFrontMajor(''); setError('')
    } catch (reason) { setError(requestError(reason, 'Could not delete this profile.')) }
  }
  async function ask() {
    if (!question.trim()) return
    setChatLoading(true); setAnswer(''); setGeneratedSql(''); setQueryResults(null)
    try {
      const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, conversation_id: conversationId }) })
      const data = await readApiResponse<{ conversation_id: string; answer: string; sql?: string; query_results?: QueryResults }>(response)
      setConversationId(data.conversation_id); setAnswer(data.answer); setGeneratedSql(data.sql || ''); setQueryResults(data.query_results || null)
    } catch (reason) { setAnswer(requestError(reason, 'Genie could not answer this question.')) }
    finally { setChatLoading(false) }
  }

  return <div className="dashboard-shell">
    <a className="skip-link" href="#dashboard">Skip to dashboard</a>
    <header className="topbar">
      <a className="brand" href="#dashboard" aria-label="CareerSync home"><span>CareerSync</span></a>
      <div className="topbar-right">
        <label className="profile-select"><span>PROFILE</span><select value={profileName} onChange={event => loadProfile(event.target.value)} aria-label="Choose a demo profile" aria-describedby={profilesError ? 'profiles-error' : undefined}><option value="">Choose profile</option><optgroup label="Starter profiles">{starterProfiles.map(profile => <option key={profile.name} value={profile.name}>{profile.name}</option>)}</optgroup>{profiles.length > 0 && <optgroup label={profilesLoading ? 'Saved profiles · loading' : 'Saved class profiles'}>{profiles.map(profile => <option key={profile.name} value={profile.name}>{profile.name}</option>)}</optgroup>}</select><ChevronDown size={13}/></label>
        <button className="refresh-button" onClick={() => { setPostOffset(0); setLoading(true); setProfilesLoading(true); setError(''); setSourceError(''); setProfilesError(''); setRefreshKey(value => value + 1) }} aria-label="Refresh dashboard" title="Refresh market data"><RefreshCw size={14}/><span>Refresh</span></button>
      </div>
    </header>

    <main id="dashboard">
      <section className="filters" aria-label="Market filters">
        <div className="filter-intro"><span className="signal-dot"/><div><strong>Hiring market</strong><small>Verified job advertisements</small></div></div>
        <label>CAREER<select value={career} onChange={event => selectCareer(event.target.value)}><option value="">All tech roles</option>{careers.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label>
        <label>COUNTRY<select value={country} onChange={event => { setLoading(true); setError(''); setSourceError(''); setCountry(event.target.value); setPostOffset(0) }}><option value="">All locations</option>{market?.country_options.map(item => <option key={item}>{item}</option>)}</select></label>
        <label>SENIORITY<select value={seniority} onChange={event => { setLoading(true); setError(''); setSourceError(''); setSeniority(event.target.value); setPostOffset(0) }}><option value="">All levels</option>{['intern','student','junior','mid','senior','lead','staff','principal','manager','director'].map(item => <option key={item}>{item}</option>)}</select></label>
        <label>WORK STYLE<select value={remote} onChange={event => { setLoading(true); setError(''); setSourceError(''); setRemote(event.target.value); setPostOffset(0) }}><option value="">Any policy</option>{['remote','hybrid','onsite','mixed','not_stated'].map(item => <option key={item} value={item}>{item.replace('_',' ')}</option>)}</select></label>
        <label>FROM<select value={period} onChange={event => { setLoading(true); setError(''); setSourceError(''); setPeriod(event.target.value); setPostOffset(0) }}><option value="all">All years</option>{['2020','2021','2022','2023','2024','2025','2026'].map(item => <option key={item}>{item}</option>)}</select></label>
      </section>

      {error && <div className="status-message" role="alert"><CircleHelp size={16}/><span>{error}</span></div>}
      {loading && market && <div className="status-message" role="status">Updating figures for the selected filters…</div>}
      {profilesError && profilesError !== error && <div className="status-message" id="profiles-error" role="alert"><CircleHelp size={16}/><span>{profilesError}</span></div>}
      {market && market.coverage.processed < market.coverage.total && <div className="coverage-banner" role="status"><span>ARCHIVE PROCESSING</span><span>{number(market.coverage.processed)} / {number(market.coverage.total)} source posts validated</span><span className="banner-muted">Charts exclude unfinished records.</span></div>}

      <Web3Bento>
        <Tile className="tile--lead" title={<>Good {profileName ? 'to see you' : 'day'}, <span className="lime-text">{profileName || 'future technologist'}</span></>} action={<span className="mono muted">{firstMonth} to {lastMonth}</span>}>
          <div className="lead-metric"><div><strong>{market ? number(summary.post_count) : loading ? '···' : 'N/A'}</strong><span>validated hiring posts</span></div><div className="lead-coverage"><small>ARCHIVE COVERAGE</small><b>{market ? `${coveragePct}%` : 'N/A'}</b></div></div>
          <div className="month-bars" aria-label="Monthly hiring post activity">{market?.months?.slice(-25).map(item => {
            const row = monthCoverage.get(item.month)
            const isPartial = !!row && Number(row.processed_posts) < Number(row.source_posts)
            const max = Math.max(1, ...market.months.map(month => month.posts))
            return <span key={item.month} title={`${monthName(item.month)} · ${number(item.posts)} verified posts${isPartial ? ' · month is still partial' : ''}`} style={{ height: `${Math.max(8, Number(item.posts) / max * 100)}%`, opacity: isPartial ? .43 : 1 }} />
          })}</div>
          <div className="month-caption"><span>{market?.months?.length ? monthName(market.months[Math.max(0,market.months.length-25)].month) : 'Monthly activity'}</span><b>Verified posts by month</b><span>{market?.months?.length ? monthName(market.months.at(-1)!.month) : 'Waiting for data'}</span></div>
          <div className="lead-foot"><span>Hacker News “Who is hiring?”</span><span>All posts: {number(market?.statuses?.needs_review)} need review <i/> {number(market?.statuses?.skipped_unavailable)} unavailable</span></div>
        </Tile>

        <Tile className="tile--allocation" title="Work arrangement" action={<span className="mono muted">POSTS</span>}>
          <div className="allocation-chart">{market?.remote?.length ? <><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={market.remote} dataKey="posts" nameKey="remote_policy" innerRadius={49} outerRadius={66} paddingAngle={3} stroke="none">{market.remote.map(item => <Cell key={item.remote_policy} fill={policyColors[item.remote_policy] || '#666'}/>)}</Pie><Tooltip formatter={(value,name) => [number(value), String(name).replace('_',' ')]} contentStyle={{ background: 'var(--tile)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text)' }}/></PieChart></ResponsiveContainer><div className="donut-center"><b>{number(summary.post_count)}</b><span>posts</span></div></> : <Empty loading={loading} unavailable={!market && !!error}/>}</div>
          <div className="policy-legend">{market?.remote?.slice(0,4).map(item => <div key={item.remote_policy}><i style={{ background: policyColors[item.remote_policy] || '#666' }}/><span>{item.remote_policy.replace('_',' ')}</span><b>{number(item.posts)}</b></div>)}</div>
        </Tile>

        <MarketMetric title="Hiring posts" value={market ? number(summary.post_count) : loading ? '···' : 'N/A'} detail="Matches the active market filters" tone="lime"/>
        <MarketMetric title="Remote posts" value={market ? number(remotePosts) : loading ? '···' : 'N/A'} detail="Posts explicitly labeled remote" tone="lilac"/>
        <MarketMetric title="Pay groups" value={market ? number(market.salaries.length) : loading ? '···' : 'N/A'} detail="Grouped by currency and pay period" tone="copper"/>
        <MarketMetric title="Skill mentions" value={market ? number(skillMentions) : loading ? '···' : 'N/A'} detail={`${market?.skills?.length || 0} distinct skills in this view`} tone="mint"/>

        <Tile className="tile--stack" title={<>Major shortlist <sup className="mono">{compare.length}/3</sup></>} action={<span className="mono muted">{selectedCareerInfo ? 'PATHWAYS' : 'EXPLORE'}</span>}>
          <MajorStack majors={displayedMajors.slice(0,3)} selected={frontMajor} compared={compare} onSelect={toggleMajor}/>
          <div className="stack-caption"><span>{frontMajor || 'Choose a subject below'}</span><span>{compare.length ? `${compare.length} saved` : 'Suggested connections'}</span></div>
        </Tile>

        <Tile className="tile--status" title="Archive coverage" action={<span className="live-marker" title="Overall archive totals are independent of market filters"><i/>{market ? 'ALL POSTS' : loading ? 'CONNECTING' : 'UNAVAILABLE'}</span>}>
          <CoverageGauge value={market ? coveragePct : null}/>
          <div className="coverage-counts"><div><span>Posts processed</span><b>{market ? number(market.coverage.processed) : 'N/A'}</b></div><div><span>Still in queue</span><b>{market ? number(Math.max(0, Number(market.coverage.total || 0) - Number(market.coverage.processed || 0))) : 'N/A'}</b></div><div><span>Needs review</span><b>{market ? number(market.statuses?.needs_review) : 'N/A'}</b></div><div><span>Non-hiring</span><b>{market ? number(market.statuses?.non_hiring) : 'N/A'}</b></div><div><span>Unavailable</span><b>{market ? number(market.statuses?.skipped_unavailable) : 'N/A'}</b></div><div><span>Failed</span><b>{market ? number(market.statuses?.failed) : 'N/A'}</b></div></div>
        </Tile>

        <Tile className="tile--trend" title="Hiring activity" action={<span className="mono muted">{firstMonth} to {lastMonth}</span>}>
          <div className="chart-summary"><div><span>Posts per month</span><b>{market?.months?.length ? number(market.months.at(-1)?.posts) : 'No data'}</b><small>Latest month, extracted posts</small></div><span className="chart-note"><i/> Hiring posts</span></div>
          <div className="trend-chart">{market?.months?.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={market.months} margin={{ top: 14, right: 8, left: -18, bottom: 0 }}><defs><linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#b0f34b" stopOpacity={.26}/><stop offset="100%" stopColor="#b0f34b" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="var(--grid)"/><XAxis dataKey="month" tickFormatter={value => value.slice(2,7)} minTickGap={40} tickLine={false} axisLine={false}/><YAxis tickLine={false} axisLine={false}/><Tooltip labelFormatter={value => monthName(String(value))} formatter={value => [number(value), 'Verified posts']} contentStyle={{ background: 'var(--tile)', border: '1px solid var(--border)', borderRadius: 12, color: 'var(--text)' }}/><Area type="monotone" dataKey="posts" stroke="var(--lime)" strokeWidth={2.5} fill="url(#trendFill)" connectNulls={false}/></AreaChart></ResponsiveContainer> : <Empty loading={loading} unavailable={!market && !!error}/>}</div>
          <p className="chart-footnote">Counts reflect posts processed so far. Partial months can change while extraction continues.</p>
        </Tile>

        <Tile className="tile--highlight" title={<span className="ink-subtle">CAREER SIGNAL</span>} action={<span className="lime-pill"><i/> {selectedCareerInfo ? 'MATCHING POSTS' : 'EXPLORING'}</span>}>
          <div className="highlight-title"><span className="highlight-glyph">{selectedCareerInfo?.icon || 'TC'}</span><div><strong>{selectedCareerInfo?.name || 'Explore a path in tech'}</strong><small>{selectedCareerInfo?.short || 'Select a career to focus the market data'}</small></div></div>
          <div className="highlight-number">{market ? number(summary.post_count) : 'N/A'}<span>{selectedCareerInfo ? 'posts mention this role family' : 'verified posts in current view'}</span></div>
          <div className="highlight-skills"><span>SKILLS IN THESE POSTS</span>{topSkills.slice(0,3).map((item,index)=><div key={item.skill}><i style={{opacity:1-index*.22}}/><b>{item.skill}</b><small>{number(item.mentions)}</small></div>)}{!topSkills.length && <p>{market ? 'No skill data in this filtered view.' : error ? 'Market data unavailable.' : 'No skill data in this filtered view.'}</p>}</div>
          <button className="highlight-action" onClick={() => document.getElementById('careers')?.scrollIntoView({ behavior: 'smooth' })}>Explore career pathways <ArrowUpRight size={15}/></button>
        </Tile>

        <Tile className="tile--salary" title="Advertised salary" action={<span className="mono muted">AS STATED</span>}>
          {market?.salaries?.length ? <div className="salary-list">{market.salaries.slice(0,4).map((item,index)=><div className="salary-entry" key={`${item.currency}-${item.period}-${index}`}><span>{item.currency || 'Currency unstated'} · {item.period?.replace('_',' ')}</span><b>{item.median_min ? number(item.median_min) : 'Not stated'} <i>to</i> {item.median_max ? number(item.median_max) : 'Not stated'}</b><small>{number(item.offers)} stated offers</small></div>)}</div> : market ? <div className="salary-empty"><span className="salary-symbol">$</span><p>Pay details appear when stated by employers.</p><small>Currency and pay period stay separate.</small></div> : <Empty loading={loading} unavailable={!!error}/>}
        </Tile>

        <Tile className="tile--skills" title="Skills requested" action={<span className="mono muted">TOP MENTIONS</span>}>
          <div className="skills-layout"><div className="skills-chart">{market?.skills?.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={market.skills.slice(0,8)} layout="vertical" margin={{ left: 0, right: 34, top: 0, bottom: 0 }}><XAxis type="number" hide/><YAxis type="category" dataKey="skill" width={105} tickLine={false} axisLine={false}/><Tooltip formatter={(value) => [number(value), 'Posts mention skill']} cursor={{ fill: 'var(--hover)' }} contentStyle={{ background: 'var(--tile)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text)' }}/><Bar dataKey="mentions" fill="var(--lilac)" radius={[0,5,5,0]} barSize={14}/></BarChart></ResponsiveContainer> : <Empty loading={loading} unavailable={!market && !!error}/>}</div><div className="skill-rank">{topSkills.slice(0,4).map((item,index)=><div key={item.skill}><span className="mono">{String(index+1).padStart(2,'0')}</span><b>{item.skill}</b><small>{number(item.mentions)}</small></div>)}</div></div>
          <p className="chart-footnote">Skills are counted at the advertisement level, not as one requirement per vacancy.</p>
        </Tile>

        <Tile className="tile--activity" title="Source advertisements" action={<a href="https://news.ycombinator.com/submitted?id=whoishiring" target="_blank" rel="noreferrer" className="text-link">Hacker News <ExternalLink size={12}/></a>}>
          {sourceError ? <div className="source-warning" role="alert">{sourceError}</div> : posts.length ? posts.map(post => <a className="activity-row" key={post.item_id} href={post.source_url} target="_blank" rel="noreferrer"><span className="activity-date mono">{post.month}</span><span className="activity-copy"><b>{post.text_plain.slice(0,125)}{post.text_plain.length>125?'…':''}</b><small>{post.skills?.slice(0,4).join(' · ') || 'Skills not stated'}</small></span><ExternalLink size={13}/></a>) : <Empty loading={loading} />}
          <div className="activity-footer"><span>Page {Math.floor(postOffset / 5) + 1}</span><div className="post-pagination"><button aria-label="Previous source posts" disabled={!postOffset} onClick={() => setPostOffset(value => Math.max(0, value - 5))}><ChevronLeft size={13}/></button><button aria-label="Next source posts" disabled={!hasMorePosts} onClick={() => setPostOffset(value => value + 5)}><ChevronRight size={13}/></button></div></div>
        </Tile>
      </Web3Bento>

      <section className="below-grid" id="careers">
        <Tile className="lower-tile career-directory" title="Choose a career to explore" action={<span className="mono muted">6 PATHS</span>}>
          <div className="career-list">{careers.map(item => <button className={`career-option ${career===item.name?'is-active':''}`} key={item.name} onClick={() => selectCareer(career===item.name?'':item.name)} aria-pressed={career===item.name}><span>{item.icon}</span><b>{item.name}</b><small>{item.short}</small><ChevronRight size={14}/></button>)}</div>
        </Tile>

        <Tile className="lower-tile major-comparison" title="Compare university subjects" action={<span className="compare-counter mono">{compare.length} / 3</span>}>
          <p className="lower-intro">Choose up to three subjects to explore how different curricula can connect to your interests. Program details vary by university.</p>
          <div className="major-picker">{majors.map((major,index) => <button key={major} onClick={() => toggleMajor(major)} className={compare.includes(major)?'chosen':''} aria-pressed={compare.includes(major)} disabled={!compare.includes(major)&&compare.length>=3}><span className="major-dot" style={{background:majorColors[index%majorColors.length]}}/><span>{major}</span>{compare.includes(major)?<Check size={14}/>:<span className="pick-box"/>}</button>)}</div>
          {compare.length>0 && <div className="comparison-cards">{compare.map((major,index)=>{const guide=subjectGuides[major];return <article className="comparison-card" key={major}><div className="comparison-head"><span className="major-dot" style={{background:majorColors[index%majorColors.length]}}/><strong>{major}</strong><button onClick={()=>toggleMajor(major)} aria-label={`Remove ${major}`}><X size={14}/></button></div><dl><div><dt>Typical curriculum themes</dt><dd>{guide.topics}</dd></div><div><dt>Entry requirements to check</dt><dd>{guide.preparation}</dd></div><div><dt>Related career paths</dt><dd>{careers.filter(item=>item.match.includes(major)).map(item=>item.name).join(' · ') || 'Explore related technology roles'}</dd></div><div><dt>Skills in the current market view</dt><dd>{market?.skills?.slice(0,3).map(item=>item.skill).join(' · ') || 'Choose a market filter to see employer skill mentions.'}</dd></div></dl><a className="curriculum-link" href={guide.url} target="_blank" rel="noreferrer">{guide.source} <ExternalLink size={11}/></a></article>})}</div>}
          <div className="source-note"><BookOpen size={14}/><span>Curriculum topics summarize professional guidance, not a university's exact requirements. Skills reflect the active job-post filters.</span></div>
        </Tile>

        <Tile className="lower-tile profile-save" title="Save this direction" action={<span className="profile-label">SHARED DEMO</span>}>
          <p className="lower-intro">Save your selected career and major shortlist as a named demo profile for the class.</p>
          <label className="profile-label-input">PROFILE NAME<input value={profileForm} onChange={event=>setProfileForm(event.target.value)} placeholder={profileName || 'e.g. Data and design'} maxLength={48}/></label>
          <div className="profile-actions"><button className="save-button" onClick={saveProfile}>Save demo profile <ChevronRight size={14}/></button>{profiles.some(profile => profile.name === profileName) && <button className="delete-profile" onClick={removeProfile}><Trash2 size={14}/> Delete shared profile</button>}</div>
          <small className="profile-disclaimer">Profiles are shared classroom examples, not private student accounts.</small>
        </Tile>

        <Tile className="lower-tile chat-tile" title="Ask about the market" action={<span className="ai-chip"><Sparkles size={12}/> DATABRICKS GENIE</span>}>
          <div className="chat-identity"><span>{identity?.user ? `Signed in: ${identity.user}` : 'Signed in with your workspace account'}</span><span>Runs as {identity?.execution_identity || 'Databricks app identity'}</span></div>
          <div className="chat-suggestions">{questions.map(item=><button key={item} onClick={()=>setQuestion(item)}>{item}<ArrowUpRight size={12}/></button>)}</div>
          <form className="chat-input" onSubmit={event=>{event.preventDefault();ask()}}><input value={question} onChange={event=>setQuestion(event.target.value)} placeholder="Ask about hiring skills, salary, or pathways…" aria-label="Ask a market question"/><button disabled={chatLoading} aria-label={chatLoading ? 'Waiting for Genie' : 'Send question'}>{chatLoading ? <RefreshCw className="chat-spinner" size={15}/> : <Send size={15}/>}</button></form>
          {chatLoading && <div className="chat-status" role="status" aria-live="polite">Genie is checking the market data…</div>}
          {answer && <div className="chat-answer" role="status">{answer}</div>}
          {queryResults?.rows?.length ? <div className="genie-results" role="region" aria-label="Genie supporting query results"><table><thead><tr>{queryResults.columns.map((column,index)=><th key={`${column}-${index}`}>{column}</th>)}</tr></thead><tbody>{queryResults.rows.slice(0,6).map((row,rowIndex)=><tr key={rowIndex}>{row.slice(0,6).map((value,columnIndex)=><td key={columnIndex}>{queryResults.columns[columnIndex]?.toLowerCase().includes('url') && typeof value === 'string' && value.startsWith('https://news.ycombinator.com/') ? <a href={value} target="_blank" rel="noreferrer">Open source <ExternalLink size={11}/></a> : value ?? 'Unknown'}</td>)}</tr>)}</tbody></table></div> : null}
          {generatedSql && <details className="generated-sql"><summary>{'Generated SQL'}{` · ${identity?.execution_identity || 'app identity'}`}</summary><pre>{generatedSql}</pre></details>}
          <small className="chat-footnote">AI answers can be wrong. Check source posts and official university requirements.</small>
        </Tile>
      </section>
      <footer className="dashboard-footer"><span>CareerSync</span><span>Hacker News “Who is hiring?” · 2020 onward</span><span>Hiring signals describe posts, not the entire job market.</span></footer>
    </main>
  </div>
}

function MajorStack({ majors: stack, selected, compared, onSelect }: { majors: string[]; selected: string; compared: string[]; onSelect: (major:string)=>void }) {
  const visible = stack.length ? stack : ['Computer science', 'Data science', 'Software engineering']
  return <div className="major-stack" aria-label="Suggested major cards. Select a card to add it to the comparison.">{visible.map((major,index)=><button key={`${major}-${index}`} className={`stack-card stack-card-${index} ${selected===major?'stack-card-front':''}`} style={{'--stack-color':majorColors[index%majorColors.length]} as CSSProperties} onClick={()=>onSelect(major)} aria-pressed={compared.includes(major)} disabled={!compared.includes(major)&&compared.length>=3}><span className="stack-card-label"><BookOpen size={13}/>{compared.includes(major)?'SHORTLISTED':'SUBJECT'}</span><strong>{major}</strong><span className="stack-card-foot">{careers.filter(item=>item.match.includes(major)).length} related career paths <ArrowUpRight size={13}/></span></button>)}</div>
}

function CoverageGauge({value}:{value:number|null}) {
  return <div className="gauge-wrap"><svg viewBox="0 0 160 92" role="img" aria-label={value === null ? 'Source coverage unavailable' : `${value}% of source posts processed`}><path d="M 15 78 A 65 65 0 0 1 145 78" fill="none" stroke="var(--gauge-track)" strokeWidth="12" strokeLinecap="round" pathLength="100"/><path d="M 15 78 A 65 65 0 0 1 145 78" fill="none" stroke="var(--lime)" strokeWidth="12" strokeLinecap="round" pathLength="100" strokeDasharray="100" strokeDashoffset={value === null ? 100 : 100-value}/></svg><strong>{value ?? 'N/A'}{value !== null && <small>%</small>}</strong><span>source coverage</span></div>
}

function Empty({loading,unavailable=false}:{loading:boolean;unavailable?:boolean}) { return <div className="empty-state">{loading?'Loading verified market data…':unavailable?'Market data unavailable. Check the connection message above.':'No matching verified posts yet.'}</div> }
