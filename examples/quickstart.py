"""Offline example using the public implementation; see README for evidence scope."""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

from research import ResearchAgent,Evidence,Assessment,Answer
doc=Evidence('local:1','Synthetic product note','fixture:product','Release year: 2020')
agent=ResearchAgent(lambda q:[doc],lambda q,d:Assessment(bool(d),.9 if d else 0,'Fixture judgement'),lambda q:[doc],lambda q,d:Answer('Released in 2020.',(d[0].key,)),lambda q,h:q,history_limit=2)
r=agent.invoke('release?','a')
print({'answer':r['answer'].text,'citations':r['answer'].citations,'trace':r['trace']})
