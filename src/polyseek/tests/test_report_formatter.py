from polyseek_sentient.report_formatter import AnalysisModel, format_response


def test_format_response_basic():
    payload = {
        "verdict": "YES",
        "confidence_pct": 62.3,
        "summary": "Market leans bullish.",
        "key_drivers": [
            {"text": "Positive polling trend", "source_ids": ["SRC1"]},
            {"text": "High liquidity", "source_ids": ["SRC2"]},
        ],
        "uncertainty_factors": ["Legal risk"],
        "sources": [
            {
                "id": "SRC1",
                "title": "Poll",
                "url": "https://example.com/poll",
                "type": "news",
                "sentiment": "pro",
            },
            {
                "id": "SRC2",
                "title": "Orderbook",
                "url": "https://example.com/orderbook",
                "type": "market",
                "sentiment": "neutral",
            },
        ],
    }
    model, markdown = format_response(payload)
    assert isinstance(model, AnalysisModel)
    assert "Verdict" in markdown
    assert "**YES**" in markdown
