"""
Basic tests for context-collapse.
Run: python -m pytest tests/ -v
"""

import sys
import os
import tempfile
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def make_test_repo():
    """Create a minimal git repo with commit history for testing."""
    tmpdir = tempfile.mkdtemp()
    subprocess.run(['git', 'init'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmpdir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmpdir, capture_output=True)

    # Create files and commits
    for i in range(5):
        path = os.path.join(tmpdir, f'file_{i % 3}.py')
        with open(path, 'w') as f:
            f.write(f'# change {i}\nprint({i})\n')
        subprocess.run(['git', 'add', '.'], cwd=tmpdir, capture_output=True)
        subprocess.run(
            ['git', 'commit', '-m', f'feat: change {i}'],
            cwd=tmpdir, capture_output=True
        )
    return tmpdir


class TestGitMiner:
    def test_mine_returns_expected_keys(self):
        from git_miner import mine
        repo = make_test_repo()
        data = mine(repo)
        assert 'churn' in data
        assert 'reentry' in data
        assert 'pairs' in data
        assert 'dna' in data

    def test_churn_is_dict(self):
        from git_miner import mine
        repo = make_test_repo()
        data = mine(repo)
        assert isinstance(data['churn'], dict)

    def test_churn_counts_are_positive(self):
        from git_miner import mine
        repo = make_test_repo()
        data = mine(repo)
        for count in data['churn'].values():
            assert count > 0

    def test_dna_percentages_sum_to_100(self):
        from git_miner import mine
        repo = make_test_repo()
        data = mine(repo)
        total = sum(data['dna'].values())
        assert 99 <= total <= 101  # allow float rounding

    def test_reentry_sequence_is_sorted(self):
        from git_miner import mine
        repo = make_test_repo()
        data = mine(repo)
        scores = [item['score'] for item in data['reentry']]
        assert scores == sorted(scores, reverse=True)

    def test_invalid_repo_raises(self):
        from git_miner import mine
        import pytest
        with pytest.raises(Exception):
            mine('/tmp/not_a_git_repo_xyzabc')


class TestReportRenderer:
    def test_render_creates_html_file(self):
        from git_miner import mine
        from report_renderer import render
        import tempfile

        repo = make_test_repo()
        data = mine(repo)
        data['ai'] = {
            'purpose': 'Test repo',
            'key_decisions': [],
            'danger_zones': [],
            'ai_powered': False
        }

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            out = f.name

        render(data, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 1000  # should be a real HTML file

    def test_render_output_contains_html(self):
        from git_miner import mine
        from report_renderer import render
        import tempfile

        repo = make_test_repo()
        data = mine(repo)
        data['ai'] = {
            'purpose': 'Test',
            'key_decisions': [],
            'danger_zones': [],
            'ai_powered': False
        }

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
            out = f.name

        render(data, out)
        with open(out, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '<!DOCTYPE html>' in content or '<html' in content
