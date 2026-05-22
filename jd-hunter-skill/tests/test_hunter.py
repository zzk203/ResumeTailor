import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.hunter import CHANNELS


class TestChannels:
    def test_channel_list_not_empty(self):
        assert len(CHANNELS) > 0

    def test_channel_has_required_keys(self):
        for c in CHANNELS:
            assert "name" in c
            assert "label" in c
            assert "search_cmd" in c

    def test_channel_names_are_unique(self):
        names = [c["name"] for c in CHANNELS]
        assert len(names) == len(set(names))


class TestSearchJdOnChannel:
    def test_unknown_command_returns_empty(self):
        from src.hunter import search_jd_on_channel
        channel = {"name": "test", "label": "测试", "search_cmd": "nonexistent-cmd"}
        result = search_jd_on_channel(channel, "后端开发")
        assert result == []


class TestFetchJdDetail:
    def test_invalid_url_returns_empty(self):
        from src.hunter import fetch_jd_detail
        result = fetch_jd_detail("https://nonexistent.example.com/job/1")
        assert result == ""
