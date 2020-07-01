from flask import Flask,render_template 
import cx_Oracle

app = Flask(__name__)
conn = cx_Oracle.connect('admin2/test@//localhost:1521/xe')


@app.route("/")
def mainTable():
    cur = conn.cursor()
    cur.execute("select * from defect")
    rows = cur.fetchall()
    conn.commit()
    return render_template('index.html',datastry=rows) 

if __name__ == "__main__":
    app.run(debug=True)