import os
from flask import Flask, render_template, request
from models import Restaurant
from __init__ import db, create_app
import requests

app = create_app()

IS_LEADER = os.environ['IS_LEADER']
print(IS_LEADER)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def get():
    if request.method == 'POST':
        result = []
        pincode = request.form.get('pincode')
        rows = Restaurant.query.filter_by(pincode=pincode).all()
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
        data = {
            "name": name,
            "address": address,
            "pincode": pincode,
            "number": number
        }
    if IS_LEADER == "True":
        requests.post('http://rl_server2:5002/add',
                                    data=data)
        requests.post('http://rl_server3:5003/add',
                                  data=data)    
    db.session.add(
        Restaurant(name=name,
                address=address,
                pincode=pincode,
                number=number))
    db.session.commit()

    return render_template('index.html')


# @app.route('/ping')
# def ping():
    
#     data = {
#             "name": "saj",
#             "address": "address",
#             "pincode": "pincode",
#             "number": "number"
#         }
#     if IS_LEADER=="yes":
#         res=requests.post('http://rl_server3:5003/add',
#                                   data=data) 
#         # requests.post('http://rl_server3:5003/add',
#         #                           data=data)    
#     return 'Ping ... ' + res.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT'))
