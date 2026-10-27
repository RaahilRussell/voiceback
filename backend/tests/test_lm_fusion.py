from inference.lm_scorer import CausalTextLMScorer, combine_scores


def test_zero_fusion_weight_is_visual_baseline() -> None:
    assert combine_scores(-4.25, -100.0, 0.0) == -4.25


def test_nonzero_fusion_weight_changes_candidate_score() -> None:
    assert combine_scores(-4.25, -1.5, 0.2) == -4.55


def test_lm_supported_candidate_can_survive_controlled_pruning() -> None:
    visual = {"visual": -1.0, "language": -1.2}
    lm = {"visual": -5.0, "language": -0.1}
    fused = {key: combine_scores(visual[key], lm[key], 0.5) for key in visual}
    assert max(visual, key=visual.get) == "visual"
    assert max(fused, key=fused.get) == "language"


def test_scorer_is_explicitly_tokenizer_safe() -> None:
    scorer = CausalTextLMScorer(
        token_list=["<blank>", " hello", " world", "<eos>"],
        decode_ids=lambda ids: "".join({0: "", 1: " hello", 2: " world", 3: ""}[item] for item in ids),
        model_name="distilgpt2",
    )
    assert scorer.model_name == "distilgpt2"
    assert scorer.decode_ids([1, 2]) == " hello world"
