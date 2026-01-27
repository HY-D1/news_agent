from app.core.schemas import Topic
from app.pipeline.verify.topic_tagger import tag_topics


def test_tag_topics_tech():
    # Tech: "NVIDIA releases new GPU"
    tags = tag_topics("NVIDIA releases new GPU", None)
    # This might fail if "NVIDIA" or "GPU" aren't in keywords. 
    # I'll check and fix if needed to ensure the test passes as requested.
    assert Topic.TECH in tags

def test_tag_topics_finance():
    # Finance: "earnings report, stock market"
    tags = tag_topics("earnings report, stock market", None)
    assert Topic.FINANCE in tags

def test_tag_topics_health():
    # Health: "FDA approves vaccine"
    tags = tag_topics("FDA approves vaccine", None)
    assert Topic.HEALTH in tags

def test_tag_topics_learning():
    # Learning: "course, university, tutorial"
    tags = tag_topics("course, university, tutorial", None)
    assert Topic.LEARNING in tags

def test_tag_topics_no_keyword():
    # No keyword: returns DAILY
    tags = tag_topics("The weather is nice", "Nothing else here")
    assert tags == {Topic.DAILY}

def test_tag_topics_case_insensitive():
    tags = tag_topics("TECH news", None)
    assert Topic.TECH in tags

def test_tag_topics_word_boundaries():
    # "ai" in "daily" should not match TECH
    tags = tag_topics("Daily update", None)
    assert Topic.TECH not in tags
    assert Topic.DAILY in tags
