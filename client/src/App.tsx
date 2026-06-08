import './App.css'

import { WebcamEmotionTracker } from './components/WebcamEmotionTracker'

const capabilities = [
  {
    title: 'Automatic speech-to-text',
    description:
      'Convert meeting and class conversations into clean, searchable notes in real time.',
  },
  {
    title: 'AI summaries and action items',
    description:
      'Generate concise summaries, key takeaways, and next steps without manual rewriting.',
  },
  {
    title: 'Attendance and engagement tracking',
    description:
      'Monitor participant presence, participation trends, and learning engagement across sessions.',
  },
  {
    title: 'Analytical reports',
    description:
      'Surface insights for educators and organizers to improve productivity and retention.',
  },
]

const outcomes = [
  'Less manual note-taking',
  'Faster knowledge retention',
  'Clearer follow-up actions',
  'Better visibility into participation',
]

function App() {
  return (
    <main className="app-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">AI note intelligence for live sessions</p>
          <h1>AI-Powered Smart Note Generator & Engagement Tracker</h1>
          <p className="lede">
            Capture conversations from meetings and online classes, turn them into
            structured notes, and track how people participate along the way.
          </p>

          <div className="hero-actions">
            <a className="primary-action" href="#capabilities">
              Explore capabilities
            </a>
            <a className="secondary-action" href="#workflow">
              See the workflow
            </a>
          </div>

          <div className="outcome-row" aria-label="Key outcomes">
            {outcomes.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="hero-panel" aria-label="Project highlights">
          <div className="panel-card panel-card--accent">
            <span>Live input</span>
            <strong>Speech to structured notes</strong>
            <p>Audio is transcribed, summarized, and organized into digestible insights.</p>
          </div>
          <div className="panel-card">
            <span>Participant tracking</span>
            <strong>Attendance and engagement</strong>
            <p>Track who joined, who spoke, and how engaged the session remained.</p>
          </div>
          <div className="panel-card">
            <span>Reporting</span>
            <strong>Actionable analytics</strong>
            <p>Review summaries, trends, and follow-up actions after each session.</p>
          </div>
        </div>
      </section>

      <section className="feature-grid" id="capabilities">
        {capabilities.map((capability) => (
          <article key={capability.title} className="feature-card">
            <h2>{capability.title}</h2>
            <p>{capability.description}</p>
          </article>
        ))}
      </section>

      <section className="workflow" id="workflow">
        <div>
          <p className="section-label">Workflow</p>
          <h2>From live conversation to usable insight</h2>
        </div>

        <div className="workflow-steps">
          <div>
            <span>01</span>
            <strong>Capture audio</strong>
            <p>Record meetings or classes with a simple interface.</p>
          </div>
          <div>
            <span>02</span>
            <strong>Generate notes</strong>
            <p>Use AI to create summaries, key points, and action items.</p>
          </div>
          <div>
            <span>03</span>
            <strong>Measure engagement</strong>
            <p>Review attendance, participation, and session analytics.</p>
          </div>
        </div>
      </section>

      <section className="emotion-lab" id="emotion-tracking">
        <div className="emotion-copy">
          <p className="section-label">Webcam emotion tracking</p>
          <h2>Sample facial emotion signals without interrupting the session.</h2>
          <p>
            The browser captures a frame every 5 seconds with <code>getUserMedia()</code>, sends it to the Flask API, and logs the
            dominant emotion with a confidence score for downstream engagement analytics.
          </p>
        </div>

        <WebcamEmotionTracker />
      </section>
    </main>
  )
}

export default App
