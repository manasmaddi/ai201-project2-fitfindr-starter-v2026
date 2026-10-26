"""Focused Unit 3 checks. Run with: python -m unittest test_unit3 -v"""

import unittest
from unittest.mock import patch

import config
import tools
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]  # S/M butterfly tee, $18, no brand

    def test_search_filters_all_inputs_and_includes_budget_boundary(self):
        matches = tools.search_listings('GRAPHIC tee', 'm', 18)
        self.assertEqual([item['id'] for item in matches], ['lst_002', 'lst_017'])
        self.assertTrue(all(item['price'] <= 18 for item in matches))

    def test_search_empty_cases(self):
        for description, size, budget in [
            ('', None, None), ('   ', None, None),
            ('unicorn spacesuit', None, None), ('tee', None, 0),
            ('tee', 'XXS', 5),
        ]:
            with self.subTest(description=description, size=size, budget=budget):
                self.assertEqual(tools.search_listings(description, size, budget), [])

    def test_size_tokens_do_not_confuse_clothing_and_shoes(self):
        for requested, listed, expected in [
            ('m', 'S/M', True), ('S', 'US 9', False),
            ('L', 'XL (oversized)', False), ('8', 'US 8', True),
            ('8', 'US 8.5', False), ('W30', 'W30 L30', True),
            ('W30 L32', 'W30 L30', False),
            ('One Size', 'One Size (adjustable)', True),
            ('M', 'One Size / Oversized', False),
        ]:
            with self.subTest(requested=requested, listed=listed):
                self.assertEqual(
                    tools._size_tokens(requested) <= tools._size_tokens(listed), expected
                )

    def test_ranking_and_result_limit(self):
        matches = tools.search_listings('vintage graphic tee')
        self.assertEqual(matches[0]['id'], 'lst_002')
        with patch.object(config, 'SEARCH_RESULT_LIMIT', 1):
            self.assertEqual(tools.search_listings('vintage graphic tee'), matches[:1])

    @patch('tools.generate', return_value='Pair the tee with your dark wash jeans.')
    def test_outfit_uses_saved_pieces_and_handles_missing_brand(self, generate):
        result = tools.suggest_outfit(self.item, get_example_wardrobe())
        self.assertTrue(result)
        prompt = generate.call_args.args[0]
        self.assertIn(self.item['title'], prompt)
        self.assertIn('Baggy straight-leg jeans, dark wash', prompt)
        self.assertIn('Name the wardrobe pieces exactly', prompt)

    @patch('tools.generate', return_value='Try neutral trousers and white sneakers.')
    def test_empty_wardrobe_requests_general_advice(self, generate):
        self.assertTrue(tools.suggest_outfit(self.item, get_empty_wardrobe()))
        self.assertIn('The wardrobe is empty', generate.call_args.args[0])
        self.assertIn('Do not claim anything is in their wardrobe', generate.call_args.args[0])

    @patch('tools.generate')
    def test_empty_outfit_skips_model(self, generate):
        for outfit in ('', ' \n\t'):
            self.assertEqual(
                tools.create_fit_card(outfit, self.item),
                'No outfit suggestion was provided. Add an outfit before creating a fit card.',
            )
        generate.assert_not_called()

    @patch('tools.generate', return_value='A butterfly find for $18.00 on depop. Y2K vibes.')
    def test_caption_prompt_includes_item_outfit_price_and_platform(self, generate):
        self.assertTrue(tools.create_fit_card('baggy jeans', self.item))
        prompt = generate.call_args.args[0]
        for fact in (self.item['title'], '$18.00', 'depop', 'baggy jeans'):
            self.assertIn(fact, prompt)

    @patch('tools.generate', return_value='  ')
    def test_blank_model_text_has_nonempty_fallbacks(self, generate):
        self.assertTrue(tools.suggest_outfit(self.item, get_empty_wardrobe()).strip())
        self.assertIn('$18.00', tools.create_fit_card('baggy jeans', self.item))


class AgentTests(unittest.TestCase):
    def test_parse_explicit_filters(self):
        from agent import _parse_query
        for query, description, size, price in [
            ('looking for a vintage graphic tee under $30, size M', 'vintage graphic tee', 'M', 30),
            ('platform sneakers size US 8.5', 'platform sneakers', 'US 8.5', None),
            ('denim size W30 L30 at most $38', 'denim', 'W30 L30', 38),
            ('tee size S/M max $18.50', 'tee', 'S/M', 18.5),
            ('hat size One Size', 'hat', 'One Size', None),
            ('tee', 'tee', None, None),
            ('tee under $0', 'tee', None, 0),
        ]:
            with self.subTest(query=query):
                self.assertEqual(_parse_query(query), {
                    'description': description, 'size': size, 'max_price': price,
                })

    def test_happy_path_passes_stored_state_to_each_tool(self):
        from agent import run_agent
        with patch('agent.suggest_outfit', return_value='jeans and sneakers') as outfit:
            with patch('agent.create_fit_card', return_value='A butterfly find. Y2K vibes.') as card:
                wardrobe = get_example_wardrobe()
                session = run_agent('graphic tee size M under $18', wardrobe)
        self.assertIsNone(session['error'])
        self.assertIs(session['selected_item'], session['search_results'][0])
        self.assertIs(outfit.call_args.args[0], session['selected_item'])
        self.assertIs(outfit.call_args.args[1], session['wardrobe'])
        card.assert_called_once_with(session['outfit_suggestion'], session['selected_item'])
        self.assertEqual(session['fit_card'], 'A butterfly find. Y2K vibes.')

    def test_impossible_query_stops_before_model_tools(self):
        from agent import run_agent
        with patch('agent.suggest_outfit') as outfit, patch('agent.create_fit_card') as card:
            session = run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
        outfit.assert_not_called()
        card.assert_not_called()
        self.assertEqual(session['search_results'], [])
        for field in ('selected_item', 'outfit_suggestion', 'fit_card'):
            self.assertIsNone(session[field])
        for change in ('keywords', 'size', 'price ceiling'):
            self.assertIn(change, session['error'])

    def test_empty_query_also_stops_early(self):
        from agent import run_agent
        with patch('agent.suggest_outfit') as outfit:
            session = run_agent('  ', get_empty_wardrobe())
        outfit.assert_not_called()
        self.assertIsNotNone(session['error'])
        self.assertIsNone(session['fit_card'])

    def test_iteration_limit_stops_before_model_calls(self):
        from agent import run_agent
        with patch.object(config, 'MAX_ITERATIONS', 2), patch('agent.suggest_outfit') as outfit:
            with self.assertRaisesRegex(RuntimeError, 'MAX_ITERATIONS'):
                run_agent('graphic tee', get_example_wardrobe())
        outfit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
