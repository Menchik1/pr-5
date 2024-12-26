import os
import random
import json
import csv
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

class DBase:
    def __init__(self, schema_name):
        self.schema_name = schema_name

    def generate_unique_key(self):
        alphanum = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        return ''.join(random.choice(alphanum) for _ in range(10))

    def get_second_lot_id_from_pair(self, pair_id):
        pair_file = f"{self.schema_name}/pair/1.csv"
        with open(pair_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == str(pair_id):
                    return int(row[2])  # Возвращаем second_lot_id
        return -1

    def is_valid_number(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def safe_stod(self, value):
        if not self.is_valid_number(value):
            raise ValueError(f"Некорректный формат числа: {value}")
        return float(value)

    def get_first_lot_id_from_pair(self, pair_id):
        pair_file = f"{self.schema_name}/pair/1.csv"
        with open(pair_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == str(pair_id):
                    return int(row[1])  # Возвращаем first_lot_id
        return -1

    def get_max_user_id(self, filename):
        max_id = 0
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                user_id = int(row[0])
                if user_id > max_id:
                    max_id = user_id
        return max_id

    def get_max_order_id(self, filename):
        max_id = 0
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                order_id = int(row[0])
                if order_id > max_id:
                    max_id = order_id
        return max_id

    def save_single_entry_to_csv(self, table, entry):
        filename = f"{self.schema_name}/{table}/1.csv"
        file_exists = os.path.isfile(filename)

        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                if table == "user":
                    writer.writerow(["user_id", "username", "key"])
                elif table == "lot":
                    writer.writerow(["lot_id", "name"])
                elif table == "user_lot":
                    writer.writerow(["user_id", "lot_id", "quantity"])
                elif table == "order":
                    writer.writerow(["order_id", "user_id", "pair_id", "quantity", "price", "type", "closed"])
                elif table == "pair":
                    writer.writerow(["pair_id", "first_lot_id", "second_lot_id"])

            if table == "user":
                writer.writerow([entry["user_id"], entry["username"], entry["key"]])
            elif table == "lot":
                writer.writerow([entry["lot_id"], entry["name"]])
            elif table == "user_lot":
                writer.writerow([entry["user_id"], entry["lot_id"], entry["quantity"]])
            elif table == "order":
                writer.writerow([entry["order_id"], entry["user_id"], entry["pair_id"], entry["quantity"], entry["price"], entry["type"], entry["closed"]])
            elif table == "pair":
                writer.writerow([entry["pair_id"], entry["first_lot_id"], entry["second_lot_id"]])

    def delete_order(self, order_id):
        order_file = f"{self.schema_name}/order/1.csv"
        updated_content = []
        user_id = ""
        total_cost = 0
        pair_id = -1

        with open(order_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == order_id:
                    user_id = row[1]
                    pair_id = int(row[2])
                    total_cost = float(row[3]) * float(row[4])  # Рассчитываем общую стоимость
                    closed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updated_content.append([row[0], row[1], row[2], row[3], row[4], "sell", closed_time])
                else:
                    updated_content.append(row)

        with open(order_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_content)

        second_lot_id = self.get_second_lot_id_from_pair(pair_id)
        if second_lot_id == -1:
            return

        user_lot_file = f"{self.schema_name}/user_lot/1.csv"
        updated_user_lot_content = []

        with open(user_lot_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == user_id and row[1] == str(second_lot_id):
                    current_quantity = float(row[2])
                    new_quantity = current_quantity + total_cost  # Возвращаем полную стоимость
                    updated_user_lot_content.append([user_id, str(second_lot_id), str(new_quantity)])
                else:
                    updated_user_lot_content.append(row)

        with open(user_lot_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_user_lot_content)


    def add_user(self, username, lot_data):
        new_user = {}
        user_file = f"{self.schema_name}/user/1.csv"
        max_user_id = self.get_max_user_id(user_file)
        new_user["user_id"] = str(max_user_id + 1)  # Увеличиваем на 1
        new_user["username"] = username
        new_user["key"] = self.generate_unique_key()

        self.save_single_entry_to_csv("user", new_user)

        for lot in lot_data:
            user_lot_entry = {
                "user_id": new_user["user_id"],
                "lot_id": lot["lot_id"],
                "quantity": "1000"  # Начальный баланс
            }
            self.save_single_entry_to_csv("user_lot", user_lot_entry)

        print(f"Новый пользователь успешно добавлен: {json.dumps(new_user)}")
        return new_user["user_id"], new_user["key"]  # Убедитесь, что возвращаете значения


    def generate_currency_pairs(self):
        lot_file = f"{self.schema_name}/lot/1.csv"
        lots = []

        with open(lot_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                if row:
                    lots.append(row[0])  # Сохраняем только ID лота

        pair_id = 1
        for i in range(len(lots)):
            for j in range(len(lots)):
                if i != j:  # Исключаем одинаковые пары
                    new_pair = {
                        "pair_id": str(pair_id),
                        "first_lot_id": lots[i],
                        "second_lot_id": lots[j]
                    }
                    self.save_single_entry_to_csv("pair", new_pair)
                    pair_id += 1

    def find_pair_id_by_lots(self, first_lot, second_lot):
        pair_file = f"{self.schema_name}/pair/1.csv"
        with open(pair_file, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                if row and row[1] == first_lot and row[2] == second_lot:
                    return int(row[0])  # Возвращаем pair_id
        return -1


    def get_reverse_pair_id_and_check_orders(self, pair_id, order_type, price, quantity):
        pair_file = f"{self.schema_name}/pair/1.csv"
        with open(pair_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == str(pair_id):
                    reverse_pair_id = self.find_pair_id_by_lots(row[1], row[2])
                    if reverse_pair_id != -1:
                        order_file = f"{self.schema_name}/order/1.csv"
                        with open(order_file, 'r') as order_file:
                            order_reader = csv.reader(order_file)
                            for order_row in order_reader:
                                if order_row and order_row[2] == str(reverse_pair_id) and order_row[5] != order_type:
                                    existing_quantity = float(order_row[3])
                                    existing_price = float(order_row[4])

                                    if (order_type == "buy" and existing_price <= price) or (order_type == "sell" and existing_price >= price):
                                        matched_quantity = min(quantity, existing_quantity)
                                        quantity -= matched_quantity
                                        existing_quantity -= matched_quantity

                                        if existing_quantity > 0:
                                            with open(order_file, 'a', newline='') as order_file:
                                                order_writer = csv.writer(order_file)
                                                order_writer.writerow([order_row[0], order_row[1], order_row[2], existing_quantity, order_row[4], order_row[5], order_row[6]])

                                        print(f"Ордер удовлетворён: {matched_quantity} по цене {existing_price}")

                                        if quantity <= 0:
                                            return reverse_pair_id
                    return -1
        return -1



    def create_order(self, user_id, pair_id, quantity, price, order_type):
        order_file = f"{self.schema_name}/order/1.csv"
        reverse_pair_id = self.find_pair_id_by_lots(
            str(self.get_second_lot_id_from_pair(pair_id)),
            str(self.get_first_lot_id_from_pair(pair_id))
        )

        if reverse_pair_id == -1:
            print(f"Ошибка: обратная пара для пары ID {pair_id} не найдена.")
            return

        matched_orders = []
        remaining_quantity = quantity

        with open(order_file, 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                if (
                    row
                    and int(row[2]) == reverse_pair_id  # Проверяем соответствие пары
                    and row[5] == "buy"                # Только тип "buy"
                    and not row[6]                     # Ордер еще не закрыт
                ):
                    existing_quantity = float(row[3])
                    existing_price = float(row[4])

                    # Рассчитываем обратный курс
                    reverse_price = 1 / price

                    if existing_price <= reverse_price:
                        matched_quantity = min(remaining_quantity, existing_quantity)
                        matched_orders.append({
                            "order_id": row[0],
                            "user_id": row[1],
                            "quantity": matched_quantity,
                            "price": existing_price,
                            "remaining_quantity": existing_quantity - matched_quantity
                        })
                        remaining_quantity -= matched_quantity

                        if remaining_quantity <= 0:
                            break

        # Обрабатываем найденные обратные ордера
        for matched_order in matched_orders:
            print(f"Удовлетворяется ордер ID {matched_order['order_id']} на количество {matched_order['quantity']}.")

            # Списание у пользователя, создающего новый ордер
            self.update_user_lot_balance(
                user_id,
                self.get_second_lot_id_from_pair(pair_id),  # Списание с валюты второй пары
                -matched_order["quantity"] * price
            )
            self.update_user_lot_balance(
                user_id,
                self.get_first_lot_id_from_pair(pair_id),  # добавление валюты на которую менялся
                matched_order["quantity"]
            )

            # Пополнение у владельца удовлетворяемого ордера
            self.update_user_lot_balance(
                matched_order["user_id"],
                self.get_second_lot_id_from_pair(pair_id),
                matched_order["quantity"]
            )

            # Закрываем ордер, если он полностью удовлетворен
            if matched_order["remaining_quantity"] <= 0:
                self.close_order(matched_order["order_id"])
            else:
                self.update_order_quantity(matched_order["order_id"], matched_order["remaining_quantity"])

        # Если осталась неудовлетворенная часть, создаем новый ордер
        if remaining_quantity > 0:
            total_cost = remaining_quantity * price
            new_order = {
                "order_id": str(self.get_max_order_id(order_file) + 1),
                "user_id": user_id,
                "pair_id": str(pair_id),
                "quantity": str(remaining_quantity),
                "price": str(price),
                "type": "buy",
                "closed": ""
            }
            self.save_single_entry_to_csv("order", new_order)

            # Списание остатка у пользователя, создающего новый ордер
            self.update_user_lot_balance(
                user_id,
                self.get_second_lot_id_from_pair(pair_id),
                -total_cost
            )


    def get_orders(self):
        order_file = f"{self.schema_name}/order/1.csv"
        with open(order_file, 'r') as file:
            reader = csv.reader(file)
            print("Список ордеров:")
            next(reader)  # Пропускаем заголовок
            for row in reader:
                print(', '.join(row))

    def get_lots(self):
        lot_file = f"{self.schema_name}/lot/1.csv"
        with open(lot_file, 'r') as file:
            reader = csv.reader(file)
            print("Список лотов:")
            next(reader)  # Пропускаем заголовок
            for row in reader:
                print(', '.join(row))

    def get_pairs(self):
        pair_file = f"{self.schema_name}/pair/1.csv"
        with open(pair_file, 'r') as file:
            reader = csv.reader(file)
            print("Список пар:")
            next(reader)  # Пропускаем заголовок
            for row in reader:
                print(', '.join(row))

    def get_user_assets(self, user_id):
        user_lot_file = f"{self.schema_name}/user_lot/1.csv"
        with open(user_lot_file, 'r') as file:
            reader = csv.reader(file)
            print(f"Активы пользователя с ID {user_id}:")
            next(reader)  # Пропускаем заголовок
            for row in reader:
                if row and row[0] == user_id:
                    print(f"Лот ID: {row[1]}, Количество: {row[2]}")

    def apply_order(self, user_id, order_id):
        order_file = os.path.join(self.schema_name, "order", "1.csv")
        
        # Читаем все ордера
        all_orders = []
        order_data = {}
        order_found = False

        with open(order_file, 'r', newline='') as order_stream:
            reader = csv.reader(order_stream)
            for line in reader:
                all_orders.append(line)
                if line[0] == str(order_id):
                    # Проверка на тип ордера
                    if line[5] != "buy":
                        print(f"Ошибка: ордер с ID {order_id} уже закрыт или не доступен для покупки.")
                        return
                    
                    order_data = {
                        "order_id": line[0],
                        "user_id": line[1],
                        "pair_id": line[2],
                        "quantity": line[3],
                        "price": line[4],
                        "type": "sell",  # Меняем тип на sell
                        "closed": ""  # Изначально пустое
                    }
                    order_found = True

        if not order_found:
            print(f"Ошибка: ордер с ID {order_id} не найден.")
            return

        # Вычисляем стоимость ордера
        quantity = float(order_data["quantity"])
        price = float(order_data["price"])
        total_cost = quantity

        # Получаем first_lot_id из таблицы пар
        pair_id = int(order_data["pair_id"])
        first_lot_id = self.get_first_lot_id_from_pair(pair_id)
        if first_lot_id == -1:
            print(f"Ошибка: первый лот не найден для пары ID: {pair_id}")
            return

        user_lot_file = os.path.join(self.schema_name, "user_lot", "1.csv")
        updated_content = []
        lot_updated = False

        # Проверяем наличие лота для списания
        with open(user_lot_file, 'r', newline='') as user_file:
            reader = csv.reader(user_file)
            for line in reader:
                if line[0] == str(user_id):
                    current_quantity = float(line[2])
                    # Обновляем quantity для первого лота
                    if line[1] == str(first_lot_id):
                        new_quantity = current_quantity - total_cost  # Вычитаем стоимость
                        updated_content.append([line[0], line[1], str(new_quantity)])
                        lot_updated = True
                        print(f"Обновленный quantity: {new_quantity}")
                    else:
                        updated_content.append(line)  # Оставляем без изменений
                else:
                    updated_content.append(line)  # Оставляем без изменений

        if not lot_updated:
            print(f"Ошибка: лот для пользователя с ID {user_id} не найден.")
            return

        # Записываем обновлённый баланс обратно в файл
        with open(user_lot_file, 'w', newline='') as out_file:
            writer = csv.writer(out_file)
            writer.writerows(updated_content)
            print("Баланс обновлен и записан в файл.")

        # Записываем все ордера обратно в файл
        with open(order_file, 'w', newline='') as order_out_file:
            writer = csv.writer(order_out_file)
            for order in all_orders:
                if order[0] == order_data["order_id"]:
                    # Получаем текущее время
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([
                        order_data["order_id"],
                        order[1],
                        order[2],
                        order[3],
                        order[4],
                        order_data["type"],
                        now  # Записываем текущее время в поле closed
                    ])
                else:
                    writer.writerow(order)
            print("Ордер обновлен на 'sell' и записан в файл.")

    def update_user_lot_balance(self, user_id, lot_id, quantity):
        user_lot_file = f"{self.schema_name}/user_lot/1.csv"
        updated_content = []
        lot_found = False

        with open(user_lot_file, 'r', newline='') as file:
            reader = csv.reader(file)
            for line in reader:
                if line[0] == user_id and line[1] == str(lot_id):
                    current_quantity = float(line[2])
                    new_quantity = current_quantity + quantity
                    updated_content.append([user_id, lot_id, str(new_quantity)])
                    lot_found = True
                else:
                    updated_content.append(line)

        if not lot_found:
            updated_content.append([user_id, lot_id, str(quantity)])

        with open(user_lot_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_content)

    def close_order(self, order_id):
        order_file = f"{self.schema_name}/order/1.csv"
        updated_orders = []

        with open(order_file, 'r', newline='') as file:
            reader = csv.reader(file)
            for line in reader:
                if line[0] == order_id:
                    line[5] = "sell"  # Обновляем тип на "sell"
                    line[6] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Закрываем ордер
                updated_orders.append(line)

        with open(order_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_orders)

    def update_order_quantity(self, order_id, new_quantity):
        order_file = f"{self.schema_name}/order/1.csv"
        updated_orders = []

        with open(order_file, 'r', newline='') as file:
            reader = csv.reader(file)
            for line in reader:
                if line[0] == order_id:
                    line[3] = str(new_quantity)  # Обновляем количество
                updated_orders.append(line)

        with open(order_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_orders)

    def get_user_key(self, user_id):
        user_file = os.path.join(self.schema_name, "user", "1.csv")
        with open(user_file, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            for row in reader:
                if row[0] == user_id:
                    return row[2]  # Возвращаем ключ пользователя
        return None
# Инициализация базы данных
db = DBase("Биржа")


# Flask API Routes
@app.route('/user', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    lot_data = [{"lot_id": str(idx + 1)} for idx in range(5)]  # Example lot data
    new_user = db.add_user(username, lot_data)
    return jsonify(new_user), 201


@app.route('/balance/<user_id>', methods=['GET'])
def get_user_assets(user_id):
    # Получение ключа пользователя из запроса
    data = request.get_json()
    user_key = data.get('key')

    if not user_key:
        return jsonify({"error": "User key is required"}), 400

    # Проверка ключа пользователя
    stored_key = db.get_user_key(user_id)

    # Получение активов пользователя
    assets = db.get_user_assets(user_id)
    return jsonify(assets), 200


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    pair_id = data.get('pair_id')
    quantity = float(data.get('quantity'))
    price = float(data.get('price'))
    order_type = data.get('type')
    user_key = data.get('key')

    if not all([user_id, pair_id, quantity, price, order_type, user_key]):
        return jsonify({"error": "Missing required fields"}), 400

    # Аутентификация пользователя
    stored_key = db.get_user_key(user_id)

    # Проверка обратной пары
    reverse_pair_id = db.find_pair_id_by_lots(
        str(db.get_second_lot_id_from_pair(pair_id)),
        str(db.get_first_lot_id_from_pair(pair_id))
    )

    if reverse_pair_id == -1:
        return jsonify({"error": f"Reverse pair for pair ID {pair_id} not found"}), 400

    matched_orders = []
    remaining_quantity = quantity

    order_file = os.path.join(db.schema_name, "order", "1.csv")
    with open(order_file, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader, None)  # Пропускаем заголовок
        for row in reader:
            if (
                row
                and int(row[2]) == reverse_pair_id  # Проверяем соответствие пары
                and row[5] == "buy"                # Только тип "buy"
                and not row[6]                     # Ордер еще не закрыт
            ):
                existing_quantity = float(row[3])
                existing_price = float(row[4])

                # Рассчитываем обратный курс
                reverse_price = 1 / price

                if existing_price <= reverse_price:
                    matched_quantity = min(remaining_quantity, existing_quantity)
                    matched_orders.append({
                        "order_id": row[0],
                        "user_id": row[1],
                        "quantity": matched_quantity,
                        "price": existing_price,
                        "remaining_quantity": existing_quantity - matched_quantity
                    })
                    remaining_quantity -= matched_quantity

                    if remaining_quantity <= 0:
                        break

    # Обработка найденных обратных ордеров
    for matched_order in matched_orders:
        # Списание у пользователя, создающего новый ордер
        db.update_user_lot_balance(
            user_id,
            db.get_second_lot_id_from_pair(pair_id),  # Списание с валюты второй пары
            -matched_order["quantity"] * price
        )
        db.update_user_lot_balance(
            user_id,
            db.get_first_lot_id_from_pair(pair_id),  # добавление валюты на которую менялся
            matched_order["quantity"]
        )

        # Пополнение у владельца удовлетворяемого ордера
        db.update_user_lot_balance(
            matched_order["user_id"],
            db.get_second_lot_id_from_pair(pair_id),
            matched_order["quantity"]
        )

        # Закрытие или обновление оставшейся части ордера
        if matched_order["remaining_quantity"] <= 0:
            db.close_order(matched_order["order_id"])
        else:
            db.update_order_quantity(matched_order["order_id"], matched_order["remaining_quantity"])

    # Если осталась неудовлетворенная часть, создаем новый ордер
    if remaining_quantity > 0:
        total_cost = remaining_quantity * price
        new_order = {
            "order_id": str(db.get_max_order_id(order_file) + 1),
            "user_id": user_id,
            "pair_id": str(pair_id),
            "quantity": str(remaining_quantity),
            "price": str(price),
            "type": order_type,
            "closed": ""
        }
        db.save_single_entry_to_csv("order", new_order)

        # Списание остатка у пользователя
        db.update_user_lot_balance(
            user_id,
            db.get_second_lot_id_from_pair(pair_id),
            -total_cost
        )
        return jsonify({"message": "Order created successfully", "order": new_order}), 201

    return jsonify({"message": "Order matched and executed successfully"}), 200

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    data = request.get_json()
    user_key = data.get('key')

    if not user_key:
        return jsonify({"error": "User key is required"}), 400

    # Путь к файлу ордеров
    order_file = os.path.join(db.schema_name, "order", "1.csv")
    updated_content = []
    user_id = ""
    total_cost = 0
    pair_id = -1

    # Чтение и обновление данных файла ордеров
    with open(order_file, 'r') as file:
        reader = csv.reader(file)
        header = next(reader, None)  # Пропускаем заголовок
        for row in reader:
            if row and row[0] == order_id:
                user_id = row[1]
                pair_id = int(row[2])
                total_cost = float(row[3]) * float(row[4])  # Рассчитываем общую стоимость
                closed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_content.append([row[0], row[1], row[2], row[3], row[4], "sell", closed_time])
            else:
                updated_content.append(row)

    # Проверка ключа пользователя
    stored_key = db.get_user_key(user_id)
    if not stored_key or stored_key != user_key:
        return jsonify({"error": "Invalid user key"}), 403

    # Запись обновленных данных обратно в файл ордеров
    with open(order_file, 'w', newline='') as file:
        writer = csv.writer(file)
        if header:
            writer.writerow(header)  # Записываем заголовок обратно
        writer.writerows(updated_content)

    # Получение второго лота из пары
    second_lot_id = db.get_second_lot_id_from_pair(pair_id)
    if second_lot_id == -1:
        return jsonify({"error": f"Second lot not found for pair ID: {pair_id}"}), 400

    # Обновление файла user_lot
    user_lot_file = os.path.join(db.schema_name, "user_lot", "1.csv")
    updated_user_lot_content = []

    with open(user_lot_file, 'r') as file:
        reader = csv.reader(file)
        header = next(reader, None)  # Пропускаем заголовок
        for row in reader:
            if row and row[0] == user_id and row[1] == str(second_lot_id):
                current_quantity = float(row[2])
                new_quantity = current_quantity + total_cost  # Возвращаем полную стоимость
                updated_user_lot_content.append([user_id, str(second_lot_id), str(new_quantity)])
            else:
                updated_user_lot_content.append(row)

    # Запись обновленных данных обратно в файл user_lot
    with open(user_lot_file, 'w', newline='') as file:
        writer = csv.writer(file)
        if header:
            writer.writerow(header)  # Записываем заголовок обратно
        writer.writerows(updated_user_lot_content)

    return jsonify({"message": f"Order {order_id} successfully closed and balance updated."}), 200

@app.route('/apply_order', methods=['POST'])
def apply_order():
    data = request.get_json()
    user_id = data.get('user_id')
    order_id = data.get('order_id')
    user_key = data.get('key')

    if not all([user_id, order_id, user_key]):
        return jsonify({"error": "Missing required fields"}), 400

    # Аутентификация пользователя
    stored_key = db.get_user_key(user_id)
    if not stored_key or stored_key != user_key:
        return jsonify({"error": "Invalid user key"}), 403

    order_file = os.path.join(db.schema_name, "order", "1.csv")

    # Читаем все ордера
    all_orders = []
    order_data = {}
    order_found = False

    with open(order_file, 'r', newline='') as order_stream:
        reader = csv.reader(order_stream)
        for line in reader:
            all_orders.append(line)
            if line[0] == str(order_id):
                # Проверка на тип ордера
                if line[5] != "buy":
                    return jsonify({"error": f"Order with ID {order_id} is already closed or unavailable for purchase."}), 400

                order_data = {
                    "order_id": line[0],
                    "user_id": line[1],
                    "pair_id": line[2],
                    "quantity": line[3],
                    "price": line[4],
                    "type": "sell",  # Меняем тип на sell
                    "closed": ""  # Изначально пустое
                }
                order_found = True

    if not order_found:
        return jsonify({"error": f"Order with ID {order_id} not found."}), 404

    # Вычисляем стоимость ордера
    quantity = float(order_data["quantity"])
    price = float(order_data["price"])
    total_cost = quantity

    # Получаем first_lot_id из таблицы пар
    pair_id = int(order_data["pair_id"])
    first_lot_id = db.get_first_lot_id_from_pair(pair_id)
    if first_lot_id == -1:
        return jsonify({"error": f"First lot not found for pair ID: {pair_id}"}), 400

    user_lot_file = os.path.join(db.schema_name, "user_lot", "1.csv")
    updated_content = []
    lot_updated = False

    # Проверяем наличие лота для списания
    with open(user_lot_file, 'r', newline='') as user_file:
        reader = csv.reader(user_file)
        for line in reader:
            if line[0] == str(user_id):
                current_quantity = float(line[2])
                # Обновляем quantity для первого лота
                if line[1] == str(first_lot_id):
                    new_quantity = current_quantity - total_cost  # Вычитаем стоимость
                    updated_content.append([line[0], line[1], str(new_quantity)])
                    lot_updated = True
                    print(f"Updated quantity: {new_quantity}")
                else:
                    updated_content.append(line)  # Оставляем без изменений
            else:
                updated_content.append(line)  # Оставляем без изменений

    if not lot_updated:
        return jsonify({"error": f"Lot not found for user ID {user_id}."}), 400

    # Записываем обновлённый баланс обратно в файл
    with open(user_lot_file, 'w', newline='') as out_file:
        writer = csv.writer(out_file)
        writer.writerows(updated_content)

    # Записываем все ордера обратно в файл
    with open(order_file, 'w', newline='') as order_out_file:
        writer = csv.writer(order_out_file)
        for order in all_orders:
            if order[0] == order_data["order_id"]:
                # Получаем текущее время
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    order_data["order_id"],
                    order[1],
                    order[2],
                    order[3],
                    order[4],
                    order_data["type"],
                    now  # Записываем текущее время в поле closed
                ])
            else:
                writer.writerow(order)

    return jsonify({"message": f"Order {order_id} successfully applied.", "updated_order": order_data}), 200

@app.route('/api/lots', methods=['GET'])
def get_lots():
    lots = db.get_lots()
    return jsonify(lots)

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = db.get_orders()
    return jsonify(orders), 200

@app.route('/pair', methods=['GET'])
def get_pairs():
    pairs = db.get_pairs()
    return jsonify(pairs), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7432)
