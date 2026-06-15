#!/usr/bin/env python3
"""Tests for transcript utilities."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from transcript_utils import (
    parse_srt,
    parse_srt_timestamp,
    format_timestamp_display,
    format_timestamp_filename,
    parse_frame_timestamp,
    get_transcript_at_timestamp,
    find_visual_cues,
    find_topic_changes,
    get_key_timestamps,
    SRTBlock,
)


# Sample SRT content for testing
SAMPLE_SRT = """1
00:00:01,000 --> 00:00:05,000
Hello and welcome to this video.

2
00:00:05,500 --> 00:00:10,000
Today I'll show you how to build an app.

3
00:00:10,500 --> 00:00:15,000
You can see here we have the main interface.

4
00:00:20,000 --> 00:00:25,000
Let me show you the configuration.

5
00:01:00,000 --> 00:01:05,000
Check this out, it's really cool.
"""


class TestParseSrtTimestamp:
    def test_basic_timestamp(self):
        assert parse_srt_timestamp("00:00:30,000") == 30.0

    def test_with_milliseconds(self):
        assert parse_srt_timestamp("00:01:30,500") == 90.5

    def test_hours(self):
        assert parse_srt_timestamp("01:30:00,000") == 5400.0

    def test_period_separator(self):
        assert parse_srt_timestamp("00:00:30.500") == 30.5


class TestFormatTimestampDisplay:
    def test_basic(self):
        assert format_timestamp_display(90) == "01:30"

    def test_zero(self):
        assert format_timestamp_display(0) == "00:00"

    def test_hour_plus(self):
        assert format_timestamp_display(3661) == "61:01"


class TestFormatTimestampFilename:
    def test_minutes_seconds(self):
        assert format_timestamp_filename(90) == "01m30s"

    def test_with_hours(self):
        assert format_timestamp_filename(3661) == "01h01m01s"

    def test_zero(self):
        assert format_timestamp_filename(0) == "00m00s"


class TestParseFrameTimestamp:
    def test_basic_mmss(self):
        assert parse_frame_timestamp("frame_0001_01m30s.jpg") == 90

    def test_with_hours(self):
        assert parse_frame_timestamp("frame_0001_01h01m01s.jpg") == 3661

    def test_cued_frame(self):
        assert parse_frame_timestamp("frame_cued_05m00s.jpg") == 300

    def test_no_match(self):
        assert parse_frame_timestamp("invalid.jpg") == 0


class TestParseSrt:
    def test_parse_blocks(self):
        blocks = parse_srt(SAMPLE_SRT)
        assert len(blocks) == 5

    def test_first_block(self):
        blocks = parse_srt(SAMPLE_SRT)
        assert blocks[0].index == 1
        assert blocks[0].start_seconds == 1.0
        assert blocks[0].end_seconds == 5.0
        assert "Hello" in blocks[0].text

    def test_timestamps(self):
        blocks = parse_srt(SAMPLE_SRT)
        assert blocks[2].start_seconds == 10.5
        assert blocks[4].start_seconds == 60.0


class TestGetTranscriptAtTimestamp:
    def test_exact_match(self):
        blocks = parse_srt(SAMPLE_SRT)
        text = get_transcript_at_timestamp(blocks, 12, window=5)
        assert "interface" in text

    def test_window_includes_adjacent(self):
        blocks = parse_srt(SAMPLE_SRT)
        text = get_transcript_at_timestamp(blocks, 7, window=5)
        # Should include both block 1 and 2
        assert "welcome" in text or "build" in text


class TestFindVisualCues:
    def test_finds_cues(self):
        blocks = parse_srt(SAMPLE_SRT)
        cues = find_visual_cues(blocks)
        # Should find "you can see", "let me show", "check this out"
        assert len(cues) >= 3

    def test_cue_types(self):
        blocks = parse_srt(SAMPLE_SRT)
        cues = find_visual_cues(blocks)
        types = {c['type'] for c in cues}
        assert 'visual reference' in types or 'demonstration' in types


class TestFindTopicChanges:
    def test_finds_gaps(self):
        blocks = parse_srt(SAMPLE_SRT)
        changes = find_topic_changes(blocks, min_gap=3.0)
        # Should find gaps between blocks 3-4 and 4-5
        assert len(changes) >= 2

    def test_timestamps_correct(self):
        blocks = parse_srt(SAMPLE_SRT)
        changes = find_topic_changes(blocks, min_gap=3.0)
        # Block 4 starts at 20s (gap after block 3 ends at 15s)
        assert 20 in changes


class TestGetKeyTimestamps:
    def test_returns_list(self):
        timestamps = get_key_timestamps(SAMPLE_SRT)
        assert isinstance(timestamps, list)

    def test_respects_max_frames(self):
        timestamps = get_key_timestamps(SAMPLE_SRT, max_frames=2)
        assert len(timestamps) <= 2

    def test_empty_srt(self):
        timestamps = get_key_timestamps("")
        assert timestamps == []

    def test_sorted_by_timestamp(self):
        timestamps = get_key_timestamps(SAMPLE_SRT)
        if len(timestamps) > 1:
            ts_values = [t['timestamp_seconds'] for t in timestamps]
            assert ts_values == sorted(ts_values)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
