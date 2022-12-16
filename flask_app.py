from flask import Flask, render_template, request, flash, redirect
from core_requirements import getPointData

app = Flask(__name__)
app.config['SECRET_KEY'] = '92ef96c52a1'

@app.route('/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        src = request.form['src']
        dest = request.form['dest']
        rng = request.form['range']
        action = request.form['action']

        if action == 'getMap':
            if not src or not dest or not rng:
                flash('Input(s) missing!')
            else:
                result_data = getPointData(src, dest, float(rng))
                return redirect(result_data['url'])

        elif action == 'getCoordinates':
            if not src or not dest or not rng:
                flash('Input(s) missing!')
            else:
                result_data = getPointData(src, dest, float(rng))
                path_list = result_data['path_list'][1:-1]
                print(path_list)
                return render_template('directions.html', options=path_list)

        else:
            pass
        
    return render_template('imp.html')

if __name__ == "__main__":
    app.run()