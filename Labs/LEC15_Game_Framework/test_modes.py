import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import game_framework
import game_world
import pause_mode
import play_mode
import title_mode
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_p


class ModeTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        game_framework.stack = [play_mode]
        game_framework.running = True
        play_mode.boy = SimpleNamespace(
            pressed_keys={1}, dir=1, state='RUN', idle_started_at=10.0,
            stop_run=Mock(), handle_event=Mock(), update=Mock(), draw=Mock())
        game_world.add_oject(play_mode.boy)

    def tearDown(self):
        game_world.clear()
        game_framework.stack = []
        game_framework.running = False

    def press(self, mode, key):
        event = SimpleNamespace(type=SDL_KEYDOWN, key=key)
        with patch.object(mode, 'get_events', return_value=[event]):
            mode.handle_events()

    def test_pause_toggle_preserves_world_and_stops_updates(self):
        boy = play_mode.boy
        with patch.object(play_mode, 'get_time', return_value=12.0):
            self.press(play_mode, SDLK_p)
        self.assertEqual(game_framework.stack, [play_mode, pause_mode])
        self.assertEqual(boy.pressed_keys, set())
        self.assertEqual(boy.dir, 0)
        boy.stop_run.assert_called_once()
        game_framework.stack[-1].update()
        boy.update.assert_not_called()
        with patch.object(play_mode, 'render') as render:
            pause_mode.render()
            render.assert_called_once()
        with patch.object(play_mode, 'get_time', return_value=22.0):
            self.press(pause_mode, SDLK_p)
        self.assertEqual(game_framework.stack, [play_mode])
        self.assertEqual(boy.idle_started_at, 20.0)
        self.assertIn(boy, game_world.world[1])
        play_mode.update()
        boy.update.assert_called_once()

    def test_escape_returns_to_title_and_clears_world(self):
        for paused in (False, True):
            with self.subTest(paused=paused):
                game_framework.stack = [play_mode]
                game_world.add_oject(object())
                if paused:
                    self.press(play_mode, SDLK_p)
                with patch.object(title_mode, 'init') as init:
                    self.press(game_framework.stack[-1], SDLK_ESCAPE)
                    init.assert_called_once()
                self.assertEqual(game_framework.stack, [title_mode])
                self.assertTrue(game_framework.running)
                self.assertTrue(all(not layer for layer in game_world.world))


if __name__ == '__main__':
    unittest.main()
