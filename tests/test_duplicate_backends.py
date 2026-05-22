import pytest

from duplicate.backends.hash_backend import HashBackend
from duplicate.backends.sequence_matcher_backend import SequenceMatcherBackend
from duplicate.backends.metadata_backend import MetadataBackend
from duplicate.backends.hybrid_duplicate_detector import HybridDuplicateDetector


def make_record(id, title, content, **meta):
    rec = {"id": id, "title": title, "content": content}
    rec.update(meta)
    return rec


def test_hash_backend_exact_match():
    hb = HashBackend()
    a = make_record("1", "Hello World", "This is content")
    b = make_record("2", "Hello World", "This is content")
    matches = hb.find_matches(a, [b])
    assert len(matches) == 1
    assert matches[0].similarity == 1.0


def test_sequence_matcher_typo_similarity():
    sm = SequenceMatcherBackend()
    a = make_record("1", "Quick brown fox", "jumps over the lazy dog")
    b = make_record("2", "Quick brown fx", "jumps over the lazy dog")
    matches = sm.find_matches(a, [b], fields=('title',), threshold=0.7)
    assert len(matches) == 1
    assert matches[0].type.name == "SIMILAR"
    assert matches[0].similarity > 0.7


def test_metadata_backend_match():
    mb = MetadataBackend()
    a = make_record("1", "T", "C", dedup_key="dk1", source="s1")
    b = make_record("2", "T2", "C2", dedup_key="dk1", source="s2")
    matches = mb.find_matches(a, [b])
    assert len(matches) == 1
    assert matches[0].metadata['matched_key'] == 'dedup_key'


def test_hybrid_detector_threshold_tuning():
    existing = [
        make_record("1", "Alpha Beta", "Some content"),
        make_record("2", "Gamma Delta", "Other content"),
    ]

    candidate = make_record("c", "Alpha Bta", "Some content")

    detector = HybridDuplicateDetector(similarity_threshold=0.9)
    result = detector.find_duplicates(candidate, existing)
    # threshold high -> should not flag
    assert not result.is_duplicate

    detector_low = HybridDuplicateDetector(similarity_threshold=0.75)
    result2 = detector_low.find_duplicates(candidate, existing)
    assert result2.is_duplicate
    assert result2.recommended_action in (result2.recommended_action.__class__,)


def test_false_positive_resistance():
    existing = [make_record("1", "Completely different", "Unrelated content")]
    candidate = make_record("c", "Near nothing", "Also nothing")
    detector = HybridDuplicateDetector(similarity_threshold=0.6)
    res = detector.find_duplicates(candidate, existing)
    assert not res.is_duplicate
