import psycopg2
from psycopg2 import Error

db_params = {
    "dbname": "4oy_6dars_db",
    "user": "postgres",
    "password": "abdulloh09",
    "host": "localhost",
    "port": "5432"
}


def create_tables():
    commands = (
        """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS authors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS book_authors (
            book_id INT REFERENCES books(id) ON DELETE CASCADE,
            author_id INT REFERENCES authors(id) ON DELETE CASCADE,
            PRIMARY KEY (book_id, author_id)
        )
        """
    )
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        print("[INFO] Jadvallar muvaffaqiyatli yaratildi yoki allaqachon mavjud.")
    except (Exception, Error) as error:
        print(f"[XATO] Jadvallarni yaratishda xatolik: {error}")
    finally:
        if conn is not None:
            conn.close()



def add_author(name):
    query = "INSERT INTO authors (name) VALUES (%s) RETURNING id;"
    conn = None
    author_id = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(query, (name,))
        author_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        print(f"[MUVAFFAQIYAT] Muallif qo'shildi: {name} (ID: {author_id})")
        return author_id
    except (Exception, Error) as error:
        print(f"[XATO] Muallif qo'shishda xatolik: {error}")
    finally:
        if conn is not None:
            conn.close()


def add_book_with_authors(title, author_ids):
    insert_book_query = "INSERT INTO books (title) VALUES (%s) RETURNING id;"
    insert_relation_query = "INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s);"

    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        cur.execute(insert_book_query, (title,))
        book_id = cur.fetchone()[0]

        for author_id in author_ids:
            cur.execute(insert_relation_query, (book_id, author_id))

        conn.commit()
        cur.close()
        print(f"[MUVAFFAQIYAT] '{title}' kitobi muvaffaqiyatli qo'shildi va mualliflarga bog'landi.")
    except (Exception, Error) as error:
        print(f"[XATO] Kitob qo'shishda xatolik: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn is not None:
            conn.close()



def get_books_by_author(author_name):
    query = """
        SELECT b.title FROM books b
        JOIN book_authors ba ON b.id = ba.book_id
        JOIN authors a ON ba.author_id = a.id
        WHERE a.name ILIKE %s;
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(query, (f"%{author_name}%",))
        rows = cur.fetchall()
        cur.close()

        print(f"\n--- '{author_name}' muallifning kitoblari ---")
        if rows:
            for row in rows:
                print(f"- {row[0]}")
        else:
            print("Hech qanday kitob topilmadi.")
    except (Exception, Error) as error:
        print(f"[XATO] Ma'lumotni o'qishda xatolik: {error}")
    finally:
        if conn is not None:
            conn.close()


def get_authors_by_book(book_title):
    query = """
        SELECT a.name FROM authors a
        JOIN book_authors ba ON a.id = ba.author_id
        JOIN books b ON ba.book_id = b.id
        WHERE b.title ILIKE %s;
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(query, (f"%{book_title}%",))
        rows = cur.fetchall()
        cur.close()

        print(f"\n--- '{book_title}' kitobining mualliflari ---")
        if rows:
            for row in rows:
                print(f"- {row[0]}")
        else:
            print("Mualliflar topilmadi.")
    except (Exception, Error) as error:
        print(f"[XATO] Ma'lumotni o'qishda xatolik: {error}")
    finally:
        if conn is not None:
            conn.close()



def delete_book(book_id):
    query = "DELETE FROM books WHERE id = %s;"
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(query, (book_id,))
        conn.commit()
        cur.close()
        print(f"[MUVAFFAQIYAT] ID: {book_id} bo'lgan kitob (va uning bog'liqliklari) o'chirildi.")
    except (Exception, Error) as error:
        print(f"[XATO] Kitobni o'chirishda xatolik: {error}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    create_tables()
    print("\n" + "=" * 40 + "\n")

    a1_id = add_author("Abdulla Qodiriy")
    a2_id = add_author("O'tkir Hoshimov")

    add_book_with_authors("O'tkan kunlar", [a1_id])
    add_book_with_authors("Dunyoning ishlari", [a2_id])
    add_book_with_authors("Adabiyot Majmuasi", [a1_id, a2_id])

    get_books_by_author("Abdulla Qodiriy")
    get_authors_by_book("Adabiyot Majmuasi")

    print("\n" + "=" * 40 + "\n")
    delete_book(1)