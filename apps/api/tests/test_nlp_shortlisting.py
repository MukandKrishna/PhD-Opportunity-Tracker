from app.services.nlp import classify_domain_tags, is_target_opportunity


def test_classifies_target_phrases_across_title_and_description():
    tags = classify_domain_tags(
        "PhD in Retrieval-Augmented Generation for Multi-Agent Systems",
        "The project combines knowledge graphs, large language models, and data science.",
    )

    assert "RAG" in tags
    assert "Multi-Agent" in tags
    assert "Agents" in tags
    assert "Knowledge Graphs" in tags
    assert "AI" in tags
    assert "Data Science" in tags


def test_classifies_computer_vision_and_deep_learning():
    tags = classify_domain_tags(
        "Computer vision for medical image segmentation",
        "Deep neural networks will be used for image analysis.",
    )

    assert "Computer Vision" in tags
    assert "DL" in tags


def test_non_target_text_is_not_shortlisted():
    assert not is_target_opportunity("PhD in medieval literature", "Archive-based historical study.")
