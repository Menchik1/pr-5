import os
import random
import json
import csv
from datetime import datetime

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
                    print(f"Закрытие ордера: {row}")
                else:
                    updated_content.append(row)

        with open(order_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_content)
            print("Ордера обновлены и записаны в файл.")

        second_lot_id = self.get_second_lot_id_from_pair(pair_id)
        if second_lot_id == -1:
            print(f"Ошибка: второй лот не найден для пары ID: {pair_id}")
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
                    print(f"Обновленный quantity для пользователя {user_id}: {new_quantity}")
                else:
                    updated_user_lot_content.append(row)

        with open(user_lot_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_user_lot_content)
            print("Баланс пользователя обновлен и записан в файл.")

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
            print(f"Создание нового ордера для пользователя {user_id} на сумму {total_cost}.")

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


def main():
    db = DBase("Биржа")

    if not os.path.exists(db.schema_name):
        os.makedirs(db.schema_name)

    tables = ["user", "lot", "user_lot", "order", "pair"]
    for table in tables:
        folder = f"{db.schema_name}/{table}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        # Создаем файл 1.csv для каждой таблицы, если он не существует
        file_path = os.path.join(folder, "1.csv")
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
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

    with open("schema.json", 'r') as input_file:
        data = json.load(input_file)

    for user in data["user"]["data"]:
        db.save_single_entry_to_csv("user", user)

    with open("config.json", 'r') as config_file:
        config = json.load(config_file)

        lots_from_config = config["lots"]

    for lot_id, lot_name in enumerate(lots_from_config, start=1):
        lot_entry = {"lot_id": str(lot_id), "name": lot_name}
        db.save_single_entry_to_csv("lot", lot_entry)


    db.generate_currency_pairs()

    while True:
        command = input("Введите команду (или 'exit' для выхода): ")
        if command == "exit":
            print("Выход из программы.")
            break

        parts = command.split()
        action = parts[0]

        try:
            if action == "insert":
                table = parts[1]
                if table == "user":
                    username = parts[2]
                    if username:
                        lot_data = [{"lot_id": str(idx + 1), "name": name} for idx, name in enumerate(lots_from_config)]
                        db.add_user(username, lot_data)
                    else:
                        print("Ошибка: имя пользователя не указано.")
            elif action == "assets":
                user_id = parts[1]
                db.get_user_assets(user_id)
            elif action == "orders":
                db.get_orders()
            elif action == "lots":
                db.get_lots()
            elif action == "pairs":
                db.get_pairs()
            elif action == "create":
                if parts[1] == "order":
                    user_id = parts[2]
                    pair_id = int(parts[3])
                    quantity = float(parts[4])
                    price = float(parts[5])
                    order_type = parts[6]
                    db.create_order(user_id, pair_id, quantity, price, order_type)
                else:
                    print("Ошибка: неизвестный тип создания.")
            elif action == "apply":
                user_id = int(parts[1])
                order_id = int(parts[2])
                db.apply_order(user_id, order_id)
            elif action == "delete":
                if parts[1] == "order":
                    order_id = parts[2]
                    db.delete_order(order_id)
                else:
                    print("Ошибка: неизвестный тип удаления.")
            else:
                print("Ошибка: неизвестная команда.")
        except IndexError:
            print("Ошибка: недостаточно аргументов для команды.")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()