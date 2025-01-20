import pytest
import os
import tempfile
from pathlib import Path
from reposcope.core import RepoScope

@pytest.fixture
def temp_repo():
    """Create a temporary repository with a comprehensive test file structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Create main directories
        (repo_dir / "src").mkdir()
        (repo_dir / "src/module1").mkdir(parents=True)
        (repo_dir / "src/module2").mkdir()
        (repo_dir / "tests").mkdir()
        (repo_dir / "tests/unit").mkdir(parents=True)
        (repo_dir / "tests/integration").mkdir()
        (repo_dir / "docs").mkdir()
        (repo_dir / "build").mkdir()
        (repo_dir / ".git").mkdir()
        (repo_dir / "src/__pycache__").mkdir()  # Create __pycache__ directory
        
        # Create test files
        # Python files
        (repo_dir / "src/main.py").write_text("main")
        (repo_dir / "src/module1/core.py").write_text("core")
        (repo_dir / "src/module2/utils.py").write_text("utils")
        
        # Test files with numbered variations
        (repo_dir / "tests/test1.py").write_text("test1")
        (repo_dir / "tests/test2.py").write_text("test2")
        (repo_dir / "tests/test3.py").write_text("test3")
        (repo_dir / "tests/unit/test_core.py").write_text("test_core")
        (repo_dir / "tests/integration/test_api.py").write_text("test_api")
        
        # Log files
        (repo_dir / "build/build1.log").write_text("build1")
        (repo_dir / "build/build2.log").write_text("build2")
        (repo_dir / "error.log").write_text("error")
        
        # Documentation
        (repo_dir / "docs/README.md").write_text("readme")
        (repo_dir / "docs/api.md").write_text("api")
        (repo_dir / "docs/temp1.txt").write_text("temp1")
        (repo_dir / "docs/temp2.txt").write_text("temp2")
        
        # Git and cache files
        (repo_dir / ".git/config").write_text("git config")
        (repo_dir / "src/__pycache__/main.cpython-39.pyc").write_text("cache")
        
        yield repo_dir

class TestExcludeMode:
    """Test exclude mode pattern matching."""
    
    def test_basic_exclude(self, temp_repo):
        """Test basic file exclusion with * pattern."""
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["*.log"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should exclude
        assert "build/build1.log" not in files
        assert "build/build2.log" not in files
        assert "error.log" not in files
        
        # Should include
        assert "src/main.py" in files
        assert "docs/README.md" in files

    def test_negation_exclude(self, temp_repo):
        """Test negation patterns in exclude mode."""
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["*.log", "!error.log"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should exclude
        assert "build/build1.log" not in files
        assert "build/build2.log" not in files
        
        # Should include (negated)
        assert "error.log" in files

    def test_question_mark_glob(self, temp_repo):
        """Test ? glob pattern in exclude mode."""
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["test?.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should exclude
        assert "tests/test1.py" not in files
        assert "tests/test2.py" not in files
        assert "tests/test3.py" not in files
        
        # Should include
        assert "tests/unit/test_core.py" in files
        assert "tests/integration/test_api.py" in files

    def test_directory_patterns(self, temp_repo):
        """Test directory-specific patterns in exclude mode."""
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["build/"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should exclude entire directory
        assert not any(f.startswith("build/") for f in files)
        
        # Should include
        assert "src/main.py" in files
        assert "error.log" in files

    def test_combine_patterns(self, temp_repo):
        """Test combining multiple patterns in exclude mode."""
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns([
            "*.log",
            "!error.log",
            "test?.py",
            "!test1.py"
        ])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Check complex pattern interactions
        assert "error.log" in files  # Negated from *.log
        assert "build/build1.log" not in files  # Excluded by *.log
        assert "tests/test1.py" in files  # Negated from test?.py
        assert "tests/test2.py" not in files  # Excluded by test?.py

    def test_gitignore_file(self, temp_repo):
        """Test patterns from .gitignore file."""
        gitignore = temp_repo / ".gitignore"
        gitignore.write_text("\n".join([
            "*.log",
            "!error.log",
            "build/",
            "__pycache__/",
            "test?.py"
        ]))
        
        scope = RepoScope(temp_repo)
        scope.use_gitignore()
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Verify .gitignore patterns
        assert "error.log" in files
        assert "build/build1.log" not in files
        assert not any(f.startswith("__pycache__/") for f in files)
        assert "tests/test1.py" not in files

    def test_exclude_file(self, temp_repo):
        """Test patterns from exclude file."""
        exclude_file = temp_repo / "exclude.txt"
        exclude_file.write_text("\n".join([
            "# Exclude logs except error.log",
            "*.log",
            "!error.log",
            "",
            "# Exclude temp files",
            "temp?.txt"
        ]))
        
        scope = RepoScope(temp_repo)
        scope.use_ignore_file(str(exclude_file))
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        assert "error.log" in files
        assert "build/build1.log" not in files
        assert "docs/temp1.txt" not in files
        assert "docs/temp2.txt" not in files

class TestIncludeMode:
    """Test include mode pattern matching."""
    
    def test_basic_include(self, temp_repo):
        """Test basic file inclusion with * pattern."""
        scope = RepoScope(temp_repo)
        scope.use_include_patterns(["*.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should include
        assert "src/main.py" in files
        assert "tests/test1.py" in files
        
        # Should exclude
        assert "docs/README.md" not in files
        assert "error.log" not in files

    def test_negation_include(self, temp_repo):
        """Test negation patterns in include mode."""
        scope = RepoScope(temp_repo)
        scope.use_include_patterns(["*.py", "!test?.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should include
        assert "src/main.py" in files
        assert "tests/unit/test_core.py" in files
        
        # Should exclude (negated)
        assert "tests/test1.py" not in files
        assert "tests/test2.py" not in files

    def test_directory_include(self, temp_repo):
        """Test directory-specific patterns in include mode."""
        scope = RepoScope(temp_repo)
        scope.use_include_patterns(["src/", "!src/module1/"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        # Should include
        assert "src/main.py" in files
        assert "src/module2/utils.py" in files
        
        # Should exclude
        assert "src/module1/core.py" not in files

    def test_include_file(self, temp_repo):
        """Test patterns from include file."""
        include_file = temp_repo / "include.txt"
        include_file.write_text("\n".join([
            "# Include all Python files",
            "*.py",
            "",
            "# But exclude test files",
            "!test?.py",
            "",
            "# Include docs",
            "docs/*.md"
        ]))
        
        scope = RepoScope(temp_repo)
        scope.use_include_file(str(include_file))
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        
        assert "src/main.py" in files
        assert "docs/README.md" in files
        assert "tests/test1.py" not in files
        assert "docs/temp1.txt" not in files

class TestEdgeCases:
    """Test edge cases and special pattern handling."""
    
    def test_empty_patterns(self, temp_repo):
        """Test behavior with empty patterns."""
        # Exclude mode with no patterns should include everything
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns([])
        files1 = set(scope.collect_files())
        assert len(files1) > 0
        
        # Include mode with no patterns should include nothing
        scope.use_include_patterns([])
        files2 = set(scope.collect_files())
        assert len(files2) == 0

    def test_invalid_patterns(self, temp_repo):
        """Test handling of invalid patterns."""
        scope = RepoScope(temp_repo)
        # Empty string, comment, whitespace only
        scope.use_ignore_patterns(["", "#comment", "   ", "!"])
        files = scope.collect_files()
        # Should collect files normally
        assert len(files) > 0

    def test_dot_git_directory(self, temp_repo):
        """Test that .git directory is always excluded."""
        scope = RepoScope(temp_repo)
        # Try to explicitly include .git
        scope.use_include_patterns([".git/*"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        # Should never include .git files
        assert not any(f.startswith(".git/") for f in files)

    def test_pattern_order(self, temp_repo):
        """Test that pattern order is respected."""
        # In exclude mode, later negations can re-include
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["*.log", "!error.log", "*.log"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        assert "error.log" not in files  # Last *.log should exclude it
        
        # In include mode, later negations can re-exclude
        scope.use_include_patterns(["*.py", "!test?.py", "test1.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        assert "tests/test1.py" in files  # Last pattern should include it

    def test_nested_patterns(self, temp_repo):
        """Test nested directory pattern handling."""
        scope = RepoScope(temp_repo)
        # Test **/ pattern
        scope.use_include_patterns(["**/test_*.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        assert "tests/unit/test_core.py" in files
        assert "tests/integration/test_api.py" in files
        
        # Test direct vs nested pattern
        scope.use_include_patterns(["tests/*.py", "!tests/**/*api.py"])
        files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
        assert "tests/test1.py" in files
        assert "tests/integration/test_api.py" not in files