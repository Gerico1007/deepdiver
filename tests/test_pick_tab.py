"""DeepDiver drives its own tab, never a person's tab on another site (2026-10-15)."""

from types import SimpleNamespace as Tab

from deepdiver.notebooklm_automator import pick_deepdiver_page


def test_prefers_a_notebook_tab_over_earlier_tabs():
    tabs = [Tab(url='https://aistudio.google.com/apps/x'), Tab(url='chrome://newtab/'),
            Tab(url='https://notebook.google.com/notebook/129987d0')]
    assert pick_deepdiver_page(tabs) is tabs[2]


def test_takes_a_blank_tab_when_no_notebook_tab():
    tabs = [Tab(url='https://miadi.tail3b11eb.ts.net/chronicle/x'), Tab(url='about:blank')]
    assert pick_deepdiver_page(tabs) is tabs[1]


def test_never_a_tab_on_another_site():
    tabs = [Tab(url='https://aistudio.google.com/apps/x'), Tab(url='https://miadi-author-desk.ai.studio/')]
    assert pick_deepdiver_page(tabs) is None


def test_old_notebooklm_host_counts():
    tabs = [Tab(url='https://example.com'), Tab(url='https://notebooklm.google.com/')]
    assert pick_deepdiver_page(tabs) is tabs[1]


def test_attach_timeout_names_the_open_tabs(monkeypatch):
    from deepdiver import notebooklm_automator as na

    class Answer:
        def json(self):
            return [{'type': 'page', 'url': 'https://miadi-author-desk.ai.studio/'},
                    {'type': 'iframe', 'url': 'https://accounts.google.com/RotateCookiesPage'},
                    {'type': 'page', 'url': 'https://notebook.google.com/notebook/3eb56742'}]
    monkeypatch.setattr(na.requests, 'get', lambda *a, **k: Answer())
    monkeypatch.setattr(na, 'find_keyring_prompt', lambda: None)  # this host may have one open
    text = na.describe_attach_timeout('http://127.0.0.1:9222')
    assert 'miadi-author-desk.ai.studio' in text and 'notebook.google.com' in text
    assert 'RotateCookiesPage' not in text
    assert 'may be a person' in text


def test_attach_timeout_when_even_the_tab_list_is_silent(monkeypatch):
    from deepdiver import notebooklm_automator as na

    def silent(*a, **k):
        raise TimeoutError
    monkeypatch.setattr(na.requests, 'get', silent)
    monkeypatch.setattr(na, 'find_keyring_prompt', lambda: None)
    assert 'the tab list did not answer either' in na.describe_attach_timeout('http://127.0.0.1:9222')


def test_daily_limit_is_read_from_the_page():
    from deepdiver.notebooklm_automator import daily_limit_message
    page = "Studio\nInfographic\nYou have reached your daily Infographic limit. Learn more.\n"
    assert daily_limit_message(page) == "You have reached your daily Infographic limit"
    assert daily_limit_message("You have reached your daily Video Overview limit.") == "You have reached your daily Video Overview limit"
    assert daily_limit_message("Limitation noted: End-to-end hosted routes are not yet built") is None
    assert daily_limit_message(None) is None


def test_wake_background_tabs_activates_each_page_then_the_first_again(monkeypatch):
    from deepdiver import notebooklm_automator as na
    calls = []

    class Answer:
        def __init__(self, data=None):
            self._data = data

        def json(self):
            return self._data

    def get(url, timeout=None):
        calls.append(url)
        if url.endswith('/json'):
            return Answer([{'type': 'page', 'id': 'A'}, {'type': 'iframe', 'id': 'X'}, {'type': 'page', 'id': 'B'}])
        return Answer()
    monkeypatch.setattr(na.requests, 'get', get)
    assert na.wake_background_tabs('http://127.0.0.1:9222/', pause=0) == 2
    assert [c.rsplit('/', 1)[1] for c in calls[1:]] == ['A', 'B', 'A']


def test_source_url_key_matches_the_forms_gemini_notebook_uses():
    from deepdiver.notebooklm_automator import source_url_key as k
    assert k('https://youtu.be/gloSM0SIgPI') == k('https://www.youtube.com/watch?v=gloSM0SIgPI') == 'yt:gloSM0SIgPI'
    assert k('https://m.youtube.com/watch?v=abc&t=10') == 'yt:abc'
    assert k('https://www.youtube.com/shorts/xyz') == 'yt:xyz'
    assert k('https://example.com/a/') == k('https://example.com/a')
    assert k('https://example.com/a') != k('https://example.com/b')
