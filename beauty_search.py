from elasticsearch import Elasticsearch
import xmltodict
import pandas as pd



def load_data(file):
    df = pd.read_csv("./data/sephora_website_dataset.csv")
    select = ['id', 'brand', 'category', 'name', 'size', 'rating',
       'number_of_reviews', 'love', 'price', 'URL', 'details',
       'how_to_use', 'ingredients']
    df = df[select]
    df["body"] = (df.brand + " " + df.name + " "+ df.details +" "+ df.how_to_use)
    return df

def index_sephora():
    if es.indices.exists(index='sephora'):
        res = "Index 'sephora' already exists, skip indexing."
        print(res)
        return res
    for i in range(df.shape[0]):
        product_id = df.iloc[i].id
        body = {"details": df.iloc[i].body,
                "ingredients": df.iloc[i].ingredients}
        es.index(index='sephora', id=product_id, body=body)
        res = "Indexing completed."
        print(res)
        return res

def search_query(query, size, param):
    body = {
        "from":0,
        "size": size,
        "query": {
            "match": {
                param:query
            }
        }
    }

    res = es.search(index="sephora", body=body)
    print("Top", size, "results for query:", query )
    ids = []
    scores = []
    for hit in res['hits']['hits']:
        i, score = hit['_id'], hit['_score']
        product = get_product(i)
        # name = type(i)
        ids.append(i)
        scores.append(score)
        print(i, score, product, sep="\t")
        
    return ids, scores

def get_product(id):
    res = " | ".join(df[df.id==int(id)][["brand","name"]].values[0])
    return res

df = load_data("./data/sephora_website_dataset.csv")
es = Elasticsearch()

    