# The array items MUST be parenthesized. jq operator precedence otherwise
# pipes "length" (a number) into the next ".result" lookup.
[
  (.result.toDeploy | length),
  (.result.conflicts | length),
  (.result.toDelete | length),
  (.result.ignored | length)
] | @tsv
