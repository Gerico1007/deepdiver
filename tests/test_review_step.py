"""The review step: a Slide Deck or Video Overview stopped at its plan.

Observed 2026-11-05 on notebook 78507190 (miadi-chronicle://251). With the
Customize dialog's review switch on, the card goes generating, then "Outline
ready" with a Review button and a More menu. Review opens the plan in the Studio
panel. Enter in its feedback field, or Proceed, closes the panel and renders on
the same card, and Studio keeps neither the plan nor the feedback. The markup
below is copied from that page.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time

import pytest
from playwright.async_api import async_playwright

from deepdiver.keep import keep_entry
from deepdiver.notebooklm_automator import NotebookLMAutomator, card_is_held
from deepdiver.outline import compose_seed, outline_body, plan_is_empty, save_feedback, save_outline

CARD_ID = '26192ae5-88f2-4443-b870-8c0df3cc4e41'
LIMIT = 'You have reached your daily Video Overview and Infographic limit.'


def paused_card(card_id=CARD_ID, family='Slide Deck', icon='tablet'):
    return f'''<artifact-library-item><div class="artifact-item-button artifact-item-button-pending-review">
      <button class="artifact-stretched-button" aria-description="{family}"></button>
      <mat-icon class="artifact-icon">{icon}</mat-icon>
      <span class="artifact-labels" id="artifact-labels-{card_id}">
        <span class="artifact-title">Outline ready</span><span class="artifact-details">Check your slide plan</span></span>
      <span class="review-plan-button"><button onclick="openPlan()">Review</button></span>
      <button aria-label="More">more_vert</button></div></artifact-library-item>'''


PLAN = '''<div class="plan-viewer-container"><div class="steps-timeline">
  <div class="step-item step-item-completed"><h3 class="step-title">Research</h3></div>
  <div class="step-item step-item-active"><h3 class="step-title">Slides outline</h3>
    <div class="plan-card-container"><div class="a2ui-plan-container"><a2ui-outliner-card>
      <span class="a2ui-card-title-text">Screenwalk to Studio Media</span>
      <div class="a2ui-outline-item"><span class="a2ui-outline-number">1.</span>
        <span class="a2ui-outline-text"><p><strong>Opening</strong>: what the pipeline does.</p></span></div>
      <div class="a2ui-outline-item"><span class="a2ui-outline-number">2.</span>
        <span class="a2ui-outline-text"><p><strong>Actors</strong>: who checks what.</p></span></div>
      <div class="a2ui-pill-input-box"><textarea aria-label="Add feedback to refine notes" id="fb"></textarea></div>
      <button id="go">Proceed</button></a2ui-outliner-card></div></div></div></div>
  <button aria-label="Close" onclick="closePlan()">collapse_content</button></div>'''


OLD_DECK = '''<artifact-library-item><button class="artifact-stretched-button" aria-description="Slide Deck"></button>
  <span class="artifact-labels" id="artifact-labels-77e0c81f-1ca9-4de5-9952-3c7e102b3d89"><span class="artifact-title">An Older Deck</span></span>
  <button aria-label="More">more_vert</button></artifact-library-item>'''


def page_html(cards, render_after_ms=1200):
    # A send records what it received, leaves the panel, shows a generating card, then a finished one.
    # As on the real page, the plan's panel hides the cards while it is open.
    return f'''<section class="studio-panel"><div id="viewer"></div><div id="cards">{cards}</div></section><script>
      window.sent = null;
      function closePlan() {{ document.getElementById('viewer').innerHTML = '';
        document.getElementById('cards').style.display = ''; }}
      function send(how, text) {{
        window.sent = {{how, text, at: Date.now()}};
        closePlan();
        const paused = document.querySelector('.artifact-item-button-pending-review').closest('artifact-library-item');
        paused.outerHTML =
          '<artifact-library-item id="this-one"><button class="mat-mdc-button-disabled" disabled></button><span class="artifact-title">Generating Slide Deck...</span></artifact-library-item>';
        setTimeout(() => {{ document.getElementById('this-one').outerHTML =
          `<artifact-library-item><button class="artifact-stretched-button" aria-description="Slide Deck"></button>
           <span class="artifact-labels" id="artifact-labels-{CARD_ID}"><span class="artifact-title">Deep Diver Media Pipeline</span></span>
           <button aria-label="More">more_vert</button></artifact-library-item>`; }}, {render_after_ms});
      }}
      function openPlan() {{
        document.getElementById('cards').style.display = 'none';
        document.getElementById('viewer').innerHTML = `{PLAN}`;
        document.getElementById('go').onclick = () => send('proceed', '');
        document.getElementById('fb').addEventListener('keydown', e => {{
          if (e.key === 'Enter') send('enter', e.target.value); }});
      }}
    </script>'''


GENERATING = ('<artifact-library-item><button class="mat-mdc-button-disabled" disabled></button>'
              '<span class="artifact-title">Generating Slide Deck...</span></artifact-library-item>')


def automator_on(page):
    automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
    automator.page = page
    automator.browser = None
    automator.session_tracker = None
    automator.config = {'STUDIO_SETTINGS': {'slide_deck': {'polling_interval': 1, 'generation_timeout': 20}}}
    automator.logger = logging.getLogger('test')
    return automator


async def _with_page(html, body):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        try:
            return await body(automator_on(page), page)
        finally:
            await browser.close()


def run(html, body):
    return asyncio.run(_with_page(html, body))


async def _watch(automator, **kwargs):
    began = time.time()
    result = await automator._monitor_artifact_generation(
        began, kwargs.pop('timeout', 10), 1, artifact_type=kwargs.pop('artifact_type', 'slide_deck'), **kwargs)
    return result, automator.last_generation_refusal, time.time() - began


def test_a_paused_card_is_not_a_finished_one():
    # Without this, a plain generate reports "Outline ready" as the deck.
    async def body(a, _):
        return await _watch(a, start_timeout=2)
    result, refusal, _ = run(page_html(paused_card()), body)
    assert result is None
    assert refusal == 'did not start'


def test_the_watch_stops_at_a_new_paused_card():
    async def body(a, _):
        return await _watch(a, stop_at_review=set())
    result, _, spent = run(page_html(paused_card()), body)
    assert result['status'] == 'awaiting_review'
    assert result['artifact_id'] == CARD_ID
    assert spent < 5


def test_a_card_already_paused_does_not_end_the_watch():
    async def body(a, _):
        return await _watch(a, stop_at_review={CARD_ID}, start_timeout=2)
    result, refusal, _ = run(page_html(paused_card()), body)
    assert result is None
    assert refusal == 'did not start'


def test_another_familys_paused_card_does_not_end_the_watch():
    async def body(a, _):
        return await _watch(a, stop_at_review=set(), start_timeout=2)
    result, _, _ = run(page_html(paused_card(family='Video Overview', icon='videocam')), body)
    assert result is None


def test_the_limit_sentence_still_ends_a_review_watch():
    # Kept at the Deep Diver seat's request, 2026-11-05.
    async def body(a, _):
        return await _watch(a, artifact_type='video_overview', stop_at_review=set())
    result, refusal, spent = run(f'<div class="studio"></div><div role="alert">{LIMIT}</div>', body)
    assert result is None
    assert refusal == LIMIT.rstrip('.')
    assert spent < 5


def test_the_list_marks_a_paused_card_and_download_can_tell():
    async def body(a, _):
        return await a.list_studio_artifacts()
    cards = run(page_html(paused_card() + GENERATING), body)
    assert cards[0]['awaiting_review'] is True
    assert cards[0]['family_label'] == 'Slide Deck'
    assert cards[1]['awaiting_review'] is False


def test_download_skips_a_paused_card_with_its_reason(tmp_path):
    async def body(a, _):
        return await a.download_all_artifacts(str(tmp_path))
    manifest = run(page_html(paused_card()), body)
    assert manifest['downloads'] == []
    assert manifest['failed'] == []
    assert 'waiting for review' in manifest['skipped'][0]['reason']
    assert manifest['skipped'][0]['artifact_id'] == CARD_ID


SWITCH = '''<div role="dialog"><button role="switch" aria-checked="false"
  onclick="this.setAttribute('aria-checked', '{after}')"></button></div>'''


def test_the_switch_is_turned_on_and_read_back():
    async def body(a, page):
        ok = await a._turn_on_review(page.locator('[role=dialog]'), {'review_switch': 'Review slide outline'})
        return ok, await page.locator('[role=switch]').get_attribute('aria-checked')
    assert run(SWITCH.format(after='true'), body) == (True, 'true')


def test_a_switch_that_stays_off_refuses_the_run():
    async def body(a, page):
        return await a._turn_on_review(page.locator('[role=dialog]'), {'review_switch': 'Review slide outline'})
    assert run(SWITCH.format(after='false'), body) is False


def test_a_dialog_with_no_switch_refuses_the_run():
    async def body(a, page):
        return await a._turn_on_review(page.locator('[role=dialog]'), {'review_switch': 'Review slide outline'})
    assert run('<div role="dialog"></div>', body) is False


SLOW_TILE = '''<section class="studio-panel"><div id="d"></div>
  <button aria-label="Slide Deck" onclick="window.clicks = (window.clicks || 0) + 1; setTimeout(() => {
    document.getElementById('d').innerHTML = '<div role=dialog>Customize Slide Deck<textarea></textarea>' +
      '<button role=switch aria-checked=false onclick=\\'this.setAttribute(&quot;aria-checked&quot;,&quot;true&quot;)\\'></button>' +
      '<button onclick=&quot;window.generated=true&quot;>Generate</button></div>'; }, 3000)">Slide Deck</button></section>'''


def test_a_dialog_slower_than_the_old_wait_is_found_with_one_click():
    from deepdiver.studio_artifacts import get_artifact_spec
    async def body(a, page):
        started = await a._drive_tile_dialog('Slide Deck', get_artifact_spec('slide_deck'), None, None, None,
                                             'A brief.', review=True)
        return started, await page.evaluate('[window.clicks, window.generated]')
    assert run(SLOW_TILE, body) == (True, [1, True])


def test_a_tile_with_no_dialog_refuses_a_review_run_and_names_what_the_page_shows(caplog):
    from deepdiver.studio_artifacts import get_artifact_spec
    html = ('<div class="cdk-overlay-pane" style="width:9px;height:9px">Something went wrong</div>'
            '<button aria-label="Slide Deck">Slide Deck</button>')
    async def body(a, _):
        return await a._drive_tile_dialog('Slide Deck', get_artifact_spec('slide_deck'), None, None, None, None,
                                          review=True)
    assert run(html, body) is False
    assert 'Something went wrong' in caplog.text


def test_review_saves_the_plan_and_leaves_the_card_paused(tmp_path):
    async def body(a, page):
        result = await a.review_outline(None, str(tmp_path))
        return result, await page.evaluate('window.sent'), await page.locator('.plan-viewer-container').count(), \
            [c['awaiting_review'] for c in await a.list_studio_artifacts()]
    result, sent, panels, paused = run(page_html(paused_card()), body)
    assert sent is None and panels == 0 and paused == [True]
    entry = result['entry']
    assert entry['outline_version'] == 1 and entry['item_count'] == 2
    text = open(entry['path'], encoding='utf-8').read()
    assert f'artifact_id: {CARD_ID}' in text and 'plan: Slides outline' in text
    assert '# Screenwalk to Studio Media' in text
    assert '1. Opening: what the pipeline does.' in text
    assert '2. Actors: who checks what.' in text


def test_review_records_the_plan_a_run_was_seeded_from(tmp_path):
    # The notebook door reads this to link two versions on the wheel (jgwill/Miadi#940).
    async def body(a, _):
        return await a.review_outline(None, str(tmp_path), seeded_from='outline-01-26192ae5.md')
    entry = run(page_html(paused_card()), body)['entry']
    assert entry['seeded_from'] == 'outline-01-26192ae5.md'


def test_review_names_a_card_when_several_wait(tmp_path, caplog):
    other = paused_card('77e0c81f-1ca9-4de5-9952-3c7e102b3d89')
    async def body(a, _):
        return await a.review_outline(None, str(tmp_path))
    assert run(page_html(paused_card() + other), body) is None
    assert 'name one' in caplog.text


def test_proceed_with_feedback_saves_both_first_then_sends_by_enter(tmp_path):
    async def body(a, page):
        result = await a.proceed_review(CARD_ID, str(tmp_path), feedback='Merge slides 1 and 2.')
        return result, await page.evaluate('window.sent')
    result, sent = run(page_html(paused_card()), body)
    assert sent['how'] == 'enter' and sent['text'] == 'Merge slides 1 and 2.'
    assert os.path.exists(result['outline']['path'])
    assert open(result['feedback']['path'], encoding='utf-8').read() == 'Merge slides 1 and 2.\n'
    assert result['artifact']['title'] == 'Deep Diver Media Pipeline'
    manifest = json.load(open(tmp_path / 'manifest.json', encoding='utf-8'))
    plan = next(e for e in manifest['downloads'] if e.get('outline_version'))
    assert plan['feedback_sent'] is True and plan['proceeded_at']
    assert plan['rendered_as']['artifact_id'] == CARD_ID


def test_proceed_without_feedback_presses_proceed(tmp_path):
    async def body(a, page):
        result = await a.proceed_review(CARD_ID, str(tmp_path))
        return result, await page.evaluate('window.sent')
    result, sent = run(page_html(paused_card()), body)
    assert sent['how'] == 'proceed'
    assert result['feedback'] is None
    assert result['artifact']['artifact_id'] == CARD_ID


def test_proceed_presses_nothing_when_the_plan_cannot_be_saved(tmp_path):
    blocked = tmp_path / 'a-file'
    blocked.write_text('in the way')
    async def body(a, page):
        result = await a.proceed_review(CARD_ID, str(blocked), feedback='x')
        return result, await page.evaluate('window.sent'), [c['awaiting_review'] for c in await a.list_studio_artifacts()]
    result, sent, paused = run(page_html(paused_card()), body)
    assert result is None and sent is None and paused == [True]


def test_proceed_watches_for_the_new_deck_and_does_not_return_an_older_one(tmp_path):
    # Live on 2026-11-05: a baseline read behind the panel was empty, so the older
    # deck was reported "rendered" 10 s after Proceed, while the new one generated.
    async def body(a, _):
        return await a.proceed_review(CARD_ID, str(tmp_path), wait=True)
    result = run(page_html(paused_card() + OLD_DECK, render_after_ms=3000), body)
    assert result['artifact']['title'] == 'Deep Diver Media Pipeline'
    assert result['artifact']['artifact_id'] == CARD_ID
    manifest = json.load(open(tmp_path / 'manifest.json', encoding='utf-8'))
    assert next(e for e in manifest['downloads'] if e.get('outline_version'))['rendered_as']['artifact_id'] == CARD_ID


def test_proceed_refuses_a_card_that_is_not_waiting(tmp_path):
    async def body(a, page):
        return await a.proceed_review('no-such-card', str(tmp_path)), await page.evaluate('window.sent')
    assert run(page_html(paused_card()), body) == (None, None)


PLAN_ONE = {'step': 'Slides outline', 'title': 'Deck', 'items': ['One', 'Two'], 'text': 'x'}


def test_each_new_plan_is_the_next_version_and_the_same_plan_is_not_saved_twice(tmp_path):
    first = save_outline(str(tmp_path), PLAN_ONE, CARD_ID, 'Slide Deck', notebook_id='nb')
    again = save_outline(str(tmp_path), dict(PLAN_ONE), CARD_ID, 'Slide Deck', notebook_id='nb')
    second = save_outline(str(tmp_path), {**PLAN_ONE, 'items': ['One', 'Three']}, 'other-card-id', 'Slide Deck',
                          seeded_from='outline-01-26192ae5.md')
    assert first['path'] == again['path']
    assert (first['outline_version'], second['outline_version']) == (1, 2)
    assert os.path.basename(second['path']) == 'outline-02-other-ca.md'
    assert 'seeded_from: outline-01-26192ae5.md' in open(second['path'], encoding='utf-8').read()
    manifest = json.load(open(tmp_path / 'manifest.json', encoding='utf-8'))
    assert len(manifest['downloads']) == 2


def test_a_saved_plan_does_not_hide_the_card_it_came_from(tmp_path):
    # The card keeps its id through the render; download skips a card it holds.
    entry = save_outline(str(tmp_path), PLAN_ONE, CARD_ID, 'Slide Deck')
    feedback = save_feedback(str(tmp_path), entry, 'Change it.')
    assert 'artifact_id' not in entry and 'artifact_id' not in feedback
    assert not card_is_held({'artifact_id': CARD_ID, 'title': 'Deep Diver Media Pipeline'}, [entry, feedback])


def test_keep_leaves_a_saved_plan_as_it_is(tmp_path):
    entry = save_outline(str(tmp_path), PLAN_ONE, CARD_ID, 'Slide Deck')
    before = dict(entry['kept'])
    assert keep_entry(entry, str(tmp_path))['kept'] == before


def test_a_plan_with_no_items_is_kept_by_its_text(tmp_path):
    # The panel of a family not seen yet still leaves its whole text.
    entry = save_outline(str(tmp_path), {'step': 'Producer notes', 'title': 'V', 'items': [], 'text': 'Scene one.'},
                         CARD_ID, 'Video Overview')
    assert 'Scene one.' in open(entry['path'], encoding='utf-8').read()
    assert plan_is_empty({'items': [], 'text': '  '}) and not plan_is_empty({'items': [], 'text': 'a'})


def test_a_seed_carries_the_brief_the_plan_and_the_changes_without_the_header(tmp_path):
    entry = save_outline(str(tmp_path), PLAN_ONE, CARD_ID, 'Slide Deck', notebook_id='nb')
    seed = compose_seed(entry['path'], focus='For the seats.', feedback='Drop Two.')
    assert seed.startswith('For the seats.')
    assert '1. One' in seed and seed.endswith('Drop Two.')
    assert 'artifact_id' not in seed and 'notebook_id' not in outline_body(entry['path'])


def test_feedback_without_an_outline_is_refused_by_the_cli(tmp_path):
    feedback = tmp_path / 'f.md'
    feedback.write_text('x')
    proc = subprocess.run([sys.executable, '-m', 'deepdiver.deepdive', 'studio', 'generate', 'slide_deck',
                           '--feedback', str(feedback)], capture_output=True, text=True)
    assert proc.returncode == 2
    assert 'goes with --from-outline' in proc.stdout


@pytest.mark.skipif(not shutil.which('gs'), reason='ghostscript not installed')
def test_keep_recompresses_a_deck_pdf_into_keep_and_removes_the_download(tmp_path):
    source = tmp_path / 'Deck-20261105.pdf'
    source.write_bytes(b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
                       b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
                       b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 72 72]>>endobj\n'
                       b'trailer<</Root 1 0 R>>\n')
    entry = keep_entry({'title': 'Deck', 'family_label': 'Slide Deck', 'path': str(source)}, str(tmp_path))
    assert entry['kept']['path'] == os.path.join('keep', 'Deck-20261105.pdf')
    assert not source.exists()
    assert (tmp_path / 'keep' / 'Deck-20261105.pdf').exists()
