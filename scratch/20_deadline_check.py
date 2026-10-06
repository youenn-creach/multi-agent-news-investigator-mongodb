"""A provider that hangs must be abandoned after the deadline, and the fallback must answer."""
import time
from langchain_core.runnables import RunnableLambda
from investigator.llm import with_deadline

hang = RunnableLambda(lambda x: time.sleep(60) or "never")
ok = RunnableLambda(lambda x: "fallback answered")
chain = with_deadline(hang, 2).with_fallbacks([with_deadline(ok, 2)])
t = time.time()
print(chain.invoke("hi"), f"after {time.time() - t:.1f}s (a hung provider cost 2s, not 60s)")
