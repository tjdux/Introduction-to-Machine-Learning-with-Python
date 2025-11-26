from pathlib import Path
import json, re, urllib.parse

# === 설정 ===
GITHUB_USER   = "tjdux"
GITHUB_REPO   = "Introduction-to-Machine-Learning-with-Python"
GITHUB_BRANCH = "main"
ROOT = Path(".")
IPYNB_GLOBS = ["**/*.ipynb"]
MD_GLOBS    = ["**/*.md"]
README_PATH = ROOT / "README.md"
IGNORE_DIR_KEYWORDS = [".ipynb_checkpoints", ".git", ".github"]

# "파이썬 라이브러리를 활용한 머신러닝" 책 표지 이미지
BOOK_COVER_IMAGE_URL = "img/B3887932883_l.jpg"
# =============

def is_ignored(p: Path) -> bool:
    s = p.as_posix()
    return any(x in s for x in IGNORE_DIR_KEYWORDS)

def make_gh_file_url(rel_path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{urllib.parse.quote(rel_path)}"

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)")

def extract_headings_from_markdown_text(md_text: str):
    """헤딩 (level, title) 목록 추출"""
    out = []
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if not m: continue
        level = len(m.group(1))
        title = m.group(2).strip()
        title = re.sub(r"\s+#+\s*$", "", title)  # 끝 해시 제거
        out.append((level, title))
    return out

def github_anchor_from_title(title: str) -> str:
    """헤딩 텍스트를 GitHub의 자동 생성 앵커 ID 형식으로 변환"""
    # 1. 소문자 변환
    anchor = title.lower()
    
    # 2. 공백과 연속된 공백을 하이픈(-)으로 변환
    anchor = re.sub(r'\s+', '-', anchor)
    
    # 3. GitHub가 보통 제거하는 특수 문자 제거
    # 영문, 숫자, 한글(\uAC00-\uD7A3), 하이픈(-)을 제외한 모든 문자 제거
    anchor = re.sub(r'[^\w\uAC00-\uD7A3-]+', '', anchor) 
    
    return anchor


def iter_md_cells_from_ipynb(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception:
        return
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown": continue
        src = "".join(cell.get("source", []))
        if src.strip(): yield src

def main():
    ipynbs, mds = [], []
    for p in ROOT.glob("**/*"):
        if not p.is_file() or is_ignored(p): continue
        if p.suffix == ".ipynb": ipynbs.append(p)
        elif p.suffix == ".md" and p.name != "README.md": mds.append(p)
    ipynbs.sort()
    mds.sort()

    lines = []
    
    lines.append(f"<p align=\"center\"><img src=\"{BOOK_COVER_IMAGE_URL}\" alt=\"파이썬 라이브러리를 활용한 머신러닝\" width=\"300\"></p>\n")
    
    lines.append("# Machine Learning Notes (Auto TOC)\n")
    lines.append(f"- GitHub: https://github.com/{GITHUB_USER}/{GITHUB_REPO}\n")

    # === ipynb ===
    if ipynbs:
        lines.append("## 📓 Notebooks\n")
        for nb_path in ipynbs:
            rel = nb_path.as_posix()
            gh = make_gh_file_url(rel)
            title = nb_path.name
            lines.append(f"- **[{title}]({gh})**")
            sub = []
            for src in iter_md_cells_from_ipynb(nb_path):
                for lvl, htitle in extract_headings_from_markdown_text(src):
                    indent = "  " * min(lvl, 6)
                    anchor = github_anchor_from_title(htitle)
                    sub.append(f"{indent}- [{htitle}]({gh}#{anchor})")
            if sub: lines.extend(sub)
            lines.append("")

    # === md ===
    if mds:
        lines.append("## 📝 Markdown Notes\n")
        for md_path in mds:
            rel = md_path.as_posix()
            gh = make_gh_file_url(rel)
            title = md_path.name
            lines.append(f"- **[{title}]({gh})**")
            try:
                text = md_path.read_text(encoding="utf-8")
            except Exception:
                continue
            for lvl, htitle in extract_headings_from_markdown_text(text):
                indent = "  " * min(lvl, 6)
                anchor = github_anchor_from_title(htitle)
                lines.append(f"{indent}- [{htitle}]({gh}#{anchor})")
            lines.append("")

    README_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"✓ Wrote {README_PATH}")

if __name__ == "__main__":
    main()