# Screen Shot report

Below is a structured deep‐dive into Agent Zero’s “web browser” support, covering how screenshots are handled today and where you could hook in explicit or auto-save behavior.

1. Overview & Documentation
   No dedicated docs in `docs/` describe the web-driving tool itself (most Markdown in `docs` covers setup, file-browser UI, etc.). The closest runtime setting is the “Use Vision” toggle, which enables vision-capable LLMs to analyze page screenshots:

   • Settings switch:
     [`python/helpers/settings.py:415`](python/helpers/settings.py:415)
     ```json
     "description": "Models capable of Vision can use it to analyze web pages from screenshots. Increases quality but also token usage."
     ```

2. Key Dependencies
   • Playwright (via [`python/helpers/playwright.py`](python/helpers/playwright.py))
   • Third-party `browser_use` Python package (imported in
     [`python/helpers/browser_use.py:3`](python/helpers/browser_use.py:3)–4)
   • Pydantic (for the browser agent’s action models)
   • Agent framework (models.get_browser_model, DeferredTask, etc.)

3. Core Implementation: `BrowserAgent`
   File: [`python/tools/browser_agent.py`](python/tools/browser_agent.py)

   • Initialization:
     Instantiates `browser_use.BrowserSession` with headless Chromium, custom profile, screen size, etc.
     [`python/tools/browser_agent.py:36–68`](python/tools/browser_agent.py:36–68)

   • Task loop & logging:
     On every step, `get_update()` is called.  Inside it we:
     1. Capture the in-memory log of LLM/browser actions
     2. Take a screenshot
     3. Save to disk
     4. Return an image URI to the agent’s log

     Screenshot code:
     [`python/tools/browser_agent.py:379–388`](python/tools/browser_agent.py:379–388)
     ```python
         path = files.get_abs_path(
             persist_chat.get_chat_folder_path(agent.context.id),
             "browser", "screenshots", f"{self.guid}.png"
         )
         files.make_dirs(path)
         await page.screenshot(path=path, full_page=False, timeout=3000)
         result["screenshot"] = f"img://{path}&t={str(time.time())}"
     ```

   • Final response formatting:
     After the agent finishes its run, if a screenshot URI was logged, it is appended to the answer text:
     [`python/tools/browser_agent.py:313–319`](python/tools/browser_agent.py:313–319)
     ```python
     if self.log.kvps and "screenshot" in self.log.kvps:
         path = self.log.kvps["screenshot"].split("//",1)[-1].split("&",1)[0]
         answer_text += f"\n\nScreenshot: {path}"
     ```

4. Commented‐out Stubs & Older Tool Variants
   Several legacy or in-progress classes hint at on-demand screenshot capabilities:

   • `python/helpers/browser.py`:
     Stub for a standalone screenshot method—currently commented.
     [`python/helpers/browser.py:318–320`](python/helpers/browser.py:318–320)

   • `python/tools/browser._py`:
     A base `Browser` tool with `save_screenshot()` stub.
     [`python/tools/browser._py:32–36`](python/tools/browser._py:32–36)

   • `python/tools/browser_open._py` & `browser_do._py`:
     Both define (commented) workflows that end with taking a screenshot and logging it.
     – [`python/tools/browser_open._py:21–24`](python/tools/browser_open._py:21–24)
     – [`python/tools/browser_do._py:47–50`](python/tools/browser_do._py:47–50)

5. Options Today
   • Automatic per-step screenshots: Every time the BrowserAgent polls `get_update()`, a PNG is saved under:
     `<chat_folder>/browser/screenshots/{guid}.png`.
   • Vision analyses: If `"Use Vision"` is ON, your chosen LLM can examine those screenshots to improve page understanding (but saving still relies on the above hook).
   • On-demand: No exposed CLI/tool command for “take screenshot” today—though you can prompt the agent (“Please take a screenshot of the current page”) and it will naturally include the next update’s screenshot.
   • Image assets: Downloading/saving every inline image is not implemented.

6. Enhancement Opportunities
   A. **Explicit Screenshot Tool**
      Un-comment and expose the stub in `python/tools/browser.py` (or create a new `browser_screenshot` tool) that calls `await self.state.browser.screenshot(...)` and returns a filesystem path.

   B. **Auto-save All Images**
      Extend `browser_use.Controller` with an action like “Save all page images” that, for each `<img>` element, fetches its `src` and writes to disk.

   C. **Smart Auto-Capture**
      Inside `BrowserAgent._run_task`, have the LLM trigger screenshots whenever it deems a page visually complex or when explaining an interface—e.g. add a controller action `@controller.registry.action("Screenshot when useful")`.

   D. **Configurable Screenshot Policy**
      Add new settings under `python/helpers/settings.py`:
      ```jsonc
      {
        "auto_save_screenshots": {"type": "switch", "description": "Save screenshots on every step"},
        "explicit_screenshot_command": {"type": "switch", "description": "Allow on-demand screenshot tool"}
      }
      ```

—
Screenshots of a real browser window during Agent Zero browsing would require running a task (e.g. `BrowserAgent.execute("go to https://example.com")`) via the UI or CLI and then capturing the browser itself via `browser_action`. If you’d like to see that in action, let me know and I can spin up a short demo with live screenshots.

## Summary

Structured summary of Agent Zero’s web browser screenshot capabilities:

1. Configuration
- Vision toggle in settings enables LLM analysis of page screenshots.
  See [`python/helpers/settings.py:415`](python/helpers/settings.py:415).

2. Automatic per‐step screenshots
- In `BrowserAgent.get_update()`, each update performs:
  ```python
  path = files.get_abs_path(
      persist_chat.get_chat_folder_path(agent.context.id),
      "browser", "screenshots", f"{self.guid}.png"
  )
  await page.screenshot(path=path, full_page=False, timeout=3000)
  result["screenshot"] = f"img://{path}&t={time.time()}"
  ```
  (Implementation at [`python/tools/browser_agent.py:379–388`](python/tools/browser_agent.py:379))
- Screenshots saved under `<chat_folder>/browser/screenshots/{guid}.png`.

3. On‐demand screenshots
- No dedicated “screenshot” CLI/tool today.
- You can prompt the BrowserAgent (“Take a screenshot…”) and the next update includes a saved image.

4. Commented‐out stubs
- Standalone API in [`python/helpers/browser.py:318–320`](python/helpers/browser.py:318).
- Base tool stub in [`python/tools/browser._py:32–36`](python/tools/browser._py:32).
- Legacy variants in [`python/tools/browser_open._py:21–24`](python/tools/browser_open._py:21) and [`python/tools/browser_do._py:47–50`](python/tools/browser_do._py:47).

5. Future enhancements
- Expose an explicit screenshot tool by un‐commenting stubs or adding `browser_screenshot`.
- Add setting flags (e.g. `"auto_save_screenshots"`) in [`python/helpers/settings.py`](python/helpers/settings.py).
- Extend the controller with a “Save all page images” action.
- Implement “smart” auto‐capture when the LLM deems it useful.

All relevant file locations and line numbers have been cited for navigation.

## Screen shot search resutls

python\helpers\browser.py:
  317
  318: #     async def screenshot(self, path: str, full_page=False):
  319  #         await self._check_page()
  320: #         await self.page.screenshot(path=path, full_page=full_page)
  321

python\helpers\settings.py:
  414              "title": "Use Vision",
  415:             "description": "Models capable of Vision can use it to analyze web pages from screenshots. Increases quality but also token usage.",
  416              "type": "switch",

python\tools\browser_agent.py:
  249                  self.update_progress("\n".join(log))
  250:                 screenshot = update.get("screenshot", None)
  251:                 if screenshot:
  252:                     self.log.update(screenshot=screenshot)
  253              except Exception as e:

  308
  309:         # update the log (without screenshot path here, user can click)
  310          self.log.update(answer=answer_text)
  311
  312:         # add screenshot to the answer if we have it
  313          if (
  314              self.log.kvps
  315:             and "screenshot" in self.log.kvps
  316:             and self.log.kvps["screenshot"]
  317          ):
  318:             path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
  319:             answer_text += f"\n\nScreenshot: {path}"
  320
  321:         # respond (with screenshot path)
  322          return Response(message=answer_text, break_loop=False)

  381                          "browser",
  382:                         "screenshots",
  383                          f"{self.guid}.png",

  385                      files.make_dirs(path)
  386:                     await page.screenshot(path=path, full_page=False, timeout=3000)
  387:                     result["screenshot"] = f"img://{path}&t={str(time.time())}"
  388

python\tools\browser_do._py:
  46  #                 response = dom
  47: #             self.update_progress("Taking screenshot...")
  48: #             screenshot = await self.save_screenshot()
  49: #             self.log.update(screenshot=screenshot)
  50  #         except Exception as e:

  54  #             try:
  55: #                 screenshot = await self.save_screenshot()
  56  #                 dom = await self.state.browser.get_clean_dom()
  57  #                 response = f"Error:\n{response}\n\nDOM:\n{dom}"
  58: #                 self.log.update(screenshot=screenshot)
  59  #             except Exception:

python\tools\browser_open._py:
  20  #             response = await self.state.browser.get_clean_dom()
  21: #             self.update_progress("Taking screenshot...")
  22: #             screenshot = await self.save_screenshot()
  23: #             self.log.update(screenshot=screenshot)
  24  #         except Exception as e:

python\tools\browser._py:
  31
  32: #     async def save_screenshot(self):
  33  #         await self.prepare_state()
  34  #         path = files.get_abs_path("tmp/browser", f"{uuid.uuid4()}.png")
  35: #         await self.state.browser.screenshot(path, True)
  36  #         return "img://" + path
