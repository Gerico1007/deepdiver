"""
DeepDiver's Chrome home: a person signs in to Google once, and every later
launch reuses that folder (2026-10-09, miadi-chronicle://251 DD8).
"""

import os

import pytest

from deepdiver import notebooklm_automator as na


def _make_chrome_home(path, profile='Profile 2'):
    os.makedirs(os.path.join(path, profile), exist_ok=True)
    with open(os.path.join(path, 'Local State'), 'w') as fh:
        fh.write('{}')
    with open(os.path.join(path, profile, 'Cookies'), 'w') as fh:
        fh.write('signed-in')
    return path


@pytest.fixture
def live_root(tmp_path):
    return _make_chrome_home(str(tmp_path / 'google-chrome'))


class TestSignedOutUrl:
    @pytest.mark.parametrize('url', [
        'https://notebook.google.com/trynow',
        'https://notebooklm.google.com/trynow?hl=en',
        'https://accounts.google.com/v3/signin/identifier?continue=https://notebook.google.com/',
    ])
    def test_signed_out_pages(self, url):
        assert na._is_signed_out_url(url)

    @pytest.mark.parametrize('url', [
        'https://notebook.google.com/',
        'https://notebook.google.com/?original_referer=https:%2F%2Faccounts.google.com%23&pli=1',
        'https://notebook.google.com/notebook/53f63f29',
        'https://example.com/trynow',
        None,
    ])
    def test_signed_in_or_other_pages(self, url):
        assert not na._is_signed_out_url(url)


class TestResolveLaunchDir:
    def test_existing_home_is_reused_not_recloned(self, tmp_path, live_root):
        home = _make_chrome_home(str(tmp_path / 'home'))
        with open(os.path.join(home, 'Profile 2', 'Cookies'), 'w') as fh:
            fh.write('sign-in made in the home')
        got = na.resolve_launch_dir(home, 'Profile 2', profile_root=live_root)
        assert got == home
        with open(os.path.join(home, 'Profile 2', 'Cookies')) as fh:
            assert fh.read() == 'sign-in made in the home'

    def test_missing_home_is_seeded_once(self, tmp_path, live_root):
        home = str(tmp_path / 'home')
        got = na.resolve_launch_dir(home, 'Profile 2', profile_root=live_root)
        assert got == home
        assert os.path.isfile(os.path.join(home, 'Local State'))
        assert os.path.isfile(os.path.join(home, 'Profile 2', 'Cookies'))

    def test_non_chrome_folder_is_never_replaced(self, tmp_path, live_root):
        home = tmp_path / 'home'
        home.mkdir()
        (home / 'notes.txt').write_text('keep me')
        assert na.resolve_launch_dir(str(home), 'Profile 2', profile_root=live_root) is None
        assert (home / 'notes.txt').read_text() == 'keep me'

    def test_fresh_clones_into_a_new_folder(self, tmp_path, live_root):
        home = _make_chrome_home(str(tmp_path / 'home'))
        got = na.resolve_launch_dir(home, 'Profile 2', profile_root=live_root, fresh=True)
        assert got and got != home
        assert os.path.isfile(os.path.join(got, 'Local State'))

    def test_default_is_deepdivers_home(self, monkeypatch, tmp_path):
        home = str(tmp_path / 'home')
        monkeypatch.setattr(na, 'DEFAULT_USER_DATA_DIR', home)
        assert na.resolve_launch_dir() == home


class TestAdopt:
    def test_moves_a_closed_signed_in_folder(self, tmp_path):
        src = _make_chrome_home(str(tmp_path / 'deepdiver-chrome-abc'))
        dest = str(tmp_path / 'home')
        assert na.adopt_user_data_dir(src, dest) == dest
        assert not os.path.exists(src)
        assert os.path.isfile(os.path.join(dest, 'Profile 2', 'Cookies'))

    def test_refuses_a_folder_chrome_still_holds(self, tmp_path):
        src = _make_chrome_home(str(tmp_path / 'deepdiver-chrome-abc'))
        os.symlink('gaia-12345', os.path.join(src, 'SingletonLock'))
        assert na.adopt_user_data_dir(src, str(tmp_path / 'home')) is None
        assert os.path.exists(src)

    def test_refuses_an_existing_destination(self, tmp_path):
        src = _make_chrome_home(str(tmp_path / 'deepdiver-chrome-abc'))
        dest = _make_chrome_home(str(tmp_path / 'home'))
        assert na.adopt_user_data_dir(src, dest) is None
        assert os.path.exists(src)

    def test_refuses_a_folder_that_is_not_chrome(self, tmp_path):
        src = tmp_path / 'random'
        src.mkdir()
        assert na.adopt_user_data_dir(str(src), str(tmp_path / 'home')) is None
