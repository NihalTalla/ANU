import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

_WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_QUERY_STOPWORDS = {
    "a", "about", "ago", "all", "am", "an", "and", "any", "are", "be", "can", "check",
    "conversation", "conversations", "could", "day", "days", "did", "do", "for",
    "from", "get", "give", "had", "have", "i", "in", "is", "it", "last", "me",
    "memory", "month", "months", "my", "note", "notes", "of", "on", "our", "please",
    "recall", "remember", "said", "search", "show", "tell", "that", "the", "this",
    "to", "today", "told", "want", "was", "week", "weeks", "what", "when", "where",
    "which", "who", "with", "yesterday", "you",
}


def _default_vault_path() -> Path:
    env_path = os.getenv("ANU_NOTES_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / "Documents" / "ANU-Notes"


def _ensure_vault() -> Path:
    vault = _default_vault_path()
    vault.mkdir(parents=True, exist_ok=True)
    return vault


def _sanitize_filename(name: str, default_name: str = "note") -> str:
    cleaned = (name or "").strip()
    cleaned = re.sub(r"[<>:\"/\\|?*]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = default_name
    return cleaned


def _slugify(name: str) -> str:
    cleaned = _sanitize_filename(name)
    slug = re.sub(r"\s+", "_", cleaned.strip())
    return slug or "note"


def _safe_path(vault: Path, relative_path: str) -> Path:
    rel = (relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        raise ValueError("No path provided.")

    target = (vault / rel).resolve()
    vault_resolved = vault.resolve()

    if target != vault_resolved and vault_resolved not in target.parents:
        raise ValueError("Path must stay inside the notes vault.")

    return target


def _note_from_title(vault: Path, title: str, folder: str = "Inbox") -> Path:
    safe_folder = _sanitize_filename(folder or "Inbox", "Inbox")
    filename = _slugify(title) + ".md"
    rel = f"{safe_folder}/{filename}"
    return _safe_path(vault, rel)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)


def _create_note(vault: Path, title: str, content: str = "", folder: str = "Inbox") -> str:
    if not title:
        return "Please provide a note title."

    note_path = _note_from_title(vault, title, folder)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if note_path.exists():
        return f"Note already exists: {note_path.relative_to(vault)}"

    body = f"# {title.strip()}\n\n"
    body += f"Created: {timestamp}\n\n"
    if content:
        body += content.strip() + "\n"

    _write_text(note_path, body)
    return f"Note created: {note_path.relative_to(vault)}"


def _append_note(vault: Path, note: str, content: str) -> str:
    if not note:
        return "Please provide a note path."
    if not content:
        return "Please provide content to append."

    note_path = _safe_path(vault, note)
    if not note_path.exists():
        return f"Note not found: {note_path.relative_to(vault)}"

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chunk = f"\n\n---\n{stamp}\n{content.strip()}\n"
    _append_text(note_path, chunk)
    return f"Appended to: {note_path.relative_to(vault)}"


def _read_note(vault: Path, note: str, max_chars: int = 4000) -> str:
    if not note:
        return "Please provide a note path."

    note_path = _safe_path(vault, note)
    if not note_path.exists():
        return f"Note not found: {note_path.relative_to(vault)}"

    text = _read_text(note_path)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n... (truncated, {len(text)} chars total)"
    return text


def _search_notes(vault: Path, query: str, max_results: int = 10) -> str:
    if not query:
        return "Please provide a search query."

    q = query.lower().strip()
    results = []

    for path in vault.rglob("*.md"):
        try:
            rel = str(path.relative_to(vault))
            name_match = q in path.name.lower()
            content_match = False
            snippet = ""

            if not name_match:
                text = _read_text(path)
                idx = text.lower().find(q)
                if idx >= 0:
                    content_match = True
                    start = max(0, idx - 60)
                    end = min(len(text), idx + 120)
                    snippet = text[start:end].replace("\n", " ").strip()

            if name_match or content_match:
                if snippet:
                    results.append(f"- {rel} :: {snippet}")
                else:
                    results.append(f"- {rel}")

            if len(results) >= max_results:
                break
        except Exception:
            continue

    if not results:
        return f"No notes found for: {query}"

    return "Search results:\n" + "\n".join(results)


def _daily_note(vault: Path, content: str = "", folder: str = "Daily") -> str:
    folder_safe = _sanitize_filename(folder or "Daily", "Daily")
    filename = datetime.now().strftime("%Y-%m-%d") + ".md"
    note_path = _safe_path(vault, f"{folder_safe}/{filename}")

    if not note_path.exists():
        heading = datetime.now().strftime("# Daily Note — %Y-%m-%d\n\n")
        _write_text(note_path, heading)

    if content:
        stamp = datetime.now().strftime("%H:%M")
        _append_text(note_path, f"- [{stamp}] {content.strip()}\n")

    return f"Daily note ready: {note_path.relative_to(vault)}"


def _list_notes(vault: Path, folder: str = "") -> str:
    if folder:
        base = _safe_path(vault, folder)
        if not base.exists() or not base.is_dir():
            return f"Folder not found: {folder}"
    else:
        base = vault

    notes = sorted(base.rglob("*.md"))
    if not notes:
        return "No notes found."

    lines = [f"Found {len(notes)} notes:"]
    for p in notes[:30]:
        lines.append(f"- {p.relative_to(vault)}")

    if len(notes) > 30:
        lines.append(f"... and {len(notes) - 30} more")

    return "\n".join(lines)


def _parse_date_from_daily_file(path: Path) -> date | None:
    try:
        return datetime.strptime(path.stem, "%Y-%m-%d").date()
    except Exception:
        return None


def _words_to_number(text: str) -> int | None:
    words = re.findall(r"[a-z]+", (text or "").lower())
    if not words:
        return None

    total = 0
    current = 0
    matched = False

    for word in words:
        if word not in _NUMBER_WORDS:
            if matched:
                break
            continue

        matched = True
        value = _NUMBER_WORDS[word]
        if value == 100:
            current = max(1, current) * value
        else:
            current += value

    if not matched:
        return None

    total += current
    return total or None


def _extract_day_count(text: str) -> int | None:
    raw = (text or "").strip().lower()

    m_digits = re.search(r"(\d{1,3})\s*days?", raw)
    if m_digits:
        return max(1, int(m_digits.group(1)))

    m_words = re.search(r"([a-z\s-]+?)\s+days?", raw)
    if m_words:
        return _words_to_number(m_words.group(1))

    return None


def _resolve_time_window(when: str) -> tuple[date | None, date | None, str]:
    today = datetime.now().date()
    text = (when or "").strip().lower()

    if not text or text in {"all", "anytime", "ever"}:
        return None, None, "all time"

    if "today" in text:
        return today, today, "today"

    m_weekday = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text)
    if m_weekday:
        weekday_name = m_weekday.group(1)
        target_idx = _WEEKDAY_INDEX[weekday_name]
        days_back = (today.weekday() - target_idx) % 7
        target_date = today - timedelta(days=days_back)
        return target_date, target_date, target_date.isoformat()

    if "day before yesterday" in text:
        d = today - timedelta(days=2)
        return d, d, "2 days ago"

    if "yesterday" in text:
        d = today - timedelta(days=1)
        return d, d, "yesterday"

    if "last week" in text or "one week" in text or "past week" in text:
        start = today - timedelta(days=7)
        return start, today, "last 7 days"

    if "last month" in text or "one month" in text or "past month" in text:
        start = today - timedelta(days=30)
        return start, today, "last 30 days"

    day_count = _extract_day_count(text)
    if day_count is not None:
        if "ago" in text:
            d = today - timedelta(days=day_count)
            label = "yesterday" if day_count == 1 else f"{day_count} days ago"
            return d, d, label

        start = today - timedelta(days=day_count)
        return start, today, f"last {day_count} days"

    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m_date:
        try:
            d = datetime.strptime(m_date.group(1), "%Y-%m-%d").date()
            return d, d, m_date.group(1)
        except Exception:
            pass

    m_day_of_month = re.search(r"\b(?:on\s+)?(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\b", text)
    if m_day_of_month:
        try:
            day = int(m_day_of_month.group(1))
            if 1 <= day <= 31:
                year = today.year
                month = today.month
                if day > today.day:
                    month -= 1
                    if month == 0:
                        month = 12
                        year -= 1
                d = date(year, month, day)
                return d, d, d.isoformat()
        except Exception:
            pass

    # Fallback: all time if we can't parse user phrase.
    return None, None, "all time"


def _query_keywords(query: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9]+", (query or "").lower())
    return [
        token for token in raw_tokens
        if len(token) >= 2 and token not in _QUERY_STOPWORDS
    ]


def _matches_recall_query(line: str, query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True

    line_lower = line.lower()
    if q in line_lower:
        return True

    keywords = _query_keywords(q)
    if not keywords:
        return True

    hits = sum(1 for token in keywords if token in line_lower)
    if hits == len(keywords):
        return True
    if len(keywords) >= 3 and hits >= 2:
        return True
    if len(keywords) == 1 and hits >= 1:
        return True
    return False


def _recall_memory(
    vault: Path,
    when: str = "",
    query: str = "",
    max_entries: int = 80,
    folder: str = "",
) -> str:
    recall_folder = _sanitize_filename(folder or os.getenv("ANU_NOTES_LOG_FOLDER", "Daily"), "Daily")
    daily_dir = vault / recall_folder
    if not daily_dir.exists() or not daily_dir.is_dir():
        return f"No daily memory logs found yet in {recall_folder}."

    start_date, end_date, label = _resolve_time_window(when)
    q = (query or "").strip()

    files = sorted(daily_dir.glob("*.md"), reverse=True)
    matched_lines = []
    matched_files = 0

    for file_path in files:
        d = _parse_date_from_daily_file(file_path)
        if d is None:
            continue

        if start_date and d < start_date:
            continue
        if end_date and d > end_date:
            continue

        text = _read_text(file_path)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("-")]
        file_had_match = False

        for ln in lines:
            if not _matches_recall_query(ln, q):
                continue
            matched_lines.append(f"{file_path.stem}: {ln}")
            file_had_match = True
            if len(matched_lines) >= max_entries:
                break

        if file_had_match:
            matched_files += 1

        if len(matched_lines) >= max_entries:
            break

    if not matched_lines:
        if q:
            return f"No memory entries found for '{query}' in {label}."
        return f"No memory entries found in {label}."

    header = f"Memory recall ({label}) — {matched_files} day(s), {len(matched_lines)} item(s):"
    return header + "\n" + "\n".join(f"- {ln}" for ln in matched_lines)


def _open_note(vault: Path, note: str) -> str:
    if not note:
        return "Please provide a note path."

    note_path = _safe_path(vault, note)
    if not note_path.exists():
        return f"Note not found: {note_path.relative_to(vault)}"

    try:
        if os.name == "nt":
            os.startfile(str(note_path))
        else:
            import subprocess
            import sys
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(note_path)])
            else:
                subprocess.Popen(["xdg-open", str(note_path)])
        return f"Opened note: {note_path.relative_to(vault)}"
    except Exception as e:
        return f"Could not open note: {e}"


def notes_vault_action(parameters: dict, response=None, player=None, session_memory=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "")).strip().lower()

    vault = _ensure_vault()
    result = "Unknown notes action."

    try:
        if action == "create":
            result = _create_note(
                vault=vault,
                title=str(params.get("title", "")).strip(),
                content=str(params.get("content", "")).strip(),
                folder=str(params.get("folder", "Inbox")).strip() or "Inbox",
            )

        elif action == "append":
            result = _append_note(
                vault=vault,
                note=str(params.get("note", "")).strip(),
                content=str(params.get("content", "")).strip(),
            )

        elif action == "read":
            result = _read_note(
                vault=vault,
                note=str(params.get("note", "")).strip(),
                max_chars=int(params.get("max_chars", 4000) or 4000),
            )

        elif action == "search":
            result = _search_notes(
                vault=vault,
                query=str(params.get("query", "")).strip(),
                max_results=int(params.get("max_results", 10) or 10),
            )

        elif action == "recall":
            result = _recall_memory(
                vault=vault,
                when=str(params.get("when", "")).strip(),
                query=str(params.get("query", "")).strip(),
                max_entries=int(params.get("max_entries", 80) or 80),
            )

        elif action == "daily":
            result = _daily_note(
                vault=vault,
                content=str(params.get("content", "")).strip(),
                folder=str(params.get("folder", "Daily")).strip() or "Daily",
            )

        elif action == "list":
            result = _list_notes(
                vault=vault,
                folder=str(params.get("folder", "")).strip(),
            )

        elif action == "open":
            result = _open_note(
                vault=vault,
                note=str(params.get("note", "")).strip(),
            )

        else:
            result = (
                "Unknown action. Use: create, append, read, search, recall, daily, list, open."
            )

    except Exception as e:
        result = f"Notes vault error: {e}"

    if player:
        player.write_log(f"[notes] {result[:120]}")

    return result
