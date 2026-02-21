from src.core.workflow import IdeaWorkflow
from unittest.mock import Mock


class TestWorkflowScaffold:
    def test_prepare_scaffold_files_empty(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {'files': []}
        result = workflow._prepare_scaffold_files(scaffold)
        assert result == []

    def test_prepare_scaffold_files_invalid_files_type(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {'files': "not a list"}
        result = workflow._prepare_scaffold_files(scaffold)
        assert result == []

    def test_prepare_scaffold_files_basic(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {
            'files': [
                {'path': 'src/main.py', 'content': 'print("hello")'},
                {'path': 'tests/test_main.py', 'content': 'def test_main(): pass'}
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 2
        assert result[0]['path'] == 'src/main.py'
        assert result[1]['path'] == 'tests/test_main.py'

    def test_prepare_scaffold_files_readme_filter(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {
            'files': [
                {'path': 'README.md', 'content': '# Title'},
                {'path': 'readme.md', 'content': '# Title'},
                {'path': 'src/main.py', 'content': 'print("hello")'}
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 1
        assert result[0]['path'] == 'src/main.py'

    def test_prepare_scaffold_files_malformed_entry(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {
            'files': [
                {'path': 'src/main.py', 'content': 'valid'},
                "not a dict",
                {'content': 'missing path'}
            ]
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 1
        assert result[0]['path'] == 'src/main.py'

    def test_prepare_scaffold_files_requirements(self):
        workflow = IdeaWorkflow(Mock(), Mock(), Mock())
        scaffold = {
            'files': [{'path': 'src/main.py', 'content': 'valid'}],
            'requirements': ['requests', 'numpy']
        }
        result = workflow._prepare_scaffold_files(scaffold)
        assert len(result) == 2
        assert result[1]['path'] == 'requirements.txt'
        assert result[1]['content'] == 'requests\nnumpy'
