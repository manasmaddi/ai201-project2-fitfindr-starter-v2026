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


if __name__ == '__main__':
    unittest.main()
