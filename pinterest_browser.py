from pathlib import Path
from playwright.sync_api import sync_playwright
from models import PinDraft


class PinterestBrowserPublisher:
    def __init__(self, config: dict):
        self.config = config
        self.profile_dir = Path(config["profile_dir"]).resolve()
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.headless = bool(config.get("headless", False))
        self.dry_run = bool(config.get("dry_run", True))
        self.timeout_ms = int(config.get("timeout_ms", 30000))
        self.create_pin_url = config.get(
            "create_pin_url",
            "https://www.pinterest.com/pin-creation-tool/",
        )

    def _launch_context(self, playwright):
        return playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            channel="chrome",
            headless=self.headless,
            chromium_sandbox=True,
            viewport={"width": 1440, "height": 1000},
        )

    def login_once(self):
        with sync_playwright() as p:
            context = self._launch_context(p)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.pinterest.com/", wait_until="domcontentloaded")
            print("Pinterest opened using the persistent browser profile.")
            print("Log in manually if needed. When your home feed is visible, return here and press ENTER.")
            input()
            context.close()
            print(f"Login session saved in: {self.profile_dir}")

    def _click_first(self, page, selectors, label):
        last_error = None
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                locator.wait_for(state="visible", timeout=4000)
                locator.click()
                return
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"Could not find Pinterest {label}. Last error: {last_error}")

    def _add_topic_tags(self, page, topics):
        """
        Search Pinterest's live topic suggestions and only select an exact
        matching topic. Missing topics are skipped instead of choosing an
        unrelated fallback suggestion.
        """
        if not topics:
            return

        try:
            topic_input = page.get_by_placeholder("Search for a tag")
            topic_input.wait_for(state="visible", timeout=4000)
        except Exception as exc:
            print(f"WARNING: Topic-tag field was not available: {exc}")
            return

        added_topics = []
        skipped_topics = []

        for topic in topics[:10]:
            try:
                topic_input.click()
                topic_input.fill("")
                topic_input.fill(topic)
                page.wait_for_timeout(700)

                candidates = page.locator('[role="option"]')
                match = None

                for index in range(candidates.count()):
                    candidate = candidates.nth(index)
                    candidate_text = (candidate.inner_text() or "").strip()
                    if candidate_text.casefold() == topic.strip().casefold():
                        match = candidate
                        break

                if match is None:
                    exact_text = page.get_by_text(topic, exact=True)
                    for index in range(exact_text.count()):
                        candidate = exact_text.nth(index)
                        if candidate.is_visible():
                            match = candidate
                            break

                if match is None:
                    skipped_topics.append(topic)
                    topic_input.fill("")
                    print(f"  Topic not available on Pinterest: {topic}")
                    continue

                match.wait_for(state="visible", timeout=2000)
                match.click()
                added_topics.append(topic)
                page.wait_for_timeout(250)

            except Exception as exc:
                skipped_topics.append(topic)
                print(f"  Skipped topic '{topic}': {exc}")
                try:
                    topic_input.fill("")
                except Exception:
                    pass

        if added_topics:
            print(
                "Added Pinterest topic tags: "
                + ", ".join(added_topics)
            )

        if skipped_topics:
            print(
                "Skipped unavailable Pinterest topics: "
                + ", ".join(skipped_topics)
            )

        if not added_topics:
            print("No matching Pinterest topic tags were available; continuing without them.")

    def publish_pin(self, draft: PinDraft):
        image = Path(draft.image_path).resolve()
        if not image.exists():
            raise FileNotFoundError(f"Image does not exist: {image}")

        with sync_playwright() as p:
            context = self._launch_context(p)
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(self.timeout_ms)
            page.goto(self.create_pin_url, wait_until="domcontentloaded")

            if "login" in page.url.lower():
                context.close()
                raise RuntimeError(
                    "Pinterest session is not logged in. Run pinterest_login.py first."
                )

            uploaded = False
            for selector in ['input[type="file"]', 'input[accept*="image"]']:
                try:
                    file_input = page.locator(selector).first
                    file_input.wait_for(state="attached", timeout=5000)
                    file_input.set_input_files(str(image))
                    uploaded = True
                    break
                except Exception:
                    pass

            if not uploaded:
                context.close()
                raise RuntimeError("Could not locate Pinterest image upload control.")

            # Known-good title selector
            title_field = page.get_by_role("textbox", name="Title")
            title_field.wait_for(state="visible", timeout=10000)
            title_field.fill(draft.title)

            # Known-good description selector from the working Windows test
            description_field = page.locator(
                'div:has-text("Description")'
            ).locator('[contenteditable="true"]').first
            description_field.wait_for(state="visible", timeout=10000)
            description_field.click()
            description_field.fill(draft.description)

            # Destination links are optional. Non-affiliate tip Pins leave
            # this field untouched so they publish as native Pinterest content.
            if draft.affiliate_url:
                link_field = page.get_by_placeholder("Add a link")
                link_field.wait_for(state="visible", timeout=10000)
                link_field.fill(draft.affiliate_url)

            board_name = draft.board_name.strip()
            if board_name:
                try:
                    self._click_first(page, [
                        '[data-test-id*="board"]',
                        'button[aria-label*="board" i]',
                        'button:has-text("Select")',
                    ], "board selector")
                    option = page.get_by_text(board_name, exact=True).first
                    option.wait_for(state="visible", timeout=8000)
                    option.click()
                except Exception as exc:
                    print(
                        f"WARNING: Could not automatically choose board "
                        f"'{board_name}': {exc}"
                    )
                    print("Choose the board manually before continuing.")

            self._add_topic_tags(page, draft.topics)

            print("Pin form populated.")

            if self.dry_run:
                print("DRY RUN is enabled. The script will NOT click Publish.")
                print("Inspect the form. Press ENTER here to close the browser.")
                input()
                context.close()
                return False

            before_publish_url = page.url

            self._click_first(page, [
                'button:has-text("Publish")',
                '[data-test-id*="publish"]',
            ], "Publish button")

            print("Publish click sent. Waiting for Pinterest to finish publishing...")

            publish_confirmed = False

            # Pinterest can auto-save the editor as a draft while the Pin is
            # being created. Do not close Chrome immediately after clicking
            # Publish; wait for Pinterest to acknowledge completion so its
            # draft state has time to clear.
            success_texts = [
                "Your Pin was published",
                "Pin published",
                "Published",
                "Saved to",
            ]

            for _ in range(30):
                page.wait_for_timeout(500)

                if page.url != before_publish_url:
                    publish_confirmed = True
                    break

                for success_text in success_texts:
                    try:
                        notice = page.get_by_text(success_text, exact=False).first
                        if notice.count() > 0 and notice.is_visible():
                            publish_confirmed = True
                            break
                    except Exception:
                        pass

                if publish_confirmed:
                    break

            if publish_confirmed:
                print("Pinterest confirmed the publish.")
            else:
                print(
                    "WARNING: Pinterest did not show a publish confirmation "
                    "before the timeout. The Pin may still have published."
                )

            # Give Pinterest a final moment to finish server-side draft cleanup,
            # then leave the editor normally before closing the browser context.
            page.wait_for_timeout(2000)
            try:
                page.goto(
                    "https://www.pinterest.com/",
                    wait_until="domcontentloaded",
                    timeout=10000,
                )
                page.wait_for_timeout(1000)
            except Exception:
                pass

            context.close()
            return publish_confirmed
