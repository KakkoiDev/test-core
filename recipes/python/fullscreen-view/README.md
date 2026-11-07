# fullscreen-view (Python)

Check that a part of the page goes full screen and comes back unchanged, with the Fullscreen API and without it.

- Kind: e2e · Tools: pytest-playwright, `document.fullscreenElement`, `context.add_init_script` (no Fullscreen API),
  `browser_context_args` (viewport, touch)
- Use for: a "Full screen" or "Focus" button on a player, a game, a generated app, a chart or a board.

## Copy
Copy, never retype: `recipes/python/fullscreen-view/test_fullscreen.py` and
`recipes/python/fullscreen-view/test_full_window.py`.

## Fill
- Native: mark the element first (`element.dataset.probe = …`); after Exit it must still carry the mark, which proves
  the view was shown as itself and not rebuilt (a rebuilt iframe or canvas loses its state). Wait for
  `document.fullscreenElement` with `page.wait_for_function`, then check Exit is focused, the state survived and focus
  came back to the opening button.
- Fallback: keep the phone `browser_context_args` and the `context` fixture with the `fullscreenEnabled = false` init
  script in a file of their own; this is what iPhone Safari does. Check the view covers the viewport, the page behind
  doesn't scroll, Exit is focused and at least 44 px, and Escape leaves.

## Run
`pytest recipes/python/fullscreen-view -q`

## Don't
- Don't press Escape to leave native full screen in a test: the browser owns that key there. Use the Exit button.
- Don't move the element into another container to show it full screen: the move reloads iframes and loses state.
