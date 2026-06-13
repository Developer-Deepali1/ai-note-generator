import { useMemo, type ReactNode } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  FiActivity,
  FiClock,
  FiEye,
  FiMic,
  FiShield,
  FiTarget,
  FiTrendingUp,
  FiUsers,
} from 'react-icons/fi'

import { WebcamEmotionTracker } from './WebcamEmotionTracker'
import { ProgressRing } from './dashboard/ProgressRing'
import { SectionCard } from './dashboard/SectionCard'
import {
  aiNotes,
  attentionTrend,
  emotionData,
  liveTranscript,
  overviewMetrics,
  presenceTrend,
  sessionHistory,
  timelineEvents,
} from './dashboard/mockData'

const chartColors = ['#8b5cf6', '#06b6d4', '#f59e0b', '#10b981', '#f97316']

function DashboardHeader() {
  return (
    <header className="dashboard-header glass-panel">
      <div>
        <p className="eyebrow">Enterprise meeting intelligence</p>
        <h1>AI-Powered Smart Note Generator & Engagement Tracker</h1>
        <p className="dashboard-header__copy">
          A premium control surface for live transcription, AI notes, emotional signals,
          and attendance tracking in one compact SaaS workspace.
        </p>
      </div>

      <div className="dashboard-header__aside">
        <div className="status-pill status-pill--live">
          <span className="status-dot" />
          Live monitoring
        </div>
        <div className="header-metric">
          <span>Session</span>
          <strong>Executive standup</strong>
        </div>
        <div className="header-metric">
          <span>Latency</span>
          <strong>1.2s</strong>
        </div>
      </div>
    </header>
  )
}

function MetricCard({
  icon,
  label,
  value,
  delta,
  hint,
}: {
  icon: ReactNode
  label: string
  value: string
  delta: string
  hint: string
}) {
  return (
    <article className="metric-card glass-panel">
      <div className="metric-card__icon">{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>
          {delta} {hint}
        </span>
      </div>
    </article>
  )
}

function TranscriptFeed() {
  return (
    <div className="stack-list">
      {liveTranscript.map((item) => (
        <article key={`${item.time}-${item.speaker}`} className="transcript-item">
          <div className={`transcript-item__time transcript-item__time--${item.mood}`}>
            {item.time}
          </div>
          <div>
            <div className="transcript-item__meta">
              <strong>{item.speaker}</strong>
              <span>{item.mood}</span>
            </div>
            <p>{item.text}</p>
          </div>
        </article>
      ))}
    </div>
  )
}

function NotesFeed() {
  return (
    <div className="notes-feed">
      {aiNotes.map((note) => (
        <article key={note.title} className="notes-feed__item">
          <h3>{note.title}</h3>
          <p>{note.text}</p>
        </article>
      ))}
      <div className="action-strip">
        <div>
          <span>Next action</span>
          <strong>Send summary draft to stakeholders</strong>
        </div>
        <button type="button" className="secondary-action secondary-action--compact">
          Export note set
        </button>
      </div>
    </div>
  )
}

function Timeline() {
  return (
    <div className="timeline">
      {timelineEvents.map((event) => (
        <article key={`${event.time}-${event.title}`} className="timeline__item">
          <div className={`timeline__marker timeline__marker--${event.tone}`} />
          <div>
            <span className="timeline__time">{event.time}</span>
            <h3>{event.title}</h3>
            <p>{event.detail}</p>
          </div>
        </article>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const overview = useMemo(() => overviewMetrics, [])

  return (
    <main className="dashboard-shell">
      <DashboardHeader />

      <section className="metric-grid" aria-label="Dashboard overview metrics">
        {overview.map((item, index) => (
          <MetricCard
            key={item.label}
            icon={
              [<FiTarget />, <FiUsers />, <FiMic />, <FiActivity />][index]
            }
            label={item.label}
            value={item.value}
            delta={item.delta}
            hint={item.hint}
          />
        ))}
      </section>

      <section className="dashboard-grid" aria-label="AI note generator dashboard">
        <SectionCard
          eyebrow="Dashboard Overview"
          title="Operational command center"
          description="Compact live health for transcription, notes, sentiment, attendance, and session quality."
          className="span-12 overview-card"
        >
          <div className="overview-grid">
            <div className="overview-summary">
              <div className="overview-summary__row">
                <FiTrendingUp />
                <span>Session health</span>
                <strong>Excellent</strong>
              </div>
              <div className="overview-summary__row">
                <FiShield />
                <span>Compliance signal</span>
                <strong>Recording active</strong>
              </div>
              <div className="overview-summary__row">
                <FiEye />
                <span>Face presence</span>
                <strong>97% stable</strong>
              </div>
            </div>
            <div className="overview-signal">
              <ProgressRing value={92} label="Engagement" caption="high attention across the session" tone="violet" />
              <div className="mini-stack">
                <div>
                  <span>Average latency</span>
                  <strong>1.2 seconds</strong>
                </div>
                <div>
                  <span>Live notes generated</span>
                  <strong>24 fragments</strong>
                </div>
                <div>
                  <span>Resolution status</span>
                  <strong>Enterprise ready</strong>
                </div>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Live Transcription"
          title="Streaming transcript with speaker-aware context"
          description="Short, searchable transcript blocks keep the surface compact and readable."
          className="span-7"
        >
          <div className="chart-frame chart-frame--compact">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={attentionTrend}>
                <defs>
                  <linearGradient id="transcriptionFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.07)" vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} width={32} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 16,
                    color: '#e2e8f0',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fill="url(#transcriptionFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <TranscriptFeed />
        </SectionCard>

        <SectionCard
          eyebrow="AI Notes"
          title="Structured summaries and action capture"
          description="A concise note layer with executive summaries and decisions extracted from the transcript."
          className="span-5"
        >
          <NotesFeed />
        </SectionCard>

        <SectionCard
          eyebrow="Emotion Analytics"
          title="Mood and focus distribution"
          description="Bar charts highlight the tone signature of the current conversation."
          className="span-4"
        >
          <div className="chart-frame chart-frame--small">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={emotionData}>
                <CartesianGrid stroke="rgba(255,255,255,0.07)" vertical={false} />
                <XAxis dataKey="label" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} width={28} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 16,
                    color: '#e2e8f0',
                  }}
                />
                <Bar dataKey="value" radius={[10, 10, 0, 0]}>
                  {emotionData.map((entry, index) => (
                    <Cell key={entry.label} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Face Presence Analytics"
          title="Real-time presence and webcam intelligence"
          description="A compact live monitor shows detection strength, face count, and presence duration."
          className="span-8"
        >
          <div className="face-presence-grid">
            <div className="face-presence-summary">
              <ProgressRing value={97} label="Presence" caption="webcam detection stayed stable" tone="cyan" />
              <div className="signal-list">
                <div>
                  <span>Faces detected</span>
                  <strong>1</strong>
                </div>
                <div>
                  <span>Session coverage</span>
                  <strong>38m active</strong>
                </div>
                <div>
                  <span>Detection state</span>
                  <strong>Continuous</strong>
                </div>
              </div>
              <div className="sparkline-card">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={presenceTrend}>
                    <Line
                      type="monotone"
                      dataKey="presence"
                      stroke="#06b6d4"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="face-presence-live">
              <WebcamEmotionTracker />
            </div>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Engagement Score"
          title="Participation momentum"
          description="The score combines speech balance, response rhythm, and visual attention signals."
          className="span-4"
        >
          <ProgressRing value={92} label="Overall score" caption="balanced participation across the room" tone="emerald" />
          <div className="score-bars">
            <div>
              <span>Speech balance</span>
              <strong>88%</strong>
            </div>
            <div>
              <span>Response rate</span>
              <strong>91%</strong>
            </div>
            <div>
              <span>Attention span</span>
              <strong>94%</strong>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Attendance Tracking"
          title="Session presence over time"
          description="A live trendline and support metrics provide an attendance snapshot at a glance."
          className="span-8"
        >
          <div className="chart-frame chart-frame--compact">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={presenceTrend}>
                <CartesianGrid stroke="rgba(255,255,255,0.07)" vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} width={32} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 16,
                    color: '#e2e8f0',
                  }}
                />
                <Line type="monotone" dataKey="presence" stroke="#10b981" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="attendance-grid">
            <div>
              <span>Presence duration</span>
              <strong>38m 12s</strong>
            </div>
            <div>
              <span>Session duration</span>
              <strong>39m 04s</strong>
            </div>
            <div>
              <span>Attendance rate</span>
              <strong>97%</strong>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Session History"
          title="Recent meetings and archived performance"
          description="Compact history rows keep the dashboard readable without endless scrolling."
          className="span-4"
        >
          <div className="session-history">
            <div className="session-history__head">
              <span>Session</span>
              <span>Attendance</span>
            </div>
            {sessionHistory.map((session) => (
              <article key={session.title} className="session-history__row">
                <div>
                  <strong>{session.title}</strong>
                  <span>{session.date}</span>
                </div>
                <div className="session-history__stats">
                  <span>{session.attendance}</span>
                  <span>{session.engagement}</span>
                </div>
                <div className="session-history__footer">
                  <FiClock />
                  <span>{session.duration}</span>
                  <strong>{session.status}</strong>
                </div>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          eyebrow="Timeline View"
          title="Auto-generated session chronology"
          description="Every key event is indexed into a fast, glanceable timeline for follow-up."
          className="span-12"
        >
          <Timeline />
        </SectionCard>
      </section>
    </main>
  )
}