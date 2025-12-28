# data_annihilator/spec/validate.py
# Validation for all schema types from DocumentSpec.py

from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, Dict, List, Sequence, Tuple

from .DocumentSpec import (
    BBox,
    BlockSpec,
    ColorRGB,
    DocumentSpec,
    FontSpec,
    PageSpec,
    StyleSpec,
)


class ValidationError(Exception):
    """Raised when the spec is invalid."""
    pass


class ValidationWarning:
    __slots__ = ("path", "message")

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message

    def __repr__(self) -> str:
        return f"ValidationWarning(path={self.path!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _err(path: str, msg: str) -> ValidationError:
    return ValidationError(f"{path}: {msg}")


def _is_number(x: Any) -> bool:
    # bool is a subclass of int, exclude it
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _within_01(x: float) -> bool:
    return 0.0 <= x <= 1.0


def _get_page_size(doc: DocumentSpec, page: PageSpec) -> Tuple[float, float]:
    return page.size if page.size is not None else doc.page_size


def _bbox_inside_page(b: BBox, page_w: float, page_h: float) -> bool:
    return (b.x >= 0.0) and (b.y >= 0.0) and (b.x2 <= page_w) and (b.y2 <= page_h)


def _require_dataclass(path: str, obj: Any) -> None:
    if not is_dataclass(obj):
        raise _err(path, f"Expected dataclass instance, got {type(obj).__name__}")


def validate_document(
    doc: DocumentSpec,
    *,
    strict: bool = True,
    check_bounds: bool = True,
    allow_empty_pages: bool = True,
) -> List[ValidationWarning]:
    warnings: List[ValidationWarning] = []

    _require_dataclass("document", doc)
    _validate_document_fields(doc, "document")

    _validate_fonts(doc.fonts, "document.fonts")
    _validate_assets(doc.assets, "document.assets")

    if not isinstance(doc.pages, list):
        raise _err("document.pages", "Must be a list of PageSpec")
    if len(doc.pages) == 0:
        raise _err("document.pages", "Must contain at least 1 page")

    _validate_unique_ids([p.page_id for p in doc.pages], "document.pages", id_name="page_id")

    for pi, page in enumerate(doc.pages):
        ppath = f"document.pages[{pi}]"
        _validate_page(
            doc,
            page,
            ppath,
            warnings,
            strict=strict,
            check_bounds=check_bounds,
            allow_empty_pages=allow_empty_pages,
        )

    return warnings


def _validate_document_fields(doc: DocumentSpec, path: str) -> None:
    if not _is_str(doc.doc_id) or not doc.doc_id:
        raise _err(f"{path}.doc_id", "Must be a non-empty string")

    if not _is_str(doc.version) or not doc.version:
        raise _err(f"{path}.version", "Must be a non-empty string")

    if doc.seed is None:
        raise _err(f"{path}.seed", "Seed must not be None after __post_init__")
    if not isinstance(doc.seed, int) or isinstance(doc.seed, bool):
        raise _err(f"{path}.seed", "Must be an int")

    if not isinstance(doc.page_size, tuple) or len(doc.page_size) != 2:
        raise _err(f"{path}.page_size", "Must be a tuple (width, height)")
    w, h = doc.page_size
    if not _is_number(w) or not _is_number(h):
        raise _err(f"{path}.page_size", "Width/height must be numbers")
    if w <= 0 or h <= 0:
        raise _err(f"{path}.page_size", "Width/height must be > 0")

    if doc.page_margin is not None:
        if not isinstance(doc.page_margin, tuple) or len(doc.page_margin) != 4:
            raise _err(f"{path}.page_margin", "Must be a tuple (left, top, right, bottom)")
        for i, v in enumerate(doc.page_margin):
            if not _is_number(v):
                raise _err(f"{path}.page_margin[{i}]", "Must be a number")
            if v < 0:
                raise _err(f"{path}.page_margin[{i}]", "Must be >= 0")

    if not isinstance(doc.meta, dict):
        raise _err(f"{path}.meta", "Must be a dict")


def _validate_fonts(fonts: Dict[str, FontSpec], path: str) -> None:
    if not isinstance(fonts, dict):
        raise _err(path, "Must be a dict[str, FontSpec]")

    for k, v in fonts.items():
        if not _is_str(k) or not k:
            raise _err(f"{path} (key)", "Font map keys must be non-empty strings")
        _require_dataclass(f"{path}[{k!r}]", v)

        if not _is_str(v.name) or not v.name:
            raise _err(f"{path}[{k!r}].name", "Must be a non-empty string")
        if v.ttf_path is not None and not _is_str(v.ttf_path):
            raise _err(f"{path}[{k!r}].ttf_path", "Must be a string or None")


def _validate_assets(assets: Dict[str, str], path: str) -> None:
    if not isinstance(assets, dict):
        raise _err(path, "Must be a dict[str, str]")

    for k, v in assets.items():
        if not _is_str(k) or not k:
            raise _err(f"{path} (key)", "Asset map keys must be non-empty strings")
        if not _is_str(v) or not v:
            raise _err(f"{path}[{k!r}]", "Asset paths must be non-empty strings")


def _validate_page(
    doc: DocumentSpec,
    page: PageSpec,
    path: str,
    warnings: List[ValidationWarning],
    *,
    strict: bool,
    check_bounds: bool,
    allow_empty_pages: bool,
) -> None:
    _require_dataclass(path, page)

    if not _is_str(page.page_id) or not page.page_id:
        raise _err(f"{path}.page_id", "Must be a non-empty string")

    if page.size is not None:
        if not isinstance(page.size, tuple) or len(page.size) != 2:
            raise _err(f"{path}.size", "Must be a tuple (width, height) or None")
        pw, ph = page.size
        if not _is_number(pw) or not _is_number(ph):
            raise _err(f"{path}.size", "Width/height must be numbers")
        if pw <= 0 or ph <= 0:
            raise _err(f"{path}.size", "Width/height must be > 0")

    if not isinstance(page.meta, dict):
        raise _err(f"{path}.meta", "Must be a dict")

    if not isinstance(page.blocks, list):
        raise _err(f"{path}.blocks", "Must be a list[BlockSpec]")

    if (not allow_empty_pages) and len(page.blocks) == 0:
        raise _err(f"{path}.blocks", "Page must contain at least one block")

    _validate_unique_ids([b.block_id for b in page.blocks], f"{path}.blocks", id_name="block_id")

    page_w, page_h = _get_page_size(doc, page)

    for bi, block in enumerate(page.blocks):
        bpath = f"{path}.blocks[{bi}]"
        _validate_block(block, bpath, warnings, strict=strict)

        if check_bounds and not _bbox_inside_page(block.bbox, page_w, page_h):
            msg = f"bbox is outside page bounds (page_size={page_w}x{page_h})"
            if strict:
                raise _err(f"{bpath}.bbox", msg)
            warnings.append(ValidationWarning(f"{bpath}.bbox", msg))


_ALLOWED_KINDS = {"text", "rect", "line", "image"}
_ALLOWED_ALIGN = {"left", "center", "right"}


def _validate_block(
    block: BlockSpec,
    path: str,
    warnings: List[ValidationWarning],
    *,
    strict: bool,
) -> None:
    _require_dataclass(path, block)

    if not _is_str(block.block_id) or not block.block_id:
        raise _err(f"{path}.block_id", "Must be a non-empty string")

    if not _is_str(block.kind) or block.kind not in _ALLOWED_KINDS:
        raise _err(f"{path}.kind", f"Must be one of {_ALLOWED_KINDS}")

    _validate_bbox(block.bbox, f"{path}.bbox")
    _validate_style(block.style, f"{path}.style")

    if not isinstance(block.content, dict):
        raise _err(f"{path}.content", "Must be a dict")

    if not isinstance(block.meta, dict):
        raise _err(f"{path}.meta", "Must be a dict")

    if block.kind == "text":
        txt = block.content.get("text", None)
        if not _is_str(txt):
            raise _err(f"{path}.content['text']", "Text blocks must include content['text'] as a string")

    if block.kind == "image":
        asset = block.content.get("asset", None)
        pth = block.content.get("path", None)
        if asset is None and pth is None:
            raise _err(f"{path}.content", "Image blocks must include content['asset'] or content['path']")
        if asset is not None and not _is_str(asset):
            raise _err(f"{path}.content['asset']", "Must be a string")
        if pth is not None and not _is_str(pth):
            raise _err(f"{path}.content['path']", "Must be a string")

    if block.kind == "line":
        x1 = block.content.get("x1")
        y1 = block.content.get("y1")
        x2 = block.content.get("x2")
        y2 = block.content.get("y2")
        if any(v is not None for v in (x1, y1, x2, y2)):
            for name, v in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
                if not _is_number(v):
                    raise _err(f"{path}.content['{name}']", "Must be a number when provided")


def _validate_bbox(b: BBox, path: str) -> None:
    _require_dataclass(path, b)

    for name in ("x", "y", "w", "h"):
        v = getattr(b, name)
        if not _is_number(v):
            raise _err(f"{path}.{name}", "Must be a number")

    if b.w <= 0:
        raise _err(f"{path}.w", "Must be > 0")
    if b.h <= 0:
        raise _err(f"{path}.h", "Must be > 0")


def _validate_style(s: StyleSpec, path: str) -> None:
    _require_dataclass(path, s)

    if not _is_str(s.font_name) or not s.font_name:
        raise _err(f"{path}.font_name", "Must be a non-empty string")

    if not _is_number(s.font_size) or s.font_size <= 0:
        raise _err(f"{path}.font_size", "Must be a number > 0")

    if not _is_number(s.line_width) or s.line_width < 0:
        raise _err(f"{path}.line_width", "Must be a number >= 0")

    if not _is_str(s.align) or s.align not in _ALLOWED_ALIGN:
        raise _err(f"{path}.align", f"Must be one of {_ALLOWED_ALIGN}")

    if s.leading is not None:
        if not _is_number(s.leading) or s.leading <= 0:
            raise _err(f"{path}.leading", "Must be a number > 0 or None")

    _validate_color(s.fill, f"{path}.fill")
    _validate_color(s.stroke, f"{path}.stroke")


def _validate_color(c: ColorRGB, path: str) -> None:
    _require_dataclass(path, c)

    for name in ("r", "g", "b"):
        v = getattr(c, name)
        if not _is_number(v):
            raise _err(f"{path}.{name}", "Must be a number in range [0, 1]")
        if not _within_01(float(v)):
            raise _err(f"{path}.{name}", "Must be in range [0, 1]")


def _validate_unique_ids(ids: Sequence[str], path: str, *, id_name: str) -> None:
    seen = set()
    for i, _id in enumerate(ids):
        if not isinstance(_id, str) or not _id:
            raise _err(f"{path}[{i}].{id_name}", "Must be a non-empty string")
        if _id in seen:
            raise _err(f"{path}[{i}].{id_name}", f"Duplicate id: {_id!r}")
        seen.add(_id)

