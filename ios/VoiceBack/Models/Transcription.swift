import Foundation

struct Transcription: Codable, Equatable {
    let original: String
    let corrected: String?
    let confidence: Double
    let requiresApproval: Bool
}

/// Response from `POST /v1/transcriptions` — the real visual-only model output.
/// `audioUsed` is always false; the backend rejects any audio-consuming result.
struct TranscriptionResponse: Codable, Equatable {
    let text: String
    let candidates: [String]
    let audioUsed: Bool
    let frames: Int
    let device: String
    let inferenceSeconds: Double
    let model: String
    let interpretation: GeminiInterpretation?

    enum CodingKeys: String, CodingKey {
        case text, candidates, frames, device, model
        case audioUsed = "audio_used"
        case inferenceSeconds = "inference_seconds"
        case interpretation
    }
}

struct GeminiInterpretation: Codable, Equatable {
    let originalText: String
    let correctedText: String
    let candidates: [String]
    let selectedIndex: Int
    let confidence: Double
    let needsClarification: Bool
    let clarificationQuestion: String?
    let wordChecks: [GeminiWordCheck]

    enum CodingKeys: String, CodingKey {
        case candidates, confidence
        case wordChecks = "word_checks"
        case originalText = "original_text"
        case correctedText = "corrected_text"
        case selectedIndex = "selected_index"
        case needsClarification = "needs_clarification"
        case clarificationQuestion = "clarification_question"
    }
}

struct GeminiWordCheck: Codable, Equatable {
    let observedWord: String
    let alternatives: [String]
    let confidence: Double
    let needsClarification: Bool

    enum CodingKeys: String, CodingKey {
        case alternatives, confidence
        case observedWord = "observed_word"
        case needsClarification = "needs_clarification"
    }
}
