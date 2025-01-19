import pytest
import tempfile
from pathlib import Path
from reposcope.core import RepoScope
from reposcope.profiles import ProfileManager

@pytest.fixture
def temp_repo():
    """Create a temporary repository with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)

        # Create directory structure
        (repo_dir / "src").mkdir()
        (repo_dir / "docs").mkdir()
        (repo_dir / "build").mkdir()

        # Create test files
        (repo_dir / "src" / "main.py").write_text("print('main')")
        (repo_dir / "src" / "utils.py").write_text("print('utils')")
        (repo_dir / "docs" / "README.md").write_text("# Documentation")
        (repo_dir / "build" / "output.log").write_text("build output")

        yield repo_dir

@pytest.fixture
def profile_manager(monkeypatch):
    """Fixture for a clean ProfileManager with isolated config directory."""
    temp_dir = tempfile.TemporaryDirectory()

    def mock_ensure_config_dir(self):
        self.config_dir = Path(temp_dir.name)
        self.profiles_file = self.config_dir / "profiles.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.profiles_file.exists():
            self.profiles_file.write_text("{}")

    # Patch the `_ensure_config_dir` method
    monkeypatch.setattr(ProfileManager, "_ensure_config_dir", mock_ensure_config_dir)

    # Instantiate the ProfileManager
    manager = ProfileManager()
    yield manager

    # Cleanup temporary directory
    temp_dir.cleanup()



def test_profile_integration_include(temp_repo, profile_manager):
    """Test using an include profile with RepoScope."""
    profile = profile_manager.create("include_profile", "include")
    profile_manager.add_patterns("include_profile", ["src/*.py", "docs/*.md"])

    scope = RepoScope(temp_repo)
    scope.use_include_patterns(profile.patterns)

    collected_files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}

    assert "src/main.py" in collected_files
    assert "src/utils.py" in collected_files
    assert "docs/README.md" in collected_files

    # Files not in include patterns should be excluded
    assert "build/output.log" not in collected_files

def test_profile_integration_exclude(temp_repo, profile_manager):
    """Test using an exclude profile with RepoScope."""
    profile = profile_manager.create("exclude_profile", "exclude")
    profile_manager.add_patterns("exclude_profile", ["build/*", "*.log"])

    scope = RepoScope(temp_repo)
    scope.use_ignore_patterns(profile.patterns)

    collected_files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}

    # Excluded files should not be present
    assert "build/output.log" not in collected_files

    # Included files
    assert "src/main.py" in collected_files
    assert "src/utils.py" in collected_files
    assert "docs/README.md" in collected_files

def test_profile_integration_gitignore_and_profile(temp_repo, profile_manager):
    """Test combining .gitignore and an exclude profile."""
    gitignore_file = temp_repo / ".gitignore"
    gitignore_file.write_text("*.log\n")

    profile = profile_manager.create("exclude_profile", "exclude")
    profile_manager.add_patterns("exclude_profile", ["docs/*"])

    scope = RepoScope(temp_repo)
    scope.use_gitignore()
    scope.use_ignore_patterns(profile.patterns)

    collected_files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}

    # Excluded by gitignore and profile
    assert "build/output.log" not in collected_files
    assert "docs/README.md" not in collected_files

    # Included files
    assert "src/main.py" in collected_files
    assert "src/utils.py" in collected_files
