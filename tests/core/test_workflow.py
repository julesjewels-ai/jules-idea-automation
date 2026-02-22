import pytest
from unittest.mock import MagicMock
from src.core.workflow import IdeaWorkflow

class TestIdeaWorkflow:
    @pytest.fixture
    def workflow(self):
        return IdeaWorkflow(
            github=MagicMock(),
            gemini=MagicMock(),
            jules=MagicMock()
        )

    def test_prepare_scaffold_files_basic(self, workflow):
        scaffold = {
            'files': [
                {'path': 'main.py', 'content': 'print("Hello")'},
                {'path': 'README.md', 'content': '# Readme'}
            ],
            'requirements': ['requests', 'pytest']
        }

        files = workflow._prepare_scaffold_files(scaffold)

        # README.md should be skipped (as per logic)
        # requirements.txt should be added
        assert len(files) == 2
        assert files[0]['path'] == 'main.py'
        assert files[0]['content'] == 'print("Hello")'
        assert files[1]['path'] == 'requirements.txt'
        assert files[1]['content'] == 'requests\npytest'

    def test_prepare_scaffold_files_empty(self, workflow):
        scaffold = {}
        files = workflow._prepare_scaffold_files(scaffold)
        assert len(files) == 0

    def test_prepare_scaffold_files_malformed_files_list(self, workflow):
        scaffold = {'files': "not a list"}
        files = workflow._prepare_scaffold_files(scaffold)
        assert len(files) == 0

    def test_prepare_scaffold_files_malformed_entry(self, workflow):
        scaffold = {
            'files': [
                {'path': 'valid.py', 'content': ''},
                "invalid_string",
                {'no_path': 'content'}
            ]
        }
        files = workflow._prepare_scaffold_files(scaffold)
        assert len(files) == 1
        assert files[0]['path'] == 'valid.py'
