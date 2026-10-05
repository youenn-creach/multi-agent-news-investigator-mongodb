from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app.py", default_timeout=60).run()
for page in list(at.sidebar.radio[0].options):
    at.sidebar.radio[0].set_value(page).run()
    print(f"{'ERR ' if at.exception else 'OK  '} {page}", [e.value[:100] for e in at.exception])
