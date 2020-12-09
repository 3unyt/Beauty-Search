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

def index_sephora(es, df):
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

def search_query(es, df, query, size, param):
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
    print("Top", size, "results for query:", query[:100] )
    ids, scores = [], []
    for hit in res['hits']['hits']:
        i, score = hit['_id'], hit['_score']
        ids.append(i)
        scores.append(score)

        title = get_product_title(df, i)
        print(i, score, title, sep="\t")
        
    return ids, scores



def get_product_result(es, df, query, size):
    ids, scores = search_query(es, df, query, size, "details")
    result = {}
    for pid in ids:
        result[pid] = get_product_by_id(df, pid)
    return result

def get_similar_product(es, df, id):
    ingredients = df[df.id==int(id)].ingredients.values[0]
    ids, scores = search_query(es, df, ingredients, 5, "ingredients")
    result = {}
    for pid in ids:
        if pid==id: continue
        result[pid] = get_product_by_id(df, pid)
    return result



def get_product_by_id(df, id):
    product = {}
    product["brand"] = df[df.id==int(id)]["brand"].values[0]
    product["name"] = df[df.id==int(id)]["name"].values[0]
    product["price"] = "$"+str(df[df.id==int(id)].price.values[0])
    product["size"] = df[df.id==int(id)]["size"].values[0]
    product["details"] = df[df.id==int(id)].details.values[0].split(".")[0]
    product["url"] = df[df.id==int(id)].URL.values[0]
    return product

def get_product_title(df, id):
    res = " | ".join(df[df.id==int(id)][["brand","name"]].values[0])
    return res

if __name__ == "__main__":
    df = load_data("./data/sephora_website_dataset.csv")
    es = Elasticsearch()
    index_sephora(es, df)
    # search_query(es, df, "skin care for men", 10, "details")
    res = get_similar_product(es, df, 1866706)
    p = get_product_by_id(df, 1866706)
    print(p)

    