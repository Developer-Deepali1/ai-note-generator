import { useEffect, useRef, useState } from 'react'

import { analyzeEyeContact } from '../services/api'

type EyeContactHistoryItem = {
	timestamp: string
	eye_contact: boolean
	eye_contact_score: number
	gaze_direction: string
	head_pose: string
	analysis_status: string
}

type EyeContactSessionStats = {
	total_frames: number
	eye_contact_frames: number
	off_screen_frames: number
	average_eye_contact_score: number
	eye_contact_percentage: number
	history: EyeContactHistoryItem[]
}

type EyeContactReading = {
	success: boolean
	face_detected: boolean
	face_count: number
	eyes_visible: boolean
	eye_contact: boolean
	eye_contact_score: number
	gaze_direction: string
	head_pose: string
	analysis_status: string
	confidence: number
	timestamp: string
	session_stats: EyeContactSessionStats
}

type TrackerStatus = 'idle' | 'requesting' | 'running' | 'error'

const CAPTURE_INTERVAL_MS = 4000
const MAX_CAPTURE_WIDTH = 640

function formatDuration(seconds: number) {
	const mins = Math.floor(seconds / 60)
	const secs = seconds % 60
	return `${mins}m ${secs}s`
}

function formatLabel(value: string) {
	if (!value) {
		return 'Unknown'
	}
	return value
		.replace(/_/g, ' ')
		.replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatError(error: unknown) {
	if (error && typeof error === 'object' && 'response' in error) {
		const response = (error as { response?: { data?: { error?: string } } }).response
		const message = response?.data?.error
		if (typeof message === 'string' && message.trim()) {
			return message
		}
	}
	if (error instanceof Error && error.message.trim()) {
		return error.message
	}
	return 'Unable to analyze the current webcam frame.'
}

export function WebcamEmotionTracker() {
	const videoRef = useRef<HTMLVideoElement | null>(null)
	const canvasRef = useRef<HTMLCanvasElement | null>(null)
	const streamRef = useRef<MediaStream | null>(null)
	const intervalRef = useRef<number | null>(null)
	const sessionStartRef = useRef<number>(Date.now())
	
	const [status, setStatus] = useState<TrackerStatus>('idle')
	const [reading, setReading] = useState<EyeContactReading | null>(null)
	const [error, setError] = useState<string | null>(null)
	const [totalSessionSeconds, setTotalSessionSeconds] = useState<number>(0)
	const [eyeContactPercent, setEyeContactPercent] = useState<number>(0)
	const [averageScore, setAverageScore] = useState<number>(0)
	const [sessionStats, setSessionStats] = useState<EyeContactSessionStats | null>(null)

	const releaseStream = () => {
		if (intervalRef.current !== null) {
			window.clearInterval(intervalRef.current)
			intervalRef.current = null
		}
		streamRef.current?.getTracks().forEach((track) => track.stop())
		streamRef.current = null
		if (videoRef.current) {
			videoRef.current.srcObject = null
		}
	}

	const captureAndAnalyze = async () => {
		const video = videoRef.current
		const canvas = canvasRef.current
		if (!video || !canvas || video.videoWidth === 0 || video.videoHeight === 0) {
			return
		}

		const context = canvas.getContext('2d')
		if (!context) {
			setError('Canvas context is unavailable.')
			return
		}

		const captureWidth = Math.min(video.videoWidth, MAX_CAPTURE_WIDTH)
		const captureHeight = Math.max(1, Math.round((video.videoHeight / video.videoWidth) * captureWidth))
		canvas.width = captureWidth
		canvas.height = captureHeight
		context.drawImage(video, 0, 0, captureWidth, captureHeight)

		try {
			const frame = canvas.toDataURL('image/jpeg', 0.82)
			const response = await analyzeEyeContact({ frame })
			const data = response.data as EyeContactReading
			const stats = data.session_stats ?? null
			setReading(data)
			setSessionStats(stats)
			setEyeContactPercent(stats?.eye_contact_percentage ?? (data.eye_contact ? 100 : 0))
			setAverageScore(stats?.average_eye_contact_score ?? data.eye_contact_score)
			const now = Date.now()
			setTotalSessionSeconds(Math.max(0, Math.round((now - sessionStartRef.current) / 1000)))
			setError(null)
		} catch (requestError) {
			setError(formatError(requestError))
		}
	}

	const startTracking = async () => {
		if (!navigator.mediaDevices?.getUserMedia) {
			setStatus('error')
			setError('This browser does not support webcam capture.')
			return
		}

		try {
			setStatus('requesting')
			setError(null)
			const stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: 'user' },
				audio: false,
			})
			streamRef.current = stream
			if (videoRef.current) {
				videoRef.current.srcObject = stream
				await videoRef.current.play()
			}
			setStatus('running')
			sessionStartRef.current = Date.now()
			setTotalSessionSeconds(0)
			setEyeContactPercent(0)
			setAverageScore(0)
			setSessionStats(null)
			
			await captureAndAnalyze()
			intervalRef.current = window.setInterval(() => {
				void captureAndAnalyze()
			}, CAPTURE_INTERVAL_MS)
		} catch (requestError) {
			releaseStream()
			setStatus('error')
			const message =
				requestError instanceof Error
					? requestError.message
					: 'Unable to access the webcam.'
			setError(message)
		}
	}

	const stopTracking = () => {
		releaseStream()
		setStatus('idle')
		setReading(null)
		setSessionStats(null)
		setEyeContactPercent(0)
		setAverageScore(0)
	}

	// Auto-start on mount
	useEffect(() => {
		startTracking()
		return () => {
			releaseStream()
		}
	}, [])

	const historyEntries = (sessionStats?.history ?? []).slice(-5).reverse()
	const statusLabel = !reading
		? 'Idle'
		: reading.eye_contact
			? 'Focused'
			: formatLabel(reading.analysis_status)

	return (
		<div className="webcam-panel">
			{/* Video Preview */}
			<div className="webcam-preview-shell">
				<video
					ref={videoRef}
					className="webcam-preview"
					autoPlay
					muted
					playsInline
				/>
				<div className="webcam-overlay">
					<span className={`webcam-status webcam-status--${status}`}>{status}</span>
				</div>
			</div>

			<canvas ref={canvasRef} className="webcam-canvas" aria-hidden="true" />

			{/* Premium Monitoring Panel */}
			<div className="monitoring-panel">
				<div className="monitoring-grid">
					<div className="monitoring-card">
						<span className="monitoring-label">Eye Contact Score</span>
						<strong className="monitoring-value">
							{reading ? `${reading.eye_contact_score}%` : '—'}
						</strong>
					</div>

					<div className="monitoring-card">
						<span className="monitoring-label">Gaze Direction</span>
						<strong className="monitoring-value">
							{reading ? formatLabel(reading.gaze_direction) : '—'}
						</strong>
					</div>

					<div className="monitoring-card">
						<span className="monitoring-label">Head Pose</span>
						<strong className="monitoring-value">
							{reading ? formatLabel(reading.head_pose) : '—'}
						</strong>
					</div>

					<div className="monitoring-card">
						<span className="monitoring-label">Looking At Screen</span>
						<strong className="monitoring-value">
							{reading ? (reading.eye_contact ? 'Yes' : 'No') : '—'}
						</strong>
					</div>

					<div className="monitoring-card">
						<span className="monitoring-label">Status</span>
						<strong className="monitoring-value status-badge" data-status={status}>
							{statusLabel}
						</strong>
					</div>

					<div className="monitoring-card">
						<span className="monitoring-label">Live Percentage</span>
						<strong className="monitoring-value">{eyeContactPercent}%</strong>
					</div>
				</div>

				<div className="attendance-details">
					<div className="detail-row">
						<span>Average Session Score:</span>
						<span>{averageScore}%</span>
					</div>
					<div className="detail-row">
						<span>Session Duration:</span>
						<span>{formatDuration(totalSessionSeconds)}</span>
					</div>
					<div className="detail-row">
						<span>Total Frames:</span>
						<span>{sessionStats?.total_frames ?? 0}</span>
					</div>
					<div className="detail-row">
						<span>Eye Contact Frames:</span>
						<span>{sessionStats?.eye_contact_frames ?? 0}</span>
					</div>
					<div className="detail-row">
						<span>Off-Screen Frames:</span>
						<span>{sessionStats?.off_screen_frames ?? 0}</span>
					</div>
					<div className="detail-row">
						<span>Eye Contact %:</span>
						<span>{sessionStats?.eye_contact_percentage ?? 0}%</span>
					</div>
				</div>

				<div className="session-history" aria-label="Eye contact history">
					<div className="session-history__head">
						<span>Recent Samples</span>
						<span>Score / State</span>
					</div>
					{historyEntries.length > 0 ? (
						historyEntries.map((entry) => (
							<div key={`${entry.timestamp}-${entry.gaze_direction}-${entry.eye_contact_score}`} className="session-history__row">
								<div>
									<strong>{formatLabel(entry.gaze_direction)}</strong>
									<span>{formatLabel(entry.analysis_status)}</span>
								</div>
								<div className="session-history__stats">
									<strong>{entry.eye_contact_score}%</strong>
								</div>
							</div>
						))
					) : (
						<div className="session-history__row">
							<div>
								<strong>No samples yet</strong>
								<span>Start tracking to collect live eye-contact history.</span>
							</div>
							<div className="session-history__stats">
								<strong>—</strong>
							</div>
						</div>
					)}
				</div>
			</div>

			{/* Error Message */}
			{error && (
				<div className="webcam-error-box" aria-live="polite">
					<p>{error}</p>
				</div>
			)}

			{/* Controls */}
			<div className="webcam-controls">
				<button
					type="button"
					className="primary-action"
					onClick={startTracking}
					disabled={status === 'requesting' || status === 'running'}
				>
					Start Tracking
				</button>
				<button
					type="button"
					className="secondary-action"
					onClick={stopTracking}
					disabled={status === 'idle'}
				>
					Stop
				</button>
			</div>
		</div>
	)
}

export default WebcamEmotionTracker