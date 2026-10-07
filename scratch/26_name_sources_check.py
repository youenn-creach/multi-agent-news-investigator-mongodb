from investigator.graph import _name_sources
src = [{"source": "euronews.com"}, {"source": "reuters.com"}, {"source": "cnbc.com"}]
for note in ["Sources [0] and [1] report it.", "Sources conflict (sources 1,2).", "Source 2 says 2.5% and the rate was 2.25%.", "Deposit rate 2.5% (2.25%) unchanged.", "see source 9"]:
    print(repr(note), "->", repr(_name_sources(note, src)))
