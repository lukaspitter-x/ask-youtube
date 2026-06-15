#!/usr/bin/env python3
"""Tests for configuration module."""

import os
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestConfigDefaults:
    def test_browser_default(self):
        # Clear any existing env var
        env_backup = os.environ.pop("YTF_BROWSER", None)
        try:
            # Re-import to get fresh defaults
            import importlib
            import config
            importlib.reload(config)
            assert config.BROWSER == "chrome"
        finally:
            if env_backup:
                os.environ["YTF_BROWSER"] = env_backup

    def test_max_frames_default(self):
        import config
        assert config.MAX_FRAMES_FAST == 30
        assert config.MAX_FRAMES_DEEP == 100

    def test_comments_defaults(self):
        import config
        assert config.MAX_COMMENTS == 20
        assert config.COMMENTS_FETCH_LIMIT == 100


class TestConfigEnvOverride:
    def test_browser_env_override(self):
        os.environ["YTF_BROWSER"] = "firefox"
        try:
            import importlib
            import config
            importlib.reload(config)
            assert config.BROWSER == "firefox"
        finally:
            os.environ.pop("YTF_BROWSER", None)

    def test_max_frames_env_override(self):
        os.environ["YTF_MAX_FRAMES_FAST"] = "50"
        try:
            import importlib
            import config
            importlib.reload(config)
            assert config.MAX_FRAMES_FAST == 50
        finally:
            os.environ.pop("YTF_MAX_FRAMES_FAST", None)


class TestYtdlpPaths:
    def test_returns_list(self):
        import config
        paths = config.get_ytdlp_search_paths()
        assert isinstance(paths, list)

    def test_paths_are_path_objects(self):
        import config
        paths = config.get_ytdlp_search_paths()
        for p in paths:
            assert isinstance(p, Path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
