import { useEffect, useRef, useState } from 'react'

import { analyzeWebcamEmotion } from '../services/api'

type EmotionReading = {
	emotion: string
	confidence: number
	source: string
	timestamp: string
}

type TrackerStatus = 'idle' | 'requesting' | 'running' | 'error'

const CAPTURE_INTERVAL_MS = 5000

function formatConfidence(value: number) {
	return `${Math.round(value * 100)}%`
}

export function WebcamEmotionTracker() {
	const videoRef = useRef<HTMLVideoElement | null>(null)
	const canvasRef = useRef<HTMLCanvasElement | null>(null)
	const streamRef = useRef<MediaStream | null>(null)
	const intervalRef = useRef<number | null>(null)
	const [status, setStatus] = useState<TrackerStatus>('idle')
	const [reading, setReading] = useState<EmotionReading | null>(null)
	const [error, setError] = useState<string | null>(null)
	const [lastCaptureAt, setLastCaptureAt] = useState<string | null>(null)

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

		canvas.width = video.videoWidth
		canvas.height = video.videoHeight
		context.drawImage(video, 0, 0, canvas.width, canvas.height)

		try {
			const frame = canvas.toDataURL('image/jpeg', 0.82)
			const response = await analyzeWebcamEmotion({ frame })
			setReading(response.data as EmotionReading)
			setError(null)
			setLastCaptureAt(new Date().toISOString())
		} catch (requestError) {
			const message =
				requestError instanceof Error
					? requestError.message
					: 'Unable to analyze the current webcam frame.'
			setError(message)
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
			await captureAndAnalyze()
			intervalRef.current = window.setInterval(() => {
				void captureAndAnalyze()
			}, CAPTURE_INTERVAL_MS)
		} catch (requestError) {
			releaseStream()
			setStatus('error')
			setError(
				requestError instanceof Error
					? requestError.message
					: 'Unable to access the webcam.',
			)
		}
	}

	const stopTracking = () => {
		releaseStream()
		setStatus('idle')
	}

	useEffect(() => {
		return () => {
			releaseStream()
		}
	}, [])

	return (
		<div className="webcam-panel">
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
					<p>Frames are sampled every 5 seconds and sent to the Flask backend.</p>
				</div>
			</div>

			<canvas ref={canvasRef} className="webcam-canvas" aria-hidden="true" />

			<div className="webcam-meta">
				<div>
					<p className="webcam-label">Latest reading</p>
					<strong>{reading?.emotion ?? 'No emotion yet'}</strong>
				</div>
				<div>
					<p className="webcam-label">Confidence</p>
					<strong>{reading ? formatConfidence(reading.confidence) : '—'}</strong>
				</div>
				<div>
					<p className="webcam-label">Source</p>
					<strong>{reading?.source ?? '—'}</strong>
				</div>
			</div>

			<div className="webcam-controls">
				<button type="button" className="primary-action" onClick={startTracking} disabled={status === 'requesting' || status === 'running'}>
					Start webcam analysis
				</button>
				<button type="button" className="secondary-action" onClick={stopTracking} disabled={status === 'idle'}>
					Stop
				</button>
			</div>

			<div className="webcam-footnote" aria-live="polite">
				{error ? (
					<p className="webcam-error">{error}</p>
				) : lastCaptureAt ? (
					<p>Last frame captured at {new Date(lastCaptureAt).toLocaleTimeString()}.</p>
				) : (
					<p>Allow access to the camera to begin emotion sampling.</p>
				)}
			</div>
		</div>
	)
}

export default WebcamEmotionTracker