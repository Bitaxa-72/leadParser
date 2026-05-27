from promotion_collector.contact_extractor import extract_contacts


def test_extract_contacts_finds_email_and_social_links() -> None:
    html = """
    <html>
      <head><title>Русское кафе в Нячанге</title></head>
      <body>
        <a href="mailto:hello@example.com">Email</a>
        <a href="https://t.me/example_channel?start=1">Telegram</a>
        <a href="/contacts">Contacts</a>
      </body>
    </html>
    """

    contacts = extract_contacts(html, "https://example.com")

    assert contacts.title == "Русское кафе в Нячанге"
    assert contacts.first_email() == "hello@example.com"
    assert contacts.first_social("telegram") == "https://t.me/example_channel"
    assert "https://example.com/contacts" in contacts.internal_links
