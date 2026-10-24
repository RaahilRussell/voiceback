import XCTest
@testable import VoiceBack

final class VoiceBackTests: XCTestCase {
    func testTranscriptionRequiresApproval() {
        let transcription = Transcription(original: "hello", corrected: "hello", confidence: 0.4, requiresApproval: true)
        XCTAssertTrue(transcription.requiresApproval)
    }
}

