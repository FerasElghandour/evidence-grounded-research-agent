import unittest
from research import ResearchAgent, Evidence, Assessment, Answer

class ResearchTests(unittest.TestCase):
    def build(self, local=True, search=None, answer=None):
        doc = Evidence('local:1', 'Synthetic product note', 'fixture:product', 'Release year: 2020')
        return ResearchAgent(lambda q: [doc] if local else [],
            lambda q, d: Assessment(bool(d), 0.9 if d else 0, 'Fixture judgement'),
            search or (lambda q: [doc]),
            answer or (lambda q,d: Answer('Released in 2020.', (d[0].key,))),
            lambda q,h: q + ' [resolved from prior turn]', history_limit=2)
    def test_local_route(self):
        self.assertEqual(self.build().invoke('release?', 'a')['trace'], ('retrieve','assess'))
    def test_fallback_reassesses(self):
        self.assertEqual(self.build(False).invoke('release?', 'a')['trace'],
                         ('retrieve','assess','web_search','assess_web'))
    def test_search_failure_abstains(self):
        def fail(q): raise RuntimeError('fixture')
        self.assertEqual(self.build(False, fail).invoke('q','a')['answer'].citations, ())
    def test_unknown_citation_rejected(self):
        with self.assertRaises(ValueError):
            self.build(answer=lambda q,d: Answer('unsupported', ('invented',))).invoke('q','a')
    def test_memory_isolated_and_bounded(self):
        a=self.build(); a.invoke('one','a'); a.invoke('two','a'); r=a.invoke('three','a')
        self.assertIn('resolved',r['resolved_question']); self.assertEqual(len(a.history('a')),2)
        self.assertEqual(a.history('b'),())
    def test_invalid_confidence(self):
        with self.assertRaises(ValueError): Assessment(True,float('nan'),'invalid')

if __name__ == '__main__': unittest.main()
