from flask import Flask, render_template, request
#from flask_cors import CORS
import requests

# Инициализируем Flask приложение
app = Flask(__name__)
#CORS(app)

# URL API для получения новой колоды карт
DECK_API_URL = "https://deckofcardsapi.com/api/deck/"

# Функция для получения новой колоды карт
def get_new_deck():
    response = requests.get(f"{DECK_API_URL}new/shuffle/?deck_count=1")
    deck_data = response.json()
    return deck_data['deck_id'], deck_data['remaining']

# Функция для получения нескольких карт из колоды
def draw_cards(deck_id, count):
    response = requests.get(f"{DECK_API_URL}{deck_id}/draw/?count={count}")
    draw_data = response.json()
    return draw_data['cards'], draw_data['remaining']

# Функция для вычисления стоимости карты
def calculate_card_value(card_value):
    if card_value.isdigit():
        return int(card_value)
    elif card_value in ["KING", "QUEEN", "JACK"]:
        return 10
    elif card_value == "ACE":
        return 11
    return 0

# Главная страница с кнопкой "Начать игру"
@app.route('/')
def home():
    return render_template('index.html')

# Начало игры: получение новой колоды и раздача двух карт игроку
@app.route('/start_game', methods=['POST'])
def start_game():
    deck_id, remaining = get_new_deck()
    cards, remaining = draw_cards(deck_id, 2)
    card_values = [calculate_card_value(card["value"]) for card in cards]
    score = sum(card_values)  # Подсчитываем начальный счет игрока
    return render_template('game.html', 
                           deck_id=deck_id, 
                           cards=cards, 
                           score=score,
                           remaining=remaining,
                           player_score=score)  # Устанавливаем initial score

# Добавление новой карты к руке игрока
@app.route('/draw_card', methods=['POST'])
def draw_card():
    deck_id = request.form['deck_id']
    score = int(request.form['score'])
    cards, remaining = draw_cards(deck_id, 1)
    card_values = [calculate_card_value(card["value"]) for card in cards]
    score += sum(card_values)  # Обновляем счет игрока
    all_cards = request.form.getlist('cards') + [cards[0]['image']]
    player_score = int(request.form.get('player_score', 0))

    return render_template('game.html', 
                           deck_id=deck_id, 
                           cards=[{'image': card} for card in all_cards],
                           score=score,
                           remaining=remaining,
                           player_score=score)  # Передаем обновленный счет игрока

# Действия дилера: вытягиваем карты до тех пор, пока счет не достигнет минимум 17
@app.route('/dealer_turn', methods=['POST'])
def dealer_turn():
    deck_id = request.form['deck_id']
    player_score = int(request.form['player_score'])
    remaining = int(request.form['remaining'])
    dealer_score = 0
    cards = []

    print(f"Player Score before dealer turn: {player_score}")  # Отладочный вывод

    while dealer_score < 17 and remaining > 0:
        new_cards, remaining = draw_cards(deck_id, 1)
        cards.extend(new_cards)
        card_values = [calculate_card_value(card["value"]) for card in new_cards]
        dealer_score += sum(card_values)

        if dealer_score > 21:
            break

    dealer_cards = [{'image': card['image']} for card in cards]

    # Отображаем карты дилера и его текущий счет
    return render_template('dealer_turn.html', 
                           deck_id=deck_id, 
                           player_score=player_score, 
                           dealer_cards=dealer_cards, 
                           dealer_score=dealer_score,
                           remaining=remaining)

# Завершение игры и вывод результата
@app.route('/finish_game', methods=['POST'])
def finish_game():
    dealer_score = int(request.form['dealer_score'])
    player_score = int(request.form['player_score'])
    remaining = int(request.form['remaining'])

    print(f"Player Score: {player_score}, Dealer Score: {dealer_score}")  # Отладочный вывод

    if (dealer_score > 21 and player_score > 21):
        message = "Оба проиграли"
    elif dealer_score == player_score == 21:
        message = "Оба выиграли"
    elif dealer_score > 21 or (player_score <= 21 and player_score > dealer_score):
        message = "Игрок, ты выиграл"
    elif player_score > 21 or (dealer_score <= 21 and dealer_score > player_score):
        message = "Дилер, ты выиграл"
    else:
        message = "Игра завершена"

    return render_template('result.html',
                           message=message,
                           player_score=player_score,
                           dealer_score=dealer_score,
                           remaining=remaining)

# Запускаем Flask сервер
if __name__ == '__main__':
    app.run(debug=True)