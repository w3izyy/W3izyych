import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class BotFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = MagicMock()
        cls.bot.message_handler.side_effect = lambda **kwargs: lambda handler: handler
        cls.bot.callback_query_handler.side_effect = lambda **kwargs: lambda handler: handler

        telebot = types.ModuleType('telebot')
        telebot.TeleBot = MagicMock(return_value=cls.bot)
        telebot.types = types.SimpleNamespace(
            ReplyKeyboardRemove=MagicMock())
        qiwi = types.ModuleType('SimpleQIWI')
        qiwi.QApi = MagicMock(return_value=types.SimpleNamespace(balance=[42]))
        config = types.ModuleType('config')
        config.token = 'test-token'
        config.QIWI_TOKEN = 'test-qiwi-token'
        config.QIWI_NUMBER = 'test-number'
        config.admin_id = 99

        cls.modules = patch.dict(sys.modules, {
            'telebot': telebot, 'SimpleQIWI': qiwi, 'config': config,
        })
        cls.modules.start()
        cls.main = importlib.import_module('main')
        cls.handlers = [call.kwargs.get('content_types')
                        for call in cls.bot.message_handler.call_args_list]

    @classmethod
    def tearDownClass(cls):
        cls.modules.stop()
        sys.modules.pop('main', None)

    def setUp(self):
        self.bot.reset_mock()
        self.chat = types.SimpleNamespace(id=7)

    def test_start_and_menu_do_not_offer_unavailable_search_or_payment(self):
        self.main.send_welcome(types.SimpleNamespace(chat=self.chat))
        self.assertIn('Поиск сейчас недоступен', self.bot.send_message.call_args.args[1])
        self.assertIn('reply_markup', self.bot.send_message.call_args.kwargs)
        self.assertEqual(self.bot.send_message.call_args.kwargs['reply_markup'],
                         sys.modules['telebot'].types.ReplyKeyboardRemove.return_value)

        for text in ('🆘 Команды', '📓 Руководство', '👁 О сервисе',
                     '79998887777', '/pas password'):
            with self.subTest(text=text):
                self.bot.reset_mock()
                self.main.message(types.SimpleNamespace(chat=self.chat, text=text))
                response = self.bot.send_message.call_args.args[1]
                self.assertIn('Поиск сейчас недоступен', response)
                self.assertNotIn('https://', response)
                self.assertEqual(self.bot.send_message.call_count, 1)

    def test_account_does_not_claim_fictitious_subscription_or_stats(self):
        self.main.message(types.SimpleNamespace(chat=self.chat, text='👤 Мой аккаунт'))
        response = self.bot.send_message.call_args.args[1]
        self.assertIn('Ваш ID: 7', response)
        self.assertIn('недоступны', response)
        self.assertNotIn('0₽', response)

    def test_advertised_media_get_immediate_feedback(self):
        for content_type in ('document', 'photo', 'location', 'voice'):
            with self.subTest(content_type=content_type):
                self.assertTrue(any(content_type in kinds for kinds in self.handlers if kinds))
                self.bot.reset_mock()
                self.main.unsupported_media(types.SimpleNamespace(chat=self.chat))
                self.bot.send_message.assert_called_once_with(7, self.main.UNAVAILABLE)

    def test_old_purchase_button_does_not_issue_payment_link(self):
        self.main.step_buy(types.SimpleNamespace(id='callback', data='buying'))
        self.bot.answer_callback_query.assert_called_once_with(
            'callback', self.main.UNAVAILABLE, show_alert=True)
        self.bot.send_message.assert_not_called()

    def test_balance_does_not_expose_credentials(self):
        self.main.send_balance(types.SimpleNamespace(chat=types.SimpleNamespace(id=99)))
        response = self.bot.send_message.call_args.args[1]
        self.assertIn('42₽', response)
        self.assertNotIn('test-qiwi-token', response)
        self.bot.reset_mock()
        self.main.send_balance(types.SimpleNamespace(chat=self.chat))
        self.assertNotIn('42₽', self.bot.send_message.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
