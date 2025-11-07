import os, sys, csv
from textgrid import TextGrid

aligned_dir = sys.argv[1] if len(sys.argv) > 1 else "./aligned"

def tokenize(text):
    text = text.lower()
    tokens = []
    cur = []

    for ch in text:
        if ('a' <= ch <= 'z') or ('0' <= ch <= '9'):
            cur.append(ch)
        else:
            if cur:
                tokens.append(''.join(cur))
                cur = []
    if cur:
        tokens.append(''.join(cur))
#        print(tokens)
    return tokens

def read_lab_tokens(lab_path: str):
    with open(lab_path, "r", encoding="utf-8") as f:
        txt = f.read()
        return tokenize(txt)

def find_lab_path_for(tg_path: str, base_no_ext: str):
    """Try to locate the paired .lab file for a given TextGrid."""
    # 1) Same directory as the TextGrid
    candidate1 = base_no_ext + ".lab"
    if os.path.isfile(candidate1):
        return candidate1

    # 2) Replace '/aligned/' with '/corpus/' in the path (keep same basename)
    #    e.g., .../Assignment/aligned/speaker1/X.TextGrid -> .../Assignment/corpus/speaker1/X.lab
    if "/aligned/" in tg_path:
        candidate2 = tg_path.replace("/aligned/", "/corpus/")
        candidate2 = os.path.splitext(candidate2)[0] + ".lab"
        if os.path.isfile(candidate2):
            return candidate2

    # 3) Sibling "corpus" directory next to "aligned" (best-effort)
    #    .../aligned/.../X.TextGrid -> .../corpus/.../X.lab
    parts = tg_path.split(os.sep)
    j = parts.index("aligned")
    parts[j] = "corpus"
    candidate3 = os.path.splitext(os.sep.join(parts))[0] + ".lab"
    if os.path.isfile(candidate3):
        return candidate3

    return None

def write_tier_csv(tier, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["start_s", "end_s", "duration_s", "label"])
        for it in getattr(tier, "intervals", []):
            label = (it.mark or "").strip()
            if not label:
                # We still write blanks into the CSV? Usually not; skip to keep file clean.
                continue
            start = float(it.minTime)
            end = float(it.maxTime)
            w.writerow([f"{start:.6f}", f"{end:.6f}", f"{(end-start):.6f}", label])

for root, _, files in os.walk(aligned_dir):
    for f in files:
        if not f.endswith(".TextGrid"):
            continue

        tg_path = os.path.join(root, f)
        base_no_ext = os.path.splitext(tg_path)[0]
        wav_stem = os.path.splitext(f)[0]

        tg = TextGrid.fromFile(tg_path)

        tiers = { (t.name or "").lower() : t for t in tg.tiers }
        words_tier  = tiers.get("words")
        phones_tier = tiers.get("phones")

        # --- write per-file CSVs
        if words_tier:
            words_csv = f"{base_no_ext}.words.csv"
            write_tier_csv(words_tier, words_csv)
            print(f"-> wrote {os.path.relpath(words_csv, aligned_dir)}")
        else:
            print(f"[WARN] {f}: no 'words' tier")

        if phones_tier:
            phones_csv = f"{base_no_ext}.phones.csv"
            write_tier_csv(phones_tier, phones_csv)
            print(f"=> wrote {os.path.relpath(phones_csv, aligned_dir)}")
        else:
            print(f"[WARN] {f}: no 'phones' tier")

        # --- comparison with transcript .lab
        lab_path = find_lab_path_for(tg_path, base_no_ext)
        lab_tokens = read_lab_tokens(lab_path) if lab_path else None

        # Collect aligned words (normalize & tokenize all non-blank word labels)
        aligned_word_tokens = []
        null_intervals = 0
        if words_tier:
            for it in getattr(words_tier, "intervals", []):
                label = (it.mark or "").strip()
                if not label:
                    null_intervals += 1
                    continue
                aligned_word_tokens.extend(tokenize(label))

        # Summarize / compare
        if lab_tokens is None:
            print(f"[INFO] {wav_stem}: transcript .lab not found; skipped comparison.")
            continue

        # Compute missing words = in transcript but NOT in aligned words (case-insensitive, tokenized)
        set_transcript = set(lab_tokens)
        set_aligned    = set(aligned_word_tokens)

        missing = sorted(set_transcript - set_aligned)
        # Optionally, extras = words aligned but not in transcript:
        # extras = sorted(set_aligned - set_transcript)

        print(
            f"{wav_stem}: words={len(aligned_word_tokens)}, "
            f"null={null_intervals}, "
            f"transcript_tokens={len(lab_tokens)}, "
            f"missing_in_alignment={len(missing)}"
            + (f" -> {missing}" if missing else "")
        )

