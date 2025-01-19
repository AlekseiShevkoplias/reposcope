#!/usr/bin/env python3
import json
from pathlib import Path
import logging
import shutil
import tempfile

logger = logging.getLogger(__name__)

class ProfileError(Exception):
    """Base exception for profile-related errors."""
    pass

class Profile:
    """A profile that stores include/exclude patterns."""
    def __init__(self, name: str, mode: str, patterns: list[str] = None):
        if mode not in ('include', 'exclude'):
            raise ProfileError(f"Invalid mode: {mode}. Must be 'include' or 'exclude'")
        self.name = name
        self.mode = mode
        self.patterns = patterns or []

    def add_patterns(self, patterns: list[str]) -> list[str]:
        """Add new patterns to the profile. Returns list of actually added patterns."""
        new_patterns = [p for p in patterns if p not in self.patterns]
        if new_patterns:
            self.patterns.extend(new_patterns)
        return new_patterns

    def remove_patterns(self, patterns: list[str]) -> list[str]:
        """Remove patterns from the profile. Returns list of actually removed patterns."""
        removed = []
        for pattern in patterns:
            if pattern in self.patterns:
                self.patterns.remove(pattern)
                removed.append(pattern)
        return removed

    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON storage."""
        return {
            "mode": self.mode,
            "patterns": self.patterns
        }

    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'Profile':
        """Create profile from JSON data."""
        return cls(
            name=name,
            mode=data["mode"],
            patterns=data.get("patterns", [])
        )

    def summary(self) -> str:
        """Get a short summary of the profile."""
        return f"{self.name} ({self.mode}, {len(self.patterns)} patterns)"

    def details(self) -> str:
        """Get detailed information about the profile."""
        header = f"{self.name} ({self.mode} mode)"
        if not self.patterns:
            return f"{header}\n  No patterns defined"
        patterns = '\n  '.join(self.patterns)
        return f"{header}\n  {patterns}"


class ProfileManager:
    """Manages profiles stored in JSON format and keeps them in memory."""
    def __init__(self, config_dir=None):
        # Use a temporary directory for config during tests
        if config_dir is None:
            config_dir = Path.home() / ".config" / "reposcope"
        
        self.config_dir = config_dir
        self.profiles_file = self.config_dir / "profiles.json"
        self._ensure_config_dir()
        self._profiles = {}
        self._load_profiles()

    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.profiles_file.exists():
            self._save_profiles({})

    def _load_profiles(self):
        try:
            # Start with an empty dict each time
            self._profiles = {}
            
            if self.profiles_file.exists():
                data = json.loads(self.profiles_file.read_text())
                self._profiles = {
                    name: Profile.from_dict(name, profile_data) 
                    for name, profile_data in data.items()
                }
        except json.JSONDecodeError as e:
            raise ProfileError(f"Invalid profiles file format: {e}")
        except Exception as e:
            raise ProfileError(f"Failed to load profiles: {e}")

    def _save_profiles(self, data=None):
        try:
            if data is None:
                data = {name: profile.to_dict() for name, profile in self._profiles.items()}
            self.profiles_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            raise ProfileError(f"Failed to save profiles: {e}")

    def create(self, name, mode):
        """Create a new profile."""
        # First, ensure a clean slate by reloading
        self._load_profiles()
        
        if name in self._profiles:
            raise ProfileError(f"Profile '{name}' already exists")
        profile = Profile(name=name, mode=mode)
        self._profiles[name] = profile
        self._save_profiles()
        return profile

    def get(self, name):
        """Retrieve a profile by name."""
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found")
        return self._profiles[name]

    def delete(self, name):
        """Delete a profile by name."""
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found")
        del self._profiles[name]
        self._save_profiles()

    def get_profiles(self):
        """List all profiles."""
        return list(self._profiles.values())

    def add_patterns(self, name, patterns):
        """Add patterns to a profile."""
        profile = self.get(name)
        added = profile.add_patterns(patterns)
        if added:
            self._save_profiles()
        return added

    def remove_patterns(self, name, patterns):
        """Remove patterns from a profile."""
        profile = self.get(name)
        removed = profile.remove_patterns(patterns)
        if removed:
            self._save_profiles()
        return removed

    def export_patterns(self, name):
        """Export patterns from a profile."""
        profile = self.get(name)
        header = f"# Profile: {profile.name} ({profile.mode} mode)\n"
        
        return header + "\n".join(profile.patterns)

    def import_patterns(self, name, file_path):
        """Import patterns from a file."""
        path = Path(file_path)
        if not path.exists():
            raise ProfileError(f"File not found: {file_path}")
        
        with open(path) as f:
            # Filter out comments and blank lines
            patterns = [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
        
        return self.add_patterns(name, patterns)