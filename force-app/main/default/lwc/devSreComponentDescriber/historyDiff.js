/**
 * M2B.1: text comparison inside TWO typed Component Histories only.
 * In-memory, bounded and read-only. No inference of canonical version or deploy.
 */
const MAX_LINES = 600;
const MAX_CELLS = 360000;

export function commonPreviewPaths(base, target) {
  const b = new Set((base?.entries || [])
    .filter(x => x.previewable && typeof x.path === "string")
    .map(x => x.path));
  return [...new Set((target?.entries || [])
    .filter(x => x.previewable && b.has(x.path))
    .map(x => x.path))].sort((a, bPath) => a.localeCompare(bPath));
}

export function lineDiff(before, after) {
  if (typeof before !== "string" || typeof after !== "string") {
    return { error: "Não foi possível ler ambos os textos para comparação." };
  }
  // Compare actual text content, preserving case, indentation and final newline.
  // Treat CRLF/LF equivalently; do not trim any source content.
  const a = before.split(/\r\n|\n|\r/);
  const b = after.split(/\r\n|\n|\r/);
  if (a.length > MAX_LINES || b.length > MAX_LINES ||
      a.length * b.length > MAX_CELLS) {
    return { error: "O arquivo excede o limite de 600 linhas por lado para Diff visual. Use o explorador ZIP para visualizar o conteúdo." };
  }
  const width = b.length + 1;
  const dp = new Uint16Array((a.length + 1) * width);
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      const index = i * width + j;
      dp[index] = a[i] === b[j] ? 1 + dp[(i + 1) * width + j + 1]
        : Math.max(dp[(i + 1) * width + j], dp[i * width + j + 1]);
    }
  }
  let i = 0; let j = 0; let number = 0; let added = 0; let removed = 0;
  const rows = [];
  const put = (kind, text, oldLine, newLine) => {
    rows.push({
      key: String(++number),
      text,
      oldLine: oldLine === null ? "" : oldLine,
      newLine: newLine === null ? "" : newLine,
      sign: kind === "added" ? "+" : kind === "removed" ? "−" : " ",
      rowClass: "cd-diff-line cd-diff-line_" + kind
    });
  };
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) {
      put("equal", a[i], i + 1, j + 1); i++; j++;
    } else if (j < b.length &&
      (i === a.length || dp[i * width + j + 1] >= dp[(i + 1) * width + j])) {
      put("added", b[j], null, j + 1); added++; j++;
    } else {
      put("removed", a[i], i + 1, null); removed++; i++;
    }
  }
  return { rows, added, removed, unchanged: added === 0 && removed === 0 };
}

/**
 * Transform an already-bounded LCS diff into two visually aligned panes.
 * Opposing additions/removals in one hunk are paired by ordinal. This is
 * presentation-only: no artificial assumption that individual lines match.
 */
export function sideBySideDiff(diff) {
  if (!diff || diff.error || !Array.isArray(diff.rows)) return [];
  const paired = [];
  const asCell = (item, side) => item ? {
    text: item.text,
    line: side === "old" ? item.oldLine : item.newLine,
    className: "cd-diff-cell cd-diff-cell_" + (side === "old" ? "removed" : "added")
  } : { text: "", line: "", className: "cd-diff-cell cd-diff-cell_empty" };
  for (let index = 0; index < diff.rows.length;) {
    const row = diff.rows[index];
    if (row.rowClass.endsWith("cd-diff-line_equal")) {
      paired.push({
        key: String(paired.length + 1),
        changed: false,
        left: { text: row.text, line: row.oldLine, className: "cd-diff-cell cd-diff-cell_equal" },
        right: { text: row.text, line: row.newLine, className: "cd-diff-cell cd-diff-cell_equal" }
      });
      index++;
      continue;
    }
    const removals = [];
    const additions = [];
    while (index < diff.rows.length && !diff.rows[index].rowClass.endsWith("cd-diff-line_equal")) {
      const current = diff.rows[index++];
      if (current.rowClass.endsWith("cd-diff-line_removed")) removals.push(current);
      else if (current.rowClass.endsWith("cd-diff-line_added")) additions.push(current);
    }
    for (let i = 0; i < Math.max(removals.length, additions.length); i++) {
      paired.push({
        key: String(paired.length + 1),
        changed: true,
        left: asCell(removals[i], "old"),
        right: asCell(additions[i], "new")
      });
    }
  }
  return paired;
}
