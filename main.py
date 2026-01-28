import arcade
from game import GameWindow


def main():
    """Главная функция"""
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()