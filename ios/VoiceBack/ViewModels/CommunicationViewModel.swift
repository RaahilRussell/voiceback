import AVFoundation
import Foundation

final class StreamingTranscriptionClient: @unchecked Sendable {
    private let task: URLSessionWebSocketTask
    private let session: URLSession
    private var receiveTask: Task<Void, Never>?
    var onEvent: ((Data) -> Void)?

    init(baseURL: URL) {
        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        components.scheme = components.scheme == "https" ? "wss" : "ws"
        components.path = "/v1/sessions/\(UUID().uuidString)/stream"
        session = URLSession(configuration: .default)
        task = session.webSocketTask(with: components.url!)
    }

    func start(fps: Int = 25) {
        task.resume()
        sendJSON(["type": "start", "fps": fps, "format": "jpeg", "audio": false, "prefix_preview": true])
        receiveTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                do {
                    let message = try await task.receive()
                    switch message {
                    case .data(let data): onEvent?(data)
                    case .string(let text): onEvent?(Data(text.utf8))
                    @unknown default: break
                    }
                } catch { return }
            }
        }
    }

    func send(frame: Data) {
        Task { try? await task.send(.data(frame)) }
    }

    func finish() {
        sendJSON(["type": "end"])
    }

    func cancel() {
        sendJSON(["type": "cancel"])
        receiveTask?.cancel()
        task.cancel(with: .goingAway, reason: nil)
        session.invalidateAndCancel()
    }

    private func sendJSON(_ value: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: value),
              let text = String(data: data, encoding: .utf8) else { return }
        Task { try? await task.send(.string(text)) }
    }
}

/// Minimal multipart client for `POST /v1/transcriptions`.
struct TranscriptionAPIClient {
    let baseURL: URL

    func transcribe(fileURL: URL) async throws -> TranscriptionResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("v1/transcriptions"))
        request.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let videoData = try Data(contentsOf: fileURL)
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"clip.mov\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: video/quicktime\r\n\r\n".data(using: .utf8)!)
        body.append(videoData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        let (data, response) = try await URLSession.shared.upload(for: request, from: body)
        guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"]
                ?? "server returned status \(http.statusCode)"
            throw NSError(domain: "VoiceBack.API", code: http.statusCode,
                          userInfo: [NSLocalizedDescriptionKey: detail])
        }
        return try JSONDecoder().decode(TranscriptionResponse.self, from: data)
    }
}

@MainActor
final class CommunicationViewModel: ObservableObject {
    enum State: Equatable {
        case ready
        case needsPermission
        case recording
        case uploading
        case streaming
        case enrolling
        case result(TranscriptionResponse)
        case approved(TranscriptionResponse)
        case failed(String)
    }

    @Published private(set) var state: State = .ready
    @Published private(set) var statusMessage = "Ready for silent speech"

    private let capture = CameraCaptureService()
    private let voiceOutput = VoiceOutputService()
    private let voiceEnrollment = VoiceEnrollmentService()
    private let backendURL: URL
    private var streamingClient: StreamingTranscriptionClient?
    private var streamingResponse: TranscriptionResponse?
    private(set) var voiceID: String?

    /// Local laptop backend. Update the LAN address if the laptop's Wi-Fi IP changes.
    init(backendURL: URL = URL(string: "http://192.168.1.196:8000")!) {
        self.backendURL = backendURL
    }

    var session: AVCaptureSession { capture.session }

    func prepare() async {
        guard await capture.requestAccess() else {
            state = .needsPermission
            statusMessage = "Camera access is required. VoiceBack never uses the microphone."
            return
        }
        do {
            try capture.configure()
            capture.startRunning()
            state = .ready
            statusMessage = "Ready — tap record and silently mouth a sentence"
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func record() async {
        state = .recording
        statusMessage = "Recording… silently mouth your sentence"
        do {
            let url = try await capture.recordClip()
            await upload(url)
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func stopRecording() {
        capture.stopRecording()
    }

    func startLiveStream() {
        state = .streaming
        statusMessage = "Live frames connected — final decode is pending"
        let client = StreamingTranscriptionClient(baseURL: backendURL)
        streamingClient = client
        client.onEvent = { [weak self] data in
            Task { @MainActor [weak self] in
                self?.handleStreamEvent(data)
            }
        }
        client.start()
        capture.startLiveFrameStreaming { [weak client] frame in
            client?.send(frame: frame)
        }
    }

    func stopLiveStream() {
        capture.stopLiveFrameStreaming()
        streamingClient?.finish()
        statusMessage = "Finalizing visual transcription…"
    }

    func approve(_ response: TranscriptionResponse) {
        guard response.interpretation != nil else { return }
        state = .approved(response)
        statusMessage = "Approved. Speech output is ready once voice synthesis is connected."
    }

    func speakApproved(_ response: TranscriptionResponse) async {
        guard let text = response.interpretation?.correctedText else { return }
        statusMessage = "Generating approved speech…"
        do {
            try await voiceOutput.speak(text: text, baseURL: backendURL, voiceID: voiceID)
            statusMessage = "Speaking approved sentence"
        } catch {
            statusMessage = error.localizedDescription
        }
    }

    func enrollVoice() async {
        state = .enrolling
        statusMessage = "Voice enrollment: speak naturally for 8 seconds"
        do {
            let sample = try await voiceEnrollment.recordSample()
            let enrolled = try await voiceEnrollment.upload(sampleURL: sample, baseURL: backendURL)
            voiceID = enrolled.voiceID
            state = .ready
            statusMessage = enrolled.ready
                ? "Personal voice ready — silent speech still uses no microphone"
                : "Voice submitted — Cartesia is finishing enrollment"
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    private func upload(_ fileURL: URL) async {
        state = .uploading
        statusMessage = "Uploading to the visual speech model…"
        do {
            let response = try await TranscriptionAPIClient(baseURL: backendURL).transcribe(fileURL: fileURL)
            state = .result(response)
            statusMessage = response.interpretation == nil
                ? "Raw transcript ready — Gemini review is temporarily unavailable"
                : "Gemini correction ready — review and approve before speech"
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func reset() {
        streamingClient?.cancel()
        streamingClient = nil
        capture.stopLiveFrameStreaming()
        state = .ready
        statusMessage = "Ready — tap record and silently mouth a sentence"
    }

    private func handleStreamEvent(_ data: Data) {
        guard let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let event = object["event"] as? String else { return }
        switch event {
        case "capture_quality":
            let count = object["frame_count"] as? Int ?? 0
            statusMessage = "Live camera stream — \(count) frames"
        case "partial_hypothesis":
            let text = object["text"] as? String ?? ""
            statusMessage = text.isEmpty
                ? "Frames received — final visual decode running"
                : "Provisional: \(text)"
        case "final_candidates":
            guard let text = object["text"] as? String else { return }
            let response = TranscriptionResponse(
                text: text,
                candidates: object["candidates"] as? [String] ?? [text],
                audioUsed: object["audio_used"] as? Bool ?? false,
                frames: object["frames"] as? Int ?? 0,
                device: object["device"] as? String ?? "unknown",
                inferenceSeconds: object["inference_seconds"] as? Double ?? 0,
                model: "mpc001/auto-avsr",
                interpretation: nil
            )
            streamingClient = nil
            streamingResponse = response
            state = .result(response)
            statusMessage = "Live transcript ready — Gemini review is still required"
        case "context_result":
            guard let raw = streamingResponse,
                  let interpretationObject = object["interpretation"] as? [String: Any],
                  let interpretationData = try? JSONSerialization.data(withJSONObject: interpretationObject),
                  let interpretation = try? JSONDecoder().decode(GeminiInterpretation.self, from: interpretationData)
            else { return }
            let response = TranscriptionResponse(
                text: raw.text,
                candidates: raw.candidates,
                audioUsed: raw.audioUsed,
                frames: raw.frames,
                device: raw.device,
                inferenceSeconds: raw.inferenceSeconds,
                model: raw.model,
                interpretation: interpretation
            )
            streamingResponse = response
            state = .result(response)
            statusMessage = "Gemini context review ready — review before speech"
        case "error":
            state = .failed(object["message"] as? String ?? "Live stream failed")
            streamingClient = nil
        default:
            break
        }
    }
}
