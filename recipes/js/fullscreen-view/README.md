# fullscreen-view (JavaScript)

Check that a part of the page goes full screen and comes back unchanged, with the Fullscreen API and without it.

- Kind: e2e · Tools: @playwright/test, `document.fullscreenElement`, `page.addInitScript` (no Fullscreen API),
  `test.use({ viewport, isMobile, hasTouch })`
- Use for: a "Full screen" or "Focus" button on a player, a game, a generated app, a chart or a board.

## Copy
Copy, never retype: `recipes/js/fullscreen-view/fullscreen.spec.js` and
`recipes/js/fullscreen-view/full-window.spec.js`.

## Fill
- Native: mark the element first (`element.dataset.probe = …`); after Exit it must still carry the mark, which proves
  the view was shown as itself and not rebuilt (a rebuilt iframe or canvas loses its state). Wait for
  `document.fullscreenElement` with `expect.poll`, then check Exit is focused, the state survived and focus came back
  to the opening button.
- Fallback: keep the phone `test.use` and the `fullscreenEnabled = false` init script in a file of their own; this is
  what iPhone Safari does. Check the view covers the viewport, the page behind doesn't scroll, Exit is focused and at
  least 44 px, and Escape leaves.

## Run
`npx playwright test recipes/js/fullscreen-view`

## Don't
- Don't press Escape to leave native full screen in a test: the browser owns that key there. Use the Exit button.
- Don't move the element into another container to show it full screen: the move reloads iframes and loses state.
