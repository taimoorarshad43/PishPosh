from unittest import TestCase
from app import app
from flask import session, jsonify

# Disable some of Flasks error behavior and disabling debugtoolbar
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class FlaskTests(TestCase):

    """Testing the functionalities of the app.py file

        Things covered:

        Does app respond with appropriate pages?

        Does app response with certain features intact?

    """
    # TODO -- write tests for every view function / feature!

    def test_app(self):
        with app.test_client() as client:
            resp = client.get('/')

            self.assertEqual(resp.status_code, 200)

    def test_words(self):
        with app.test_client() as client:
            with client.session_transaction() as change_session:
                boggle_game = Boggle()
                board = boggle_game.make_board()
                change_session['board'] = board
                
            resp = client.get(f"/guess?guess='cat'")
            self.assertIn(resp.json[0], ['ok', 'not-word'])