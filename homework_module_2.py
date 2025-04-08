from collections import UserDict
import re
from datetime import datetime, timedelta
import pickle

from abc import ABC, abstractmethod

'''
Додаток, який буде працювати з книгою контактів та календарем

1) Зберігати ім'я та номер телефону
2) Знаходити номер телефону за ім'ям
3) Змінювати записаний номер телефону
4) Виводити в консоль всі записи, які збереглись

{"name": "John", "phone": "80977333967"}

'''


contacts_file = "contacts.txt"
data_file = "addressbook.pkl"

commands = """
1) add [name] [number] - to add a new contact
2) change [name] [old number] [new number] - to change contact's phone number
3) phone [name] - to print name 
4) all - will show all number from the contacts
5) add-birthday [name] [birthday] - to add birthday to a contact
6) show-birthday [name] - to show the birthday of a contact
7) birthdays - will show upcoming birthdays
8) exit - to exit the application
"""


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r'\d{10}', value):
            raise ValueError("Phone number must contain exactly 10 digits")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            self.value = value
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        if phone in [p.value for p in self.phones]:
            raise ValueError("This phone number is already added")
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Phone number not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = f", Birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, Phones: {phones}{birthday}"



class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                birthday = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                birthday_this_year = birthday.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday.replace(year=today.year + 1)
                if birthday_this_year.weekday() == 5:
                    birthday_this_year += timedelta(days=2)
                elif birthday_this_year.weekday() == 6:
                    birthday_this_year += timedelta(days=1)
                if 0 <= (birthday_this_year - today).days <= 7:
                    upcoming.append({"name": record.name.value, "birthday": birthday_this_year.strftime('%d.%m.%Y')})
        return upcoming


    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

    def save_contacts(self):
        with open(contacts_file, 'w', encoding="utf-8") as file:
            for record in self.data.values():
                phones = ";".join(p.value for p in record.phones)
                birthday = record.birthday.value.strftime('%d.%m.%Y') if record.birthday else""
                file.write(f'{record.name.value}: {phones}, {birthday}\n')

    def read_contacts(self):
        try:
            with open(contacts_file, 'r', encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(': ', 1)
                    if len(parts) != 2:
                        print(f'Skipping invalid line in contacts file: {line}')
                        continue
                    name, rest = parts
                    phones, _, birthday = rest.partition(", ")
                    record = Record(name)
                    for phone in phones.split(";"):
                        try:
                            record.add_phone(phone)
                        except ValueError:
                            print(f'Skipping invalid phone number "{phone}" for contact {name}')
                    if birthday:
                        try:
                            record.add_birthday(birthday)
                        except ValueError:
                            print(f'Skipping invalid birthday "{birthday}" for contact {name}')
                    self.add_record(record)
        except FileNotFoundError:
            open(contacts_file, 'w', encoding="utf-8").close()

def save_data(book, filename="addressbook.pkl"):
    with open(filename,"wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me a valid name and phone number please"
        except KeyError:
            return "User not found."
        except IndexError:
            return "Enter user name."
        except TypeError:
            return "Invalid command format."
    return inner

@input_error
def parse_input(user_input):
    cmd, *args = user_input.lower().split()
    return cmd, args

@input_error
def add_contact(args, book):
    name, phone = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return f"Contact {name} added/updated."

@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}"
    return "Contact not found"


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday.value}"
    return "Contact or birthday not found"

@input_error
def birthdays(book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{entry['name']}: {entry['birthday']}" for entry in upcoming) if upcoming else "No upcoming birthdays."


@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
            record.edit_phone(old_phone, new_phone)
            return f"Contact {name} updated"
    return "Contact not found"

@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    return str(record) if record else "Contact not found"

@input_error
def show_all(book):
    return str(book)

class View(ABC):
    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_commands(self, commands):
        pass

    @abstractmethod
    def get_user_input(self, prompt):
        pass


class ConsoleView(View):
    def show_message(self, message):
        print(message)

    def show_contacts(self, contacts):
        if not contacts:
            print("No contacts found.")
        else:
            for contact in contacts:
                print(contact)

    def show_commands(self, commands):
        print(commands)

    def get_user_input(self, prompt):
        return input(prompt)

def main():
    book = load_data()
    view = ConsoleView()
    #print ("Welcome to the assistant bot!")
    view.show_message("Welcome to the assistant bot!")
    view.show_commands(commands)

    while True:
        user_input = view.get_user_input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            view.show_message("Good bye!")
            break
        elif command == "hello":
            view.show_message("How can I help you?")
        elif command == "add":
            view.show_message(add_contact(args, book))
        elif command == "change":
            view.show_message(change_contact(args, book))
        elif command == "phone":
            view.show_message(show_phone(args, book))
        elif command == "all":
            view.show_contacts(book.data.values())
        elif command == "add-birthday":
            view.show_message(add_birthday(args, book))
        elif command == "show-birthday":
            view.show_message(show_birthday(args, book))
        elif command == "birthdays":
            view.show_message(birthdays(book))
        elif command == "help":
            view.show_commands(commands)
        else:
            view.show_message("Invalid command.")



if __name__ == "__main__":
    main()

