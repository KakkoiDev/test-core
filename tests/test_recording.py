"""Recorder boundaries, using the unit-nodeps Arrange/Act/Assert table recipe."""
import ast
import json
import unittest
from recording.flows import clean_flow, convert


class RecordingTest(unittest.TestCase):
    def test_typed_values_are_redacted_even_when_the_client_sends_plain_text(self):
        flow = {'title': 'private title', 'steps': [{'type': 'change', 'selectors': [['input:nth-of-type(1)']], 'value': 'private words'}]}
        clean = clean_flow(flow)
        self.assertEqual(clean['steps'][0]['value'], {'redacted': True, 'length': 13})
        self.assertNotIn('private', json.dumps(clean))

    def test_only_structural_selectors_and_loopback_navigation_survive(self):
        cases = [
            ({'type': 'click', 'selectors': [['aria/private name'], ['#private-name'], ['button:nth-of-type(2)']]}, 'button:nth-of-type(2)'),
            ({'type': 'navigate', 'url': 'https://example.invalid/private?token=x'}, None),
            ({'type': 'keyDown', 'key': 'p'}, None),
            ({'type': 'customStep', 'name': 'secret'}, None),
        ]
        for step, selector in cases:
            with self.subTest(step=step):
                steps = clean_flow({'steps': [step]})['steps']
                if selector:
                    self.assertEqual(steps[0]['selectors'], [[selector]])
                else:
                    self.assertEqual(steps, [])

    def test_navigation_strips_credentials_route_query_and_fragment_by_default(self):
        flow = clean_flow({'steps': [{'type': 'navigate', 'url': 'http://user:pass@127.0.0.1:1234/private?token=x#secret'}]})
        self.assertEqual(flow['steps'][0]['url'], 'http://127.0.0.1:1234/')

    def test_converter_leaves_an_explicit_failing_assertion_in_both_languages(self):
        for target in ('python', 'javascript'):
            with self.subTest(target=target):
                source = convert({'steps': [{'type': 'click', 'selectors': [['button:nth-of-type(1)']]}]}, target=target)
                self.assertIn('Add the expected outcome', source)
                self.assertIn('button:nth-of-type(1)', source)
                if target == 'python':
                    ast.parse(source)
                    self.assertIn('assert False', source)
                else:
                    self.assertIn('throw new Error', source)

    def test_converter_does_not_replay_redaction_objects_as_strings(self):
        source = convert({'steps': [{'type': 'change', 'selectors': [['input:nth-of-type(1)']], 'value': 'private words'}]}, target='python')
        self.assertNotIn('private words', source)
        self.assertNotIn('.fill(', source)
        self.assertIn('Supply a synthetic value', source)

    def test_unknown_target_and_invalid_flows_fail_closed(self):
        for flow in (None, [], {'steps': 'oops'}, {'steps': [None]}):
            with self.subTest(flow=flow):
                with self.assertRaises(ValueError):
                    clean_flow(flow)
        with self.assertRaises(ValueError):
            convert({'steps': []}, target='shell')

    def test_normalization_is_idempotent_and_bounded(self):
        flow = clean_flow({'steps': [{'type': 'click', 'selectors': [['button:nth-of-type(1)']]}] * 20}, max_steps=5)
        self.assertEqual(len(flow['steps']), 5)
        self.assertEqual(clean_flow(flow), flow)


class FocusRecordingTest(unittest.TestCase):
    def test_focus_and_blur_keep_only_structural_targets(self):
        flow = clean_flow({'steps': [
            {'type': kind, 'selectors': [['#secret'], ['input:nth-of-type(1)']], 'value': 'private', 'relatedTarget': 'secret'}
            for kind in ('focus', 'blur')
        ]})
        self.assertEqual(flow['steps'], [
            {'type': kind, 'selectors': [['input:nth-of-type(1)']]} for kind in ('focus', 'blur')
        ])
        for target in ('python', 'javascript'):
            source = convert(flow, target=target)
            self.assertIn('.focus()', source)
            self.assertIn('.blur()', source)
            self.assertIn('Add the expected outcome', source)
            self.assertNotIn('private', source)
