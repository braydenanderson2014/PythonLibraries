import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

from PyQt6.QtCore import QObject, QPoint, QRect, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QImageReader, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QRubberBand,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}
SETTINGS_FILE = Path.home() / ".aiprepper_settings.json"
WORKSPACE_DIR = Path(__file__).resolve().parent
HF_CACHE_DIR = WORKSPACE_DIR / ".aiprepper_hf_cache"
VLM_REPOS = [
    "microsoft/git-base-coco",
    "HuggingFaceTB/SmolVLM-256M-Instruct",
]
BLIP_REPO = "Salesforce/blip-image-captioning-base"
TAG_SELECTOR_REPO = "openai/clip-vit-base-patch32"
DEFAULT_AI_PROMPT = (
    "Write a LoRA training caption as a comma-separated list of short visible tags or short fragments. "
    "Prefer compact descriptions like 'brown hair, blue eyes, standing outdoors' instead of long prose. "
    "Include subject attributes, clothing colors, accessories, pose, camera angle, background, and lighting. "
    "Do not mention dates, months, years, or guessed context not visible in the image."
)
KEYPOINT_AI_PROMPT = (
    "Return comma-separated visible tags only. Focus on: nude or clothed status, "
    "body parts, clothing items with colors, shoes or barefoot, pose, camera angle, "
    "and obvious background details."
)

MONTH_TOKENS = {
    "jan", "january", "feb", "february", "mar", "march", "apr", "april", "may",
    "jun", "june", "jul", "july", "aug", "august", "sep", "sept", "september",
    "oct", "october", "nov", "november", "dec", "december",
}

BASE_CANDIDATE_TAGS = [
    "portrait",
    "close-up",
    "upper body",
    "full body",
    "looking at viewer",
    "outdoors",
    "indoors",
    "natural light",
    "studio lighting",
    "nude",
    "naked",
    "water",
    "aqua",
]

TAG_BANK_CACHE: dict[str, tuple[tuple[int, int], list[tuple[str, int]]]] = {}
TAG_SELECTOR_PIPE: object | None = None
TAG_SELECTOR_ERROR: str | None = None

SYNONYM_EXPANSIONS = {
    "nude": ["naked", "unclothed"],
    "naked": ["nude", "unclothed"],
    "water": ["aqua"],
    "aqua": ["water"],
    "blue eyes": ["azure eyes"],
    "brown hair": ["brunette hair"],
    "black hair": ["dark hair"],
    "white hair": ["silver hair"],
    "red hair": ["auburn hair"],
    "blonde hair": ["fair hair"],
    "male": ["man"],
    "female": ["woman"],
}


class LocalBLIPAnalyzer:
    """Stable local BLIP captioner that avoids pipeline task/input mismatches."""

    def __init__(self, processor: object, model: object, device: str) -> None:
        self.processor = processor
        self.model = model
        self.device = device

    def caption(self, image: object, prompt: str | None = None) -> str:
        import torch

        if prompt:
            inputs = self.processor(images=image, text=prompt, return_tensors="pt")
        else:
            inputs = self.processor(images=image, return_tensors="pt")

        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=140,
                min_new_tokens=24,
                num_beams=5,
                repetition_penalty=1.2,
                no_repeat_ngram_size=2,
            )

        return self.processor.decode(outputs[0], skip_special_tokens=True)


class LocalVLMAnalyzer:
    """Local VLM captioner using image-text-to-text chat-style inference."""

    def __init__(self, pipe: object, backend_name: str) -> None:
        self.pipe = pipe
        self.backend_name = backend_name

    def _extract_assistant_text_from_content(self, content: object) -> str | None:
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text = item.get("text")
                        if isinstance(text, str) and text.strip():
                            return text.strip()
                    # Some models use direct text keys without type.
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
        return None

    def _extract_caption(self, value: object) -> str | None:
        """Extract assistant response text from common VLM pipeline output shapes."""
        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, list):
            # First try chat-message shape, preferring the last assistant message.
            assistant_candidates: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    role = item.get("role")
                    if role == "assistant":
                        text = self._extract_assistant_text_from_content(item.get("content"))
                        if text:
                            assistant_candidates.append(text)

            if assistant_candidates:
                return assistant_candidates[-1]

            # Otherwise recurse through elements.
            for item in value:
                text = self._extract_caption(item)
                if text:
                    return text
            return None

        if isinstance(value, dict):
            # If this is a chat message dict, only take assistant content.
            role = value.get("role")
            if role == "assistant":
                text = self._extract_assistant_text_from_content(value.get("content"))
                if text:
                    return text

            # Many pipelines return {"generated_text": ...}
            if "generated_text" in value:
                text = self._extract_caption(value.get("generated_text"))
                if text:
                    return text

            # As a controlled fallback, try content/text keys.
            if "content" in value:
                text = self._extract_assistant_text_from_content(value.get("content"))
                if text:
                    return text
            if "text" in value:
                text_val = value.get("text")
                if isinstance(text_val, str) and text_val.strip():
                    return text_val.strip()

        return None

    def caption(self, image: object, prompt: str | None = None) -> str:
        attempts = [
            lambda: self.pipe(images=image, text="", max_new_tokens=220),
            lambda: self.pipe(image=image, text="", max_new_tokens=220),
            lambda: self.pipe(images=image, text=prompt or DEFAULT_AI_PROMPT, max_new_tokens=220),
            lambda: self.pipe(image=image, text=prompt or DEFAULT_AI_PROMPT, max_new_tokens=220),
        ]

        errors: list[str] = []
        for attempt in attempts:
            try:
                result = attempt()
                text = self._extract_caption(result)
                if text:
                    return text
                errors.append("VLM returned empty caption text.")
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")

        raise ValueError("VLM caption failed. " + " | ".join(errors))


def analyzer_backend_name(analyzer: object | None) -> str:
    if analyzer is None:
        return "None"
    if isinstance(analyzer, LocalVLMAnalyzer):
        return f"VLM ({analyzer.backend_name})"
    if isinstance(analyzer, LocalBLIPAnalyzer):
        return "BLIP Fallback (blip-image-captioning-base)"
    return type(analyzer).__name__


def configure_hf_cache_dirs() -> None:
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (HF_CACHE_DIR / "hub").mkdir(parents=True, exist_ok=True)
    (HF_CACHE_DIR / "transformers").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))
    os.environ.setdefault("HF_HUB_CACHE", str(HF_CACHE_DIR / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(HF_CACHE_DIR / "transformers"))
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def prefetch_ai_model_files(fetch_blip: bool = True) -> tuple[bool, str]:
    """Prefetch required AI model files into local cache."""
    try:
        from transformers import BlipForConditionalGeneration, BlipProcessor
    except ImportError as exc:
        module_name = getattr(exc, "name", "unknown")
        return False, f"Missing Python package: {module_name}"

    configure_hf_cache_dirs()

    try:
        # Warm the actual primary VLM path first. This downloads only what the
        # current environment can actually use, instead of snapshot symlinks.
        analyzer, err = load_image_analyzer(allow_fallback=fetch_blip)
        if analyzer is None:
            return False, err or "Unable to load AI models."

        # Optionally warm BLIP directly if fallback is allowed.
        if fetch_blip and not isinstance(analyzer, LocalBLIPAnalyzer):
            BlipProcessor.from_pretrained(BLIP_REPO, cache_dir=str(HF_CACHE_DIR), local_files_only=False)
            BlipForConditionalGeneration.from_pretrained(BLIP_REPO, cache_dir=str(HF_CACHE_DIR), local_files_only=False)

        return True, f"AI files ready. Active backend: {analyzer_backend_name(analyzer)}"
    except Exception as exc:
        return False, f"Prefetch failed: {type(exc).__name__}: {exc}"


def clean_ai_caption(raw_text: str) -> str:
    """Normalize model output by stripping prompt echoes and repeated tokens."""
    text = raw_text.strip()
    if not text:
        return ""

    # Strip prompt-echo variants (including malformed echoes like "labels.s").
    text = re.sub(
        r"^describe\s+this\s+image(?:\s+in\s+detail)?(?:\s+for\s+training\s+labels?)?\.?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).lstrip(" .,:;-\n\t")

    text = re.sub(
        r"^a\s+detailed\s+caption\s+of(?:\s+this(?:\s+image)?)?(?:\s+in\s+detail)?(?:\s+for\s+training\s+labels?)?\.?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).lstrip(" .,:;-\n\t")

    if text.lower().startswith(DEFAULT_AI_PROMPT.lower()):
        text = text[len(DEFAULT_AI_PROMPT):].lstrip(" .,:;-\n\t")

    if text.lower().startswith(KEYPOINT_AI_PROMPT.lower()):
        text = text[len(KEYPOINT_AI_PROMPT):].lstrip(" .,:;-\n\t")

    # Handle leftover single-letter debris from prompt echo, e.g. "s, person, ...".
    text = re.sub(r"^[a-zA-Z]\s*,\s*", "", text)

    # Normalize sentence punctuation into comma-style tag separators.
    text = re.sub(r"[.!?;:]+", ",", text)

    # Remove month/year hallucinations that are typically noise for LoRA labels.
    text = re.sub(r"\b\d{4}\b", "", text)

    month_pattern = r"\b(?:" + "|".join(sorted(MONTH_TOKENS, key=len, reverse=True)) + r")\b"
    text = re.sub(month_pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s+", " ", text)

    # Collapse repeated comma-separated fragments like "person, person, person".
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 2:
        collapsed: list[str] = []
        for part in parts:
            if not collapsed or collapsed[-1].lower() != part.lower():
                collapsed.append(part)
        text = ", ".join(collapsed)

    # Remove repeated trailing word patterns.
    words = text.split()
    if len(words) >= 6:
        deduped: list[str] = []
        for word in words:
            if len(deduped) >= 2 and deduped[-1].lower() == word.lower() and deduped[-2].lower() == word.lower():
                continue
            deduped.append(word)
        text = " ".join(deduped)

    return text.strip(" ,.;")


def expand_ai_caption_synonyms(text: str) -> str:
    """Expand a cleaned AI caption with a small set of close synonym tags."""
    cleaned = text.strip(" ,.;")
    if not cleaned:
        return ""

    expanded: list[str] = []
    seen: set[str] = set()

    def add_part(part: str) -> None:
        normalized = re.sub(r"\s+", " ", part.strip(" ,.;")).lower()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        expanded.append(part.strip())

    for part in [p.strip() for p in cleaned.split(",") if p.strip()]:
        add_part(part)
        for synonym in SYNONYM_EXPANSIONS.get(part.lower(), []):
            add_part(synonym)

    return ", ".join(expanded)


def _normalize_tag(tag: str) -> str:
    return re.sub(r"\s+", " ", tag.strip().lower())


def _caption_parts(caption: str) -> list[str]:
    return [p.strip() for p in caption.split(",") if p.strip()]


def _caption_words(caption: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", caption.lower()))


def _folder_tag_bank(folder: Path) -> list[tuple[str, int]]:
    """Build frequent tags from existing sidecars to steer future captions."""
    folder_key = str(folder.resolve())
    txt_files = [p for p in folder.glob("*.txt") if not p.name.endswith("_AI.txt")]
    if not txt_files:
        return []

    latest_mtime = int(max((p.stat().st_mtime for p in txt_files), default=0))
    signature = (len(txt_files), latest_mtime)
    cached = TAG_BANK_CACHE.get(folder_key)
    if cached and cached[0] == signature:
        return cached[1]

    tag_counts: Counter[str] = Counter()
    for path in txt_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if not text:
            continue

        for part in _caption_parts(clean_ai_caption(text)):
            normalized = _normalize_tag(part)
            if len(normalized) < 2:
                continue
            if normalized in {"image", "photo", "picture"}:
                continue
            tag_counts[normalized] += 1

    for base_tag in BASE_CANDIDATE_TAGS:
        tag_counts[_normalize_tag(base_tag)] += 1

    ranked = tag_counts.most_common(200)
    TAG_BANK_CACHE[folder_key] = (signature, ranked)
    return ranked


def enrich_caption_from_prelabels(caption: str, image_folder: Path) -> str:
    """Add likely useful tags from existing dataset labels based on word overlap."""
    cleaned = caption.strip(" ,.;")
    if not cleaned:
        return ""

    bank = _folder_tag_bank(image_folder)
    if not bank:
        return cleaned

    parts = _caption_parts(cleaned)
    existing_norm = {_normalize_tag(p) for p in parts}
    words = _caption_words(cleaned)

    candidates: list[tuple[int, int, str]] = []
    for tag, freq in bank:
        if tag in existing_norm:
            continue
        tag_words = _caption_words(tag)
        overlap = len(words.intersection(tag_words))
        if overlap == 0:
            continue
        candidates.append((overlap, freq, tag))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    for _, _, tag in candidates[:6]:
        parts.append(tag)

    return ", ".join(parts)


def boost_keypoint_tags(caption: str) -> str:
    """Enrich captions with high-value LoRA keypoint tags from visible text cues."""
    cleaned = caption.strip(" ,.;")
    if not cleaned:
        return ""

    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    part_set = {_normalize_tag(p) for p in parts}
    text = " ".join(parts).lower()

    def add(tag: str) -> None:
        norm = _normalize_tag(tag)
        if norm not in part_set:
            parts.append(tag)
            part_set.add(norm)

    nudity_terms = {
        "nude", "naked", "topless", "bottomless", "nsfw", "genitals", "nipples", "breasts", "areola",
    }
    clothing_terms = {
        "shirt", "t-shirt", "top", "dress", "skirt", "pants", "jeans", "shorts", "jacket", "hoodie", "sweater",
        "bra", "underwear", "bikini", "swimsuit", "coat",
    }
    footwear_terms = {
        "shoes", "shoe", "sneakers", "boots", "heels", "sandals", "slippers", "barefoot", "sock", "socks",
    }
    body_terms = {
        "eyes", "hair", "face", "lips", "teeth", "hands", "arms", "legs", "thighs", "feet", "torso", "chest", "abs",
    }
    colors = "black|white|red|blue|green|yellow|brown|pink|purple|orange|gray|grey|blonde|silver"
    garments = "shirt|t-shirt|top|dress|skirt|pants|jeans|shorts|jacket|hoodie|sweater|bra|bikini|swimsuit|shoes|sneakers|boots|heels|sandals"

    if any(term in text for term in nudity_terms):
        add("nude")
        add("naked")
        add("no clothes")
    elif any(term in text for term in clothing_terms):
        add("clothed")

    if "barefoot" in text:
        add("barefoot")
        add("no shoes")
    elif any(term in text for term in footwear_terms):
        add("wearing shoes")

    for match in re.findall(rf"\\b({colors})\\s+({garments})\\b", text):
        add(f"{match[0]} {match[1]}")

    if "trees" in text and "green" in text:
        add("green trees")
    if "grass" in text and "green" in text:
        add("green grass")

    # Keep body keywords as-is from model output; avoid adding generic filler terms.
    _ = body_terms

    return ", ".join(parts)


def is_useful_caption(text: str) -> bool:
    """Basic quality check to avoid saving tiny/junk captions."""
    cleaned = text.strip()
    if not cleaned:
        return False

    lowered_text = cleaned.lower()

    # Reject obvious filename/path-like garbage.
    if re.search(r"\b(?:png|jpg|jpeg|webp|bmp|gif|tiff)\b", lowered_text):
        return False
    if re.search(r"\b\d+(?:/\d+){2,}/?\b", lowered_text):
        return False
    if re.search(r"\b[a-z0-9_-]{1,6}\.[a-z]{2,4}\b", lowered_text):
        return False

    words = re.findall(r"[A-Za-z0-9']+", cleaned)
    if not words:
        return False

    lowered = [w.lower() for w in words]
    unique = set(lowered)
    if len(unique) == 1 and len(words) > 1:
        return False

    content_words = [
        w
        for w in lowered
        if len(w) > 1 and w not in {"the", "and", "with", "for", "from", "this", "that", "there", "here", "image", "photo", "picture"}
    ]
    if not content_words:
        return False

    return True


def load_image_analyzer(allow_fallback: bool = True) -> tuple[object | None, str | None]:
    """Load transformers pipeline for image-to-text analysis.

    Returns:
        (pipeline, None) on success or (None, error_message) on failure.
    """
    try:
        import torch
        from PIL import Image  # noqa: F401 - validates Pillow import availability
        from transformers import BlipForConditionalGeneration, BlipProcessor, pipeline
    except ImportError as exc:
        module_name = getattr(exc, "name", "unknown")
        return None, f"Missing Python package: {module_name}"

    configure_hf_cache_dirs()

    device = 0 if torch.cuda.is_available() else -1
    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    init_errors: list[str] = []

    # Primary path: local VLM for richer instruction-following captions.
    for vlm_repo in VLM_REPOS:
        try:
            # On this transformers build, compatible VLM repos are exposed via
            # image-text-to-text task. SmolVLM additionally needs remote code.
            task = "image-text-to-text"
            trust_remote_code = "SmolVLM" in vlm_repo

            try:
                vlm_pipe = pipeline(
                    task,
                    model=vlm_repo,
                    device=device,
                    trust_remote_code=trust_remote_code,
                    cache_dir=str(HF_CACHE_DIR),
                    local_files_only=True,
                )
            except Exception:
                vlm_pipe = pipeline(
                    task,
                    model=vlm_repo,
                    device=device,
                    trust_remote_code=trust_remote_code,
                    cache_dir=str(HF_CACHE_DIR),
                    local_files_only=False,
                )

            return LocalVLMAnalyzer(vlm_pipe, backend_name=vlm_repo), None
        except Exception as exc:
            init_errors.append(f"primary-vlm({vlm_repo}): {type(exc).__name__}: {exc}")

    if not allow_fallback:
        return None, "VLM unavailable and BLIP fallback is disabled. " + " | ".join(init_errors)

    # Backup path: direct BLIP model + processor for consistent image captioning.
    try:
        processor = BlipProcessor.from_pretrained(
            BLIP_REPO,
            cache_dir=str(HF_CACHE_DIR),
            local_files_only=True,
        )
        model = BlipForConditionalGeneration.from_pretrained(
            BLIP_REPO,
            cache_dir=str(HF_CACHE_DIR),
            local_files_only=True,
        )
        model = model.to(device_name)
        model.eval()
        return LocalBLIPAnalyzer(processor=processor, model=model, device=device_name), None
    except Exception as exc:
        init_errors.append(f"direct-blip: {type(exc).__name__}: {exc}")

    # transformers 4.x commonly uses "image-to-text" while newer versions expose
    # "image-text-to-text". Try both for compatibility.
    for task_name in ("image-to-text", "image-text-to-text"):
        try:
            pipe = pipeline(task_name, model="Salesforce/blip-image-captioning-base", device=device)

            # Configure generation defaults once to avoid deprecation warnings from
            # passing generation args on every inference call.
            if hasattr(pipe, "model") and hasattr(pipe.model, "generation_config"):
                gen_cfg = pipe.model.generation_config
                if hasattr(gen_cfg, "max_new_tokens"):
                    gen_cfg.max_new_tokens = 140
                if hasattr(gen_cfg, "min_new_tokens"):
                    gen_cfg.min_new_tokens = 24
                if hasattr(gen_cfg, "max_length"):
                    gen_cfg.max_length = None
                if hasattr(gen_cfg, "repetition_penalty"):
                    gen_cfg.repetition_penalty = 1.2
                if hasattr(gen_cfg, "no_repeat_ngram_size"):
                    gen_cfg.no_repeat_ngram_size = 2
                if hasattr(gen_cfg, "num_beams"):
                    gen_cfg.num_beams = 5

            return pipe, None
        except Exception as exc:
            init_errors.append(f"{task_name}: {type(exc).__name__}: {exc}")

    return None, "AI model initialization failed. " + " | ".join(init_errors)


def load_tag_selector() -> tuple[object | None, str | None]:
    """Load zero-shot image tag selector for choosing best tags from a candidate list."""
    global TAG_SELECTOR_PIPE, TAG_SELECTOR_ERROR

    if TAG_SELECTOR_PIPE is not None:
        return TAG_SELECTOR_PIPE, None
    if TAG_SELECTOR_ERROR is not None:
        return None, TAG_SELECTOR_ERROR

    try:
        import torch
        from transformers import pipeline
    except ImportError as exc:
        module_name = getattr(exc, "name", "unknown")
        TAG_SELECTOR_ERROR = f"Missing Python package: {module_name}"
        return None, TAG_SELECTOR_ERROR

    configure_hf_cache_dirs()
    device = 0 if torch.cuda.is_available() else -1

    try:
        try:
            TAG_SELECTOR_PIPE = pipeline(
                "zero-shot-image-classification",
                model=TAG_SELECTOR_REPO,
                device=device,
                cache_dir=str(HF_CACHE_DIR),
                local_files_only=True,
            )
        except Exception:
            TAG_SELECTOR_PIPE = pipeline(
                "zero-shot-image-classification",
                model=TAG_SELECTOR_REPO,
                device=device,
                cache_dir=str(HF_CACHE_DIR),
                local_files_only=False,
            )
        return TAG_SELECTOR_PIPE, None
    except Exception as exc:
        TAG_SELECTOR_ERROR = f"Tag selector init failed: {type(exc).__name__}: {exc}"
        return None, TAG_SELECTOR_ERROR


def select_best_candidate_tags(image: object, candidate_tags: list[str], top_k: int = 6) -> tuple[list[str], str | None]:
    """Pick best-fitting tags from user-provided candidates for the given image."""
    tags = [re.sub(r"\s+", " ", t.strip()) for t in candidate_tags if t and t.strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        low = tag.lower()
        if low in seen:
            continue
        seen.add(low)
        deduped.append(tag)

    if not deduped:
        return [], None

    selector, err = load_tag_selector()
    if selector is None:
        return [], err

    try:
        result = selector(
            image,
            candidate_labels=deduped,
            hypothesis_template="This image contains {}.",
        )
    except Exception as exc:
        return [], f"Tag selector run failed: {type(exc).__name__}: {exc}"

    scored: list[tuple[str, float]] = []
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                label = item.get("label")
                score = item.get("score")
                if isinstance(label, str) and isinstance(score, (int, float)):
                    scored.append((label, float(score)))
    elif isinstance(result, dict):
        labels = result.get("labels")
        scores = result.get("scores")
        if isinstance(labels, list) and isinstance(scores, list):
            for label, score in zip(labels, scores):
                if isinstance(label, str) and isinstance(score, (int, float)):
                    scored.append((label, float(score)))

    if not scored:
        return [], "Tag selector returned no usable scores."

    scored.sort(key=lambda x: x[1], reverse=True)
    keep = max(1, min(top_k, len(scored)))
    threshold = 0.20
    picked = [label for label, score in scored[:keep] if score >= threshold]

    if not picked:
        picked = [scored[0][0]]

    return picked, None


def analyze_image_with_ai_verbose(
    image_path: Path,
    analyzer: object,
    candidate_tags: list[str] | None = None,
    candidate_top_k: int = 6,
    use_tag_selector: bool = False,
) -> tuple[str | None, str | None]:
    """Analyze image and return (description, error_message)."""
    if analyzer is None:
        return None, "AI analyzer is not initialized."

    try:
        from PIL import Image

        img = Image.open(str(image_path)).convert("RGB")
        selected_tags: list[str] = []
        selector_error: str | None = None

        if use_tag_selector and candidate_tags:
            selected_tags, selector_error = select_best_candidate_tags(
                img,
                candidate_tags,
                top_k=candidate_top_k,
            )

        # Different transformers versions/tasks accept different input signatures.
        # Try common forms sequentially until a useful caption is produced.
        if hasattr(analyzer, "caption"):
            attempts = [
                lambda: analyzer.caption(img, prompt=""),
                lambda: analyzer.caption(img, prompt=KEYPOINT_AI_PROMPT),
                lambda: analyzer.caption(img, prompt=DEFAULT_AI_PROMPT),
            ]
        else:
            attempts = [
                lambda: analyzer(images=img, text=""),
                lambda: analyzer(images=img, text=KEYPOINT_AI_PROMPT),
                lambda: analyzer(img, prompt=DEFAULT_AI_PROMPT),
                lambda: analyzer(images=img, text=DEFAULT_AI_PROMPT),
                lambda: analyzer({"image": img, "text": DEFAULT_AI_PROMPT}),
                lambda: analyzer(img),
            ]
        invocation_errors: list[str] = []

        def extract_caption(results: object) -> str | None:
            if isinstance(results, str) and results.strip():
                return clean_ai_caption(results)

            if isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict):
                    text = first.get("generated_text", "")
                    if isinstance(text, str) and text.strip():
                        return clean_ai_caption(text)

                    content = first.get("content")
                    if isinstance(content, str) and content.strip():
                        return clean_ai_caption(content)

                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                candidate = item.get("text")
                                if isinstance(candidate, str) and candidate.strip():
                                    return clean_ai_caption(candidate)
            return None

        for attempt in attempts:
            try:
                results = attempt()
                caption = extract_caption(results)
                if caption:
                    caption = expand_ai_caption_synonyms(caption)
                    caption = enrich_caption_from_prelabels(caption, image_path.parent)
                    caption = boost_keypoint_tags(caption)
                if selected_tags:
                    if caption:
                        merged_parts = [p.strip() for p in caption.split(",") if p.strip()]
                        merged_set = {_normalize_tag(p) for p in merged_parts}
                        for tag in selected_tags:
                            norm = _normalize_tag(tag)
                            if norm not in merged_set:
                                merged_parts.append(tag)
                                merged_set.add(norm)
                        caption = ", ".join(merged_parts)
                    else:
                        caption = ", ".join(selected_tags)
                if caption and is_useful_caption(caption):
                    return caption, None
                detail = "AI output was too short or low quality."
                if selector_error:
                    detail += f" Tag selector: {selector_error}"
                invocation_errors.append(detail)
            except Exception as exc:
                invocation_errors.append(f"{type(exc).__name__}: {exc}")

        return None, "AI call failed. " + " | ".join(invocation_errors)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def analyze_image_with_ai(
    image_path: Path,
    analyzer: object,
    candidate_tags: list[str] | None = None,
    candidate_top_k: int = 6,
    use_tag_selector: bool = False,
) -> str | None:
    """Backward-compatible wrapper that returns description or None."""
    text, _ = analyze_image_with_ai_verbose(
        image_path,
        analyzer,
        candidate_tags=candidate_tags,
        candidate_top_k=candidate_top_k,
        use_tag_selector=use_tag_selector,
    )
    if text:
        return text
    return None


class AILabelDialog(QDialog):
    """Dialog for reviewing and editing AI-generated labels."""
    def __init__(self, parent: QWidget | None, ai_label: str, image_filename: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review AI Label")
        self.resize(500, 300)
        self.label_text = ai_label

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"AI-generated label for: {image_filename}"))

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(ai_label)
        layout.addWidget(self.text_edit)

        button_row = QHBoxLayout()
        accept_btn = QPushButton("Accept & Save")
        accept_btn.clicked.connect(self.accept)
        button_row.addWidget(accept_btn)

        discard_btn = QPushButton("Discard")
        discard_btn.clicked.connect(self.reject)
        button_row.addWidget(discard_btn)

        layout.addLayout(button_row)
        self.setLayout(layout)

    def get_label(self) -> str:
        return self.text_edit.toPlainText().strip()


class CropPreviewLabel(QLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self._drag_origin: QPoint | None = None
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_preview_pixmap(self, pixmap: QPixmap) -> None:
        self.setPixmap(pixmap)
        self.clear_selection()

    def clear_selection(self) -> None:
        self._drag_origin = None
        self._rubber_band.hide()
        self._rubber_band.setGeometry(QRect())

    def has_selection(self) -> bool:
        rect = self.selection_rect()
        return rect is not None and rect.width() > 2 and rect.height() > 2

    def _clamp_to_display_rect(self, point: QPoint) -> QPoint:
        display_rect = self.displayed_pixmap_rect()
        if display_rect is None:
            return point
        x = min(max(point.x(), display_rect.left()), display_rect.right())
        y = min(max(point.y(), display_rect.top()), display_rect.bottom())
        return QPoint(x, y)

    def displayed_pixmap_rect(self) -> QRect | None:
        pix = self.pixmap()
        if pix is None or pix.isNull():
            return None

        width = pix.width()
        height = pix.height()
        x = (self.width() - width) // 2
        y = (self.height() - height) // 2
        return QRect(x, y, width, height)

    def selection_rect(self) -> QRect | None:
        if not self._rubber_band.isVisible():
            return None

        rect = self._rubber_band.geometry().normalized()
        display_rect = self.displayed_pixmap_rect()
        if display_rect is None:
            return None

        clipped = rect.intersected(display_rect)
        if clipped.width() < 2 or clipped.height() < 2:
            return None
        return clipped

    def mousePressEvent(self, event) -> None:  # noqa: N802
        display_rect = self.displayed_pixmap_rect()
        if event.button() == Qt.MouseButton.LeftButton and display_rect is not None:
            start = self._clamp_to_display_rect(event.position().toPoint())
            self._drag_origin = start
            self._rubber_band.setGeometry(QRect(start, start))
            self._rubber_band.show()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_origin is not None:
            current = self._clamp_to_display_rect(event.position().toPoint())
            self._rubber_band.setGeometry(QRect(self._drag_origin, current).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            current = self._clamp_to_display_rect(event.position().toPoint())
            self._rubber_band.setGeometry(QRect(self._drag_origin, current).normalized())
            self._drag_origin = None
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ImageLoader(QObject):
    """Loads and scales an image in a background thread. QImage is thread-safe; QPixmap is not."""

    loaded = pyqtSignal(str, object, object)  # (path_str, full_QImage_or_None, scaled_QImage_or_None)

    def __init__(self, image_path: Path, display_w: int, display_h: int) -> None:
        super().__init__()
        self._image_path = image_path
        self._display_w = display_w
        self._display_h = display_h
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        full_img = QImage(str(self._image_path))
        if self._cancelled or full_img.isNull():
            self.loaded.emit(str(self._image_path), None, None)
            return
        scaled = full_img.scaled(
            self._display_w,
            self._display_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if self._cancelled:
            self.loaded.emit(str(self._image_path), None, None)
            return
        self.loaded.emit(str(self._image_path), full_img, scaled)


class AIWorker(QObject):
    """Runs AI image analysis in a background thread to keep the UI responsive."""

    progress = pyqtSignal(int, str)  # (completed_count, current_filename)
    batch_item_done = pyqtSignal(str, str, str, bool, bool)
    # args: (image_path_str, description, error, was_skipped, was_backfilled)
    single_done = pyqtSignal(str, str, str)  # (image_path_str, description, error)
    finished = pyqtSignal()

    def __init__(
        self,
        images_batch: list,
        analyzer: object,
        candidate_tags: list,
        use_candidate_selector: bool,
        candidate_top_k: int,
        batch_mode: bool = True,
    ) -> None:
        super().__init__()
        self._images_batch = images_batch
        self._analyzer = analyzer
        self._candidate_tags = candidate_tags
        self._use_candidate_selector = use_candidate_selector
        self._candidate_top_k = candidate_top_k
        self._batch_mode = batch_mode
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        if self._batch_mode:
            self._run_batch()
        else:
            self._run_single()
        self.finished.emit()

    def _run_single(self) -> None:
        image_path, _, _ = self._images_batch[0]
        description, error = analyze_image_with_ai_verbose(
            image_path,
            self._analyzer,
            candidate_tags=self._candidate_tags,
            candidate_top_k=self._candidate_top_k,
            use_tag_selector=self._use_candidate_selector,
        )
        self.single_done.emit(str(image_path), description or "", error or "")

    def _run_batch(self) -> None:
        for i, (image_path, ai_sidecar_path, standard_sidecar_path) in enumerate(self._images_batch):
            if self._cancel:
                break
            self.progress.emit(i, image_path.name)
            if ai_sidecar_path.exists():
                backfilled = False
                if not standard_sidecar_path.exists():
                    try:
                        ai_text = ai_sidecar_path.read_text(encoding="utf-8").strip()
                        if ai_text:
                            standard_sidecar_path.write_text(ai_text + "\n", encoding="utf-8")
                            backfilled = True
                    except OSError:
                        pass
                self.batch_item_done.emit(str(image_path), "", "", True, backfilled)
                continue
            description, error = analyze_image_with_ai_verbose(
                image_path,
                self._analyzer,
                candidate_tags=self._candidate_tags,
                candidate_top_k=self._candidate_top_k,
                use_tag_selector=self._use_candidate_selector,
            )
            self.batch_item_done.emit(str(image_path), description or "", error or "", False, False)


class TaggerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Image Tagging Helper")
        self.resize(950, 620)

        self.current_dir: Path | None = None
        self.images: list[Path] = []
        self.current_index = -1
        self.current_original_pixmap: QPixmap | None = None

        self.caption_history: list[str] = []
        self.ai_analyzer: object | None = None
        self.ai_init_error: str | None = None
        self.ai_load_attempted = False
        self.ai_backend = "Not loaded"

        self._loaded_trigger = ""
        self._loaded_auto_prepend = True
        self._loaded_backup_crop = True
        self._loaded_allow_blip_fallback = False
        self._loaded_use_candidate_selector = False
        self._loaded_candidate_top_k = 6
        self._loaded_candidate_tags_text = ""
        self._loaded_jump_to = 1
        self._loaded_ai_range_start = 1
        self._loaded_ai_range_end = 1
        self._last_folder: Path | None = None

        self._ai_thread: QThread | None = None
        self._ai_worker: AIWorker | None = None
        self._batch_stats: dict = {}
        self._batch_progress: QProgressDialog | None = None

        self._image_thread: QThread | None = None
        self._image_worker: ImageLoader | None = None
        self._pending_image_path: Path | None = None

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self._do_resize_show)

        self._image_load_timer = QTimer(self)
        self._image_load_timer.setSingleShot(True)
        self._image_load_timer.setInterval(50)
        self._image_load_timer.timeout.connect(self._start_image_load)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self.save_settings)

        self.load_settings()

        self.setup_ui()
        self.update_ui_state()
        
        if self._last_folder is not None:
            self.current_dir = self._last_folder
            self.folder_label.setText(str(self._last_folder))
            self.scan_images()

    def setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Top controls
        top_row = QHBoxLayout()
        self.open_button = QPushButton("Open Folder")
        self.open_button.clicked.connect(self.open_folder)
        top_row.addWidget(self.open_button)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("color: #555;")
        self.folder_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        top_row.addWidget(self.folder_label, 1)

        root.addLayout(top_row)

        # Trigger row
        trigger_row = QHBoxLayout()
        trigger_row.addWidget(QLabel("Trigger Word:"))
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Example: my_character")
        self.trigger_input.textChanged.connect(self.save_settings)
        trigger_row.addWidget(self.trigger_input, 1)

        self.auto_prepend_checkbox = QCheckBox("Auto-prepend trigger on save")
        self.auto_prepend_checkbox.setChecked(True)
        self.auto_prepend_checkbox.stateChanged.connect(self.save_settings)
        trigger_row.addWidget(self.auto_prepend_checkbox)

        root.addLayout(trigger_row)

        # Main content row
        content_row = QHBoxLayout()

        left_col = QVBoxLayout()
        self.preview_label = CropPreviewLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(420, 420)
        self.preview_label.setStyleSheet(
            "background: #f0f0f0; border: 1px solid #ccc; color: #666;"
        )
        left_col.addWidget(self.preview_label)

        self.crop_help_label = QLabel("Drag on preview to select crop area")
        self.crop_help_label.setStyleSheet("color: #666;")
        left_col.addWidget(self.crop_help_label)

        self.file_label = QLabel("File: -")
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.file_label.setWordWrap(True)
        self.file_label.setMaximumHeight(40)
        left_col.addWidget(self.file_label)

        self.index_label = QLabel("Image 0 / 0")
        self.index_label.setStyleSheet("font-weight: bold;")
        left_col.addWidget(self.index_label)

        left_col.addStretch(1)
        content_row.addLayout(left_col, 3)

        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("Caption"))
        self.caption_combo = QComboBox()
        self.caption_combo.setEditable(True)
        self.caption_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        right_col.addWidget(self.caption_combo)

        self.caption_combo.lineEdit().setPlaceholderText(
            "Type caption, then Save Caption"
        )

        nav_row = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.go_previous)
        nav_row.addWidget(self.prev_button)

        nav_row.addWidget(QLabel("Go to:"))
        self.jump_spinbox = QSpinBox()
        self.jump_spinbox.setMinimum(1)
        self.jump_spinbox.setMaximum(1)
        self.jump_spinbox.valueChanged.connect(self.jump_to_image)
        self.jump_spinbox.valueChanged.connect(self.save_settings)
        nav_row.addWidget(self.jump_spinbox)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_next)
        nav_row.addWidget(self.next_button)
        right_col.addLayout(nav_row)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("Save Caption (.txt)")
        self.save_button.clicked.connect(self.save_current_caption)
        action_row.addWidget(self.save_button)

        self.crop_button = QPushButton("Crop Image")
        self.crop_button.clicked.connect(self.crop_current_image)
        action_row.addWidget(self.crop_button)

        self.crop_variant_button = QPushButton("Save Crop Variant")
        self.crop_variant_button.clicked.connect(self.save_crop_variant)
        action_row.addWidget(self.crop_variant_button)

        self.clear_crop_button = QPushButton("Clear Crop")
        self.clear_crop_button.clicked.connect(self.preview_label.clear_selection)
        action_row.addWidget(self.clear_crop_button)

        self.revert_crop_button = QPushButton("Revert Crop")
        self.revert_crop_button.clicked.connect(self.revert_crop)
        action_row.addWidget(self.revert_crop_button)

        self.ai_button = QPushButton("AI Analyze")
        self.ai_button.clicked.connect(self.analyze_with_ai)
        action_row.addWidget(self.ai_button)

        self.delete_button = QPushButton("Delete Image")
        self.delete_button.clicked.connect(self.delete_current_image)
        action_row.addWidget(self.delete_button)

        right_col.addLayout(action_row)

        range_ai_row = QHBoxLayout()
        range_ai_row.addWidget(QLabel("Batch AI:"))
        range_ai_row.addWidget(QLabel("From:"))
        self.ai_range_start = QSpinBox()
        self.ai_range_start.setMinimum(1)
        self.ai_range_start.setMaximum(1)
        self.ai_range_start.valueChanged.connect(self.save_settings)
        range_ai_row.addWidget(self.ai_range_start)

        range_ai_row.addWidget(QLabel("To:"))
        self.ai_range_end = QSpinBox()
        self.ai_range_end.setMinimum(1)
        self.ai_range_end.setMaximum(1)
        self.ai_range_end.valueChanged.connect(self.save_settings)
        range_ai_row.addWidget(self.ai_range_end)

        self.batch_ai_button = QPushButton("Run Batch AI")
        self.batch_ai_button.clicked.connect(self.run_batch_ai_analysis)
        range_ai_row.addWidget(self.batch_ai_button)

        self.fetch_ai_files_button = QPushButton("Fetch AI Files")
        self.fetch_ai_files_button.clicked.connect(self.fetch_ai_files)
        range_ai_row.addWidget(self.fetch_ai_files_button)

        self.allow_blip_fallback_checkbox = QCheckBox("Allow BLIP fallback")
        self.allow_blip_fallback_checkbox.setChecked(False)
        self.allow_blip_fallback_checkbox.stateChanged.connect(self.save_settings)
        range_ai_row.addWidget(self.allow_blip_fallback_checkbox)

        self.clear_ai_button = QPushButton("Clear AI Captions")
        self.clear_ai_button.clicked.connect(self.clear_ai_captions)
        range_ai_row.addWidget(self.clear_ai_button)

        right_col.addLayout(range_ai_row)

        selector_row = QHBoxLayout()
        self.use_candidate_selector_checkbox = QCheckBox("Use candidate tag selector")
        self.use_candidate_selector_checkbox.setChecked(False)
        self.use_candidate_selector_checkbox.stateChanged.connect(self.save_settings)
        selector_row.addWidget(self.use_candidate_selector_checkbox)

        selector_row.addWidget(QLabel("Top picks:"))
        self.candidate_top_k_spinbox = QSpinBox()
        self.candidate_top_k_spinbox.setMinimum(1)
        self.candidate_top_k_spinbox.setMaximum(30)
        self.candidate_top_k_spinbox.setValue(6)
        self.candidate_top_k_spinbox.valueChanged.connect(self.save_settings)
        selector_row.addWidget(self.candidate_top_k_spinbox)
        selector_row.addStretch(1)
        right_col.addLayout(selector_row)

        right_col.addWidget(QLabel("Candidate tags (comma or newline separated)"))
        self.candidate_tags_input = QTextEdit()
        self.candidate_tags_input.setPlaceholderText(
            "nude, naked, clothed, red shirt, blue jeans, sneakers, barefoot, green trees"
        )
        self.candidate_tags_input.setMaximumHeight(80)
        self.candidate_tags_input.textChanged.connect(self._save_timer.start)
        right_col.addWidget(self.candidate_tags_input)

        self.backup_crop_checkbox = QCheckBox("Backup original before crop")
        self.backup_crop_checkbox.setChecked(True)
        self.backup_crop_checkbox.stateChanged.connect(self.save_settings)
        right_col.addWidget(self.backup_crop_checkbox)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #444;")
        right_col.addWidget(self.status_label)

        right_col.addStretch(1)
        content_row.addLayout(right_col, 2)

        root.addLayout(content_row)

        self.refresh_caption_combo()
        self.trigger_input.setText(getattr(self, "_loaded_trigger", ""))
        self.auto_prepend_checkbox.setChecked(getattr(self, "_loaded_auto_prepend", True))
        self.backup_crop_checkbox.setChecked(getattr(self, "_loaded_backup_crop", True))
        self.allow_blip_fallback_checkbox.setChecked(getattr(self, "_loaded_allow_blip_fallback", False))
        self.use_candidate_selector_checkbox.setChecked(getattr(self, "_loaded_use_candidate_selector", False))
        self.candidate_top_k_spinbox.setValue(getattr(self, "_loaded_candidate_top_k", 6))
        self.candidate_tags_input.setPlainText(getattr(self, "_loaded_candidate_tags_text", ""))

    def load_settings(self) -> None:
        if not SETTINGS_FILE.exists():
            return

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        self.caption_history = [x for x in data.get("caption_history", []) if isinstance(x, str)]

        self._loaded_trigger = data.get("trigger_word", "") if isinstance(data.get("trigger_word"), str) else ""
        self._loaded_auto_prepend = bool(data.get("auto_prepend", True))
        self._loaded_backup_crop = bool(data.get("backup_crop", True))
        self._loaded_allow_blip_fallback = bool(data.get("allow_blip_fallback", False))
        self._loaded_use_candidate_selector = bool(data.get("use_candidate_selector", False))
        self._loaded_candidate_top_k = int(data.get("candidate_top_k", 6) or 6)
        if self._loaded_candidate_top_k < 1:
            self._loaded_candidate_top_k = 1
        self._loaded_candidate_tags_text = data.get("candidate_tags_text", "") if isinstance(data.get("candidate_tags_text"), str) else ""
        self._loaded_jump_to = int(data.get("jump_to", 1) or 1)
        self._loaded_ai_range_start = int(data.get("ai_range_start", 1) or 1)
        self._loaded_ai_range_end = int(data.get("ai_range_end", 1) or 1)
        
        last_folder = data.get("last_folder", "")
        self._last_folder = Path(last_folder) if last_folder and Path(last_folder).exists() else None

    def save_settings(self) -> None:
        trigger_word = self.trigger_input.text().strip() if hasattr(self, "trigger_input") else ""
        auto_prepend = (
            bool(self.auto_prepend_checkbox.isChecked())
            if hasattr(self, "auto_prepend_checkbox")
            else True
        )

        backup_crop = (
            bool(self.backup_crop_checkbox.isChecked())
            if hasattr(self, "backup_crop_checkbox")
            else True
        )

        allow_blip_fallback = (
            bool(self.allow_blip_fallback_checkbox.isChecked())
            if hasattr(self, "allow_blip_fallback_checkbox")
            else False
        )

        use_candidate_selector = (
            bool(self.use_candidate_selector_checkbox.isChecked())
            if hasattr(self, "use_candidate_selector_checkbox")
            else False
        )

        candidate_top_k = (
            int(self.candidate_top_k_spinbox.value())
            if hasattr(self, "candidate_top_k_spinbox")
            else 6
        )

        candidate_tags_text = (
            self.candidate_tags_input.toPlainText().strip()
            if hasattr(self, "candidate_tags_input")
            else ""
        )
        
        last_folder = str(self.current_dir) if self.current_dir is not None else ""
        jump_to = self.current_index + 1 if self.current_index >= 0 else 1
        ai_range_start = self.ai_range_start.value() if hasattr(self, "ai_range_start") else 1
        ai_range_end = self.ai_range_end.value() if hasattr(self, "ai_range_end") else 1

        data = {
            "trigger_word": trigger_word,
            "auto_prepend": auto_prepend,
            "backup_crop": backup_crop,
            "allow_blip_fallback": allow_blip_fallback,
            "use_candidate_selector": use_candidate_selector,
            "candidate_top_k": candidate_top_k,
            "candidate_tags_text": candidate_tags_text,
            "caption_history": self.caption_history[-500:],
            "last_folder": last_folder,
            "jump_to": jump_to,
            "ai_range_start": ai_range_start,
            "ai_range_end": ai_range_end,
        }

        try:
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if not folder:
            return

        selected_dir = Path(folder)
        self.current_dir = selected_dir
        self.folder_label.setText(str(selected_dir))
        self.scan_images()
        self.save_settings()

    def scan_images(self) -> None:
        if self.current_dir is None:
            return

        images = [
            path
            for path in sorted(self.current_dir.iterdir(), key=lambda p: p.name.lower())
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]

        self.images = images
        self.current_index = 0 if self.images else -1

        if not self.images:
            self.preview_label.setText("No images found in folder")
            self.preview_label.clear_selection()
            self.file_label.setText("File: -")
            self.index_label.setText("Image 0 / 0")
            self.status_label.setText("No images found.")
            self.update_ui_state()
            return

        self.show_current_image()
        self.status_label.setText(f"Loaded {len(self.images)} images.")

        self.jump_spinbox.blockSignals(True)
        self.jump_spinbox.setMaximum(len(self.images))
        if self.current_dir == self._last_folder:
            target_jump = min(max(self._loaded_jump_to, 1), len(self.images))
        else:
            target_jump = 1
        self.jump_spinbox.setValue(target_jump)
        self.jump_spinbox.blockSignals(False)

        self.current_index = target_jump - 1
        self.show_current_image()

        self.ai_range_start.blockSignals(True)
        self.ai_range_start.setMaximum(len(self.images))
        if self.current_dir == self._last_folder:
            start_value = min(max(self._loaded_ai_range_start, 1), len(self.images))
        else:
            start_value = 1
        self.ai_range_start.setValue(start_value)
        self.ai_range_start.blockSignals(False)

        self.ai_range_end.blockSignals(True)
        self.ai_range_end.setMaximum(len(self.images))
        if self.current_dir == self._last_folder:
            end_value = min(max(self._loaded_ai_range_end, 1), len(self.images))
        else:
            end_value = len(self.images)
        self.ai_range_end.setValue(end_value)
        self.ai_range_end.blockSignals(False)

        self.save_settings()

    def show_current_image(self) -> None:
        if not self.images or self.current_index < 0:
            self.preview_label.setText("Preview")
            self.preview_label.clear_selection()
            self.current_original_pixmap = None
            self.file_label.setText("File: -")
            self.index_label.setText("Image 0 / 0")
            self.caption_combo.lineEdit().setText("")
            self.update_ui_state()
            return

        image_path = self.images[self.current_index]
        self._pending_image_path = image_path

        # Update labels and caption instantly — no I/O cost
        self.file_label.setText(f"File: {image_path.name}")
        self.index_label.setText(f"Image {self.current_index + 1} / {len(self.images)}")

        self.jump_spinbox.blockSignals(True)
        self.jump_spinbox.setValue(self.current_index + 1)
        self.jump_spinbox.blockSignals(False)

        existing_caption = self.read_caption_for_image(image_path)
        self.caption_combo.lineEdit().setText(existing_caption)

        # Show placeholder while image loads, cancel any stale in-flight load
        self.preview_label.clear_selection()
        self.preview_label.setText("Loading...")
        self.current_original_pixmap = None
        if self._image_worker is not None:
            self._image_worker.cancel()

        # Debounce: wait 50ms in case the user is navigating quickly
        self._image_load_timer.start()
        self.update_ui_state()

    def _start_image_load(self) -> None:
        """Called by debounce timer — starts the background image load."""
        if self._pending_image_path is None:
            return
        image_path = self._pending_image_path
        display_w = max(1, self.preview_label.width())
        display_h = max(1, self.preview_label.height())

        thread = QThread(self)
        worker = ImageLoader(image_path, display_w, display_h)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.loaded.connect(self._on_image_loaded)
        worker.loaded.connect(thread.quit)

        self._image_thread = thread
        self._image_worker = worker
        thread.start()

    def _on_image_loaded(self, image_path_str: str, full_image: object, scaled_image: object) -> None:
        """Receives the loaded image from the background thread."""
        # Ignore if the user navigated away before this load completed
        if self._pending_image_path is None or image_path_str != str(self._pending_image_path):
            return

        if full_image is None:
            self.preview_label.setText("Unable to load image preview")
            self.current_original_pixmap = None
        else:
            self.current_original_pixmap = QPixmap.fromImage(full_image)
            self.preview_label.set_preview_pixmap(QPixmap.fromImage(scaled_image))

        self.update_ui_state()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._resize_timer.start()

    def _do_resize_show(self) -> None:
        if self.images and self.current_index >= 0:
            self.show_current_image()

    def go_previous(self) -> None:
        if not self.images:
            return
        self.current_index = max(0, self.current_index - 1)
        self.show_current_image()
        self.save_settings()

    def go_next(self) -> None:
        if not self.images:
            return
        self.current_index = min(len(self.images) - 1, self.current_index + 1)
        self.show_current_image()
        self.save_settings()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Left:
            self.go_previous()
            return
        if event.key() == Qt.Key.Key_Right:
            self.go_next()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            self.save_current_caption()
            return
        super().keyPressEvent(event)

    def sidecar_path(self, image_path: Path) -> Path:
        return image_path.with_suffix(".txt")

    def read_caption_for_image(self, image_path: Path) -> str:
        sidecar = self.sidecar_path(image_path)
        if not sidecar.exists():
            return ""

        try:
            text = sidecar.read_text(encoding="utf-8").strip()
        except OSError:
            return ""

        if text:
            self.add_caption_to_history(text)
        return text

    def save_current_caption(self) -> None:
        if not self.images or self.current_index < 0:
            return

        image_path = self.images[self.current_index]
        sidecar = self.sidecar_path(image_path)

        caption = self.caption_combo.currentText().strip()
        trigger = self.trigger_input.text().strip()

        if trigger and self.auto_prepend_checkbox.isChecked() and not caption.startswith(trigger):
            caption = f"{trigger}, {caption}" if caption else trigger
            self.caption_combo.lineEdit().setText(caption)

        try:
            sidecar.write_text(caption + "\n", encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", f"Could not save caption:\n{exc}")
            return

        if caption:
            self.add_caption_to_history(caption)

        self.save_settings()
        self.status_label.setText(f"Saved: {sidecar.name}")

    def add_caption_to_history(self, caption: str) -> None:
        clean = caption.strip()
        if not clean:
            return
        if clean in self.caption_history:
            self.caption_history.remove(clean)
        self.caption_history.append(clean)
        self.refresh_caption_combo()

    def refresh_caption_combo(self) -> None:
        current_text = self.caption_combo.currentText() if hasattr(self, "caption_combo") else ""
        if hasattr(self, "caption_combo"):
            self.caption_combo.blockSignals(True)
            self.caption_combo.clear()
            self.caption_combo.addItems(reversed(self.caption_history[-300:]))
            self.caption_combo.setCurrentText(current_text)
            self.caption_combo.blockSignals(False)

    def delete_current_image(self) -> None:
        if not self.images or self.current_index < 0:
            return

        image_path = self.images[self.current_index]
        confirm = QMessageBox.question(
            self,
            "Delete Image",
            f"Delete image permanently?\n\n{image_path.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        sidecar = self.sidecar_path(image_path)

        try:
            image_path.unlink(missing_ok=False)
            if sidecar.exists():
                sidecar.unlink(missing_ok=False)
        except OSError as exc:
            QMessageBox.critical(self, "Delete Failed", f"Could not delete file:\n{exc}")
            return

        removed_name = image_path.name
        del self.images[self.current_index]

        if self.current_index >= len(self.images):
            self.current_index = len(self.images) - 1

        if not self.images:
            self.current_index = -1

        self.show_current_image()
        self.status_label.setText(f"Deleted: {removed_name}")

    def backup_path_for(self, image_path: Path) -> Path:
        backup_dir = image_path.parent / "_original_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        candidate = backup_dir / image_path.name
        if not candidate.exists():
            return candidate

        stem = image_path.stem
        suffix = image_path.suffix
        index = 1
        while True:
            candidate = backup_dir / f"{stem}_{index}{suffix}"
            if not candidate.exists():
                return candidate
            index += 1

    def next_crop_variant_path(self, image_path: Path) -> Path:
        base_stem = image_path.stem
        suffix = image_path.suffix
        index = 1
        while True:
            candidate = image_path.with_name(f"{base_stem}_crop{index}{suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def selected_crop_pixmap(self) -> QPixmap | None:
        if self.current_original_pixmap is None or self.current_original_pixmap.isNull():
            QMessageBox.warning(self, "Crop", "No image available for cropping.")
            return None

        selection = self.preview_label.selection_rect()
        display_rect = self.preview_label.displayed_pixmap_rect()
        if selection is None or display_rect is None:
            QMessageBox.information(self, "Crop", "Drag a crop box on the preview first.")
            return None

        source_w = self.current_original_pixmap.width()
        source_h = self.current_original_pixmap.height()
        display_w = max(1, display_rect.width())
        display_h = max(1, display_rect.height())

        x_ratio = source_w / display_w
        y_ratio = source_h / display_h

        relative_x = selection.x() - display_rect.x()
        relative_y = selection.y() - display_rect.y()

        crop_x = max(0, int(round(relative_x * x_ratio)))
        crop_y = max(0, int(round(relative_y * y_ratio)))
        crop_w = max(1, int(round(selection.width() * x_ratio)))
        crop_h = max(1, int(round(selection.height() * y_ratio)))

        if crop_x + crop_w > source_w:
            crop_w = source_w - crop_x
        if crop_y + crop_h > source_h:
            crop_h = source_h - crop_y

        crop_rect = QRect(crop_x, crop_y, crop_w, crop_h)
        cropped = self.current_original_pixmap.copy(crop_rect)
        if cropped.isNull():
            QMessageBox.warning(self, "Crop Failed", "Could not crop image.")
            return None

        return cropped

    def crop_current_image(self) -> None:
        if not self.images or self.current_index < 0:
            return
        cropped = self.selected_crop_pixmap()
        if cropped is None:
            return

        image_path = self.images[self.current_index]
        backup_path: Path | None = None

        if self.backup_crop_checkbox.isChecked():
            backup_path = self.backup_path_for(image_path)
            try:
                shutil.move(str(image_path), str(backup_path))
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    "Crop Failed",
                    f"Could not move original to backup:\n{exc}",
                )
                return

        save_ok = cropped.save(str(image_path))
        if not save_ok:
            if backup_path is not None and backup_path.exists() and not image_path.exists():
                try:
                    shutil.move(str(backup_path), str(image_path))
                except OSError:
                    pass
            QMessageBox.critical(self, "Crop Failed", "Could not save cropped image.")
            return

        self.preview_label.clear_selection()
        self.show_current_image()
        if backup_path is not None:
            self.status_label.setText(f"Cropped and backed up original to: {backup_path.name}")
        else:
            self.status_label.setText("Cropped image saved.")

    def save_crop_variant(self) -> None:
        if not self.images or self.current_index < 0:
            return

        cropped = self.selected_crop_pixmap()
        if cropped is None:
            return

        image_path = self.images[self.current_index]
        variant_path = self.next_crop_variant_path(image_path)
        save_ok = cropped.save(str(variant_path))
        if not save_ok:
            QMessageBox.critical(self, "Crop Failed", "Could not save crop variant.")
            return

        source_sidecar = self.sidecar_path(image_path)
        variant_sidecar = self.sidecar_path(variant_path)
        if source_sidecar.exists() and not variant_sidecar.exists():
            try:
                shutil.copy2(source_sidecar, variant_sidecar)
            except OSError:
                pass

        # Splice into the sorted images list rather than rescanning the whole folder.
        # Images are sorted by name.lower(), so find the correct insertion point.
        variant_name_lower = variant_path.name.lower()
        insert_index = len(self.images)
        for i, p in enumerate(self.images):
            if p.name.lower() > variant_name_lower:
                insert_index = i
                break
        self.images.insert(insert_index, variant_path)
        self.current_index = insert_index

        total = len(self.images)
        for spinbox in (self.jump_spinbox, self.ai_range_start, self.ai_range_end):
            spinbox.blockSignals(True)
            spinbox.setMaximum(total)
            spinbox.blockSignals(False)

        self.show_current_image()
        self.status_label.setText(f"Saved crop variant: {variant_path.name}")

    def backup_exists_for(self, image_path: Path) -> Path | None:
        """Check if a backup exists for this image in _original_backup. Return backup path or None."""
        backup_dir = image_path.parent / "_original_backup"
        if not backup_dir.exists():
            return None

        candidate = backup_dir / image_path.name
        if candidate.exists():
            return candidate

        return None

    def revert_crop(self) -> None:
        """Restore original image from backup."""
        if not self.images or self.current_index < 0:
            return

        image_path = self.images[self.current_index]
        backup_path = self.backup_exists_for(image_path)

        if backup_path is None:
            QMessageBox.information(self, "Revert Crop", "No backup found for this image.")
            return

        confirm = QMessageBox.question(
            self,
            "Revert Crop",
            f"Restore original from backup?\n\nThis will replace the current image with the backup.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            backup_path.unlink(missing_ok=False)
            if image_path.exists():
                image_path.unlink(missing_ok=False)
            shutil.move(str(backup_path), str(image_path))
        except OSError as exc:
            QMessageBox.critical(self, "Revert Failed", f"Could not restore backup:\n{exc}")
            return

        self.preview_label.clear_selection()
        self.show_current_image()
        self.status_label.setText(f"Reverted: {image_path.name}")

    def jump_to_image(self, image_number: int) -> None:
        """Jump to a specific image by number (1-indexed)."""
        if not self.images or image_number < 1 or image_number > len(self.images):
            return
        self.current_index = image_number - 1
        self.show_current_image()
        self.save_settings()

    def ensure_ai_analyzer(self) -> bool:
        if self.ai_analyzer is not None:
            return True

        if self.ai_load_attempted and self.ai_init_error:
            return False

        self.status_label.setText("Loading local AI model (first time can take a while)...")
        self.status_label.update()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            allow_fallback = (
                bool(self.allow_blip_fallback_checkbox.isChecked())
                if hasattr(self, "allow_blip_fallback_checkbox")
                else False
            )
            self.ai_analyzer, self.ai_init_error = load_image_analyzer(allow_fallback=allow_fallback)
            self.ai_load_attempted = True
            self.ai_backend = analyzer_backend_name(self.ai_analyzer)
        finally:
            QApplication.restoreOverrideCursor()

        if self.ai_analyzer is not None:
            self.status_label.setText(f"AI backend loaded: {self.ai_backend}")

        return self.ai_analyzer is not None

    def fetch_ai_files(self) -> None:
        """Download AI model files ahead of time so runtime init is local-only."""
        self.status_label.setText("Fetching AI files...")
        self.status_label.update()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            fetch_blip = (
                bool(self.allow_blip_fallback_checkbox.isChecked())
                if hasattr(self, "allow_blip_fallback_checkbox")
                else False
            )
            ok, message = prefetch_ai_model_files(fetch_blip=fetch_blip)
        finally:
            QApplication.restoreOverrideCursor()

        if ok:
            # Force a fresh analyzer load next run so new files are picked up.
            self.ai_analyzer = None
            self.ai_init_error = None
            self.ai_load_attempted = False
            self.ai_backend = "Not loaded"
            self.status_label.setText(message)
            QMessageBox.information(self, "Fetch AI Files", message)
        else:
            self.status_label.setText("AI file fetch failed.")
            QMessageBox.warning(self, "Fetch AI Files", message)

    def run_batch_ai_analysis(self) -> None:
        """Run AI analysis on a range of images using a background thread."""
        if not self.images:
            QMessageBox.warning(self, "Batch AI", "No images loaded.")
            return

        if not self.ensure_ai_analyzer():
            error_text = self.ai_init_error or "AI model is unavailable."
            QMessageBox.warning(
                self,
                "Batch AI Disabled",
                f"{error_text}\n\nIf dependencies are installed, this is usually a model load/download issue.",
            )
            return

        start = self.ai_range_start.value()
        end = self.ai_range_end.value()

        if start < 1 or end < 1 or start > len(self.images) or end > len(self.images):
            QMessageBox.warning(self, "Batch AI", "Invalid image range.")
            return

        if start > end:
            start, end = end, start
            self.ai_range_start.setValue(start)
            self.ai_range_end.setValue(end)

        candidate_tags = self.get_candidate_tags()
        use_candidate_selector = (
            bool(self.use_candidate_selector_checkbox.isChecked())
            if hasattr(self, "use_candidate_selector_checkbox")
            else False
        ) and bool(candidate_tags)
        candidate_top_k = self.candidate_top_k_spinbox.value() if hasattr(self, "candidate_top_k_spinbox") else 6

        images_batch = [
            (
                self.images[idx],
                self.ai_label_path(self.images[idx]),
                self.sidecar_path(self.images[idx]),
            )
            for idx in range(start - 1, end)
        ]
        total_items = len(images_batch)

        self._batch_stats = {
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "attempted": 0,
            "backfilled_standard": 0,
            "failure_samples": [],
        }

        self._batch_progress = QProgressDialog(
            "Running AI analysis...", "Cancel", 0, total_items, self
        )
        self._batch_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._batch_progress.canceled.connect(self._cancel_batch_ai)
        self._batch_progress.show()

        self._cleanup_ai_thread()
        self._ai_thread = QThread(self)
        self._ai_worker = AIWorker(
            images_batch=images_batch,
            analyzer=self.ai_analyzer,
            candidate_tags=candidate_tags,
            use_candidate_selector=use_candidate_selector,
            candidate_top_k=candidate_top_k,
            batch_mode=True,
        )
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.progress.connect(self._on_batch_progress)
        self._ai_worker.batch_item_done.connect(self._on_batch_item_done)
        self._ai_worker.finished.connect(self._on_batch_finished)
        self._ai_worker.finished.connect(self._ai_thread.quit)

        self.batch_ai_button.setEnabled(False)
        self.ai_button.setEnabled(False)
        self._ai_thread.start()

    def _cleanup_ai_thread(self) -> None:
        if self._ai_thread is not None:
            self._ai_thread.quit()
            self._ai_thread.wait(3000)
            self._ai_thread = None
            self._ai_worker = None

    def _cancel_batch_ai(self) -> None:
        if self._ai_worker is not None:
            self._ai_worker.cancel()

    def _on_batch_progress(self, completed: int, filename: str) -> None:
        if self._batch_progress is not None:
            self._batch_progress.setLabelText(f"Processing: {filename}")
            self._batch_progress.setValue(completed)

    def _on_batch_item_done(
        self, image_path_str: str, description: str, error: str, was_skipped: bool, was_backfilled: bool
    ) -> None:
        stats = self._batch_stats
        if was_skipped:
            stats["skipped"] += 1
            if was_backfilled:
                stats["backfilled_standard"] += 1
            return

        stats["attempted"] += 1
        if description:
            image_path = Path(image_path_str)
            saved_ok, save_error = self.save_ai_sidecars(image_path, description)
            if saved_ok:
                clean = description.strip()
                if clean:
                    if clean in self.caption_history:
                        self.caption_history.remove(clean)
                    self.caption_history.append(clean)
                stats["successful"] += 1
            else:
                stats["failed"] += 1
                if len(stats["failure_samples"]) < 3:
                    stats["failure_samples"].append(f"{image_path.name}: save error ({save_error})")
        else:
            stats["failed"] += 1
            if len(stats["failure_samples"]) < 3:
                details = error or "no caption returned"
                stats["failure_samples"].append(f"{Path(image_path_str).name}: {details}")

    def _on_batch_finished(self) -> None:
        if self._batch_progress is not None:
            self._batch_progress.close()
            self._batch_progress = None

        self._cleanup_ai_thread()
        self.refresh_caption_combo()
        self.batch_ai_button.setEnabled(bool(self.images))
        has_image = bool(self.images) and self.current_index >= 0
        self.ai_button.setEnabled(has_image)

        stats = self._batch_stats
        successful = stats["successful"]
        failed = stats["failed"]
        skipped = stats["skipped"]
        attempted = stats["attempted"]
        backfilled_standard = stats["backfilled_standard"]
        failure_samples = stats["failure_samples"]

        msg = (
            f"Backend: {self.ai_backend}\n"
            f"Batch complete: {successful} analyzed, {skipped} skipped, "
            f"{failed} failed, {attempted} attempted."
        )
        if backfilled_standard > 0:
            msg += f"\nStandard sidecars backfilled: {backfilled_standard}."
        if failure_samples:
            msg += "\n\nSample failures:\n- " + "\n- ".join(failure_samples)

        if successful == 0 and attempted > 0:
            QMessageBox.warning(self, "Batch AI Complete (No Success)", msg)
        else:
            QMessageBox.information(self, "Batch AI Complete", msg)
        self.status_label.setText(msg)

    def ai_label_path(self, image_path: Path) -> Path:
        """Get path for AI-labeled sidecar file."""
        base_stem = image_path.stem
        suffix = image_path.suffix
        return image_path.with_name(f"{base_stem}_AI.txt")

    def save_ai_sidecars(self, image_path: Path, caption: str) -> tuple[bool, str | None]:
        """Save AI marker sidecar and ensure standard sidecar exists."""
        ai_sidecar_path = self.ai_label_path(image_path)
        standard_sidecar_path = self.sidecar_path(image_path)

        try:
            ai_sidecar_path.write_text(caption + "\n", encoding="utf-8")
            if not standard_sidecar_path.exists():
                standard_sidecar_path.write_text(caption + "\n", encoding="utf-8")
        except OSError as exc:
            return False, str(exc)

        return True, None

    def clear_ai_captions(self) -> None:
        """Delete AI-generated caption files to allow a fresh AI pass."""
        if self.current_dir is None or not self.current_dir.exists():
            QMessageBox.information(self, "Clear AI Captions", "Open a folder first.")
            return

        ai_files = sorted(self.current_dir.glob("*_AI.txt"), key=lambda p: p.name.lower())
        if not ai_files:
            QMessageBox.information(self, "Clear AI Captions", "No AI caption files found.")
            return

        confirm = QMessageBox.question(
            self,
            "Clear AI Captions",
            (
                f"Delete {len(ai_files)} AI caption files?\n\n"
                "This removes *_AI.txt files. If a matching standard .txt has the same content, "
                "it will also be removed."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        removed_ai = 0
        removed_standard = 0
        failed = 0

        for ai_file in ai_files:
            try:
                ai_text = ai_file.read_text(encoding="utf-8").strip()
            except OSError:
                ai_text = ""

            base_name = ai_file.name[:-7]  # remove "_AI.txt"
            standard_sidecar = ai_file.with_name(f"{base_name}.txt")

            if standard_sidecar.exists() and ai_text:
                try:
                    standard_text = standard_sidecar.read_text(encoding="utf-8").strip()
                    if standard_text == ai_text:
                        standard_sidecar.unlink()
                        removed_standard += 1
                except OSError:
                    failed += 1

            try:
                ai_file.unlink()
                removed_ai += 1
            except OSError:
                failed += 1

        msg = f"Removed {removed_ai} AI files"
        if removed_standard:
            msg += f" and {removed_standard} matching standard sidecars"
        msg += "."
        if failed:
            msg += f" {failed} file operations failed."

        if self.images and self.current_index >= 0:
            self.show_current_image()

        self.status_label.setText(msg)
        QMessageBox.information(self, "Clear AI Captions", msg)

    def analyze_with_ai(self) -> None:
        if not self.images or self.current_index < 0:
            return

        if not self.ensure_ai_analyzer():
            error_text = self.ai_init_error or "AI model is unavailable."
            QMessageBox.warning(
                self,
                "AI Disabled",
                f"{error_text}\n\nIf needed, reinstall with: pip install -r requirements.txt",
            )
            return

        image_path = self.images[self.current_index]
        self.status_label.setText(f"Analyzing image with AI ({self.ai_backend})...")
        self.status_label.update()

        candidate_tags = self.get_candidate_tags()
        use_candidate_selector = (
            bool(self.use_candidate_selector_checkbox.isChecked())
            if hasattr(self, "use_candidate_selector_checkbox")
            else False
        ) and bool(candidate_tags)
        candidate_top_k = self.candidate_top_k_spinbox.value() if hasattr(self, "candidate_top_k_spinbox") else 6

        images_batch = [
            (image_path, self.ai_label_path(image_path), self.sidecar_path(image_path))
        ]
        self._cleanup_ai_thread()
        self._ai_thread = QThread(self)
        self._ai_worker = AIWorker(
            images_batch=images_batch,
            analyzer=self.ai_analyzer,
            candidate_tags=candidate_tags,
            use_candidate_selector=use_candidate_selector,
            candidate_top_k=candidate_top_k,
            batch_mode=False,
        )
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.single_done.connect(self._on_single_ai_done)
        self._ai_worker.finished.connect(self._on_single_ai_finished)
        self._ai_worker.finished.connect(self._ai_thread.quit)

        self.ai_button.setEnabled(False)
        self.batch_ai_button.setEnabled(False)
        self._ai_thread.start()

    def _on_single_ai_done(self, image_path_str: str, description: str, error: str) -> None:
        image_path = Path(image_path_str)
        if not description:
            QMessageBox.critical(self, "AI Analysis Failed", "Could not analyze image.")
            self.status_label.setText("AI analysis failed.")
            return

        existing_caption = ""
        existing_sidecar = self.sidecar_path(image_path)
        if existing_sidecar.exists():
            try:
                existing_caption = existing_sidecar.read_text(encoding="utf-8").strip()
            except OSError:
                pass

        final_label = description
        if existing_caption:
            final_label = f"{description} (existing: {existing_caption})"

        dialog = AILabelDialog(self, final_label, image_path.name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ai_label = dialog.get_label()
            saved_ok, save_error = self.save_ai_sidecars(image_path, ai_label)
            if saved_ok:
                self.status_label.setText(f"Saved AI label: {self.ai_label_path(image_path).name}")
                self.add_caption_to_history(ai_label)
            else:
                QMessageBox.critical(self, "Save Failed", f"Could not save AI label:\n{save_error}")
                self.status_label.setText("Failed to save AI label.")
        else:
            self.status_label.setText("AI label discarded.")

    def _on_single_ai_finished(self) -> None:
        self._cleanup_ai_thread()
        has_image = bool(self.images) and self.current_index >= 0
        self.ai_button.setEnabled(has_image)
        self.batch_ai_button.setEnabled(bool(self.images))

    def get_candidate_tags(self) -> list[str]:
        if not hasattr(self, "candidate_tags_input"):
            return []

        raw = self.candidate_tags_input.toPlainText()
        if not raw.strip():
            return []

        parts = re.split(r"[\n,]", raw)
        tags: list[str] = []
        seen: set[str] = set()
        for part in parts:
            tag = re.sub(r"\s+", " ", part.strip())
            if not tag:
                continue
            low = tag.lower()
            if low in seen:
                continue
            seen.add(low)
            tags.append(tag)
        return tags

    def update_ui_state(self) -> None:
        has_image = bool(self.images) and self.current_index >= 0

        self.prev_button.setEnabled(has_image and self.current_index > 0)
        self.next_button.setEnabled(has_image and self.current_index < len(self.images) - 1)
        self.save_button.setEnabled(has_image)
        self.crop_button.setEnabled(has_image)
        self.crop_variant_button.setEnabled(has_image)
        self.clear_crop_button.setEnabled(has_image)
        has_backup = has_image and self.backup_exists_for(self.images[self.current_index]) is not None
        self.revert_crop_button.setEnabled(has_backup)
        self.ai_button.setEnabled(has_image)
        self.delete_button.setEnabled(has_image)
        self.caption_combo.setEnabled(has_image)
        
        has_images = bool(self.images)
        self.jump_spinbox.setEnabled(has_images)
        self.ai_range_start.setEnabled(has_images)
        self.ai_range_end.setEnabled(has_images)
        self.batch_ai_button.setEnabled(has_images)
        self.clear_ai_button.setEnabled(self.current_dir is not None)


def supported_formats_note() -> str:
    formats = sorted({f".{fmt.data().decode('ascii').lower()}" for fmt in QImageReader.supportedImageFormats()})
    return ", ".join(formats)


def main() -> None:
    app = QApplication(sys.argv)
    window = TaggerWindow()
    window.show()
    window.status_label.setText(f"Ready. Qt supports: {supported_formats_note()}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
