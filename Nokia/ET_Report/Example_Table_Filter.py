from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)


@app.route('/')
def index():
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Emily'],
        'age': [25, 30, 35, 40, 45],
        'gender': ['F', 'M', 'M', 'M', 'F'],
        'occupation': ['Doctor', 'Lawyer', 'Teacher', 'Engineer', 'Writer']
    }
    df = pd.DataFrame(data)
    return render_template('example_table_filter.html', data=df.to_dict('records'))


if __name__ == '__main__':
    app.run(debug=True)
