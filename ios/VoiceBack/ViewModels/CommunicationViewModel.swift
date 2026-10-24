import AVFoundation
import Foundation

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
        case result(TranscriptionResponse)
        case failed(String)
    }

    @Published private(set) var state: State = .ready
    @Published private(set) var statusMessage = "Ready for silent speech"

    private let capture = CameraCaptureService()
    private let backendURL: URL

    /// Public Modal HTTPS endpoint so a physical iPhone can reach the backend
    /// even when campus Wi-Fi blocks phone-to-Mac LAN traffic.
    init(backendURL: URL = URL(string: "https://raahil-32424--voiceback-inference-web.us-east.modal.run")!) {
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

    private func upload(_ fileURL: URL) async {
        state = .uploading
        statusMessage = "Uploading to the visual speech model…"
        do {
            let response = try await TranscriptionAPIClient(baseURL: backendURL).transcribe(fileURL: fileURL)
            state = .result(response)
            statusMessage = response.text
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func reset() {
        state = .ready
        statusMessage = "Ready — tap record and silently mouth a sentence"
    }
}
