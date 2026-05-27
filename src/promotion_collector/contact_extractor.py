from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from promotion_collector.http_client import is_http_url


EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}(?![\w.-])")
SOCIAL_HOSTS = {
    "t.me": "telegram",
    "telegram.me": "telegram",
    "vk.com": "vk",
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "wa.me": "whatsapp",
    "api.whatsapp.com": "whatsapp",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
}
CONTACT_PATH_HINTS = ("contact", "contacts", "kontakty", "about", "o-nas", "contacts")


@dataclass(slots=True)
class ExtractedContacts:
    emails: set[str] = field(default_factory=set)
    social_links: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    internal_links: set[str] = field(default_factory=set)
    title: str = ""
    text_excerpt: str = ""

    def first_email(self) -> str:
        return sorted(self.emails)[0] if self.emails else ""

    def first_social(self, network: str) -> str:
        values = self.social_links.get(network) or set()
        return sorted(values)[0] if values else ""

    def other_social(self) -> str:
        known = set(SOCIAL_HOSTS.values())
        values: list[str] = []
        for network, links in self.social_links.items():
            if network not in known:
                values.extend(sorted(links))
        return ", ".join(values)


def extract_contacts(html: str, base_url: str) -> ExtractedContacts:
    soup = BeautifulSoup(html, "html.parser")
    result = ExtractedContacts()

    if soup.title and soup.title.string:
        result.title = soup.title.string.strip()

    visible_text = soup.get_text(" ", strip=True)
    result.text_excerpt = visible_text[:1500]
    result.emails.update(_clean_email(email) for email in EMAIL_RE.findall(unescape(html)))

    base_domain = urlparse(base_url).netloc.lower()
    for tag in soup.find_all("a", href=True):
        href = str(tag["href"]).strip()
        if href.startswith("mailto:"):
            email = href.split(":", 1)[1].split("?", 1)[0]
            result.emails.add(_clean_email(email))
            continue

        absolute_url = urljoin(base_url, href)
        if not is_http_url(absolute_url):
            continue

        parsed = urlparse(absolute_url)
        host = parsed.netloc.lower().removeprefix("www.")
        network = _network_for_host(host)
        if network:
            result.social_links[network].add(_strip_tracking(absolute_url))
        elif host == base_domain.removeprefix("www."):
            if _looks_like_contact_page(parsed.path):
                result.internal_links.add(_strip_tracking(absolute_url))

    result.emails = {email for email in result.emails if email}
    return result


def _clean_email(email: str) -> str:
    return email.strip().strip(".,;:)(").lower()


def _network_for_host(host: str) -> str:
    for social_host, network in SOCIAL_HOSTS.items():
        if host == social_host or host.endswith(f".{social_host}"):
            return network
    return ""


def _looks_like_contact_page(path: str) -> bool:
    normalized = path.strip("/").casefold()
    return any(hint in normalized for hint in CONTACT_PATH_HINTS)


def _strip_tracking(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()
