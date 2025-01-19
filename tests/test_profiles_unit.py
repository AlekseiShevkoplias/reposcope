import pytest
import tempfile
import os
from pathlib import Path
from reposcope.profiles import ProfileManager, ProfileError

def create_temp_file(content):
    """Helper function to create a temporary file with given content."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

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



def test_create_profile(profile_manager):
    """Test creating a new profile."""
    profile = profile_manager.create("test_profile", "include")
    assert profile.name == "test_profile"
    assert profile.mode == "include"
    assert profile.patterns == []

    # Ensure profile is saved and retrievable
    retrieved = profile_manager.get("test_profile")
    assert retrieved.name == "test_profile"
    assert retrieved.mode == "include"


def test_add_remove_patterns(profile_manager):
    """Test adding and removing patterns from a profile."""
    profile = profile_manager.create("test_profile", "exclude")

    # Add patterns
    added = profile_manager.add_patterns("test_profile", ["*.py", "docs/*"])
    assert added == ["*.py", "docs/*"]
    assert profile.patterns == ["*.py", "docs/*"]

    # Remove patterns
    removed = profile_manager.remove_patterns("test_profile", ["docs/*"])
    assert removed == ["docs/*"]
    assert profile.patterns == ["*.py"]


def test_import_patterns(profile_manager):
    """Test importing patterns from a file."""
    profile = profile_manager.create("test_profile", "include")

    temp_file = create_temp_file("*.md\nlogs/*\n")
    added = profile_manager.import_patterns("test_profile", temp_file)

    assert added == ["*.md", "logs/*"]
    assert profile.patterns == ["*.md", "logs/*"]

    os.unlink(temp_file)


def test_export_patterns(profile_manager):
    """Test exporting patterns from a profile."""
    profile = profile_manager.create("test_profile", "exclude")
    profile_manager.add_patterns("test_profile", ["*.log", "cache/*"])

    exported = profile_manager.export_patterns("test_profile")
    assert "# Profile: test_profile (exclude mode)" in exported
    assert "*.log" in exported
    assert "cache/*" in exported


def test_delete_profile(profile_manager):
    """Test deleting a profile."""
    profile_manager.create("test_profile", "include")

    profile_manager.delete("test_profile")

    with pytest.raises(ProfileError, match="Profile 'test_profile' not found"):
        profile_manager.get("test_profile")


def test_list_profiles(profile_manager):
    """Test listing all profiles."""
    profile_manager.create("profile1", "include")
    profile_manager.create("profile2", "exclude")

    profiles = profile_manager.get_profiles()
    assert len(profiles) == 2
    assert profiles[0].name == "profile1"
    assert profiles[1].name == "profile2"
