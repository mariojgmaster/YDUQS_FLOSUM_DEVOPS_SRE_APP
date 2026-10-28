/**
 * Compare any number of lines without quadratic global memory.
 * Exact LCS on small sections, stable unique-line anchors on large sections.
 * If there are no stable anchors, conservatively show both changed blocks.
 */
const MAX_EXACT_CELLS = 360000;

/**
 * Summary of *accessible ZIP inventory paths*, not a comparison of file content.
 * A shared path is comparable only when both ZIP readers explicitly mark it previewable.
 * Never infer that same-named files contain equal code. This is a bounded (<=200 per
 * ZIP) read-only view over entries returned by the existing Apex reader.
 */
export function archivePathInventory(base, target) {
  const toMap = archive => {
    const entries = new Map();
    for (const entry of archive?.entries || []) {
      if (typeof entry?.path !== "string" || !entry.path || !entry.path.trim()) continue;
      const existing = entries.get(entry.path);
      // Duplicate paths cannot safely be treated as comparable.
      entries.set(entry.path, existing === undefined ? entry.previewable === true : false);
    }
    return entries;
  };
  const b = toMap(base), t = toMap(target);
  const rows = [...new Set([...b.keys(), ...t.keys()])].sort((a, bPath) => a.localeCompare(bPath))
    .map(path => {
      const inBase = b.has(path), inTarget = t.has(path);
      const status = !((inBase ? b.get(path) : true) && (inTarget ? t.get(path) : true)) ?
        "blocked" : inBase && inTarget ? "common" : inBase ? "base" : "target";
      const labels = {
        common: "Em ambos · conteúdo ainda não comparado",
        base: "Somente na base",
        target: "Somente no destino",
        blocked: "Pré-visualização indisponível"
      };
      return {path, status, label: labels[status], rowClass: "cd-zip-index-row cd-zip-index-row_" + status};
    });
  const counts = {common:0,base:0,target:0,blocked:0};
  for (const row of rows) counts[row.status]++;
  return {rows,counts};
}

export function commonPreviewPaths(base, target) {
  const b = new Set((base?.entries || [])
    .filter(x => x.previewable && typeof x.path === "string")
    .map(x => x.path));
  return [...new Set((target?.entries || [])
    .filter(x => x.previewable && b.has(x.path))
    .map(x => x.path))].sort((a, bPath) => a.localeCompare(bPath));
}

function stableAnchors(a, b, sa, ea, sb, eb) {
  const uniqueA = new Map();
  const uniqueB = new Map();
  for (let i=sa;i<ea;i++) uniqueA.set(a[i],uniqueA.has(a[i])?-1:i);
  for (let j=sb;j<eb;j++) uniqueB.set(b[j],uniqueB.has(b[j])?-1:j);
  const candidates=[];
  for(let i=sa;i<ea;i++) {
    if(uniqueA.get(a[i])===i && uniqueB.has(a[i]) && uniqueB.get(a[i])>=0)
      candidates.push({i,j:uniqueB.get(a[i])});
  }
  const tails=[];
  const previous=new Int32Array(candidates.length);
  for(let k=0;k<candidates.length;k++) {
    const value=candidates[k].j;
    let low=0,high=tails.length;
    while(low<high) {
      const mid=(low+high)>>>1;
      if(candidates[tails[mid]].j<value) low=mid+1;
      else high=mid;
    }
    previous[k]=low?tails[low-1]:-1;
    tails[low]=k;
  }
  const result=[];
  let current=tails.length?tails[tails.length-1]:-1;
  while(current>=0) {result.push(candidates[current]);current=previous[current];}
  return result.reverse();
}

export function lineDiff(before, after) {
  if (typeof before!=="string" || typeof after!=="string")
    return {error:"Não foi possível ler ambos os textos para comparação."};
  const a=before.split(/\r\n|\n|\r/),b=after.split(/\r\n|\n|\r/);
  const rows=[];
  let added=0,removed=0;
  const put=(kind,value,i,j)=>{
    rows.push({
      key:String(rows.length+1),text:value,oldLine:i===null?"":i+1,
      newLine:j===null?"":j+1,sign:kind==="added"?"+":kind==="removed"?"−":" ",
      rowClass:"cd-diff-line cd-diff-line_"+kind
    });
    if(kind==="added") added++;
    if(kind==="removed") removed++;
  };
  const work=[{sa:0,ea:a.length,sb:0,eb:b.length}];
  while(work.length) {
    const task=work.pop();
    if(task.equal!==undefined) {put("equal",a[task.equal],task.equal,task.equalB);continue;}
    let {sa,ea,sb,eb}=task;
    let prefix=0;
    while(sa+prefix<ea&&sb+prefix<eb&&a[sa+prefix]===b[sb+prefix])prefix++;
    let suffix=0;
    while(ea-suffix>sa+prefix&&eb-suffix>sb+prefix&&
      a[ea-suffix-1]===b[eb-suffix-1])suffix++;
    for(let i=0;i<prefix;i++)put("equal",a[sa+i],sa+i,sb+i);
    sa+=prefix;sb+=prefix;ea-=suffix;eb-=suffix;
    // The suffix must be popped AFTER the unmatched section.
    for(let k=suffix-1;k>=0;k--)work.push({equal:ea+k,equalB:eb+k});
    const n=ea-sa,m=eb-sb;
    if(!n||!m) {
      for(let i=sa;i<ea;i++)put("removed",a[i],i,null);
      for(let j=sb;j<eb;j++)put("added",b[j],null,j);
    } else if(n*m<=MAX_EXACT_CELLS) {
      const width=m+1;
      const dp=new Uint16Array((n+1)*width);
      for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)
        dp[i*width+j]=a[sa+i]===b[sb+j]?
          1+dp[(i+1)*width+j+1]:Math.max(dp[(i+1)*width+j],dp[i*width+j+1]);
      let i=0,j=0;
      while(i<n||j<m) {
        if(i<n&&j<m&&a[sa+i]===b[sb+j]){put("equal",a[sa+i],sa+i,sb+j);i++;j++;}
        else if(j<m&&(i===n||dp[i*width+j+1]>=dp[(i+1)*width+j])) {
          put("added",b[sb+j],null,sb+j);j++;
        } else {put("removed",a[sa+i],sa+i,null);i++;}
      }
    } else {
      const anchors=stableAnchors(a,b,sa,ea,sb,eb);
      if(!anchors.length) {
        for(let i=sa;i<ea;i++)put("removed",a[i],i,null);
        for(let j=sb;j<eb;j++)put("added",b[j],null,j);
      } else {
        const subtasks=[];
        let prevA=sa,prevB=sb;
        for(const anchor of anchors) {
          subtasks.push({sa:prevA,ea:anchor.i,sb:prevB,eb:anchor.j});
          subtasks.push({equal:anchor.i,equalB:anchor.j});
          prevA=anchor.i+1;prevB=anchor.j+1;
        }
        subtasks.push({sa:prevA,ea,sb:prevB,eb});
        for(let i=subtasks.length-1;i>=0;i--)work.push(subtasks[i]);
      }
    }
  }
  return {rows,added,removed,unchanged:added===0&&removed===0};
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
