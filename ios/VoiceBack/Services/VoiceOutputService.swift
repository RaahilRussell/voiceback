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
