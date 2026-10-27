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
    let developerDiagnostics: DeveloperDiagnostics?

    enum CodingKeys: String, CodingKey {
        case text, candidates, frames, device, model
        case audioUsed = "audio_used"
        case inferenceSeconds = "inference_seconds"
        case interpretation
        case developerDiagnostics = "developer_diagnostics"
    }
}

struct DeveloperDiagnostics: Codable, Equatable {
    let enabled: Bool
    let visualCandidates: [DeveloperCandidate]?
    let fusion: DeveloperFusion?
    let languageModelTrace: [DeveloperLMTrace]?
    let gemini: DeveloperGemini?

    enum CodingKeys: String, CodingKey {
        case enabled, fusion, gemini
        case visualCandidates = "visual_candidates"
        case languageModelTrace = "language_model_trace"
    }
}

struct DeveloperCandidate: Codable, Equatable, Identifiable {
    let text: String
    let rawScore: Double?
    let scoreType: String?
    var id: String { text }

    enum CodingKeys: String, CodingKey {
        case text
        case rawScore = "raw_score"
        case scoreType = "score_type"
    }
}

struct DeveloperFusion: Codable, Equatable {
    let modelName: String?
    let weight: Double
    let enabled: Bool
    let scoreFormula: String

    enum CodingKeys: String, CodingKey {
        case weight, enabled
        case modelName = "model_name"
        case scoreFormula = "score_formula"
    }
}

struct DeveloperLMTrace: Codable, Equatable, Identifiable {
    let prefix: String
    let candidateTokenID: Int
    let candidateText: String
    let lmLogProbability: Double
    let lmProbability: Double
    var id: String { "\(prefix)-\(candidateTokenID)-\(candidateText)" }

    enum CodingKeys: String, CodingKey {
        case prefix
        case candidateTokenID = "candidate_token_id"
        case candidateText = "candidate_text"
        case lmLogProbability = "lm_log_probability"
        case lmProbability = "lm_probability"
    }
}

struct DeveloperGemini: Codable, Equatable {
    let available: Bool?
    let invoked: Bool?
    let model: String?
    let reason: String?
    let request: DeveloperGeminiRequest?
    let responseText: String?

    enum CodingKeys: String, CodingKey {
        case available, invoked, model, reason, request
        case responseText = "response_text"
    }
}

struct DeveloperGeminiRequest: Codable, Equatable {
    let prompt: String?
    let temperature: Double?
    let topP: Double?
    let seed: Int?
    let maxOutputTokens: Int?

    enum CodingKeys: String, CodingKey {
        case prompt, temperature, seed
        case topP = "top_p"
        case maxOutputTokens = "max_output_tokens"
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
