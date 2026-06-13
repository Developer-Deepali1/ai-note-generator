export const overviewMetrics = [
  {
    label: 'Engagement Score',
    value: '92%',
    delta: '+8.4%',
    hint: 'vs previous session',
  },
  {
    label: 'Attendance',
    value: '97%',
    delta: '+2.1%',
    hint: 'real-time presence',
  },
  {
    label: 'Transcript Accuracy',
    value: '98.6%',
    delta: '+1.3%',
    hint: 'AI confidence',
  },
  {
    label: 'Action Items',
    value: '14',
    delta: '+5',
    hint: 'auto-generated today',
  },
]

export const liveTranscript = [
  {
    time: '00:02',
    speaker: 'Host',
    text: 'Welcome team. Today we are reviewing the release plan and open risks.',
    mood: 'settled',
  },
  {
    time: '01:18',
    speaker: 'Product',
    text: 'We should lock the launch checklist before Friday so the rollout is predictable.',
    mood: 'priority',
  },
  {
    time: '03:40',
    speaker: 'Design',
    text: 'The new dashboard needs clearer hierarchy and less scrolling on smaller screens.',
    mood: 'insight',
  },
  {
    time: '05:11',
    speaker: 'AI Summary',
    text: 'Deadline, owner assignments, and QA checkpoints were converted into action items.',
    mood: 'ai',
  },
]

export const aiNotes = [
  {
    title: 'Executive summary',
    text: 'Release readiness is on track, but three follow-up tasks need clear ownership before handoff.',
  },
  {
    title: 'Decisions captured',
    text: 'Ship date, validation checkpoints, and approver sequence were all confirmed in session.',
  },
  {
    title: 'Action items',
    text: 'Publish QA checklist, confirm deployment owner, and update the launch status page.',
  },
]

export const emotionData = [
  { label: 'Calm', value: 82 },
  { label: 'Focused', value: 91 },
  { label: 'Curious', value: 74 },
  { label: 'Alert', value: 67 },
  { label: 'Distraction', value: 18 },
]

export const attentionTrend = [
  { time: '09:00', score: 74 },
  { time: '09:10', score: 79 },
  { time: '09:20', score: 87 },
  { time: '09:30', score: 91 },
  { time: '09:40', score: 89 },
  { time: '09:50', score: 94 },
  { time: '10:00', score: 92 },
]

export const presenceTrend = [
  { time: '09:00', presence: 88 },
  { time: '09:10', presence: 93 },
  { time: '09:20', presence: 96 },
  { time: '09:30', presence: 97 },
  { time: '09:40', presence: 98 },
  { time: '09:50', presence: 97 },
  { time: '10:00', presence: 97 },
]

export const sessionHistory = [
  {
    title: 'Executive standup',
    date: 'Today · 09:00',
    duration: '38m',
    attendance: '97%',
    engagement: '92%',
    status: 'Live',
  },
  {
    title: 'Customer sync',
    date: 'Yesterday · 15:00',
    duration: '44m',
    attendance: '95%',
    engagement: '89%',
    status: 'Reviewed',
  },
  {
    title: 'Training workshop',
    date: 'Jun 10 · 11:30',
    duration: '52m',
    attendance: '94%',
    engagement: '86%',
    status: 'Archived',
  },
]

export const timelineEvents = [
  {
    time: '09:00',
    title: 'Session started',
    detail: 'Meeting room connected and webcam monitoring activated.',
    tone: 'emerald',
  },
  {
    time: '09:08',
    title: 'Key decision captured',
    detail: 'Launch date and approval path were summarized by the AI note engine.',
    tone: 'violet',
  },
  {
    time: '09:20',
    title: 'Presence stayed high',
    detail: 'Face detection remained steady across the live attendance window.',
    tone: 'cyan',
  },
  {
    time: '09:33',
    title: 'Action items generated',
    detail: 'Three owners were assigned directly from the transcript context.',
    tone: 'amber',
  },
]