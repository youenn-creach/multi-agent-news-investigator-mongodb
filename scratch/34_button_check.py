from streamlit.testing.v1 import AppTest
at = AppTest.from_file("../app.py", default_timeout=60).run()
primary = next(b for b in at.button if b.label == "Investigate")
primary.click().run()
print("empty URL ->", [w.value for w in at.warning], "| exceptions:", len(at.exception))
