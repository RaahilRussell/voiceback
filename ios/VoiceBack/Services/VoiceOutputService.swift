import AVFoundation
import Foundation

struct SpeechRequest: Encodable {
    let userID: String
    let text: String
    let approved: Bool
    let voiceID: String?

    enum CodingKeys: String, CodingKey {
        case userID = "user_id"
        case text, approved
        case voiceID = "voice_id"
    }
}

struct SpeechResponse: Decodable {
    let audioBase64: String
    let contentType: String

    enum CodingKeys: String, CodingKey {
        case audioBase64 = "audio_base64"
        case contentType = "content_type"
    }
}

final class VoiceOutputService: NSObject, AVAudioPlayerDelegate, @unchecked Sendable {
    private var player: AVAudioPlayer?

    func speak(text: String, baseURL: URL, userID: String = "local-user", voiceID: String? = nil) async throws {
        var request = URLRequest(url: baseURL.appendingPathComponent("v1/speech"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            SpeechRequest(userID: userID, text: text, approved: true, voiceID: voiceID)
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"]
                ?? "speech synthesis failed"
            throw NSError(domain: "VoiceBack.Speech", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: detail])
        }
        let result = try JSONDecoder().decode(SpeechResponse.self, from: data)
        guard let audio = Data(base64Encoded: result.audioBase64) else {
            throw NSError(domain: "VoiceBack.Speech", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "speech provider returned invalid audio"])
        }
        try await MainActor.run {
            self.player = try AVAudioPlayer(data: audio)
            self.player?.prepareToPlay()
            self.player?.play()
        }
    }
}

struct VoiceCloneResponse: Decodable {
    let voiceID: String
    let status: String
    let ready: Bool

    enum CodingKeys: String, CodingKey {
        case voiceID = "voice_id"
        case status, ready
    }
}

/// The only microphone path: explicit, consent-gated personal voice enrollment.
@MainActor
final class VoiceEnrollmentService {
    private var recorder: AVAudioRecorder?

    func recordSample(seconds: UInt64 = 8) async throws -> URL {
        let allowed = await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
        guard allowed else {
            throw NSError(domain: "VoiceBack.VoiceEnrollment", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "Microphone access is required only for voice enrollment"])
        }
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement)
        try session.setActive(true)
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("voiceback-enrollment-\(UUID().uuidString).wav")
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 44_100,
            AVNumberOfChannelsKey: 1, AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false,
        ]
        recorder = try AVAudioRecorder(url: url, settings: settings)
        recorder?.record()
        try await Task.sleep(for: .seconds(seconds))
        recorder?.stop()
        recorder = nil
        try? session.setActive(false, options: .notifyOthersOnDeactivation)
        return url
    }

    func upload(sampleURL: URL, baseURL: URL, userID: String = "local-user") async throws -> VoiceCloneResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("v1/voices/clone"))
        request.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        let audio = try Data(contentsOf: sampleURL)
        var body = Data()
        func field(_ name: String, _ value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        field("user_id", userID); field("name", "VoiceBack personal voice")
        field("language", "en"); field("consent", "true")
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"clip\"; filename=\"voice-sample.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audio)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        let (data, response) = try await URLSession.shared.upload(for: request, from: body)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONDecoder().decode([String: String].self, from: data))?["detail"] ?? "voice enrollment failed"
            throw NSError(domain: "VoiceBack.VoiceEnrollment", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: detail])
        }
        return try JSONDecoder().decode(VoiceCloneResponse.self, from: data)
    }
}
