from investigator import graphview
import re
html = graphview.build_graph_html([{"_id": 1, "text": "The bank's rate </script> x", "article_urls": []}], [])
for m in re.finditer(r"bank.{0,60}", html): print(repr(m.group(0)))
