"""
Example usage of CDP MAX

This shows how to use the production-grade CDP client with all MAX features.
"""

from .client import CDPClientMAX, CDPClientConfig
from .waits import WaitCondition, ConditionType
from .actions import Postcondition, IdempotentGuard
from .observability import ReasonCode


def example_basic_usage():
    """Basic usage example"""
    # Create client with configuration
    config = CDPClientConfig(
        remote_port=9222,  # From Hidemium browser
        step_timeout_ms=10000,
        state_timeout_ms=30000,
        enable_recovery=True,
        enable_watchdog=True
    )

    client = CDPClientMAX(config)

    # Connect
    success, reason = client.connect()
    if not success:
        print(f"Connection failed: {reason}")
        return

    try:
        # Navigate to page
        nav_result = client.navigate("https://facebook.com/groups/example")

        if not nav_result.success:
            print(f"Navigation failed: {nav_result.error}")
            return

        # Wait for page to be ready
        client.wait_for_network_idle()

        # Find and click button using semantic locator (priority 1)
        write_button = client.by_aria_label("Viết gì đó")
        click_result = client.click(write_button)

        if not click_result.success:
            # Try alternative locator
            write_button = client.by_text("Viết gì đó")
            click_result = client.click(write_button)

        # Type content
        textarea = client.by_css('[role="textbox"][contenteditable="true"]')
        type_result = client.type_text(textarea, "Hello World!")

        # Click post button with postcondition
        post_button = client.by_aria_label("Đăng")
        click_result = client.click(
            post_button,
            postcondition=Postcondition(
                check=lambda: not client.is_visible(textarea),
                description="Post dialog should close",
                timeout_ms=10000
            )
        )

    finally:
        client.close()


def example_with_recovery():
    """Example with recovery handling"""
    config = CDPClientConfig(
        remote_port=9222,
        enable_recovery=True,
        max_step_retries=3
    )

    client = CDPClientMAX(config)
    success, _ = client.connect()

    if not success:
        return

    try:
        # Start job tracking
        client.start_job("like_post_001", "like_post", {
            'post_url': 'https://facebook.com/post/123'
        })

        # Use with_recovery for automatic retry on failure
        success, result, reason = client.with_recovery(
            lambda: client.click(client.by_aria_label("Like")),
            current_state="ACTION_EXECUTE"
        )

        if not success:
            print(f"Action failed after recovery: {reason}")

        # End job
        client.end_job(success, reason)

    finally:
        client.close()


def example_idempotent_action():
    """Example with idempotent guard"""
    config = CDPClientConfig(remote_port=9222)
    client = CDPClientMAX(config)
    success, _ = client.connect()

    if not success:
        return

    try:
        # Like button - idempotent (clicking twice shouldn't break)
        like_button = client.by_aria_label("Like")

        # Guard checks if already liked
        already_liked_guard = IdempotentGuard(
            check_fn=lambda: client.exists(client.by_aria_label("Unlike")),
            description="Post already liked"
        )

        result = client.click(
            like_button,
            idempotent_guard=already_liked_guard
        )

        if result.reason and result.reason.code == ReasonCode.SKIPPED_IDEMPOTENT:
            print("Action skipped - already done")
        elif result.success:
            print("Like successful")
        else:
            print(f"Like failed: {result.error}")

    finally:
        client.close()


def example_spa_navigation():
    """Example handling SPA navigation"""
    config = CDPClientConfig(remote_port=9222)
    client = CDPClientMAX(config)
    success, _ = client.connect()

    if not success:
        return

    try:
        # SPA-aware navigation
        nav_result = client.navigate_spa(
            action=lambda: client.click(client.by_text("Groups")),
            url_pattern="/groups",
            timeout_ms=30000
        )

        if nav_result.is_spa:
            print("SPA navigation detected")

        # Wait for SPA content to load
        client.wait_for_network_idle()

    finally:
        client.close()


def example_file_upload():
    """Example file upload with verification"""
    config = CDPClientConfig(remote_port=9222)
    client = CDPClientMAX(config)
    success, _ = client.connect()

    if not success:
        return

    try:
        # Upload file
        file_input = client.by_css('input[type="file"]')
        upload_result = client.upload_file(
            file_input,
            "/path/to/image.jpg",
            verify_preview=True
        )

        if upload_result.success:
            if upload_result.preview_verified:
                print("Upload successful with preview")
            else:
                print("Upload successful but preview not verified")
        else:
            print(f"Upload failed: {upload_result.error}")

    finally:
        client.close()


def example_diagnostics():
    """Example getting diagnostics"""
    config = CDPClientConfig(remote_port=9222)
    client = CDPClientMAX(config)
    success, _ = client.connect()

    if not success:
        return

    try:
        # Get health status
        health = client.get_health()

        print("Session status:", health['session']['state'])
        print("Targets:", health['targets']['total_targets'])
        print("Cache hits:", health['performance']['cache_hit_rate'])

        if 'watchdog' in health:
            print("Healthy contexts:", health['watchdog']['healthy'])

    finally:
        client.close()


# Locator priority examples
def locator_examples():
    """
    Locator priority examples

    Priority 1: Semantic/ARIA (most stable)
    - by_role("button", "Submit")
    - by_aria_label("Submit form")

    Priority 2: Test IDs
    - by_test_id("submit-btn")

    Priority 3: Text (within scope)
    - by_text("Submit")
    - by_placeholder("Enter email")

    Priority 4: CSS/XPath (last resort)
    - by_css(".submit-button")
    - by_xpath("//button[@type='submit']")
    """
    pass
