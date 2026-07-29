"""
Repair card relations by parsing [[wikilinks]] from card bodies.

When the RelationRepairEngine resolves zero (all hash-based IDs are random),
this script falls back to extracting wikilinks from card body content,
matching them against actual card titles, and rewriting YAML frontmatter.

Usage:
    cd E:/hermes-mini-os
    python repair_relations_from_wikilinks.py

Expected: 154/196 cards fixed, ~526/784 wikilinks resolved.
Remaining unmatched wikilinks point to external content (video IDs, etc.).
"""
import re
import yaml
import glob
import os

CARDS_DIR = 'knowledge/cards'


def normalize(text: str) -> str:
    """Strip non-word, non-CJK characters for fuzzy matching."""
    return re.sub(r'[^\w\u4e00-\u9fff]', '', text.lower().strip())


def build_title_index(cards_dir: str) -> dict[str, str]:
    """Build {title: id} index from all card YAML frontmatter."""
    title_to_id = {}
    for f in glob.glob(os.path.join(cards_dir, '*.md')):
        with open(f, 'r', encoding='utf-8') as fh:
            raw = fh.read()
        parts = raw.split('---\n')
        if len(parts) >= 2:
            try:
                fm = yaml.safe_load(parts[1])
            except Exception:
                continue
            if fm and 'title' in fm and 'id' in fm:
                title_to_id[fm['title'].strip()] = fm['id']
    return title_to_id


def repair(cards_dir: str) -> dict:
    """Main repair: parse wikilinks, resolve to IDs, rewrite cards."""
    WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
    title_to_id = build_title_index(cards_dir)
    norm_to_id = {normalize(t): tid for t, tid in title_to_id.items()}

    fixed = 0
    total_wikilinks = 0
    total_resolved = 0
    unmatched = set()

    for filepath in glob.glob(os.path.join(cards_dir, '*.md')):
        with open(filepath, 'r', encoding='utf-8') as fh:
            raw = fh.read()

        parts = raw.split('---\n')
        if len(parts) < 4:
            continue

        try:
            fm = yaml.safe_load(parts[1])
        except Exception:
            continue

        if not fm or 'title' not in fm:
            continue

        # Body starts after the second --- block
        body_start = raw.index('---\n', raw.index('---\n') + 4) + 4
        body = raw[body_start:]

        wikilinks = WIKILINK_RE.findall(body)
        resolved = []

        for wl in wikilinks:
            total_wikilinks += 1
            wl_clean = wl.strip()

            # Layer 1: exact title match
            if wl_clean in title_to_id:
                resolved.append(f'related:{title_to_id[wl_clean]}')
                total_resolved += 1
                continue

            # Layer 2: normalized match
            n = normalize(wl_clean)
            if n in norm_to_id:
                resolved.append(f'related:{norm_to_id[n]}')
                total_resolved += 1
                continue

            # Layer 3: substring match
            found = False
            for title, tid in title_to_id.items():
                if wl_clean in title or title in wl_clean:
                    resolved.append(f'related:{tid}')
                    total_resolved += 1
                    found = True
                    break

            if not found:
                unmatched.add(wl_clean)

        # Only rewrite if relations changed
        old_rels = fm.get('relations', [])
        if resolved and set(resolved) != set(old_rels):
            fm['relations'] = resolved
            new_raw = (
                '---\n'
                + yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
                + '---\n'
                + body
            )
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(new_raw)
            fixed += 1

    return {
        'cards_fixed': fixed,
        'total_wikilinks': total_wikilinks,
        'total_resolved': total_resolved,
        'unmatched_count': len(unmatched),
        'unmatched_sample': sorted(unmatched)[:25],
    }


if __name__ == '__main__':
    result = repair(CARDS_DIR)
    print(f"Cards with updated relations: {result['cards_fixed']}")
    print(f"Total wikilinks found: {result['total_wikilinks']}")
    print(f"Total resolved: {result['total_resolved']}")
    print(f"Unmatched wikilink titles ({result['unmatched_count']}):")
    for t in result['unmatched_sample']:
        print(f'  - [[{t}]]')
