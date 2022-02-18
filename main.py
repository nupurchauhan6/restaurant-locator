from flask import flash, render_template, request
from app import create_app, db
from app.models import Restaurant

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def get():
    if request.method == 'POST':
        result = []
        pincode = request.form.get('pincode')
        rows = Restaurant.query.filter_by(pincode=pincode).all()
        if (len(rows) == 0):
            flash('No record found!', category='error')
        else:
            for row in rows:
                result.append({
                    'name': row.name,
                    'address': row.address,
                    'pincode': row.pincode,
                    'number': row.number,
                })
        return render_template('index.html', result=result)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        number = request.form.get('number')
        db.session.add(Restaurant(name=name, address=address,
                       pincode=pincode, number=number))
        db.session.commit()
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
