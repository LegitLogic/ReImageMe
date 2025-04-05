from flask import Flask, render_template, request, redirect, url_for
import datetime
import sqlite3

app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL,
            owner TEXT,
            department TEXT,
            received_date TEXT,
            status TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('SELECT * FROM queue ORDER BY received_date ASC')
    items = c.fetchall()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/add', methods=['POST'])
def add():
    serial = request.form['serial'].strip()
    owner = request.form['owner']
    department = request.form['department']
    status = request.form['status']
    notes = request.form['notes']
    received = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('queue.db')
    c = conn.cursor()

    # Check for existing serial in the queue (not completed)
    c.execute('SELECT * FROM queue WHERE serial_number = ? AND status != "Complete"', (serial,))
    duplicate = c.fetchone()

    if duplicate:
        c.execute('SELECT * FROM queue ORDER BY received_date ASC')
        items = c.fetchall()
        conn.close()
        return render_template('index.html', items=items,
                               warning=f"Warning: Serial number '{serial}' is already in the queue!")

    c.execute('''
        INSERT INTO queue (serial_number, owner, department, received_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (serial, owner, department, received, status, notes))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:item_id>')
def complete(item_id):
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('UPDATE queue SET status = "Complete" WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>')
def delete(item_id):
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('DELETE FROM queue WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:item_id>', methods=['GET'])
def edit(item_id):
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('SELECT * FROM queue WHERE id = ?', (item_id,))
    item = c.fetchone()
    conn.close()
    return render_template('edit.html', item=item)

@app.route('/update/<int:item_id>', methods=['POST'])
def update(item_id):
    serial = request.form['serial']
    owner = request.form['owner']
    department = request.form['department']
    status = request.form['status']
    notes = request.form['notes']

    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('''
        UPDATE queue SET serial_number = ?, owner = ?, department = ?, status = ?, notes = ? WHERE id = ?
    ''', (serial, owner, department, status, notes, item_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('serial', '').strip()

    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('SELECT * FROM queue WHERE serial_number LIKE ?', ('%' + query + '%',))
    results = c.fetchall()
    conn.close()

    return render_template('index.html', items=results, search_term=query)

@app.route('/completed')
def completed():
    conn = sqlite3.connect('queue.db')
    c = conn.cursor()
    c.execute('SELECT * FROM queue WHERE status = "Complete" ORDER BY received_date DESC')
    completed_items = c.fetchall()
    conn.close()
    return render_template('completed.html', completed=completed_items)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)