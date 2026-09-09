import importlib.util
import io
import json
import sys
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import ownership
spec = importlib.util.spec_from_file_location('hook', Path(__file__).with_name('warn-duplicate-write.py'))
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

class CoordinationTest(unittest.TestCase):
    def test_missing_owner_is_unknown_with_explicit_coverage(self):
        with patch.object(ownership, 'live_sessions', return_value=[]), patch.object(ownership, 'worktrees', return_value=[('/repo','main')]):
            row = ownership.survey('/repo')[0]
        self.assertEqual(row.get('ownership_status'), 'unknown')
        self.assertEqual(row.get('coverage'), 'claude-only')

    def test_all_sessions_warns_about_incomplete_coverage(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(ownership, 'live_sessions', return_value=[]), redirect_stdout(out), redirect_stderr(err):
            ownership.main(['--all', '--json'])
        self.assertEqual(json.loads(out.getvalue()), [])
        self.assertIn('Codex', err.getvalue())

    def collisions(self, answers):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a', Path(d)/'b'
            a.mkdir(); b.mkdir(); (b/'file.md').write_text('shared')
            def git(_repo, _deadline, *args):
                return answers.get(args[0])
            with patch.object(hook,'attached_worktrees',return_value=[(str(a),'main'),(str(b),'feature')]), patch.object(hook,'git',side_effect=git), patch.object(ownership,'live_sessions',return_value=[{}]), patch.object(ownership,'owner_of',return_value={'name':'test'}):
                return hook.collisions(str(a),'file.md',hook.Deadline(5))

    def test_git_failure_never_claims_collision(self):
        self.assertEqual(self.collisions({}), [])

    def test_missing_merge_base_never_claims_collision(self):
        self.assertEqual(self.collisions({'ls-files':'file.md','rev-parse':'tip'}), [])

    def test_failed_base_tree_probe_never_claims_collision(self):
        self.assertEqual(self.collisions({'ls-files':'file.md','rev-parse':'tip','merge-base':'base'}), [])

    def test_known_inherited_file_is_not_new(self):
        self.assertEqual(self.collisions({'ls-files':'file.md','rev-parse':'tip','merge-base':'base','ls-tree':'file.md'}), [])

    def test_confirmed_untracked_file_still_collides(self):
        self.assertEqual(len(self.collisions({'ls-files':''})), 1)

    def test_confirmed_new_tracked_file_still_collides(self):
        self.assertEqual(len(self.collisions({'ls-files':'file.md','rev-parse':'tip','merge-base':'base','ls-tree':''})), 1)

class RealGitHookTest(unittest.TestCase):
    def test_denial_read_unlock_and_changed_content(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); repo = root/'repo'; sibling = root/'sibling'
            def git(*args):
                subprocess.run(['git', *args], check=True, capture_output=True)
            git('init', '-q', '-b', 'main', str(repo))
            (repo/'base.md').write_text('base')
            git('-C',str(repo),'add','base.md')
            git('-C',str(repo),'-c','user.name=test','-c','user.email=test@example.invalid','commit','-qm','base')
            git('-C',str(repo),'worktree','add','-qb','feature',str(sibling))
            git('-C',str(repo),'config','agents.duplicate-write-guard','true')
            candidate = sibling/'new.md'; candidate.write_text('first')
            git('-C',str(sibling),'add','new.md')
            git('-C',str(sibling),'-c','user.name=test','-c','user.email=test@example.invalid','commit','-qm','new')
            payload={'tool_name':'Write','cwd':str(repo),'session_id':'reader','tool_input':{'file_path':'new.md'}}
            sessions=[{'name':'writer','cwd':str(sibling)}]
            def verdict():
                output=io.StringIO()
                with redirect_stdout(output): hook.pre_tool_use(payload,hook.Deadline(5))
                return output.getvalue()
            with patch.object(ownership,'live_sessions',return_value=sessions),patch.object(hook,'STATE',root/'markers'):
                self.assertIn('deny',verdict())
                self.assertIn('deny',verdict())
                hook.post_tool_use({'tool_name':'Read','session_id':'reader','tool_input':{'file_path':str(candidate)}})
                self.assertEqual(verdict(),'')
                candidate.write_text('changed')
                self.assertIn('deny',verdict())
                with patch.object(ownership,'live_sessions',return_value=[]):
                    self.assertEqual(verdict(),'')

if __name__ == '__main__': unittest.main()
