import pytest
from unittest.mock import MagicMock
from src.core.workflow import IdeaWorkflow

class TestPrepareScaffoldFiles:
    @pytest.fixture
    def workflow(self):
        # Mock dependencies to avoid instantiation side effects
        return IdeaWorkflow(
            github=MagicMock(),
            gemini=MagicMock(),
            jules=MagicMock()
        )

    def test_prepare_scaffold_files_valid(self, workflow):
        scaffold = {
            'files': [
                {'path': 'main.py', 'content': 'print("Hello")'},
                {'path': 'utils.py', 'content': 'def helper(): pass'}
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 2
        assert result[0] == {'path': 'main.py', 'content': 'print("Hello")'}
        assert result[1] == {'path': 'utils.py', 'content': 'def helper(): pass'}

    def test_prepare_scaffold_files_empty_files(self, workflow):
        assert workflow._prepare_scaffold_files({}) == []
        assert workflow._prepare_scaffold_files({'files': []}) == []

    def test_prepare_scaffold_files_not_a_list(self, workflow):
        scaffold = {'files': "not a list"}
        result = workflow._prepare_scaffold_files(scaffold)
        assert result == []

    def test_prepare_scaffold_files_malformed_entry(self, workflow):
        scaffold = {
            'files': [
                {'path': 'valid.py', 'content': ''},
                "not a dict",
                {'no_path': 'here'},
                {'path': 'valid2.py'} # Missing content is allowed, defaults to ''
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 2
        assert result[0]['path'] == 'valid.py'
        assert result[1]['path'] == 'valid2.py'
        assert result[1]['content'] == ''

    def test_prepare_scaffold_files_readme_filtering(self, workflow):
        scaffold = {
            'files': [
                {'path': 'README.md', 'content': '# Readme'},
                {'path': 'readme.md', 'content': '# readme'},
                {'path': 'src/main.py', 'content': 'pass'}
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 1
        assert result[0]['path'] == 'src/main.py'

    def test_prepare_scaffold_files_requirements(self, workflow):
        scaffold = {
            'files': [{'path': 'main.py', 'content': 'pass'}],
            'requirements': ['requests', 'pytest']
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 2

        # Check requirements.txt
        req_file = next(f for f in result if f['path'] == 'requirements.txt')
        assert req_file['content'] == 'requests\npytest'
