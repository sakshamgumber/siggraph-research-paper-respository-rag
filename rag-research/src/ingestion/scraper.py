from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

_log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
MANIFEST_DIR = Path(__file__).resolve().parents[2] / "data" / "manifests"

DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "research_chunks_jina_v5")
CROSSREF_WORKS_URL = "https://api.crossref.org/works"
ACM_TOG_ISSN = "0730-0301"
DEFAULT_USER_AGENT = "SIGGRAPHResearchEngine/1.0 (mailto:researcher@siggraph-engine.org; https://github.com/)"


def sanitize_filename(name: str) -> str:
    """Sanitize string for filesystem paths."""
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", name).strip("_")
    return sanitized or "paper"


def get_disk_free_gb(path: str | Path | None = None) -> float:
    """Return free disk space in Gigabytes for the specified path."""
    target_path = Path(path or RAW_DIR)
    target_path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(target_path)
    return usage.free / (1024**3)


# ==============================================================================
# Phase 1: Metadata Harvesting
# ==============================================================================


def _resolve_arxiv_pdf_by_title(title: str) -> str | None:
    """Resolve an academic paper title to an open-access arXiv PDF URL."""
    if not title or len(title.strip()) < 5:
        return None
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    clean_title = urllib.parse.quote(f'ti:"{title.strip()}"')
    url = f"http://export.arxiv.org/api/query?search_query={clean_title}&max_results=1"
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is not None:
                for l in entry.findall("atom:link", ns):
                    if l.attrib.get("title") == "pdf":
                        return l.attrib.get("href")
    except Exception:
        pass
    return None


def harvest_arxiv_metadata(
    *,
    limit: int = 100,
    search_query: str = "cat:cs.GR AND (all:SIGGRAPH OR all:TOG)",
    output_manifest: str | Path | None = None,
    batch_size: int = 50,
) -> Path:
    """Harvest open-access computer graphics and SIGGRAPH paper metadata from arXiv."""
    manifest_path = Path(output_manifest or (MANIFEST_DIR / "siggraph_metadata.jsonl"))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    existing_ids: set[str] = set()
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "paper_id" in record:
                            existing_ids.add(record["paper_id"])
                    except Exception:
                        continue

    total_harvested = 0
    start = 0

    _log.info("Starting arXiv harvest for query '%s' (target: %d new papers). Existing in manifest: %d", search_query, limit, len(existing_ids))

    with manifest_path.open("a", encoding="utf-8") as outfile:
        while total_harvested < limit:
            current_batch = min(batch_size, limit - total_harvested)
            encoded_query = urllib.parse.quote(search_query)
            url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start={start}&max_results={current_batch}"
            req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    root = ET.fromstring(resp.read())
                    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
                    entries = root.findall("atom:entry", ns)

                    if not entries:
                        break

                    for e in entries:
                        raw_id = e.find("atom:id", ns).text.split("/abs/")[-1].strip()
                        paper_id = sanitize_filename(raw_id)
                        if paper_id in existing_ids:
                            continue

                        title = e.find("atom:title", ns).text.strip().replace("\n", " ")
                        authors = [a.find("atom:name", ns).text.strip() for a in e.findall("atom:author", ns)]
                        published = e.find("atom:published", ns).text[:4]
                        year = int(published) if published.isdigit() else None
                        summary_elem = e.find("atom:summary", ns)
                        summary = summary_elem.text.strip() if summary_elem is not None else ""

                        comment_elem = e.find("arxiv:comment", ns)
                        comment = comment_elem.text.strip().replace("\n", " ") if comment_elem is not None and comment_elem.text else ""

                        journal_elem = e.find("arxiv:journal_ref", ns)
                        journal_ref = journal_elem.text.strip().replace("\n", " ") if journal_elem is not None and journal_elem.text else ""

                        venue = journal_ref or comment or "ACM SIGGRAPH / TOG (arXiv cs.GR)"

                        pdf_url = f"https://arxiv.org/pdf/{raw_id}.pdf"
                        doi = f"arxiv:{raw_id}"

                        record = {
                            "paper_id": paper_id,
                            "doi": doi,
                            "title": title,
                            "authors": authors,
                            "year": year,
                            "volume": None,
                            "issue": None,
                            "venue": venue,
                            "comment": comment,
                            "journal_ref": journal_ref,
                            "abstract": summary,
                            "pdf_url": pdf_url,
                            "acm_url": f"https://arxiv.org/abs/{raw_id}",
                        }

                        outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                        outfile.flush()
                        existing_ids.add(paper_id)
                        total_harvested += 1

                        if total_harvested >= limit:
                            break

                    start += len(entries)
                    _log.info("Harvested %d arXiv papers so far...", total_harvested)
                    time.sleep(1.0)
            except Exception as exc:
                _log.error("arXiv harvesting error: %s", exc)
                break

    _log.info("Harvested %d arXiv papers into %s", total_harvested, manifest_path)
    return manifest_path


def harvest_metadata(
    *,
    start_year: int = 2002,
    end_year: int = 2026,
    limit: int = 3000,
    issn: str = ACM_TOG_ISSN,
    source: str = "arxiv",
    output_manifest: str | Path | None = None,
    mailto: str = "researcher@siggraph-engine.org",
    rows_per_page: int = 100,
    query: str | None = None,
) -> Path:
    """Harvest paper metadata for SIGGRAPH / TOG papers.

    Args:
        start_year: Beginning publication year.
        end_year: Ending publication year.
        limit: Maximum total papers to harvest metadata for.
        issn: Journal ISSN for Crossref.
        source: 'arxiv' (direct open-access PDFs) or 'crossref' (official DOI index).
        output_manifest: Filepath to store the JSONL metadata manifest.
        mailto: Contact email for Crossref polite pool.
        rows_per_page: Number of records per API page.
        query: Custom query string for arXiv search.
    """
    if source == "arxiv":
        kwargs: dict[str, Any] = {"limit": limit, "output_manifest": output_manifest}
        if query:
            kwargs["search_query"] = query
        return harvest_arxiv_metadata(**kwargs)

    manifest_path = Path(output_manifest or (MANIFEST_DIR / "siggraph_metadata.jsonl"))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": f"SIGGRAPHResearchEngine/1.0 (mailto:{mailto})",
    }

    session = requests.Session()
    cursor = "*"
    total_harvested = 0

    # Load existing DOIs to avoid duplicates if re-running
    existing_dois: set[str] = set()
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "doi" in record:
                            existing_dois.add(record["doi"].lower())
                    except json.JSONDecodeError:
                        continue

    _log.info(
        "Starting Crossref harvest for ISSN %s (years %d-%d, target limit: %d). Existing records: %d",
        issn,
        start_year,
        end_year,
        limit,
        len(existing_dois),
    )

    with manifest_path.open("a", encoding="utf-8") as outfile:
        while total_harvested < limit:
            params = {
                "filter": f"issn:{issn},from-pub-date:{start_year}-01-01,until-pub-date:{end_year}-12-31",
                "rows": min(rows_per_page, limit - total_harvested),
                "cursor": cursor,
                "mailto": mailto,
                "select": "DOI,title,author,issued,volume,issue,page,link,abstract,URL",
            }

            try:
                response = session.get(
                    CROSSREF_WORKS_URL,
                    params=params,
                    headers=headers,
                    timeout=30.0,
                )
                if response.status_code == 429:
                    _log.warning("Crossref rate limit hit. Waiting 5 seconds...")
                    time.sleep(5.0)
                    continue

                if response.status_code != 200:
                    _log.error("Crossref request failed (HTTP %d): %s", response.status_code, response.text)
                    break

                data = response.json().get("message", {})
                items = data.get("items", [])
                next_cursor = data.get("next-cursor")

                if not items:
                    _log.info("No more items returned by Crossref.")
                    break

                for item in items:
                    doi = item.get("DOI", "").strip()
                    if not doi or doi.lower() in existing_dois:
                        continue

                    raw_titles = item.get("title", [])
                    title = raw_titles[0].strip() if raw_titles else "Untitled Paper"

                    # Format authors
                    authors: list[str] = []
                    for auth in item.get("author", []):
                        given = auth.get("given", "").strip()
                        family = auth.get("family", "").strip()
                        name = f"{given} {family}".strip()
                        if name:
                            authors.append(name)

                    # Extract year
                    date_parts = item.get("issued", {}).get("date-parts", [[]])[0]
                    year = date_parts[0] if date_parts else None

                    volume = item.get("volume")
                    issue = item.get("issue")

                    # Primary PDF direct link on ACM DL Open Access
                    # Format: https://dl.acm.org/doi/pdf/{doi}
                    pdf_url = f"https://dl.acm.org/doi/pdf/{doi}"

                    # Clean paper ID from DOI (e.g. 10.1145/3528223.3530123 -> 3528223.3530123)
                    paper_id = doi.split("/")[-1] if "/" in doi else doi
                    paper_id = sanitize_filename(paper_id)

                    metadata_record = {
                        "paper_id": paper_id,
                        "doi": doi,
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "volume": volume,
                        "issue": issue,
                        "venue": f"ACM Transactions on Graphics (TOG)",
                        "abstract": item.get("abstract"),
                        "pdf_url": pdf_url,
                        "acm_url": item.get("URL", f"https://doi.org/{doi}"),
                    }

                    outfile.write(json.dumps(metadata_record, ensure_ascii=False) + "\n")
                    outfile.flush()
                    existing_dois.add(doi.lower())
                    total_harvested += 1

                    if total_harvested >= limit:
                        break

                _log.info("Harvested %d papers so far...", total_harvested)

                if not next_cursor or next_cursor == cursor:
                    break
                cursor = next_cursor

                # Polite delay between pagination calls
                time.sleep(0.3)

            except Exception as exc:
                _log.error("Error during Crossref harvesting: %s", exc)
                time.sleep(2.0)
                break

    _log.info("Metadata harvesting completed. Manifest saved to %s (Total records: %d)", manifest_path, total_harvested)
    return manifest_path


# ==============================================================================
# Phase 2: Multithreaded Resilient Downloader
# ==============================================================================


class DownloadManager:
    """Thread-safe download manager with progress tracking, jitter delay, and magic-byte validation."""

    def __init__(
        self,
        manifest_path: str | Path,
        raw_dir: str | Path = RAW_DIR,
        state_file: str | Path | None = None,
        max_workers: int = 5,
        min_delay: float = 0.3,
        max_delay: float = 0.8,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file or (self.raw_dir.parent / "manifests" / "download_manifest.json"))
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.user_agent = user_agent

        self._lock = threading.Lock()
        self.state: dict[str, dict[str, Any]] = self._load_state()

    def _load_state(self) -> dict[str, dict[str, Any]]:
        if self.state_file.exists():
            try:
                with self.state_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self) -> None:
        with self._lock:
            with self.state_file.open("w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

    def is_paper_downloaded(self, paper_id: str) -> bool:
        """Check if paper is already downloaded and verified on disk."""
        target_path = self.raw_dir / f"{paper_id}.pdf"
        if not target_path.exists() or target_path.stat().st_size < 10:
            return False
        # Fast magic byte verification
        try:
            with target_path.open("rb") as f:
                return f.read(5).startswith(b"%PDF-")
        except Exception:
            return False

    def download_single_paper(
        self,
        record: dict[str, Any],
        session: requests.Session,
    ) -> tuple[str, bool, str]:
        """Worker function to download a single paper.

        Returns:
            Tuple of (paper_id, success, message).
        """
        paper_id = record.get("paper_id")
        if not paper_id:
            return "unknown", False, "Missing paper_id"

        target_file = self.raw_dir / f"{paper_id}.pdf"
        part_file = self.raw_dir / f"{paper_id}.pdf.part"

        # Check existing verified file
        if self.is_paper_downloaded(paper_id):
            with self._lock:
                self.state[paper_id] = {
                    "status": "downloaded",
                    "file": str(target_file),
                    "size_bytes": target_file.stat().st_size,
                }
            return paper_id, True, "Already downloaded and verified"

        # Polite jitter delay before request
        time.sleep(random.uniform(self.min_delay, self.max_delay))

        pdf_url = record.get("pdf_url")
        doi = record.get("doi")
        if not pdf_url and doi:
            pdf_url = f"https://dl.acm.org/doi/pdf/{doi}"

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/pdf,application/octet-stream,*/*",
        }

        try:
            response = session.get(pdf_url, headers=headers, stream=True, timeout=45.0, allow_redirects=True)

            if response.status_code != 200 or not response.headers.get("content-type", "").lower().startswith("application/pdf"):
                # Try arXiv open-access fallback by title
                arxiv_url = _resolve_arxiv_pdf_by_title(record.get("title", ""))
                if arxiv_url and arxiv_url != pdf_url:
                    _log.info("Primary URL failed (HTTP %s); retrying via open-access arXiv: %s", response.status_code, arxiv_url)
                    response = session.get(arxiv_url, headers=headers, stream=True, timeout=45.0, allow_redirects=True)

            if response.status_code != 200:
                with self._lock:
                    self.state[paper_id] = {
                        "status": "failed",
                        "error": f"HTTP {response.status_code}",
                        "url": pdf_url,
                    }
                return paper_id, False, f"HTTP {response.status_code}"

            # Stream response chunks to part_file and verify magic bytes
            with part_file.open("wb") as out_f:
                is_first_chunk = True
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    if is_first_chunk:
                        is_first_chunk = False
                        if not chunk.startswith(b"%PDF-"):
                            # Try one last arXiv fallback if not tried yet
                            arxiv_url = _resolve_arxiv_pdf_by_title(record.get("title", ""))
                            if arxiv_url and arxiv_url != pdf_url:
                                part_file.unlink(missing_ok=True)
                                _log.info("Non-PDF response; retrying via open-access arXiv: %s", arxiv_url)
                                response = session.get(arxiv_url, headers=headers, stream=True, timeout=45.0, allow_redirects=True)
                                for c2 in response.iter_content(chunk_size=64 * 1024):
                                    if c2:
                                        out_f.write(c2)
                                break
                            else:
                                part_file.unlink(missing_ok=True)
                                with self._lock:
                                    self.state[paper_id] = {
                                        "status": "failed",
                                        "error": "Invalid magic bytes (not a PDF stream)",
                                        "url": pdf_url,
                                    }
                                return paper_id, False, "Not a valid PDF (HTML error or challenge page received)"
                    out_f.write(chunk)

            # Atomic rename from part_file to target_file
            part_file.replace(target_file)
            size = target_file.stat().st_size

            with self._lock:
                self.state[paper_id] = {
                    "status": "downloaded",
                    "file": str(target_file),
                    "size_bytes": size,
                    "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            return paper_id, True, f"Successfully downloaded ({size / (1024*1024):.1f} MB)"

        except Exception as exc:
            part_file.unlink(missing_ok=True)
            with self._lock:
                self.state[paper_id] = {
                    "status": "failed",
                    "error": str(exc),
                    "url": pdf_url,
                }
            return paper_id, False, str(exc)

    def download_batch(
        self,
        records: list[dict[str, Any]],
    ) -> list[tuple[str, bool, str]]:
        """Download a batch of paper records in parallel using ThreadPoolExecutor."""
        results: list[tuple[str, bool, str]] = []

        with requests.Session() as session:
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=self.max_workers * 2,
                pool_maxsize=self.max_workers * 2,
            )
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_record = {
                    executor.submit(self.download_single_paper, rec, session): rec for rec in records
                }
                for future in as_completed(future_to_record):
                    try:
                        res = future.result()
                        results.append(res)
                    except Exception as exc:
                        rec = future_to_record[future]
                        results.append((rec.get("paper_id", "unknown"), False, str(exc)))

        self._save_state()
        return results


def download_papers(
    manifest_path: str | Path,
    raw_dir: str | Path = RAW_DIR,
    *,
    limit: int | None = None,
    max_workers: int = 5,
    min_delay: float = 0.3,
    max_delay: float = 0.8,
) -> int:
    """Download papers specified in manifest_path using multithreaded workers."""
    records: list[dict[str, Any]] = []
    with Path(manifest_path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if limit:
        records = records[:limit]

    manager = DownloadManager(
        manifest_path=manifest_path,
        raw_dir=raw_dir,
        max_workers=max_workers,
        min_delay=min_delay,
        max_delay=max_delay,
    )

    _log.info("Starting multithreaded download of %d papers with %d workers...", len(records), max_workers)
    results = manager.download_batch(records)

    success_count = sum(1 for _, success, _ in results if success)
    _log.info("Download finished. Successful: %d/%d", success_count, len(records))
    return success_count


# ==============================================================================
# Phase 3: Stream, Index & Purge Pipeline (Option 1 - Under 1 GB Disk Usage)
# ==============================================================================


def stream_pipeline(
    *,
    manifest_path: str | Path | None = None,
    batch_size: int = 25,
    max_workers: int = 5,
    total_limit: int = 3000,
    purge_raw: bool = True,
    collection_name: str = DEFAULT_COLLECTION,
    raw_dir: str | Path = RAW_DIR,
    processed_dir: str | Path = PROCESSED_DIR,
) -> int:
    """Stream-process papers in batches: download -> Docling chunk -> Qdrant Cloud index -> purge raw PDF.

    This ensures local disk usage never exceeds ~1 GB regardless of the number of papers processed.
    """
    from src.chunking.chunker import extract_pdf_chunks
    from src.retrieval.vector_search import index_chunks

    manifest_file = Path(manifest_path or (MANIFEST_DIR / "siggraph_metadata.jsonl"))
    if not manifest_file.exists():
        _log.info("Manifest %s not found. Harvesting metadata first...", manifest_file)
        manifest_file = harvest_metadata(limit=total_limit, output_manifest=manifest_file)

    raw_path = Path(raw_dir)
    proc_path = Path(processed_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    proc_path.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    with manifest_file.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    manager = DownloadManager(
        manifest_path=manifest_file,
        raw_dir=raw_path,
        max_workers=max_workers,
    )

    pending_records: list[dict[str, Any]] = []
    skipped_count = 0
    for rec in records:
        pid = rec.get("paper_id")
        chunk_path = proc_path / f"{pid}_chunks.jsonl"
        state_status = manager.state.get(pid, {}).get("status")
        if (chunk_path.exists() and chunk_path.stat().st_size > 0) or state_status == "indexed":
            skipped_count += 1
            continue
        pending_records.append(rec)

    if total_limit:
        pending_records = pending_records[:total_limit]

    total_indexed_papers = 0
    _log.info(
        "=== Starting Stream & Purge Pipeline: %d pending papers (%d already processed/skipped, batch size: %d, workers: %d, purge_raw: %s) ===",
        len(pending_records),
        skipped_count,
        batch_size,
        max_workers,
        purge_raw,
    )

    for i in range(0, len(pending_records), batch_size):
        batch_records = pending_records[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(pending_records) + batch_size - 1) // batch_size

        free_gb = get_disk_free_gb(raw_path)
        _log.info(
            "--- Processing Batch %d/%d (%d papers). Free Disk Space: %.2f GB ---",
            batch_num,
            total_batches,
            len(batch_records),
            free_gb,
        )

        if free_gb < 1.0:
            _log.error("Disk space dangerously low (%.2f GB < 1.0 GB). Pausing pipeline to avoid disk overflow!", free_gb)
            break

        # 1. Download batch in parallel
        download_results = manager.download_batch(batch_records)

        # 2. Process and index downloaded PDFs
        for rec in batch_records:
            paper_id = rec.get("paper_id")
            pdf_path = raw_path / f"{paper_id}.pdf"

            if not pdf_path.exists():
                continue

            try:
                # Docling HybridChunker
                chunk_file = extract_pdf_chunks(
                    pdf_path,
                    paper_id=paper_id,
                    title=rec.get("title"),
                    authors=rec.get("authors"),
                    year=rec.get("year"),
                    venue=rec.get("venue"),
                    out_dir=proc_path,
                    repeat_table_header=True,
                    omit_header_on_overflow=False,
                )

                if chunk_file and chunk_file.exists():
                    # Index into Qdrant Cloud cluster
                    indexed_count = index_chunks(
                        chunk_file,
                        collection_name=collection_name,
                        batch_size=16,
                        recreate=False,
                    )
                    total_indexed_papers += 1
                    with manager._lock:
                        if paper_id in manager.state:
                            manager.state[paper_id]["status"] = "indexed"
                            manager.state[paper_id]["chunks_indexed"] = indexed_count
                    manager._save_state()
                    _log.info(
                        "Indexed %d chunks for paper %s into Qdrant Cloud collection '%s'",
                        indexed_count,
                        paper_id,
                        collection_name,
                    )

                # 3. Purge raw PDF if requested to save disk space
                if purge_raw and pdf_path.exists():
                    size_mb = pdf_path.stat().st_size / (1024 * 1024)
                    pdf_path.unlink(missing_ok=True)
                    _log.debug("Purged raw PDF %s (freed %.1f MB)", pdf_path.name, size_mb)

            except Exception as exc:
                _log.error("Failed to process/index paper %s: %s", paper_id, exc)

        # Free PyTorch MPS / CPU memory cache after each batch to prevent macOS swapfile growth
        import gc
        gc.collect()
        try:
            import torch
            if hasattr(torch, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

        _log.info(
            "Batch %d/%d complete. Total indexed papers: %d. Free disk: %.2f GB",
            batch_num,
            total_batches,
            total_indexed_papers,
            get_disk_free_gb(raw_path),
        )

    _log.info("Stream pipeline finished. Total papers processed and indexed: %d", total_indexed_papers)
    return total_indexed_papers


# ==============================================================================
# CLI Arguments Parser
# ==============================================================================


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ACM SIGGRAPH & TOG Paper Scraper, Downloader & Stream Pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: harvest
    harvest_parser = subparsers.add_parser("harvest", help="Harvest metadata from Crossref API.")
    harvest_parser.add_argument("--start-year", type=int, default=2002)
    harvest_parser.add_argument("--end-year", type=int, default=2026)
    harvest_parser.add_argument("--limit", type=int, default=3000)
    harvest_parser.add_argument("--issn", default=ACM_TOG_ISSN)
    harvest_parser.add_argument("--source", choices=["arxiv", "crossref"], default="arxiv", help="Source for papers and open-access PDFs (default: arxiv).")
    harvest_parser.add_argument("--query", default=None, help="Custom arXiv search query string.")
    harvest_parser.add_argument("--output", type=Path, default=MANIFEST_DIR / "siggraph_metadata.jsonl")
    harvest_parser.add_argument("--mailto", default="researcher@siggraph-engine.org")

    # Subcommand: download
    download_parser = subparsers.add_parser("download", help="Download PDFs from harvested metadata manifest.")
    download_parser.add_argument("--manifest", type=Path, default=MANIFEST_DIR / "siggraph_metadata.jsonl")
    download_parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    download_parser.add_argument("--limit", type=int, default=None)
    download_parser.add_argument("--workers", type=int, default=5, help="Number of concurrent download threads.")
    download_parser.add_argument("--min-delay", type=float, default=0.3)
    download_parser.add_argument("--max-delay", type=float, default=0.8)

    # Subcommand: stream
    stream_parser = subparsers.add_parser(
        "stream",
        help="Stream pipeline: download batch -> Docling chunk -> Qdrant Cloud index -> purge raw PDF.",
    )
    stream_parser.add_argument("--manifest", type=Path, default=MANIFEST_DIR / "siggraph_metadata.jsonl")
    stream_parser.add_argument("--batch-size", type=int, default=25)
    stream_parser.add_argument("--workers", type=int, default=5)
    stream_parser.add_argument("--limit", type=int, default=3000)
    stream_parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    stream_parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    stream_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    stream_parser.add_argument(
        "--purge-raw",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete raw PDF after successful Qdrant indexing to keep disk usage under 1 GB (default: True).",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    args = _parse_args()

    if args.command == "harvest":
        out = harvest_metadata(
            start_year=args.start_year,
            end_year=args.end_year,
            limit=args.limit,
            issn=args.issn,
            source=args.source,
            output_manifest=args.output,
            mailto=args.mailto,
            query=args.query,
        )
        print(f"Metadata harvest complete! Output: {out}")

    elif args.command == "download":
        count = download_papers(
            manifest_path=args.manifest,
            raw_dir=args.raw_dir,
            limit=args.limit,
            max_workers=args.workers,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
        )
        print(f"Downloaded {count} papers into {args.raw_dir}")

    elif args.command == "stream":
        indexed = stream_pipeline(
            manifest_path=args.manifest,
            batch_size=args.batch_size,
            max_workers=args.workers,
            total_limit=args.limit,
            purge_raw=args.purge_raw,
            collection_name=args.collection,
            raw_dir=args.raw_dir,
            processed_dir=args.processed_dir,
        )
        print(f"Stream pipeline complete! Successfully processed and indexed {indexed} papers.")
