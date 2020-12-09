import os
from flask import Flask, render_template, request
from beauty_search import index_sephora, search_query, get_product

app = Flask(__name__)

APP__ROOT = os.path.dirname(os.path.abspath(__file__))
stopwords = set()
inv_index = {}
norm_weights = {}
init_text = []




@app.route('/')
def index():
    return render_template('index.html')

@app.route("/init", methods=['POST'])
def initialize():
    res = index_sephora()
    init_text = [res]

    return render_template("index.html", init=init_text)

@app.route("/query", methods=['POST'])
def process_query():
    query = request.form['query']
    if not query:
        query = "n/a"
        result = []
    else:
        k = 10
        ids, scores = search_query(query, k, "details")

        result = ['{}\t {:.4f} \t {}'.format(ids[i], scores[i], get_product(ids[i])) for i in range(k)]
    return render_template("result.html", init=init_text, query=query, result=result)

if __name__ == '__main__':
    app.run(debug=True)