---
type: regex
target: last_message
pattern: "AVIF-MAP|avif-map|asset map|Asset map|intrinsic"
match: contains
---

`background-size` needs each image's intrinsic width (rule 4). The converter generates the map; the
reader has to actually surface it, because the next stage reads those numbers.
