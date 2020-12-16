import os
from flask import Flask, render_template, request
from beauty_search import load_data, index_sephora, get_product_result, get_similar_product
from elasticsearch import Elasticsearch

app = Flask(__name__)

APP__ROOT = os.path.dirname(os.path.abspath(__file__))

# global variables for flask app
es = Elasticsearch()

print("data loaded")

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/init", methods=['POST'])
def initialize():
    res = index_sephora(es)
    init_text = [res]

    return render_template("index.html", init=init_text)

@app.route("/query", methods=['POST'])
def process_query():
    query = request.form['query']
    if query:
        k = 10
        products = get_product_result(es, query, k)
        similar_products = {}
        for pid in products.keys():
            similar_products[pid] = get_similar_product(es, pid)
             
    return render_template("result.html", query=query, result={"products":products, "similar":similar_products})



if __name__ == '__main__':
    app.run(debug=True)